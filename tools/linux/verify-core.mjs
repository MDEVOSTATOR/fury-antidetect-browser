#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later
// Exercise the real patched browser with private profiles and a closed upstream.
// Run under Xvfb or a desktop session. Software GPU is an explicit QA option.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, mkdir, writeFile, open, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import net from 'node:net';

const [coreArg, agentArg, personaArg, outArg] = process.argv.slice(2);
assert(coreArg && agentArg && personaArg && outArg,
  'Usage: verify-core.mjs <core> <agent> <Linux-persona.json> <output-directory>');
const [core, agent, persona, out] = [coreArg, agentArg, personaArg, outArg].map((p) => resolve(p));
assert(process.env.DISPLAY || process.env.WAYLAND_DISPLAY, 'A display is required; use xvfb-run -a');
await mkdir(out, { recursive: true });
const root = await mkdtemp(join(tmpdir(), 'fury-core-qa-'));
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
const quote = (s) => "'" + s.replaceAll("'", "'\\''") + "'";
const wrapper = join(root, 'core');
const requireWidevine = process.env.FURY_QA_REQUIRE_WIDEVINE === '1';
const cookie = { name: 'fury_linux_qa', value: 'disposable-persistence-control' };
const gpuArgs = process.env.FURY_QA_SOFTWARE_GPU === '1'
  ? ' --use-angle=swiftshader --enable-unsafe-swiftshader' : '';
await writeFile(wrapper, `#!/bin/sh\nexec ${quote(core)}${gpuArgs} "$@"\n`, { mode: 0o700 });

async function freePort() {
  const server = net.createServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = server.address().port;
  await new Promise((done) => server.close(done));
  return port;
}

async function retry(fn, description, timeout = 60000) {
  const until = Date.now() + timeout;
  let last;
  while (Date.now() < until) {
    try { const value = await fn(); if (value) return value; } catch (error) { last = error; }
    await sleep(200);
  }
  throw new Error(`${description} timed out${last ? ': ' + last.message : ''}`);
}

async function connect(url) {
  const ws = new WebSocket(url);
  await once(ws, 'open');
  let serial = 0;
  const pending = new Map();
  ws.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    const call = pending.get(message.id);
    if (!call) return;
    pending.delete(message.id);
    clearTimeout(call.timer);
    if (message.error) call.reject(new Error(JSON.stringify(message.error)));
    else call.resolve(message.result);
  });
  const send = (method, params = {}) => new Promise((resolveCall, reject) => {
    const id = ++serial;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`${method} timed out`)); }, 45000);
    pending.set(id, { resolve: resolveCall, reject, timer });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return {
    send,
    async evaluate(expression) {
      // Do not Runtime.enable: attaching CDP and enabling console events are
      // distinct actions, and the latter changes console timing.
      const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
      assert(!r.exceptionDetails, JSON.stringify(r.exceptionDetails));
      return r.result.value;
    },
    close() { ws.close(); },
  };
}

async function capture(seed, label = String(seed)) {
  const port = await freePort();
  const log = await open(join(out, `seed-${label}.log`), 'w', 0o600);
  const child = spawn(agent, ['launch', persona, '--core', wrapper, '--seed', String(seed),
    '--proxy', 'http://127.0.0.1:9', '--country', 'US', '--timezone', 'America/New_York',
    '--profile-dir', join(root, `profile-${seed}`), '--debug-port', String(port)], {
    detached: true,
    env: { ...process.env, FURY_HOME: join(root, `home-${seed}`), FURY_CORE: core },
    stdio: ['ignore', log.fd, log.fd],
  });
  let cdp;
  try {
    const page = await retry(async () => {
      assert(child.exitCode === null, `Agent exited; see seed-${seed}.log`);
      const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      return pages.find((p) => p.type === 'page' && p.webSocketDebuggerUrl);
    }, 'Browser startup');
    cdp = await connect(page.webSocketDebuggerUrl);
    const probe = await retry(() => cdp.evaluate("document.querySelector('a[href*=\"/probe/\"]')?.href"), 'Local probe link');
    if (label === '73-restarted') {
      const { cookies } = await cdp.send('Network.getCookies', { urls: [probe] });
      assert(cookies.some((c) => c.name === cookie.name && c.value === cookie.value),
        'Cookie was lost after closing and reopening the same profile');
    } else if (seed === 73) {
      const saved = await cdp.send('Network.setCookie', {
        ...cookie, url: probe, path: '/', expires: Math.floor(Date.now() / 1000) + 86400,
      });
      assert.equal(saved.success, true, 'Could not write a persistence control cookie');
    }
    await cdp.send('Page.navigate', { url: 'chrome://sandbox' });
    const sandbox = await retry(async () => {
      const text = await cdp.evaluate('document.body.innerText');
      return text?.includes('Seccomp') && text;
    }, 'Sandbox status');
    await writeFile(join(out, `sandbox-${label}.txt`), sandbox);
    assert.match(sandbox, /Seccomp-BPF sandbox\s+Yes/, 'Seccomp sandbox is not active');
    await cdp.send('Page.navigate', { url: probe });
    await retry(() => cdp.evaluate("typeof furyProbe === 'function'"), 'Probe script');
    const first = await cdp.evaluate('furyProbe()');
    const second = await cdp.evaluate('furyProbe()');
    for (const [index, dump] of [first, second].entries()) {
      await writeFile(join(out, `seed-${label}-run-${index + 1}.json`), JSON.stringify(dump, null, 2), { mode: 0o600 });
      assert.equal(dump.navigator.platform, 'Linux x86_64');
      assert.equal(dump.clientHints.platform, 'Linux');
      assert.equal(dump.navigator.webdriver, false);
      assert.equal(dump.crossContext.consistent, true, JSON.stringify(dump.crossContext.disagreements));
      assert.equal(dump.canvas2d.stableAcrossCalls, true);
      if (requireWidevine) assert.equal(dump.drm['com.widevine.alpha'].available, true,
        'The locally installed Widevine CDM did not load');
    }
    assert.equal(first.canvas2d.toDataURL, second.canvas2d.toDataURL, 'Canvas changed in one profile');
    return first.canvas2d.toDataURL;
  } finally {
    if (cdp) {
      // Browser.close flushes profile storage; session-ending signals do not
      // exercise the close/reopen behavior a desktop user expects.
      try { await cdp.send('Browser.close'); } catch {}
      cdp.close();
    }
    if (child.exitCode === null) await Promise.race([once(child, 'exit'), sleep(3000)]);
    try { process.kill(-child.pid, 'SIGTERM'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
    if (child.exitCode === null) await Promise.race([once(child, 'exit'), sleep(3000)]);
    try { process.kill(-child.pid, 'SIGKILL'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
    await log.close();
  }
}

try {
  const first = await capture(73);
  const second = await capture(74);
  assert.notEqual(first, second, 'Different profile seeds produced the same Canvas');
  const restarted = await capture(73, '73-restarted');
  assert.equal(first, restarted, 'Canvas changed after restarting the same profile');
  const result = { ok: true, softwareGpu: Boolean(gpuArgs), widevineRequired: requireWidevine,
    checks: ['sandboxed browser launch', 'Linux platform and Client Hints', 'native webdriver=false',
      'cross-context consistency', 'stable Canvas per profile and restart', 'different Canvas across seeds',
      'cookie persistence across browser restart', ...(requireWidevine ? ['locally staged Widevine'] : [])] };
  await writeFile(join(out, 'SUMMARY.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally {
  await rm(root, { recursive: true, force: true });
}

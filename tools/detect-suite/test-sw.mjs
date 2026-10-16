// Verify the generated worker's event reply and template literal semantics.
// SPDX-License-Identifier: AGPL-3.0-or-later
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const probe = await readFile(new URL('probe.js', import.meta.url), 'utf8');
const literal = probe.match(/const WORKER_PROBE_SRC = (`[\s\S]*?`);/)[1];
const dedicatedSource = vm.runInNewContext(literal);
const serviceSource = await readFile(new URL('sw-probe.js', import.meta.url), 'utf8');

async function run(source, serviceWorker) {
  const messages = [];
  const text = [];
  const self = { postMessage: (value) => messages.push(value) };
  class Canvas {
    getContext(kind) {
      if (kind !== '2d') return null;
      return { fillRect() {}, fillText(value) { text.push(value); },
        getImageData() { return { data: new Uint8Array(4) }; } };
    }
  }
  vm.runInNewContext(source, { self, navigator: { platform: 'Linux x86_64' }, OffscreenCanvas: Canvas });
  // No MessagePort: this exercises the previously recursive fallback branch.
  await self.onmessage(serviceWorker ? { data: 'go' } : undefined);
  assert.equal(messages.length, 1);
  assert.equal(messages[0].platform, 'Linux x86_64');
  return text;
}
const dedicatedText = await run(dedicatedSource, false);
const serviceText = await run(serviceSource, true);
assert.deepEqual(dedicatedText, ['Fury <canvas> 1.0 ASCII control']);
assert.deepEqual(serviceText, dedicatedText);
console.log('Worker source and generated ServiceWorker use identical text; no-port reply works');

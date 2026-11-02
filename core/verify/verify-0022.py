#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""CSS system colours must follow a Windows persona on a non-Windows host.

Uses a private loopback fixture, real style resolution and canvas paint, with
native/Linux controls, same-origin and cross-site frames, a new tab and restart.
Dark and forced-colours results must retain the native Chromium behaviour.

Usage: verify-0022.py <core binary> [private output directory]
"""
import http.server
import json
import os
from pathlib import Path
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import Claims, launch

CORE = sys.argv[1]
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else None
NAMES = ["ActiveText", "LinkText", "VisitedText", "Highlight", "GrayText",
         "ButtonFace", "Scrollbar", "Canvas", "CanvasText", "HighlightText"]
WINDOWS_LIGHT = {
    "ActiveText": "rgb(0, 102, 204)",
    "LinkText": "rgb(0, 102, 204)",
    "VisitedText": "rgb(0, 102, 204)",
    "Highlight": "rgb(0, 120, 215)",
    "GrayText": "rgb(109, 109, 109)",
    "ButtonFace": "rgb(240, 240, 240)",
    # The legacy CSS keyword aliases Canvas, not kColorCssSystemScrollbar.
    "Scrollbar": "rgb(255, 255, 255)",
}
SCRIPT = """
function palette(doc) {
  const win = doc.defaultView;
  const out = {platform: win.navigator.platform, light: {}, dark: {}, paint: {}};
  for (const scheme of ['light', 'dark']) {
    for (const name of NAMES) {
      const el = doc.createElement('div');
      el.style.setProperty('color-scheme', scheme, 'important');
      el.style.setProperty('color', name, 'important');
      doc.body.append(el);
      out[scheme][name] = win.getComputedStyle(el).color;
      el.remove();
    }
    const canvas = doc.createElement('canvas');
    canvas.width = canvas.height = 4;
    canvas.style.colorScheme = scheme;
    doc.body.append(canvas);
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'ActiveText';
    ctx.fillRect(0, 0, 4, 4);
    out.paint[scheme] = Array.from(ctx.getImageData(1, 1, 1, 1).data);
    canvas.remove();
  }
  return out;
}
async function snapshot() {
  document.querySelectorAll('iframe').forEach(f => f.remove());
  const main = palette(document);
  const same = document.createElement('iframe');
  const loaded = new Promise(r => same.onload = r);
  same.srcdoc = '<!doctype html><body></body>';
  document.body.append(same);
  await loaded;
  const sameOrigin = palette(same.contentDocument);
  const cross = document.createElement('iframe');
  const other = new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      window.removeEventListener('message', receive);
      reject(new Error('Cross-site palette timed out'));
    }, 10000);
    function receive(event) {
      if (event.source !== cross.contentWindow || event.origin !== CROSS_ORIGIN ||
          event.data?.kind !== 'fury-colours') return;
      clearTimeout(timer);
      window.removeEventListener('message', receive);
      resolve(event.data.value);
    }
    window.addEventListener('message', receive);
  });
  cross.src = CROSS_ORIGIN + '/frame';
  document.body.append(cross);
  return {main, sameOrigin, crossSite: await other};
}
if (location.pathname === '/frame') {
  parent.postMessage({kind: 'fury-colours', value: palette(document)}, PARENT_ORIGIN);
}
"""


class Pages(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        script = ("const NAMES = " + json.dumps(NAMES) + ";\n"
                  + "const CROSS_ORIGIN = " + json.dumps(CROSS_ORIGIN) + ";\n"
                  + "const PARENT_ORIGIN = " + json.dumps(URL.rstrip("/")) + ";\n"
                  + SCRIPT)
        body = ("<!doctype html><meta charset=utf-8><title>Private colour fixture</title>"
                "<body><script>" + script + "</script></body>").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Pages)
URL = f"http://127.0.0.1:{server.server_port}/"
CROSS_ORIGIN = f"http://localhost:{server.server_port}"
threading.Thread(target=server.serve_forever, daemon=True).start()


def evaluate_tab(session, expression):
    result = session.ws.call("Runtime.evaluate", {
        "expression": expression, "returnByValue": True, "awaitPromise": True,
        "timeout": 20000,
    }, session=session.session)
    assert "exceptionDetails" not in result, result.get("exceptionDetails")
    return result["result"]["value"]


def capture(config):
    with launch(CORE, config, page=URL) as session:
        # All four maps are tested independently of the desktop theme.
        def media(scheme, forced):
            session.ws.call("Emulation.setEmulatedMedia", {"features": [
                {"name": "prefers-color-scheme", "value": scheme},
                {"name": "forced-colors", "value": forced},
            ]}, session=session.session)

        media("light", "none")
        normal = evaluate_tab(session, "snapshot()")
        targets = session.ws.call("Target.getTargets")["targetInfos"]
        oopif = any(t["type"] == "iframe" and t["url"].startswith(CROSS_ORIGIN)
                    for t in targets)
        media("dark", "none")
        dark_preference = evaluate_tab(session, "palette(document)")
        forced = {}
        for scheme in ("light", "dark"):
            media(scheme, "active")
            forced[scheme] = evaluate_tab(session, """({
                enabled: matchMedia('(forced-colors: active)').matches,
                palette: palette(document)
            })""")
        media("light", "none")
        # A new WebContents must receive the same colour maps.
        target = session.ws.call("Target.createTarget", {"url": URL})["targetId"]
        tab = session.ws.call("Target.attachToTarget", {
            "targetId": target, "flatten": True,
        })["sessionId"]
        result = session.ws.call("Runtime.evaluate", {
            "expression": "new Promise((resolve,reject) => { const start=Date.now();"
                          "const wait=()=>typeof palette==='function' ? resolve(palette(document))"
                          ": Date.now()-start>10000 ? reject(Error('New tab timed out'))"
                          ": setTimeout(wait,50);wait();})",
            "returnByValue": True, "awaitPromise": True, "timeout": 15000,
        }, session=tab)
        assert "exceptionDetails" not in result, result.get("exceptionDetails")
        new_tab = result["result"]["value"]
        return {"normal": normal, "oopif": oopif, "darkPreference": dark_preference,
                "forced": forced, "newTab": new_tab}


def main():
    claims = Claims("0022 — persona CSS system colours", CORE)
    results = {}
    try:
        for label, config in [
            ("native", None),
            ("linux", {"navigator": {"platform": "Linux x86_64"}}),
            ("windows", {"navigator": {"platform": "Win32"}}),
            ("windows-restarted", {"navigator": {"platform": "Win32"}}),
        ]:
            results[label] = capture(config)
            print(label, "ActiveText light:",
                  results[label]["normal"]["main"]["light"]["ActiveText"])
        if OUT:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "colours.json").write_text(json.dumps(results, indent=2) + "\n")
        native, linux, windows = (results[x] for x in ("native", "linux", "windows"))
        claims.control(native["normal"]["main"]["light"]["ActiveText"]
                       != WINDOWS_LIGHT["ActiveText"],
                       "native host differs from the Windows light palette")
        for label, result in results.items():
            claims.check(result["oopif"], f"{label}: cross-site frame is a separate target")
            for scheme in ("light", "dark"):
                claims.check(result["forced"][scheme]["enabled"],
                             f"{label}: forced-colours {scheme} control is actually enabled")
        for context in ("main", "sameOrigin", "crossSite"):
            claims.check(linux["normal"][context]["light"] == native["normal"][context]["light"],
                         f"{context}: Linux light colours remain native")
            claims.check(linux["normal"][context]["dark"] == native["normal"][context]["dark"],
                         f"{context}: Linux dark colours remain native")
            for name, value in WINDOWS_LIGHT.items():
                claims.check(windows["normal"][context]["light"][name] == value,
                             f"{context}: Windows light {name} = {value}")
            claims.check(windows["normal"][context]["paint"]["light"] == [0, 102, 204, 255],
                         f"{context}: canvas really paints the Windows ActiveText colour")
            claims.check(windows["normal"][context]["dark"] == native["normal"][context]["dark"],
                         f"{context}: Windows dark palette retains native defaults")
        for label in ("linux", "windows"):
            for scheme in ("light", "dark"):
                actual = results[label]["forced"][scheme]["palette"]
                expected = native["forced"][scheme]["palette"]
                claims.check(actual["light"] == expected["light"] and actual["dark"] == expected["dark"],
                             f"{label}: forced-colours {scheme} retains the native palette")
        claims.check(windows["darkPreference"]["light"] == windows["normal"]["main"]["light"],
                     "explicit light colours work even with a dark preference")
        claims.check(windows["newTab"]["light"] == windows["normal"]["main"]["light"],
                     "a new tab receives the same Windows light palette")
        claims.check(results["windows-restarted"]["normal"] == windows["normal"],
                     "Windows colours agree after a new browser session")
        return claims.done()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    sys.exit(main())

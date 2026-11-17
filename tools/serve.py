#!/usr/bin/env python3
"""Live-reloading preview of the slides.

Serves _slides/ over HTTP, watches the deck sources, rebuilds with ./build.sh
on every change and tells open browser tabs to reload (staying on the current
slide). Build errors are shown as an overlay in the browser.

Usage: python3 tools/serve.py [--port 8000]
"""
import argparse
import functools
import http.server
import json
import os
import subprocess
import sys
import threading
import time

DECK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DECK, "_slides")
WATCH_FILES = ["Main.lean", "lakefile.lean", "tools/figures.py"]
WATCH_DIRS = ["static", "Slides"]
WATCH_GLOB_TOP = (".lean",)

CLIENT_JS = r"""
<script>
(() => {
  const key = 'live-reload-indices';
  try {
    const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (saved) {
      sessionStorage.removeItem(key);
      const go = () => Reveal.slide(saved.h, saved.v, saved.f);
      if (window.Reveal?.isReady()) go(); else window.addEventListener('load', () => Reveal.on('ready', go));
    }
  } catch {}
  let overlay;
  const show = text => {
    if (!overlay) {
      overlay = document.createElement('pre');
      overlay.style.cssText = 'position:fixed;inset:2vh 2vw auto;max-height:90vh;overflow:auto;z-index:9999;' +
        'background:#fff1f2;color:#881337;border:2px solid #e11d48;padding:1em;font-size:14px;white-space:pre-wrap';
      document.body.append(overlay);
    }
    overlay.textContent = text;
  };
  const source = new EventSource('/__live');
  source.addEventListener('building', () => { document.title = '⏳ ' + document.title.replace(/^⏳ /, ''); });
  source.addEventListener('error-build', e => { document.title = document.title.replace(/^⏳ /, ''); show(JSON.parse(e.data)); });
  source.addEventListener('reload', () => {
    try { sessionStorage.setItem(key, JSON.stringify(Reveal.getIndices())); } catch {}
    location.reload();
  });
})();
</script>
"""


class State:
    def __init__(self):
        self.cond = threading.Condition()
        self.generation = 0
        self.event = None  # (name, data)

    def publish(self, name, data=""):
        with self.cond:
            self.generation += 1
            self.event = (name, data)
            self.cond.notify_all()


STATE = State()


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/__live":
            return self.live()
        if path in ("/", "/index.html"):
            try:
                with open(os.path.join(OUT, "index.html"), encoding="utf-8") as f:
                    html = f.read()
            except FileNotFoundError:
                html = "<html><head><title>Building…</title></head><body><p>No build yet.</p></body></html>"
            html = html.replace("</body>", CLIENT_JS + "</body>")
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def live(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        with STATE.cond:
            seen = STATE.generation
        try:
            while True:
                with STATE.cond:
                    STATE.cond.wait_for(lambda: STATE.generation != seen, timeout=15)
                    if STATE.generation == seen:
                        event = None
                    else:
                        seen = STATE.generation
                        event = STATE.event
                if event is None:
                    self.wfile.write(b": ping\n\n")
                else:
                    name, data = event
                    self.wfile.write(f"event: {name}\ndata: {json.dumps(data)}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def snapshot():
    mtimes = {}
    paths = [os.path.join(DECK, f) for f in WATCH_FILES]
    paths += [os.path.join(DECK, f) for f in os.listdir(DECK) if f.endswith(WATCH_GLOB_TOP)]
    for d in WATCH_DIRS:
        for root, _, files in os.walk(os.path.join(DECK, d)):
            paths += [os.path.join(root, f) for f in files]
    for p in paths:
        try:
            mtimes[p] = os.stat(p).st_mtime_ns
        except FileNotFoundError:
            pass
    return mtimes


def build():
    STATE.publish("building")
    print(time.strftime("[%H:%M:%S]"), "building…", flush=True)
    start = time.time()
    proc = subprocess.run(["./build.sh"], cwd=DECK, capture_output=True, text=True)
    output = proc.stdout + proc.stderr
    if proc.returncode == 0:
        print(time.strftime("[%H:%M:%S]"), f"built in {time.time() - start:.1f}s, reloading", flush=True)
        STATE.publish("reload")
    else:
        print(output, file=sys.stderr, flush=True)
        print(time.strftime("[%H:%M:%S]"), "build FAILED", flush=True)
        STATE.publish("error-build", output[-20000:])


def watch():
    last = snapshot()
    build()
    while True:
        time.sleep(0.5)
        current = snapshot()
        if current != last:
            # Let editors finish writing (e.g. save-all) before building.
            time.sleep(0.3)
            last = snapshot()
            build()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    threading.Thread(target=watch, daemon=True).start()
    handler = functools.partial(Handler, directory=OUT)
    server = http.server.ThreadingHTTPServer((args.bind, args.port), handler)
    server.daemon_threads = True
    print(f"Serving slides on http://{args.bind}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin.
# Copyright (c) 2026 The_Mead_Maker & Odin. MIT License, see LICENSE. Keep this notice.
"""Asgard Theme Studio.exe entry point (windowed, no console). Python standard library only.

- Serves the Studio page from this folder on http://127.0.0.1:<port>/ (this PC only) and opens it as an app window in
  Brave, else Google Chrome (each with its own small profile in the settings folder), else the default browser.
  Microsoft Edge is never picked by this program.
- Works offline: the page loads only its own files (a Content-Security-Policy blocks everything else).
- Saves themes to Documents\\Asgard Themes. "Use in Asgard" talks to Asgard on 127.0.0.1:8777 if it is running.
- Closes itself about a minute after the Studio window is closed (the page pings every 10 seconds).
- Single instance: if the Studio already runs, a second start just opens another window on it.
Test-only overrides: STUDIO_PORT, STUDIO_NO_BROWSER=1, STUDIO_THEMES_DIR, STUDIO_DATA_DIR, STUDIO_ASGARD_URL, STUDIO_IDLE_EXIT (seconds).
"""
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
sys.path.insert(0, BASE)
import theme_check  # noqa: E402

APP = "asgard-theme-studio"
VERSION = "1.0.0"
CREDIT = "Created November 22, 2026 by The_Mead_Maker & Odin"
PREFERRED_PORT = 8791
ASGARD_URL = os.environ.get("STUDIO_ASGARD_URL", "http://127.0.0.1:8777").rstrip("/")
STATIC = os.path.join(BASE, "static")
FILES = {  # the only files the page may load
    "/": "index.html", "/index.html": "index.html", "/studio.css": "studio.css", "/studio.js": "studio.js", "/starters.js": "starters.js",
    "/theme-kit.js": "theme-kit.js", "/theme-kit.css": "theme-kit.css", "/preview.html": "preview.html", "/preview.css": "preview.css",
    "/preview.js": "preview.js", "/studio-icon.svg": "studio-icon.svg",
}
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".svg": "image/svg+xml"}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; "
       "connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'")
MAX_BODY = theme_check.FILE_BYTES + 4096

state = {"port": 0, "last_ping": 0.0, "bye_at": 0.0, "started": time.time()}


def data_dir():
    env = os.environ.get("STUDIO_DATA_DIR", "").strip()
    if env:
        return os.path.abspath(env)
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        return os.path.join(os.environ["APPDATA"], "Asgard Theme Studio")
    return os.path.join(os.path.expanduser("~"), ".asgard-theme-studio")


def documents_dir():
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:  # CSIDL_PERSONAL (follows OneDrive moves)
                return buf.value
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def themes_dir():
    env = os.environ.get("STUDIO_THEMES_DIR", "").strip()
    return os.path.abspath(env) if env else os.path.join(documents_dir(), "Asgard Themes")


def safe_file_name(name):
    stem = re.sub(r"[^a-z0-9]+", "-", str(name or "").lower().replace(".asgard-theme", "")).strip("-")[:40] or "my-theme"
    return stem + ".asgard-theme"


def browser_exe():
    """Brave, else Chrome, else None (then the default browser is used). Never Microsoft Edge."""
    roots = [os.environ.get(k, "") for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    for rel in (("BraveSoftware", "Brave-Browser", "Application", "brave.exe"), ("Google", "Chrome", "Application", "chrome.exe")):
        for r in roots:
            p = os.path.join(r, *rel) if r else ""
            if p and os.path.isfile(p) and "msedge" not in p.lower():
                return p
    return None


def open_window(url):
    if os.environ.get("STUDIO_NO_BROWSER"):
        return
    exe = browser_exe()
    if exe:
        prof = os.path.join(data_dir(), "window")
        try:
            subprocess.Popen([exe, "--app=" + url, "--user-data-dir=" + prof, "--no-first-run", "--no-default-browser-check",
                              "--disable-session-crashed-bubble", "--window-size=1440,900"], shell=False)
            return
        except OSError:
            pass
    webbrowser.open(url)


class ApiError(Exception):
    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message


def asgard_call(path, body=None, timeout=3):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(ASGARD_URL + path, data=data, method="GET" if body is None else "POST",
                                 headers={"Content-Type": "application/json", "X-Asgard-Studio": "1", "User-Agent": "AsgardThemeStudio/" + VERSION})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read(65536).decode("utf-8"))


def asgard_status():
    try:
        urllib.request.urlopen(ASGARD_URL + "/", timeout=1.5).read(64)
    except Exception:
        return {"ok": True, "running": False, "inbox": False}
    try:
        j = asgard_call("/api/themes/inbox", timeout=2)
        return {"ok": True, "running": True, "inbox": bool(j.get("ok") and j.get("accepts", 0) >= 2)}
    except Exception:
        return {"ok": True, "running": True, "inbox": False}


class Handler(BaseHTTPRequestHandler):
    server_version = "AsgardThemeStudio/" + VERSION
    sys_version = ""

    def log_message(self, fmt, *args):
        pass

    def allowed_host(self):
        h = (self.headers.get("Host") or "").lower()
        return h in ("127.0.0.1:%d" % state["port"], "localhost:%d" % state["port"])

    def same_origin(self):
        o = self.headers.get("Origin")
        if o is not None and o.lower() not in ("http://127.0.0.1:%d" % state["port"], "http://localhost:%d" % state["port"]):
            return False
        return (self.headers.get("Sec-Fetch-Site") or "").lower() in ("", "same-origin", "none")

    def send(self, status, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed_host() or self.client_address[0] not in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
            return self.send(403, {"ok": False, "message": "This page only opens on this PC."})
        path = self.path.split("?", 1)[0]
        if path == "/api/hello":
            return self.send(200, {"ok": True, "app": APP, "version": VERSION})
        if path.startswith("/api/"):
            if not self.same_origin():
                return self.send(403, {"ok": False, "message": "Not allowed."})
            if path == "/api/asgard":
                return self.send(200, asgard_status())
            return self.send(404, {"ok": False, "message": "Unknown request."})
        name = FILES.get(path)
        if not name:
            return self.send(404, b"Not found", "text/plain; charset=utf-8")
        try:
            with open(os.path.join(STATIC, name), "rb") as f:
                body = f.read()
        except OSError:
            return self.send(404, b"Not found", "text/plain; charset=utf-8")
        return self.send(200, body, TYPES.get(os.path.splitext(name)[1], "application/octet-stream"))

    def read_body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n < 0 or n > MAX_BODY:
            raise ApiError(413, "That theme is too big (the limit is 1.5 MB).")
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        try:
            d = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "That request wasn't readable.")
        if not isinstance(d, dict):
            raise ApiError(400, "That request wasn't readable.")
        return d

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if not self.allowed_host() or self.client_address[0] not in ("127.0.0.1", "::1", "::ffff:127.0.0.1") or not self.same_origin():
            return self.send(403, {"ok": False, "message": "Not allowed."})
        if path == "/api/bye":  # the window is closing (sendBeacon can't add headers)
            state["bye_at"] = time.time()
            return self.send(200, {"ok": True})
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if self.headers.get("X-Studio") != "1" or ctype != "application/json":
            return self.send(403, {"ok": False, "message": "Not allowed."})
        try:
            body = self.read_body()
            if path == "/api/ping":
                state["last_ping"] = time.time()
                state["bye_at"] = 0.0
                return self.send(200, {"ok": True})
            if path == "/api/save":
                return self.send(200, self.save(body))
            if path == "/api/show":
                return self.send(200, self.show(body))
            if path == "/api/asgard/send":
                return self.send(200, self.send_to_asgard(body))
            return self.send(404, {"ok": False, "message": "Unknown request."})
        except ApiError as exc:
            return self.send(exc.status, {"ok": False, "message": exc.message})
        except Exception as exc:  # keep running on surprises
            print("error:", repr(exc))
            return self.send(500, {"ok": False, "message": "Something went wrong: %s" % exc})

    @staticmethod
    def checked_text(body):
        text = body.get("text")
        if not isinstance(text, str):
            raise ApiError(400, "No theme was sent.")
        theme, _warn, err = theme_check.check(text)
        if err:
            raise ApiError(400, err)
        return text, theme

    def save(self, body):
        text, _theme = self.checked_text(body)
        d = themes_dir()
        os.makedirs(d, exist_ok=True)
        fn = safe_file_name(body.get("file"))
        p = os.path.join(d, fn)
        if os.path.exists(p) and not body.get("overwrite"):
            return {"ok": True, "exists": True, "file": fn}
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, p)
        return {"ok": True, "path": p, "file": fn, "dir": d}

    def show(self, body):
        fn = safe_file_name(body.get("file"))
        p = os.path.join(themes_dir(), fn)
        if sys.platform == "win32" and os.path.isfile(p):
            subprocess.Popen(["explorer.exe", "/select,", p], shell=False)
        return {"ok": True}

    def send_to_asgard(self, body):
        text, theme = self.checked_text(body)
        try:
            j = asgard_call("/api/themes/inbox", {"text": text}, timeout=6)
        except urllib.error.HTTPError as exc:
            try:
                msg = json.loads(exc.read(4096).decode("utf-8")).get("message")
            except Exception:
                msg = None
            raise ApiError(502, msg or "Asgard said no (error %d)." % exc.code)
        except Exception:
            raise ApiError(502, "Asgard didn't answer. Is it still open?")
        if not j.get("ok"):
            raise ApiError(502, j.get("message") or "Asgard couldn't take the theme.")
        return {"ok": True, "name": theme["name"]}


def studio_alive(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/hello" % port, timeout=1.5) as r:
            return json.loads(r.read(500).decode("utf-8")).get("app") == APP
    except Exception:
        return False


def pick_port():
    env = int(os.environ.get("STUDIO_PORT") or 0)
    for port in ([env] if env else [PREFERRED_PORT, PREFERRED_PORT + 1, PREFERRED_PORT + 2, 0]):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            return s.getsockname()[1]
        except OSError:
            continue
        finally:
            s.close()
    return 0


def main():
    home = data_dir()
    os.makedirs(home, exist_ok=True)
    if getattr(sys, "frozen", False) or sys.stdout is None:
        try:  # windowed exe: keep a tiny log (never holds theme contents)
            log = open(os.path.join(home, "studio.log"), "a", encoding="utf-8", buffering=1)
            sys.stdout = sys.stderr = log
        except OSError:
            pass
    port0 = int(os.environ.get("STUDIO_PORT") or PREFERRED_PORT)
    if studio_alive(port0):  # already open: just show another window
        open_window("http://127.0.0.1:%d/" % port0)
        return
    port = pick_port()
    state["port"] = port
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    url = "http://127.0.0.1:%d/" % port
    print("%s Asgard Theme Studio %s on %s (%s)" % (time.strftime("%Y-%m-%d %H:%M:%S"), VERSION, url, CREDIT))
    idle = int(os.environ.get("STUDIO_IDLE_EXIT") or 75)

    def watchdog():
        while True:
            time.sleep(2)
            now = time.time()
            if state["bye_at"] and now - state["bye_at"] > 8 and state["last_ping"] < state["bye_at"]:
                break  # window closed (and not reloaded)
            if state["last_ping"] and now - state["last_ping"] > idle:
                break  # no window for a while
            if not state["last_ping"] and now - state["started"] > max(idle, 180):
                break  # the window never opened
        print("Studio window closed; stopping.")
        httpd.shutdown()
    if idle > 0:
        threading.Thread(target=watchdog, daemon=True).start()
    threading.Timer(0.3, open_window, args=(url,)).start()
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()

# Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
"""Fails (exit 1) if a built Studio folder (or the source tree) contains personal data, keys or private words.
Same idea as Asgard's release_check.py. Text files get the full scan; binaries get a scan for this PC's user name and the
private words. Optional private-words.txt (one word per line, never committed) next to this file or in the parent folder."""
import fnmatch
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "."
here = os.path.dirname(os.path.abspath(__file__))
DENY = ("config*.json", "*session*.json", "*state*.json", "*.log", "*.log.*", "*.bak", "*backup*", "*.tmp", "private-words.txt", "*.pem", "*.key", ".env")
SKIP_DIRS = {"venv", "build", "__pycache__", ".git", "Output", "node_modules"}
words = []
for cand in (os.path.join(here, "private-words.txt"), os.path.join(here, "..", "private-words.txt")):
    if os.path.isfile(cand):
        words += [w.strip().lower() for w in open(cand, encoding="utf-8", errors="replace") if len(w.strip()) >= 4 and not w.startswith("#")]
user = (os.environ.get("USERNAME") or os.environ.get("USER") or "").lower()
BIN_PRIVATE = sorted({w for w in words + ([user] if len(user) >= 4 and user not in ("box", "root", "runner") else [])})
PERSONAL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\b192\.168\.\d+\.\d+\b|\b10\.\d+\.\d+\.\d+\b|"
                      r"(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
                      r"-----BEGIN [A-Z ]*PRIVATE KEY-----|C:\\\\Users\\\\(?!Public)[A-Za-z0-9_.-]+", re.I)
TEXT = (".py", ".js", ".html", ".css", ".json", ".txt", ".md", ".iss", ".bat", ".svg", ".asgard-theme")
bad = []
for dp, dns, fns in os.walk(root):
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    rel_dir = os.path.relpath(dp, root)
    third_party = rel_dir != "." and not rel_dir.startswith(("static", "docs", "themes", "windows", "tests"))
    for fn in fns:
        p = os.path.join(dp, fn)
        rel = os.path.relpath(p, root)
        if any(fnmatch.fnmatch(fn.lower(), pat) for pat in DENY):
            bad.append("private file: " + rel)
            continue
        try:
            data = open(p, "rb").read()
        except OSError:
            continue
        low = data.lower()
        for s in BIN_PRIVATE:
            if s.encode() in low:
                bad.append("%s contains a private word" % rel)
        if fn.lower().endswith(TEXT) and not third_party and fn != "release_check.py":
            txt = data.decode("utf-8", "replace")
            for m in PERSONAL.finditer(txt):
                bad.append("%s: %s" % (rel, m.group(0)[:40]))
if bad:
    print("RELEASE CHECK FAILED:\n  " + "\n  ".join(sorted(set(bad))[:50]))
    sys.exit(1)
print("release check OK:", root, "(%d private words checked)" % len(BIN_PRIVATE))

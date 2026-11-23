# Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
"""Writes cases.json: theme files that must load (ok=True) or be refused (ok=False). Both validators run the same list."""
import base64, json, os, struct, zlib

here = os.path.dirname(os.path.abspath(__file__))
P = {"bg": "#0b0d14", "box": "#151a26", "accent": "#22e1ff", "accent2": "#ff3df0"}

def t(**kw):
    d = {"asgard_theme": 2, "name": "Test", "palette": dict(P)}
    d.update(kw)
    return json.dumps(d)

def png(w, h, noise=False):
    """A real PNG built by hand (standard library only). noise=True makes it too big to squeeze."""
    def chunk(k, d):
        return struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d) & 0xFFFFFFFF)
    rows = b"".join(b"\0" + (os.urandom(w * 3) if noise else bytes((30, 60, 90)) * w) for _ in range(h))
    raw = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
    return "data:image/png;base64," + base64.b64encode(raw).decode()

small = png(64, 64)
cases = [
    ("v1 matrix example (Asgard 1.2 file)", json.dumps({"asgard_theme": 1, "name": "Matrix", "author": "Asgard", "base": "custom",
        "colors": {"bg": "#0d0208", "box": "#020d04", "accent": "#00ff41", "accent2": "#008f11", "text": "#7dff9a"},
        "effects": {"transparency": 22, "glow": 45, "corners": 2}, "effect": "matrix-rain", "effectOptions": {"density": 70, "speed": 55, "opacity": 38}}), True),
    ("v2 trash rain example", open(os.path.join(here, "..", "themes", "trash-rain.asgard-theme")).read(), True),
    ("v2 minimal", t(), True),
    ("v2 with picture", t(image={"use": "background", "data": small}), True),
    ("v2 every option", t(base="custom", author="Odin", boxes={"transparency": 30, "glow": 60, "corners": 8}, buttons="sticker", logo="glitch",
                          texture={"kind": "grunge", "strength": 40, "boxes": True}, font={"text": "clean", "headings": "marker"},
                          background={"effect": "embers", "density": 70, "speed": 40, "opacity": 50},
                          image={"use": "sticker", "corner": "bottom-left", "size": 150, "tilt": -8, "dim": 0, "data": small}), True),
    ("script tag", t(name="<script>alert(1)</script>"), False),
    ("escaped script tag", '{"asgard_theme":2,"name":"\\u003cscript\\u003ex","palette":%s}' % json.dumps(P), False),
    ("javascript link", t(name="javascript:alert(1)"), False),
    ("web link in name", t(name="Get it at https://example.com"), False),
    ("escaped web link", '{"asgard_theme":2,"name":"see http:\\/\\/example.com","palette":%s}' % json.dumps(P), False),
    ("www link", t(author="www.example.com"), False),
    ("css url()", t(name="url(evil)"), False),
    ("css @import", t(name="@import x"), False),
    ("css expression", t(name="expression(alert(1))"), False),
    ("event handler key", t(onload="x"), False),
    ("unknown key", t(css="body{}"), False),
    ("color that is code", t(palette=dict(P, accent="red;background:url(x)")), False),
    ("unknown effect", t(background={"effect": "fireworks"}), False),
    ("unknown font", t(font={"text": "comic-sans-from-web"}), False),
    ("svg picture", t(image={"use": "background", "data": "data:image/svg+xml;base64," + base64.b64encode(b"<svg onload=alert(1)/>").decode()}), False),
    ("picture from web", t(image={"use": "background", "data": "https://example.com/a.png"}), False),
    ("picture lies about its type", t(image={"use": "background", "data": "data:image/png;base64," + base64.b64encode(b"GIF89a" + b"\0" * 64).decode()}), False),
    ("html hidden in picture", t(image={"use": "background", "data": "data:image/png;base64," + base64.b64encode(b"<html><script>x</script>").decode()}), False),
    ("oversize picture", t(image={"use": "background", "data": png(616, 616, noise=True)}), False),
    ("picture bigger than the file limit", t(image={"use": "background", "data": png(900, 900, noise=True)}), False),
    ("built-in style plus colors", json.dumps({"asgard_theme": 2, "name": "x", "base": "viking", "palette": P}), False),
    ("built-in style", json.dumps({"asgard_theme": 2, "name": "x", "base": "viking", "background": "snow"}), True),
    ("oversize file", t(author="x" * 10) [:-1] + ',"pad":"' + "a" * 1_600_000 + '"}', False),
    ("newer format", json.dumps({"asgard_theme": 3, "name": "x", "palette": P}), False),
    ("not json", "hello there", False),
    ("not a theme", json.dumps([1, 2, 3]), False),
    ("v1 dark colors still load (as before)", json.dumps({"asgard_theme": 1, "name": "x", "base": "custom", "colors": {"bg": "#000000", "box": "#010101", "accent": "#020202", "accent2": "#030303"}}), True),
]


def write():
    json.dump([{"name": n, "text": s, "ok": ok} for n, s, ok in cases], open(os.path.join(here, "cases.json"), "w"))
    return cases


if __name__ == "__main__":
    print(len(write()), "cases written")

# Asgard Theme Kit (theme format v2) - Created November 22, 2026 by The_Mead_Maker & Odin.
# Copyright (c) 2026 The_Mead_Maker & Odin. MIT License, see LICENSE. Keep this notice.
"""Python twin of theme-kit.js validate(): the strict whitelist check for .asgard-theme files (v1 and v2).
Used by Asgard Theme Studio before it saves or sends a theme, and by Asgard's /api/themes/inbox before it accepts one.
Standard library only. check(text) -> (theme_dict_normalized, None) or (None, "plain-words error")."""
import base64
import json
import re

FILE_BYTES = 1572864      # 1.5 MB
V1_BYTES = 16000
IMAGE_CHARS = 1500000
NAME_CHARS = 40
BASES = ("custom", "asgard", "cyberpunk", "viking", "gothic", "mono", "pop", "gachi")
RENAMED = {"retro": "viking", "romance": "gothic"}
BUTTONS = ("plain", "pill", "sticker", "clipped", "neon", "rose-gold")
EFFECTS = ("none", "matrix-rain", "embers", "snow", "scanlines", "film-grain")
TEXTURES = ("none", "marble", "grunge", "paper", "carbon")
LOGOS = ("plain", "neon", "glitch", "sticker", "gold", "chrome", "stencil")
FONTS = ("clean", "rounded", "bold", "techno", "mono", "typewriter", "serif", "fancy", "gothic", "marker")
CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")
RANGES = {"transparency": (0, 80, 0), "glow": (0, 100, 40), "corners": (0, 24, 12), "density": (10, 100, 60), "speed": (10, 100, 50),
          "opacity": (5, 60, 30), "strength": (0, 100, 50), "dim": (0, 90, 45), "size": (60, 360, 180), "tilt": (-20, 20, 0)}
TOP_V1 = ("asgard_theme", "name", "base", "colors", "effects", "author", "effect", "effectOptions")
TOP_V2 = ("asgard_theme", "name", "author", "base", "palette", "boxes", "buttons", "logo", "font", "texture", "background", "image")
CODE = re.compile(r"url\s*\(|expression\s*\(|javascript\s*:|vbscript\s*:|<\s*/?\s*(script|style|iframe|object|embed|svg|link|meta)|@import|\\u003c|<!--", re.I)
LINK = re.compile(r"\b(?:https?|ftp|file|data(?!:image/(?:png|jpeg|webp);base64,))\s*:|\bwww\.[a-z0-9-]", re.I)
DATA_URI = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class Bad(Exception):
    pass


def clean_text(s, n):
    s = re.sub(r"[\x00-\x1f\x7f<>{}\\;`\"]", "", "" if s is None else str(s))
    return re.sub(r"\s+", " ", s).strip()[:n]


def _lum(h):
    n = int(h[1:], 16)

    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(n >> 16 & 255) + 0.7152 * f(n >> 8 & 255) + 0.0722 * f(n & 255)


def contrast(a, b):
    x, y = _lum(a), _lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v not in (float("inf"), float("-inf"))


def _num(v, key, strict=False):
    lo, hi, d = RANGES[key]
    if v is None:
        return d
    if not _is_num(v) or (strict and (not float(v).is_integer() or v < lo or v > hi)):
        raise Bad("“%s” must be a whole number from %d to %d." % (key, lo, hi))
    return int(round(min(hi, max(lo, v))))


def _only(o, allowed, what):
    for k in o:
        if k not in allowed:
            raise Bad("Unknown %s in theme file: %s" % (what, clean_text(k, 30)))


def _pick(v, allowed, d, what):
    if v is None:
        return d
    if not isinstance(v, str) or v not in allowed:
        raise Bad("Unknown %s: %s" % (what, clean_text(v, 30)))
    return v


def check_image(d):
    if not isinstance(d, str):
        raise Bad("The picture is missing.")
    if len(d) > IMAGE_CHARS:
        raise Bad("The picture is too big (the limit is about 1.1 MB).")
    m = DATA_URI.match(d)
    if not m:
        raise Bad("The picture must be a PNG, JPG or WebP image.")
    head = base64.b64decode(m.group(2)[:16] + "==")[:12] if len(m.group(2)) >= 16 else b""
    ok = {"png": head[:8] == b"\x89PNG\r\n\x1a\n", "jpeg": head[:3] == b"\xff\xd8\xff", "webp": head[:4] == b"RIFF" and head[8:12] == b"WEBP"}[m.group(1)]
    if not ok:
        raise Bad("The picture's data doesn't match its type.")
    try:
        base64.b64decode(m.group(2), validate=True)
    except Exception:
        raise Bad("The picture's data is damaged.")
    return "image/" + m.group(1)


def _blank():
    return {"v": 2, "name": "", "author": "", "base": "custom", "palette": None, "boxes": None, "buttons": "plain", "logo": "plain",
            "font": {"headings": "clean", "text": "clean"}, "texture": {"kind": "none", "strength": 50, "boxes": False},
            "background": {"effect": "none", "density": 60, "speed": 50, "opacity": 30}, "image": None}


def _name_base(d, t):
    t["name"] = clean_text(d.get("name"), NAME_CHARS)
    if not t["name"]:
        raise Bad("The theme needs a name.")
    t["author"] = clean_text(d.get("author"), NAME_CHARS)
    base = d.get("base", "custom")
    if base is None:
        base = "custom"
    if isinstance(base, str):
        base = RENAMED.get(base, base)
    if not isinstance(base, str) or base not in BASES:
        raise Bad("Unknown base style: %s" % clean_text(base, 30))
    t["base"] = base


def _palette(c, t, strict_text, warn):
    if not isinstance(c, dict):
        raise Bad("A custom theme needs its colours (bg, box, accent, accent2).")
    _only(c, ("bg", "box", "accent", "accent2", "text"), "colour")
    p = {}
    for k in ("bg", "box", "accent", "accent2"):
        if not isinstance(c.get(k), str) or not HEX.match(c[k]):
            raise Bad("Colour “%s” must look like #12ab34." % k)
        p[k] = c[k].lower()
    if c.get("text") is not None:
        if not isinstance(c["text"], str) or not HEX.match(c["text"]):
            raise Bad("Colour “text” must look like #12ab34.")
        ok = contrast(c["text"], p["bg"]) >= 4.5 and contrast(c["text"], p["box"]) >= 4.5
        if not ok and strict_text:
            raise Bad("The “text” colour is too hard to read on that background.")
        if ok:
            p["text"] = c["text"].lower()
        else:
            warn.append("The text colour was too hard to read, so a readable one is used instead.")
    t["palette"] = p


def _boxes(e, t, strict):
    e = {} if e is None else e
    if not isinstance(e, dict):
        raise Bad("The box settings must be a list of numbers.")
    _only(e, ("transparency", "glow", "corners"), "box setting")
    t["boxes"] = {k: _num(e.get(k), k, strict) for k in ("transparency", "glow", "corners")}


def _v1(d, warn):
    t = _blank()
    t["v"] = 1
    _only(d, TOP_V1, "setting")
    _name_base(d, t)
    if t["base"] == "custom":
        _palette(d.get("colors"), t, True, warn)
        _boxes(d.get("effects"), t, True)
    elif d.get("colors") is not None or d.get("effects") is not None:
        raise Bad('Only themes with base "custom" can set colours.')
    eff = d.get("effect")
    if isinstance(eff, str) and eff in EFFECTS and eff != "none":
        o = d.get("effectOptions") if isinstance(d.get("effectOptions"), dict) else {}
        t["background"] = {"effect": eff}
        for k in ("density", "speed", "opacity"):
            v = o.get(k)
            t["background"][k] = _num(v if _is_num(v) else None, k)
    return t


def _v2(d, warn):
    t = _blank()
    _only(d, TOP_V2, "setting")
    _name_base(d, t)
    if t["base"] == "custom":
        _palette(d.get("palette"), t, False, warn)
        _boxes(d.get("boxes"), t, False)
    else:
        if d.get("palette") is not None or d.get("boxes") is not None:
            raise Bad('Only themes with base "custom" can set colours.')
        for k in ("buttons", "logo", "font", "texture"):
            if d.get(k) is not None:
                raise Bad('“%s” needs base "custom" (built-in styles have their own).' % k)
    t["buttons"] = _pick(d.get("buttons"), BUTTONS, "plain", "button style")
    t["logo"] = _pick(d.get("logo"), LOGOS, "plain", "logo style")
    f = d.get("font")
    if f is not None:
        if isinstance(f, str):
            f = {"headings": f, "text": f}
        if not isinstance(f, dict):
            raise Bad("“font” must name fonts from the built-in list.")
        _only(f, ("headings", "text"), "font setting")
        t["font"] = {k: _pick(f.get(k), FONTS, "clean", "font") for k in ("headings", "text")}
    x = d.get("texture")
    if x is not None:
        x = {"kind": x} if isinstance(x, str) else x
        if not isinstance(x, dict):
            raise Bad("“texture” must be one of: %s." % ", ".join(TEXTURES))
        _only(x, ("kind", "strength", "boxes"), "texture setting")
        if x.get("boxes") is not None and not isinstance(x.get("boxes"), bool):
            raise Bad("texture “boxes” must be true or false.")
        t["texture"] = {"kind": _pick(x.get("kind"), TEXTURES, "none", "texture"), "strength": _num(x.get("strength"), "strength"), "boxes": bool(x.get("boxes"))}
    x = d.get("background")
    if x is not None:
        x = {"effect": x} if isinstance(x, str) else x
        if not isinstance(x, dict):
            raise Bad("“background” must name an effect.")
        _only(x, ("effect", "density", "speed", "opacity"), "background setting")
        t["background"] = {"effect": _pick(x.get("effect"), EFFECTS, "none", "background effect")}
        for k in ("density", "speed", "opacity"):
            t["background"][k] = _num(x.get(k), k)
    x = d.get("image")
    if x is not None:
        if not isinstance(x, dict):
            raise Bad("“image” must be a picture with its settings.")
        _only(x, ("use", "data", "dim", "corner", "size", "tilt"), "picture setting")
        if x.get("use") not in ("background", "sticker"):
            raise Bad('A picture must be used as "background" or "sticker".')
        check_image(x.get("data"))
        img = {"use": x["use"], "data": x["data"], "corner": "bottom-right"}
        for k in ("dim", "size", "tilt"):
            img[k] = _num(x.get(k), k)
        if x.get("dim") is None:
            img["dim"] = RANGES["dim"][2] if x["use"] == "background" else 0
        if x.get("corner") is not None:
            if x["corner"] not in CORNERS:
                raise Bad("Unknown sticker corner: %s" % clean_text(x["corner"], 20))
            img["corner"] = x["corner"]
        t["image"] = img
    return t


def check(text):
    """-> (theme, warnings, None) or (None, None, error)."""
    if isinstance(text, bytes):
        if len(text) > FILE_BYTES:
            return None, None, "That theme file is too big (the limit is 1.5 MB)."
        try:
            text = text.decode("utf-8-sig")
        except UnicodeDecodeError:
            return None, None, "That isn't a theme file."
    if not isinstance(text, str):
        return None, None, "That isn't a theme file."
    if len(text.encode("utf-8")) > FILE_BYTES:
        return None, None, "That theme file is too big (the limit is 1.5 MB)."
    if CODE.search(text):
        return None, None, "That theme file contains code or links, so it wasn't loaded."
    try:
        d = json.loads(text)
    except ValueError:
        return None, None, "That isn't a theme file (it isn't readable theme data)."
    if not isinstance(d, dict):
        return None, None, "That isn't an .asgard-theme file."
    flat = json.dumps(d, ensure_ascii=False)  # again on the decoded text, so escapes can't hide code or links
    if CODE.search(flat):
        return None, None, "That theme file contains code or links, so it wasn't loaded."
    if LINK.search(flat):
        return None, None, "That theme file contains a web link, so it wasn't loaded."
    warn = []
    try:
        if d.get("asgard_theme") == 1 and not isinstance(d.get("asgard_theme"), bool):
            if len(text.encode("utf-8")) > V1_BYTES:
                return None, None, "That theme file is too big."
            return _v1(d, warn), warn, None
        if d.get("asgard_theme") == 2 and not isinstance(d.get("asgard_theme"), bool):
            return _v2(d, warn), warn, None
    except Bad as exc:
        return None, None, str(exc)
    if d.get("asgard_theme") is None:
        return None, None, "That isn't an .asgard-theme file."
    return None, None, "This theme was made for a newer version. Update to load it."

# Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
"""Checks theme_check.py (the Python twin used by the Studio and Asgard servers). Standard library only. Exit 1 on failure."""
import json, os, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
import theme_check  # noqa: E402
import make_cases  # noqa: E402

fails = 0
for name, text, ok in make_cases.write():
    theme, warn, err = theme_check.check(text)
    good = (err is None) == ok
    fails += not good
    print("%s %-30s %s" % ("PASS" if good else "FAIL", name, err or ("ok" + (" (warnings: %s)" % "; ".join(warn) if warn else ""))))

# Values out of range are pulled back into range, not refused.
theme, warn, err = theme_check.check(json.dumps({"asgard_theme": 2, "name": "x", "palette": {"bg": "#000000", "box": "#111111", "accent": "#22e1ff", "accent2": "#ff3df0"},
                                                 "background": {"effect": "snow", "density": 999, "speed": -5, "opacity": 50}}))
good = err is None and theme["background"]["density"] == 100 and theme["background"]["speed"] == 10
fails += not good
print("%s %-30s %s" % ("PASS" if good else "FAIL", "out-of-range numbers clamp", theme and theme["background"]))
print("\n%s" % ("ALL PASSED" if not fails else "%d FAILED" % fails))
sys.exit(1 if fails else 0)

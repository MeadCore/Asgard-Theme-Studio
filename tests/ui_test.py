# Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
"""End-to-end check in a headless browser (Playwright): starter looks, every tab, a picture, undo/redo, save -> open round trip,
an unsafe file refused, and Use in Asgard -> Asgard's Add it -> the theme on screen. Screenshots go to tests/out/.
Needs the Studio on STUDIO (default 127.0.0.1:8801, run with STUDIO_THEMES_DIR) and a box copy of Asgard 1.3 on ASGARD."""
import json, os, sys, time
from playwright.sync_api import sync_playwright

STUDIO = os.environ.get("STUDIO", "http://127.0.0.1:8801")
ASGARD = os.environ.get("ASGARD", "http://127.0.0.1:8777")
THEMES = os.environ.get("STUDIO_THEMES_DIR", "/tmp/ts-themes")
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
here = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(here, "out"); os.makedirs(out, exist_ok=True)
res = []
SAMPLE = os.path.join(out, "sample-sticker.png")
if not os.path.exists(SAMPLE):   # a plain test picture (needs Pillow)
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (400, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(200, 10), (390, 200), (200, 390), (10, 200)], fill=(232, 38, 31, 255), outline=(255, 212, 0, 255)); im.save(SAMPLE)
def ok(name, cond, info=""):
    res.append(bool(cond)); print("%s %-44s %s" % ("PASS" if cond else "FAIL", name, info)); sys.stdout.flush()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 1600, "height": 960})
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(STUDIO + "/"); pg.wait_for_timeout(1200)
    ok("start screen shows 7 looks", pg.locator("#starterCards [data-starter]").count() == 7)
    pg.screenshot(path=os.path.join(out, "studio-0-start.png"))
    for i, sid in enumerate(("gachi", "cyber", "matrix")):
        if i: pg.click("#startBtn"); pg.wait_for_timeout(300)
        pg.click('[data-starter="%s"]' % sid); pg.wait_for_timeout(1600)
        st = pg.evaluate("studio.state")
        ok("starter %s applied" % sid, st and st["name"], st["name"] + " / " + st["buttons"] + " / " + st["background"]["effect"])
        pg.screenshot(path=os.path.join(out, "studio-%d-%s.png" % (i + 1, sid)))
    # Every tab renders.
    for tab in ("colors", "buttons", "effects", "textures", "pictures"):
        pg.click('.tab[data-tab="%s"]' % tab); pg.wait_for_timeout(250)
        ok("tab %s has controls" % tab, pg.locator("#pane button, #pane input, #pane .drop, #pane [role=button]").count() >= 1)
    # Back to Gachiakuta, add a picture as sticker.
    pg.click("#startBtn"); pg.wait_for_timeout(300); pg.click('[data-starter="gachi"]'); pg.wait_for_timeout(800)
    pg.click('.tab[data-tab="pictures"]'); pg.wait_for_timeout(200)
    pg.set_input_files("#filePic", SAMPLE); pg.wait_for_timeout(1500)
    st = pg.evaluate("studio.state")
    ok("picture added and re-encoded", st.get("image") and st["image"]["data"].startswith("data:image/"), st.get("image") and (st["image"]["use"], len(st["image"]["data"])))
    pg.screenshot(path=os.path.join(out, "studio-4-picture.png"))
    # Undo / redo.
    before = pg.evaluate("JSON.stringify(studio.state)")
    pg.evaluate("studio.surprise()"); pg.wait_for_timeout(500)
    mid = pg.evaluate("JSON.stringify(studio.state)")
    pg.click("#undoBtn"); pg.wait_for_timeout(300)
    ok("surprise then undo restores", mid != before and pg.evaluate("JSON.stringify(studio.state)") == before)
    pg.click("#redoBtn"); pg.wait_for_timeout(300)
    ok("redo brings the surprise back", pg.evaluate("JSON.stringify(studio.state)") == mid)
    pg.click("#undoBtn"); pg.wait_for_timeout(300)
    # Readability warning + fix.
    pg.evaluate("studio.openText(JSON.stringify({asgard_theme:2,name:'Low contrast',palette:{bg:'#202020',box:'#262626',accent:'#2e2e2e',accent2:'#333333',text:'#3a3a3a'}}), 'x.asgard-theme')"); pg.wait_for_timeout(600)
    w = pg.locator("#warnings").inner_text()
    ok("hard-to-read colors get a warning", len(w.strip()) > 0, w.strip().splitlines()[0][:70] if w.strip() else "")
    if pg.locator("#modal:not(.hidden) button").count():
        pg.locator("#modal button").last.click(); pg.wait_for_timeout(300)
    pg.screenshot(path=os.path.join(out, "studio-5-warning.png"))
    if pg.locator("#warnings [data-fix]").count():
        pg.locator("#warnings [data-fix]").first.click(); pg.wait_for_timeout(500)
    pg.evaluate("studio.undo()"); pg.evaluate("studio.undo()"); pg.wait_for_timeout(300)
    # Unsafe file refused.
    pg.evaluate("studio.openText(JSON.stringify({asgard_theme:2,name:'<script>alert(1)</script>',palette:{bg:'#000000',box:'#111111',accent:'#22e1ff',accent2:'#ff3df0'}}), 'bad.asgard-theme')"); pg.wait_for_timeout(400)
    ok("unsafe file refused with a message", "code" in pg.locator("#modal").inner_text().lower())
    pg.screenshot(path=os.path.join(out, "studio-6-refused.png"))
    if pg.locator("#modal:not(.hidden) button").count():
        pg.locator("#modal button").last.click(); pg.wait_for_timeout(300)
    # Back to the picture theme and save -> open round trip.
    pg.click("#startBtn"); pg.wait_for_timeout(300); pg.click('[data-starter="gachi"]'); pg.wait_for_timeout(500)
    pg.set_input_files("#filePic", SAMPLE); pg.wait_for_timeout(1500)
    pg.fill("#themeName", "Trash Test"); pg.wait_for_timeout(300)
    want = pg.evaluate("studio.serialize()")
    for f in os.listdir(THEMES):
        os.remove(os.path.join(THEMES, f))
    pg.click("#saveBtn"); pg.wait_for_timeout(800)
    files = os.listdir(THEMES)
    ok("save writes a .asgard-theme file", files == ["Trash Test.asgard-theme"] or (len(files) == 1 and files[0].endswith(".asgard-theme")), files)
    pg.screenshot(path=os.path.join(out, "studio-7-saved.png"))
    if pg.locator("#modal:not(.hidden) button").count():
        pg.locator("#modal button").last.click(); pg.wait_for_timeout(200)
    saved = open(os.path.join(THEMES, files[0]), encoding="utf-8").read() if files else ""
    ok("saved file = what the Studio shows", saved == want, "%d bytes" % len(saved))
    pg.click("#startBtn"); pg.wait_for_timeout(200); pg.click('[data-starter="blank"]'); pg.wait_for_timeout(300)
    pg.set_input_files("#fileTheme", os.path.join(THEMES, files[0])); pg.wait_for_timeout(1500)
    if pg.locator("#modal:not(.hidden) button").count():
        pg.locator("#modal button").last.click(); pg.wait_for_timeout(200)
    got = pg.evaluate("studio.serialize()")
    if got != want:
        import difflib
        gj, wj = json.loads(got), json.loads(want)
        for k in sorted(set(gj) | set(wj)):
            if gj.get(k) != wj.get(k): print("   differs:", k, str(wj.get(k))[:90], "->", str(gj.get(k))[:90])
    gj, wj = json.loads(got), json.loads(want)
    gi, wi = gj.pop("image", {}), wj.pop("image", {})
    same_pic = gi.get("use") == wi.get("use") and gi.get("data", "")[:22] == wi.get("data", "")[:22] and {k: v for k, v in gi.items() if k != "data"} == {k: v for k, v in wi.items() if k != "data"}
    # The picture is re-drawn on every open (that strips anything hidden), so its bytes change; everything else must match exactly.
    ok("open gives back the same theme", gj == wj and same_pic, "settings identical; picture re-drawn (%d -> %d chars)" % (len(wi.get("data", "")), len(gi.get("data", ""))))
    # Use in Asgard.
    pg.click("#useBtn"); pg.wait_for_timeout(800)
    send = pg.get_by_role("button", name="🚀 Send to Asgard")
    ok("Use in Asgard finds the running Asgard", send.count() == 1)
    if send.count():
        send.click(); pg.wait_for_timeout(1200)
        ok("Studio says it was sent", "Sent" in pg.locator("#modal").inner_text())
        pg.screenshot(path=os.path.join(out, "studio-8-sent.png"))
    ok("no script errors in the Studio", not errs, "; ".join(errs[:3]))

    # Asgard (box copy, headless): Add it.
    ag = ctx.new_page(); aerrs = []
    ag.on("pageerror", lambda e: aerrs.append(str(e)))
    ag.add_init_script("try{localStorage.setItem('gh_setup_done','true');localStorage.setItem('gh_setup_seen','true');localStorage.setItem('gh_wx_skip','true');}catch(e){}")
    ag.goto(ASGARD + "/"); ag.wait_for_timeout(3500)
    act = ag.locator(".toast-act")
    ok("Asgard shows the Add it message", act.count() > 0, ag.locator("#toast").inner_text()[:80] if ag.locator("#toast").count() else "")
    ag.screenshot(path=os.path.join(out, "asgard-1-toast.png"))
    if act.count():
        act.first.click(timeout=8000); ag.wait_for_timeout(3000)
    ds = ag.evaluate("JSON.stringify(document.documentElement.dataset)")
    ok("Asgard wears the theme", '"tkBtn":"sticker"' in ds, ds[:160])
    ok("Asgard shows the picture", ag.evaluate("!!document.querySelector('#tk-art img')"))
    ok("Asgard runs the effect", ag.evaluate("!!document.getElementById('bgfx')"))
    ag.screenshot(path=os.path.join(out, "asgard-2-themed.png"))
    # Reload: still on.
    ag.reload(); ag.wait_for_timeout(3000)
    ok("theme still on after reload", '"tkBtn":"sticker"' in ag.evaluate("JSON.stringify(document.documentElement.dataset)") and ag.evaluate("!!document.querySelector('#tk-art img')"))
    ok("no script errors in Asgard", not aerrs, "; ".join(aerrs[:3]))
    b.close()
print("\n%s" % ("ALL PASSED" if all(res) else "%d FAILED" % res.count(False)))
sys.exit(0 if all(res) else 1)

/* Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin.
   Copyright (c) 2026 The_Mead_Maker & Odin. MIT License, see LICENSE. Keep this notice.
   The Studio screen: starting looks, the five tabs, undo/redo, Surprise me, Open/Save and "Use in Asgard".
   The theme being edited is always the checked v2 shape from theme-kit.js; it's saved with AsgardThemeKit.serialize(). */
(function () {
  "use strict";
  const K = window.AsgardThemeKit, STARTERS = window.STUDIO_STARTERS;
  const VERSION = "1.0.0";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const HAS_APP = /^https?:$/.test(location.protocol);   // served by the Studio program (not opened as a plain file)
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } },
  };

  let state = null, tab = "colors", mode = "asgard", picOriginal = null, imgLum = null, previewReady = false;
  const hist = { past: [], future: [], key: "", at: 0 };

  // ---------------------------------------------------------------- theme helpers
  function clone(t) {
    return Object.assign({}, t, { palette: Object.assign({}, t.palette), boxes: Object.assign({}, t.boxes), font: Object.assign({}, t.font),
      texture: Object.assign({}, t.texture), background: Object.assign({}, t.background), image: t.image ? Object.assign({}, t.image) : null });
  }
  function normalize(part) {
    const b = K.blank();
    const t = Object.assign(b, part || {});
    t.v = 2; t.base = "custom";
    t.palette = Object.assign({ bg: "#0b0712", box: "#171024", accent: "#ff3d81", accent2: "#22e1ff" }, part && part.palette);
    t.boxes = Object.assign({ transparency: 0, glow: 40, corners: 12 }, part && part.boxes);
    t.font = Object.assign({ headings: "clean", text: "clean" }, part && part.font);
    t.texture = Object.assign({ kind: "none", strength: 50, boxes: false }, part && part.texture);
    t.background = Object.assign({ effect: "none", density: 60, speed: 50, opacity: 30 }, part && part.background);
    t.image = part && part.image ? Object.assign({}, part.image) : null;
    return t;
  }
  const textColor = (t) => t.palette.text || K.autoText(t.palette.bg);
  const fileSlug = (n) => (String(n || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "my-theme").slice(0, 40);

  // ---------------------------------------------------------------- history (Undo / Redo)
  // Each change saves the step before it. Dragging a slider counts as one step (changes to the same thing within a second merge).
  function change(key, fn, opts) {
    const now = Date.now();
    if (!(key && key === hist.key && now - hist.at < 1000)) { hist.past.push(clone(state)); if (hist.past.length > 120) hist.past.shift(); }
    hist.future = []; hist.key = key || ""; hist.at = now;
    fn(state);
    refresh(opts && opts.pane);
  }
  function setState(t, label) { if (state) { hist.past.push(clone(state)); hist.future = []; hist.key = ""; } state = t; refresh(true); if (label) status(label, "good"); }
  function undo() { if (!hist.past.length) return status("Nothing to undo."); hist.future.push(clone(state)); state = hist.past.pop(); hist.key = ""; refresh(true); status("Undone."); }
  function redo() { if (!hist.future.length) return status("Nothing to redo."); hist.past.push(clone(state)); state = hist.future.pop(); hist.key = ""; refresh(true); status("Redone."); }

  let saveTimer = 0;
  function refresh(pane) {
    $("themeName").value !== state.name && ($("themeName").value = state.name);
    $("undoBtn").disabled = !hist.past.length; $("redoBtn").disabled = !hist.future.length;
    if (previewReady) frameWin().studioPreview.show(state);
    if (pane) renderPane(); else updatePaneValues();
    renderWarnings();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => { if (!store.set("studio_autosave", state)) store.set("studio_autosave", Object.assign(clone(state), { image: null })); }, 400);
  }
  const frameWin = () => $("preview").contentWindow;

  // ---------------------------------------------------------------- status + dialogs
  let stTimer = 0;
  function status(msg, kind) { const s = $("status"); s.textContent = msg; s.className = kind || ""; clearTimeout(stTimer); stTimer = setTimeout(() => { s.textContent = "Ready."; s.className = ""; }, 6000); }
  // modal(title, html, [{label, cls, value}]) -> Promise(value)
  function modal(title, html, buttons) {
    return new Promise((resolve) => {
      const m = $("modal"), box = $("modalBox"), last = document.activeElement;
      box.innerHTML = "<h3 id=\"mTitle\">" + esc(title) + "</h3>" + html + '<div class="modal-actions">' +
        (buttons || [{ label: "OK", cls: "go", value: true }]).map((b, i) => '<button type="button" class="tbtn ' + (b.cls || "") + '" data-i="' + i + '">' + esc(b.label) + "</button>").join("") + "</div>";
      m.setAttribute("aria-labelledby", "mTitle");
      m.classList.remove("hidden");
      const btns = buttons || [{ value: true }];
      const done = (v) => { m.classList.add("hidden"); m.onclick = null; document.removeEventListener("keydown", key, true); if (last && last.focus) last.focus(); resolve(v); };
      const key = (e) => { if (e.key === "Escape") { e.stopPropagation(); done(null); } };
      document.addEventListener("keydown", key, true);
      m.onclick = (e) => { const b = e.target.closest("[data-i]"); if (b) done(btns[+b.dataset.i].value); else if (e.target === m) done(null); };
      const first = box.querySelector(".tbtn.go") || box.querySelector(".tbtn"); if (first) first.focus();
      box.querySelectorAll("[data-run]").forEach((el) => el.addEventListener("click", () => { const f = modalRuns[el.dataset.run]; if (f) f(); }));
    });
  }
  const modalRuns = {};

  // ---------------------------------------------------------------- readability warnings
  function bestText(bg, box) {
    const c = ["#f4f6fb", "#11141b", "#ffffff", "#000000"];
    let best = c[0], score = 0;
    for (const x of c) { const s = Math.min(K.contrast(x, bg), K.contrast(x, box)); if (s > score) { score = s; best = x; } }
    return { color: best, score };
  }
  function problems() {
    const p = state.palette, txt = textColor(state), out = [];
    if (K.contrast(txt, p.bg) < 4.5) out.push({ msg: "Text may be hard to read on the background.", fix: "text" });
    else if (K.contrast(txt, p.box) < 4.5) out.push({ msg: "Text may be hard to read inside the boxes.", fix: "text" });
    if (K.contrast(p.accent, p.box) < 1.8) out.push({ msg: "Your main color is hard to see on the boxes.", fix: "accent" });
    if (state.image && state.image.use === "background" && imgLum != null) {
      const shown = imgLum * (1 - state.image.dim / 100) + K.lum(p.bg) * (state.image.dim / 100);
      if (K.lum(txt) > 0.5 && shown > 0.3) out.push({ msg: "Your picture is bright, so text on top may be hard to read.", fix: "dim" });
    }
    return out;
  }
  function renderWarnings() {
    const w = problems();
    $("warnings").innerHTML = w.map((x) => '<div class="warn">⚠️ <span>' + esc(x.msg) + '</span><button type="button" class="fix" data-fix="' + x.fix + '">Fix it for me</button></div>').join("");
  }
  function fix(kind) {
    change("", (t) => {
      const p = t.palette;
      if (kind === "text") {
        let b = bestText(p.bg, p.box);
        let n = 0;
        while (b.score < 4.5 && n++ < 20) {   // still not enough: nudge the background and boxes darker (or lighter)
          const dark = K.lum(b.color) > 0.5;
          p.bg = shade(p.bg, dark ? -0.12 : 0.12); p.box = shade(p.box, dark ? -0.12 : 0.12);
          b = bestText(p.bg, p.box);
        }
        if (b.color === K.autoText(p.bg)) delete p.text; else p.text = b.color;
      } else if (kind === "accent") {
        const dark = K.lum(p.box) < 0.3; let n = 0;
        while (K.contrast(p.accent, p.box) < 3 && n++ < 20) p.accent = shade(p.accent, dark ? 0.1 : -0.1);
      } else if (kind === "dim" && t.image) t.image.dim = Math.min(90, Math.max(t.image.dim + 25, 60));
    }, { pane: true });
    status("Fixed.", "good");
  }

  // ---------------------------------------------------------------- colour maths (Surprise me, fixes)
  function hexToRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
  function rgbToHex(r, g, b) { return "#" + [r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join(""); }
  function shade(h, amt) { const c = hexToRgb(h); return amt < 0 ? rgbToHex(...c.map((v) => v * (1 + amt))) : rgbToHex(...c.map((v) => v + (255 - v) * amt)); }
  function hsl(h, s, l) {
    h = ((h % 360) + 360) % 360; s /= 100; l /= 100;
    const k = (n) => (n + h / 30) % 12, a = s * Math.min(l, 1 - l), f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
    return rgbToHex(f(0) * 255, f(8) * 255, f(4) * 255);
  }
  const rnd = (a, b) => a + Math.random() * (b - a), pick = (l) => l[(Math.random() * l.length) | 0];
  function surprise() {
    const h = rnd(0, 360), h2 = h + pick([0, 25, 150, 180, 200, -30]), h3 = h2 + pick([60, 120, 160, 200]);
    const lightTheme = Math.random() < 0.08;
    const p = lightTheme ? { bg: hsl(h, rnd(20, 40), rnd(90, 95)), box: hsl(h, rnd(15, 30), rnd(97, 99)), accent: hsl(h2, rnd(70, 90), rnd(38, 46)), accent2: hsl(h3, rnd(70, 90), rnd(36, 44)) }
      : { bg: hsl(h, rnd(25, 60), rnd(3, 8)), box: hsl(h, rnd(20, 45), rnd(9, 15)), accent: hsl(h2, rnd(80, 100), rnd(52, 64)), accent2: hsl(h3, rnd(80, 100), rnd(50, 62)) };
    if (Math.random() < 0.4) { const tt = lightTheme ? hsl(h, 30, 12) : hsl(h, rnd(20, 50), rnd(88, 95)); if (Math.min(K.contrast(tt, p.bg), K.contrast(tt, p.box)) >= 4.5) p.text = tt; }
    const fontPairs = [["bold", "clean"], ["techno", "techno"], ["mono", "mono"], ["fancy", "serif"], ["serif", "clean"], ["marker", "rounded"], ["gothic", "serif"], ["bold", "rounded"], ["typewriter", "typewriter"], ["clean", "clean"]];
    const fp = pick(fontPairs);
    const effect = Math.random() < 0.35 ? "none" : pick(["matrix-rain", "embers", "snow", "scanlines", "film-grain"]);
    const words1 = ["Neon", "Frost", "Ember", "Shadow", "Iron", "Velvet", "Static", "Rune", "Storm", "Midnight", "Toxic", "Golden", "Crimson", "Ghost", "Chrome"];
    const words2 = ["Wolf", "Raven", "Arcade", "Forge", "Garden", "Signal", "Tide", "Hall", "Circuit", "Rose", "Alley", "Dragon", "Comet", "Saga", "Riot"];
    const t = normalize({
      name: pick(words1) + " " + pick(words2), author: state ? state.author : "", palette: p,
      boxes: { transparency: Math.round(rnd(0, 30)), glow: Math.round(rnd(10, 80)), corners: pick([0, 2, 6, 10, 12, 18, 24]) },
      buttons: pick(Object.keys(K.BUTTONS)), logo: pick(Object.keys(K.LOGOS)), font: { headings: fp[0], text: fp[1] },
      texture: Math.random() < 0.5 ? { kind: "none", strength: 50, boxes: false } : { kind: pick(["marble", "grunge", "paper", "carbon"]), strength: Math.round(rnd(25, 70)), boxes: Math.random() < 0.4 },
      background: { effect, density: Math.round(rnd(25, 80)), speed: Math.round(rnd(25, 75)), opacity: Math.round(rnd(15, 45)) },
      image: state && state.image ? state.image : null,
    });
    setState(t, "🎲 Here's “" + t.name + "”. Press Surprise me again for another.");
  }

  // ---------------------------------------------------------------- the tabs
  const SW = {
    bg: ["#07080b", "#0b0712", "#0d0208", "#120424", "#17130f", "#1b140e", "#0a1420", "#120a0e", "#101418", "#f3efe6"],
    box: ["#141821", "#171024", "#020d04", "#1d0b3a", "#2a241e", "#2a1f15", "#10202e", "#1e1218", "#22262e", "#ffffff"],
    accent: ["#ff3d81", "#8b6cff", "#22e1ff", "#00ff41", "#fcee0a", "#ff2bd6", "#e8261f", "#ffd400", "#7fc8e8", "#e8b49a", "#ff8a00", "#3ddc84"],
    accent2: ["#22e1ff", "#ff3d81", "#008f11", "#00f0ff", "#ffd400", "#b76e79", "#c9a25a", "#00e5ff", "#a6e22e", "#9b3fe0", "#ff5c6c", "#4aa8ff"],
    text: ["#f4f6fb", "#ece6dc", "#7dff9a", "#f3e9d2", "#fdf2ff", "#d6f3ff", "#ffe8c2", "#11141b"],
  };
  const COLOR_ROWS = [
    ["bg", "Background", "The color behind everything."],
    ["box", "Boxes", "The panels that hold your games, music and more."],
    ["accent", "Main color", "Buttons, highlights and glow."],
    ["accent2", "Second color", "Hover color, labels and little details."],
    ["text", "Text", "The words. “Automatic” always picks a readable one."],
  ];
  const BTN_INFO = {
    plain: ["▭", "Clean and simple, like Asgard's normal look."], pill: ["💊", "Soft, fully rounded buttons and labels."],
    sticker: ["🏷️", "Tilted paper stickers with tape (Gachiakuta)."], clipped: ["✂️", "Cut corners that change color on hover (Cyberpunk)."],
    neon: ["💡", "Glowing outlines, like neon signs."], "rose-gold": ["🌹", "Thin rose-gold edges and soft serif labels."],
  };
  const LOGO_INFO = { plain: "▭", neon: "💡", glitch: "📺", sticker: "🏷️", gold: "👑", chrome: "🪞", stencil: "🔳" };
  const FX_INFO = {
    none: ["⬛", "A still background."], "matrix-rain": ["🟩", "Falling green code."], embers: ["🔥", "Glowing sparks floating up."],
    snow: ["❄️", "Gentle snowflakes."], scanlines: ["📺", "Old-TV lines with a slow sweep."], "film-grain": ["🎞️", "Flickering old-film grain."],
  };
  const TEX_INFO = { none: ["⬛", "Smooth."], marble: ["🏛️", "Stone with soft veins."], grunge: ["🧱", "Dirty, worn and spray-painted."], paper: ["📜", "Old paper grain."], carbon: ["🏎️", "Woven carbon fiber."] };

  function slider(path, label, desc, min, max, unit) {
    const v = getPath(path);
    return '<label class="sl"><span class="sl-l">' + esc(label) + '</span><span class="sl-v" data-out="' + path + '">' + v + (unit || "") + "</span>" +
      '<input type="range" min="' + min + '" max="' + max + '" step="1" value="' + v + '" data-range="' + path + '" data-unit="' + esc(unit || "") + '" aria-label="' + esc(label) + '">' +
      (desc ? '<span class="sl-d">' + esc(desc) + "</span>" : "") + "</label>";
  }
  function sw(path, label, on) { return '<label class="switch"><input type="checkbox" data-check="' + path + '"' + (on ? " checked" : "") + "><span></span>" + esc(label) + "</label>"; }
  function choices(path, list, info, cls) {
    const cur = getPath(path);
    return '<div class="choices ' + (cls || "") + '" role="radiogroup">' + Object.keys(list).map((k) => {
      const i = info[k] || []; const emoji = typeof i === "string" ? i : i[0], small = typeof i === "string" ? "" : i[1];
      return '<button type="button" class="choice' + (k === cur ? " on" : "") + '" role="radio" aria-checked="' + (k === cur) + '" data-pick="' + path + '" data-val="' + k + '">' +
        '<span class="ce">' + emoji + "</span><b>" + esc(list[k]) + "</b>" + (small ? "<small>" + esc(small) + "</small>" : "") + "</button>";
    }).join("") + "</div>";
  }
  function getPath(path) { return path.split(".").reduce((o, k) => (o == null ? o : o[k]), state); }
  function setPath(t, path, v) { const ks = path.split("."), last = ks.pop(); ks.reduce((o, k) => o[k], t)[last] = v; }

  function paneColors() {
    const showHex = store.get("studio_hex", false), p = state.palette;
    const rows = COLOR_ROWS.map(([k, label, desc]) => {
      const auto = k === "text" && !p.text, val = k === "text" ? textColor(state) : p[k];
      return '<div class="crow"><span class="swatch" style="background:' + val + '" title="Click to pick any color"><input type="color" value="' + val + '" data-color="' + k + '" aria-label="' + esc(label) + ' color"></span>' +
        '<span class="cl">' + esc(label) + (auto ? ' <span class="muted">(automatic)</span>' : "") + "</span>" +
        (showHex ? '<input class="hexin" type="text" maxlength="7" spellcheck="false" value="' + val + '" data-hex="' + k + '" aria-label="' + esc(label) + ' color code">' : "") +
        '<span class="cd">' + esc(desc) + "</span>" +
        '<div class="quick">' + SW[k].map((c) => '<button type="button" class="qs" style="background:' + c + '" data-quick="' + k + '" data-val="' + c + '" title="Use this color" aria-label="Use this color"></button>').join("") + "</div>" +
        (k === "text" ? '<div class="autotext">' + sw("autotext", "Automatic (always readable)", auto) + "</div>" : "") + "</div>";
    }).join("");
    return "<h2>Colors</h2><p>Click a big square to pick any color, or tap a little one to use it.</p>" + rows +
      "<h3>Boxes</h3>" + slider("boxes.transparency", "See-through boxes", "Higher lets the background (and effects) show through.", 0, 80, "%") +
      slider("boxes.glow", "Glow", "How much the boxes glow in your main color.", 0, 100, "") +
      slider("boxes.corners", "Rounded corners", "0 is square, 24 is very round.", 0, 24, "") +
      '<label class="switch small"><input type="checkbox" data-pref="hex"' + (showHex ? " checked" : "") + "><span></span>Show color codes (for people who like them)</label>" +
      '<div class="tip">💡 <b>Tip:</b> dark backgrounds with one bright main color look best. If something is hard to read, a yellow note appears above the preview with a <b>Fix it for me</b> button.</div>';
  }
  function paneButtons() {
    return "<h2>Buttons &amp; Labels</h2><p>How buttons, box titles and the little status tags look.</p>" + choices("buttons", K.BUTTONS, BTN_INFO) +
      "<h3>Logo</h3><p>The app name in the top-left corner.</p>" + choices("logo", K.LOGOS, LOGO_INFO, "three") +
      '<div class="tip">💡 <b>Tip:</b> move your mouse over the buttons in the preview to see how they react.</div>';
  }
  function paneEffects() {
    const on = state.background.effect !== "none";
    return "<h2>Background Effects</h2><p>Something moving behind your boxes.</p>" + choices("background.effect", K.EFFECTS, FX_INFO) +
      (on ? "<h3>Adjust it</h3>" + slider("background.density", "How much", "More rain, sparks or snow.", 10, 100, "") +
        slider("background.speed", "How fast", "", 10, 100, "") + slider("background.opacity", "How bright", "Keep it low so text stays easy to read.", 5, 60, "") : "") +
      '<div class="tip">💡 <b>Good to know:</b> effects stop by themselves when Asgard is in Lite layout, in Game mode, or hidden, so they never slow down your games. Tip: “See-through boxes” on the Colors tab lets more of the effect show.</div>';
  }
  function paneTextures() {
    const f = state.font, sample = (k) => '<div class="fontsample" style="font-family:' + esc(K.FONTS[f[k]].stack) + '">' + (k === "headings" ? "ASGARD · Games · Music" : "Starfall Odyssey · 3h 20m this week") + "</div>";
    const sel = (k) => '<select class="fontsel" data-font="' + k + '">' + Object.keys(K.FONTS).map((id) => '<option value="' + id + '"' + (f[k] === id ? " selected" : "") + ">" + esc(K.FONTS[id].label) + "</option>").join("") + "</select>";
    return "<h2>Textures</h2><p>A pattern on the background.</p>" + choices("texture.kind", K.TEXTURES, TEX_INFO, "three") +
      (state.texture.kind !== "none" ? slider("texture.strength", "How strong", "", 0, 100, "") + sw("texture.boxes", "Put it on the boxes too", state.texture.boxes) : "") +
      "<h3>Fonts</h3><p>Only fonts that come with Windows, so your theme looks the same on every PC.</p>" +
      "<b>Titles and logo</b>" + sel("headings") + sample("headings") + "<b>Everyday text</b>" + sel("text") + sample("text");
  }
  function panePictures() {
    const im = state.image;
    let h = "<h2>Your Pictures</h2><p>Add your own art: fill the background with it, or stick it in a corner.</p>" +
      '<div class="drop" id="dropZone" tabindex="0" role="button"><div class="big">🖼️</div><b>Drag a picture here</b><span class="muted">or click to choose one · PNG, JPG or WebP</span></div>';
    if (im) {
      h += '<div class="picbox"><img src="' + esc(im.data) + '" alt="Your picture"><div><b>Your picture</b><div class="muted">' + Math.round(im.data.length * 0.75 / 1024) + " KB, cleaned and ready</div>" +
        '<button type="button" class="tbtn dangerish" data-act="rmpic" style="margin-top:6px">🗑 Remove picture</button></div></div>' +
        '<div class="choices">' + [["background", "🌄", "Fill the background"], ["sticker", "🏷️", "Stick it in a corner"]].map((u) =>
          '<button type="button" class="choice' + (im.use === u[0] ? " on" : "") + '" data-picuse="' + u[0] + '"><span class="ce">' + u[1] + "</span><b>" + u[2] + "</b></button>").join("") + "</div>";
      if (im.use === "background") h += slider("image.dim", "Darken it", "Darker makes text easier to read on top of your picture.", 0, 90, "%");
      else h += "<h3>Which corner</h3><div class=\"corners\">" + [["top-left", "↖ Top left"], ["top-right", "↗ Top right"], ["bottom-left", "↙ Bottom left"], ["bottom-right", "↘ Bottom right"]].map((c) =>
        '<button type="button" class="choice' + (im.corner === c[0] ? " on" : "") + '" data-corner="' + c[0] + '"><b>' + c[1] + "</b></button>").join("") + "</div>" +
        slider("image.size", "Size", "", 60, 360, "px") + slider("image.tilt", "Tilt", "Tip it a little for a sticker feel.", -20, 20, "°");
    }
    return h + '<div class="tip">💡 <b>Good to know:</b> the picture is saved inside the theme file, so sharing one file shares everything. Big pictures are shrunk automatically (themes stay under 1.5 MB), and only the picture itself is kept, never hidden extras.</div>';
  }
  const PANES = { colors: paneColors, buttons: paneButtons, effects: paneEffects, textures: paneTextures, pictures: panePictures };
  function renderPane() {
    const pane = $("pane"), y = pane.scrollTop, focusKey = document.activeElement && pane.contains(document.activeElement) ? keyOf(document.activeElement) : null;
    pane.innerHTML = PANES[tab]();
    pane.scrollTop = y;
    if (focusKey) { const el = pane.querySelector(focusKey); if (el) el.focus(); }
    document.querySelectorAll(".tab").forEach((b) => { const on = b.dataset.tab === tab; b.classList.toggle("on", on); b.setAttribute("aria-selected", String(on)); });
  }
  function keyOf(el) {
    for (const a of ["data-range", "data-pick", "data-color", "data-hex", "data-check", "data-font", "data-quick", "data-corner", "data-picuse"]) {
      if (el.hasAttribute(a)) return "[" + a + '="' + el.getAttribute(a) + '"]' + (el.dataset.val ? '[data-val="' + el.dataset.val + '"]' : "");
    }
    return el.id ? "#" + el.id : null;
  }
  function updatePaneValues() {
    $("pane").querySelectorAll("[data-range]").forEach((i) => { const v = getPath(i.dataset.range); if (document.activeElement !== i) i.value = v; const o = $("pane").querySelector('[data-out="' + i.dataset.range + '"]'); if (o) o.textContent = v + i.dataset.unit; });
  }

  // ---------------------------------------------------------------- pane events
  function wirePane() {
    const pane = $("pane");
    pane.addEventListener("input", (e) => {
      const el = e.target;
      if (el.dataset.range) { const path = el.dataset.range, v = Math.round(+el.value); change("r:" + path, (t) => setPath(t, path, v)); }
      else if (el.dataset.color) { const k = el.dataset.color, v = el.value.toLowerCase(); change("c:" + k, (t) => { t.palette[k] = v; }); const s = el.parentElement; if (s) s.style.background = v; }
    });
    pane.addEventListener("change", (e) => {
      const el = e.target;
      if (el.dataset.color) renderPane();
      else if (el.dataset.hex) {
        let v = el.value.trim(); if (/^[0-9a-f]{6}$/i.test(v)) v = "#" + v;
        if (!K.isHex(v)) { status("Color codes look like #12ab34.", "bad"); renderPane(); return; }
        const k = el.dataset.hex; change("", (t) => { t.palette[k] = v.toLowerCase(); }, { pane: true });
      } else if (el.dataset.check === "autotext") change("", (t) => { if (el.checked) delete t.palette.text; else t.palette.text = textColor(t); }, { pane: true });
      else if (el.dataset.check) { const path = el.dataset.check; change("", (t) => setPath(t, path, el.checked), { pane: true }); }
      else if (el.dataset.font) { const k = el.dataset.font; change("", (t) => { t.font[k] = el.value; }, { pane: true }); }
      else if (el.dataset.pref === "hex") { store.set("studio_hex", el.checked); renderPane(); }
    });
    pane.addEventListener("click", (e) => {
      const b = e.target.closest("button, #dropZone"); if (!b) return;
      if (b.dataset.quick) { const k = b.dataset.quick, v = b.dataset.val; change("", (t) => { t.palette[k] = v; }, { pane: true }); }
      else if (b.dataset.pick) { const path = b.dataset.pick, v = b.dataset.val; change("", (t) => setPath(t, path, v), { pane: true }); }
      else if (b.dataset.corner) { const v = b.dataset.corner; change("", (t) => { t.image.corner = v; }, { pane: true }); }
      else if (b.dataset.picuse) usePicAs(b.dataset.picuse);
      else if (b.dataset.act === "rmpic") { picOriginal = null; imgLum = null; change("", (t) => { t.image = null; }, { pane: true }); status("Picture removed."); }
      else if (b.id === "dropZone") $("filePic").click();
    });
    pane.addEventListener("keydown", (e) => { if (e.target.id === "dropZone" && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); $("filePic").click(); } });
  }

  // ---------------------------------------------------------------- pictures
  function measure(data) {
    return new Promise((res) => {
      const im = new Image();
      im.onload = () => { try { const c = document.createElement("canvas"); c.width = 24; c.height = 24; const x = c.getContext("2d"); x.drawImage(im, 0, 0, 24, 24);
        const d = x.getImageData(0, 0, 24, 24).data; let s = 0, n = 0; for (let i = 0; i < d.length; i += 4) { s += K.lum(rgbToHex(d[i], d[i + 1], d[i + 2])) * (d[i + 3] / 255); n++; } res(s / n); } catch (e) { res(null); } };
      im.onerror = () => res(null); im.src = data;
    });
  }
  async function addPicture(file) {
    if (!/^image\/(png|jpeg|webp)$/.test(file.type)) { modal("That picture type isn't supported", "<p>Please use a <b>PNG</b>, <b>JPG</b> or <b>WebP</b> picture.</p>"); return; }
    if (file.size > 40 * 1024 * 1024) { modal("That picture is very large", "<p>Please pick a picture under 40 MB. (It will be shrunk to fit a theme anyway.)</p>"); return; }
    status("Getting your picture ready…");
    const src = await new Promise((res) => { const r = new FileReader(); r.onload = () => res(r.result); r.onerror = () => res(null); r.readAsDataURL(file); });
    if (!src) { status("Couldn't read that picture.", "bad"); return; }
    const use = state.image ? state.image.use : "background";
    const out = await K.reencode(src, use);
    if (out.err) { modal("Couldn't use that picture", "<p>" + esc(out.err) + "</p>"); status(out.err, "bad"); return; }
    picOriginal = src; imgLum = await measure(out.data);
    change("", (t) => { t.image = Object.assign({ use, dim: 45, corner: "bottom-right", size: 180, tilt: use === "sticker" ? -6 : 0 }, t.image || {}, { data: out.data, use }); }, { pane: true });
    if (tab !== "pictures") { tab = "pictures"; renderPane(); }
    status("Picture added (" + out.w + "×" + out.h + ").", "good");
  }
  async function usePicAs(use) {
    if (!state.image || state.image.use === use) return;
    const out = await K.reencode(picOriginal || state.image.data, use);
    if (out.err) { status(out.err, "bad"); return; }
    imgLum = await measure(out.data);
    change("", (t) => { t.image.use = use; t.image.data = out.data; if (use === "sticker" && !t.image.tilt) t.image.tilt = -6; }, { pane: true });
  }

  // ---------------------------------------------------------------- open / save
  async function openText(text, fileName) {
    const r = K.validate(text);
    if (r.err) { modal("Couldn't open that theme", "<p>" + esc(r.err) + "</p><p class=\"muted\">Only .asgard-theme files made for Asgard or this Studio can be opened.</p>"); status(r.err, "bad"); return false; }
    let t = r.theme, note = "";
    if (t.base !== "custom") {
      const map = { cyberpunk: "cyber", gachi: "gachi", viking: "viking", gothic: "romance", pop: "retro", mono: "blank", asgard: "blank" };
      const st = STARTERS.find((s) => s.id === (map[t.base] || "blank"));
      const keep = { background: t.background, image: t.image, name: t.name, author: t.author };
      t = normalize(Object.assign({}, st.theme, keep));
      note = "This theme used one of Asgard's built-in styles, so it opened with the closest starting look. Its effect and picture were kept.";
    } else t = normalize(t);
    if (t.image) {
      const out = await K.reencode(t.image.data, t.image.use);   // re-draw it so only plain pixels remain
      if (out.err) { t.image = null; note += " Its picture couldn't be read, so it was left out."; } else { t.image.data = out.data; picOriginal = null; imgLum = await measure(out.data); }
    }
    hideStart();
    setState(t, "Opened “" + t.name + "”" + (fileName ? " from " + fileName : "") + ".");
    if (r.warnings && r.warnings.length) note += " " + r.warnings.join(" ");
    if (note.trim()) modal("Opened “" + t.name + "”", "<p>" + esc(note.trim()) + "</p>");
    return true;
  }
  function openFile(file) {
    if (!file) return;
    if (file.size > K.LIMITS.fileBytes) { modal("That file is too big", "<p>Theme files are at most 1.5 MB.</p>"); return; }
    const r = new FileReader();
    r.onload = () => openText(String(r.result), file.name);
    r.onerror = () => status("Couldn't read that file.", "bad");
    r.readAsText(file);
  }
  function themeText() {
    const name = K.cleanText($("themeName").value, 40) || "My theme";
    if (name !== state.name) state.name = name;
    const text = K.serialize(state);
    const chk = K.validate(text);
    if (chk.err) { modal("This theme can't be saved yet", "<p>" + esc(chk.err) + "</p>"); return null; }
    return text;
  }
  async function api(path, body) {
    const r = await fetch(path, body === undefined ? { headers: { "X-Studio": "1" } } : { method: "POST", headers: { "Content-Type": "application/json", "X-Studio": "1" }, body: JSON.stringify(body) });
    let j = null; try { j = await r.json(); } catch (e) { /* not json */ }
    if (!r.ok || !j) throw new Error((j && j.message) || "The Studio program didn't answer.");
    return j;
  }
  function download(name, text) {
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: "application/json" })); a.download = name;
    document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  // -> {path, file} or null
  async function saveToDisk(text, quiet) {
    const file = fileSlug(state.name) + ".asgard-theme";
    if (!HAS_APP) { download(file, text); return { path: "your Downloads folder", file }; }
    try {
      let r = await api("/api/save", { file, text, overwrite: !!quiet });
      if (r.exists) {
        const ok = await modal("Replace the old file?", "<p>A theme file called <b>" + esc(file) + "</b> is already in your <b>Asgard Themes</b> folder.</p>",
          [{ label: "Cancel", value: false }, { label: "Replace it", cls: "go", value: true }]);
        if (!ok) return null;
        r = await api("/api/save", { file, text, overwrite: true });
      }
      return { path: r.path, file: r.file, dir: r.dir };
    } catch (e) { modal("Couldn't save", "<p>" + esc(e.message) + "</p>"); return null; }
  }
  async function save() {
    const text = themeText(); if (!text) return;
    const r = await saveToDisk(text); if (!r) return;
    status("Saved " + r.file, "good");
    modalRuns.showFolder = () => api("/api/show", { file: r.file }).catch(() => {});
    modal("Saved! 🎉", "<p>Your theme is saved as <b>" + esc(r.file) + "</b> in:</p><p><code>" + esc(r.dir || r.path) + "</code></p><p>Share that one file with friends. It has everything, pictures included.</p>" +
      (HAS_APP ? '<p><button type="button" class="tbtn" data-run="showFolder">📁 Show it in its folder</button></p>' : ""));
  }
  const STEPS_ASGARD = (file) => "<ol><li>In Asgard, click the <b>🎨</b> button at the top.</li><li>Click <b>⇧ Import theme…</b> at the bottom, then pick <b>" + esc(file) + "</b> from your <b>Documents › Asgard Themes</b> folder.</li></ol><p class=\"muted\">Needs Asgard 1.3 or newer for buttons, fonts, textures and pictures.</p>";
  const STEPS_VALHALLA = (file) => "<ol><li>In Valhalla, tap the <b>scene button</b> at the top (it shows the current colors, like ᛟ Valhalla).</li><li>Tap <b>⇧ Import theme…</b>, then pick <b>" + esc(file) + "</b> from your <b>Documents › Asgard Themes</b> folder.</li></ol>";
  async function useInAsgard() {
    const text = themeText(); if (!text) return;
    let st = { running: false, inbox: false };
    if (HAS_APP) { try { st = await api("/api/asgard"); } catch (e) { /* treat as not running */ } }
    if (st.running && st.inbox) {
      const go = await modal("Send it to Asgard?", "<p>Asgard is open on this PC. Send <b>" + esc(state.name) + "</b> to it now?</p><p class=\"muted\">Asgard shows a message at the bottom of its screen. Click <b>Add it</b> there and your theme is on.</p>",
        [{ label: "Cancel", value: false }, { label: "Just save the file", value: "save" }, { label: "🚀 Send to Asgard", cls: "go", value: "send" }]);
      if (!go) return;
      const saved = await saveToDisk(text, true);
      if (go === "save") { if (saved) modal("Saved", "<p>To use it:</p>" + STEPS_ASGARD(saved.file)); return; }
      try {
        await api("/api/asgard/send", { text });
        status("Sent to Asgard.", "good");
        modal("Sent! 🚀", "<p>Now look at Asgard: click <b>Add it</b> in the message at the bottom of the screen.</p><p class=\"muted\">Missed it? You can also add it the usual way:</p>" + STEPS_ASGARD(saved ? saved.file : fileSlug(state.name) + ".asgard-theme"));
      } catch (e) { modal("Couldn't send it", "<p>" + esc(e.message) + "</p><p>Your theme is saved, so you can add it by hand:</p>" + STEPS_ASGARD(saved ? saved.file : "")); }
      return;
    }
    const saved = await saveToDisk(text, true); if (!saved) return;
    const why = st.running ? "<p class=\"muted\">This copy of Asgard is an older version that can't receive themes directly, so here's the quick way.</p>"
      : "<p class=\"muted\">Asgard isn't open right now, so the theme was saved for you.</p>";
    modal("Two quick steps", "<p>Saved as <b>" + esc(saved.file) + "</b>.</p>" + why + STEPS_ASGARD(saved.file));
  }
  async function useInValhalla() {
    const text = themeText(); if (!text) return;
    const saved = await saveToDisk(text, true); if (!saved) return;
    modal("Use it in Valhalla", "<p>Saved as <b>" + esc(saved.file) + "</b>. Then:</p>" + STEPS_VALHALLA(saved.file) + "<p class=\"muted\">Needs Valhalla 2.2 or newer.</p>");
  }

  // ---------------------------------------------------------------- start screen
  function showStart(first) {
    const saved = store.get("studio_autosave", null);
    const cont = saved && saved.palette ? [{ id: "_continue", title: "Continue my theme", blurb: "“" + K.cleanText(saved.name, 40) + "”, right where you left off", emoji: "↩️", theme: saved }] : [];
    $("starterCards").innerHTML = cont.concat(STARTERS).map((s) => {
      const p = Object.assign({ text: K.autoText(s.theme.palette.bg) }, s.theme.palette);
      return '<button type="button" class="scard" data-starter="' + s.id + '"><div class="mini" style="background:' + p.bg + '"><span class="se">' + s.emoji + "</span>" +
        '<div class="mb" style="background:' + p.box + ";color:" + p.text + ";border:1px solid " + p.accent + '">' + esc(s.id === "_continue" ? K.cleanText(s.theme.name, 20) : s.title).toUpperCase() + "</div>" +
        '<div class="mr"><i style="background:' + p.accent + '"></i><i style="background:' + p.accent2 + '"></i><i style="background:' + p.box + '"></i></div></div>' +
        '<div class="st"><b>' + esc(s.title) + "</b><small>" + esc(s.blurb) + "</small></div></button>";
    }).join("");
    $("startClose").classList.toggle("hidden", first === true);
    $("start").classList.remove("hidden");
    const f = $("starterCards").querySelector(".scard"); if (f) f.focus();
  }
  function hideStart() { $("start").classList.add("hidden"); }
  function pickStarter(id) {
    if (id === "_continue") { const s = normalize(store.get("studio_autosave", null)); hideStart(); setState(s, "Welcome back."); return; }
    const s = STARTERS.find((x) => x.id === id); if (!s) return;
    const t = normalize(JSON.parse(JSON.stringify(s.theme)));
    picOriginal = null; imgLum = null;
    hideStart(); setState(t, "Started from " + s.title + ". Change anything you like.");
  }

  // ---------------------------------------------------------------- wiring
  window.studioPreviewReady = () => { previewReady = true; const w = frameWin(); w.studioPreview.mode(mode); w.studioPreview.freeze($("freezeFx").checked); if (state) w.studioPreview.show(state); };
  function start() {
    wirePane();
    document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => { tab = b.dataset.tab; renderPane(); $("pane").scrollTop = 0; }));
    $("themeName").addEventListener("input", (e) => { const v = K.cleanText(e.target.value, 40); change("name", (t) => { t.name = v || "My theme"; }); });
    $("undoBtn").onclick = undo; $("redoBtn").onclick = redo; $("surpriseBtn").onclick = surprise;
    $("startBtn").onclick = () => showStart(false); $("openBtn").onclick = () => $("fileTheme").click(); $("startOpen").onclick = () => $("fileTheme").click();
    $("startClose").onclick = hideStart;
    $("saveBtn").onclick = save; $("useBtn").onclick = useInAsgard; $("useVBtn").onclick = useInValhalla;
    $("fileTheme").onchange = (e) => { openFile(e.target.files[0]); e.target.value = ""; };
    $("filePic").onchange = (e) => { if (e.target.files[0]) addPicture(e.target.files[0]); e.target.value = ""; };
    $("starterCards").addEventListener("click", (e) => { const b = e.target.closest("[data-starter]"); if (b) pickStarter(b.dataset.starter); });
    $("warnings").addEventListener("click", (e) => { const b = e.target.closest("[data-fix]"); if (b) fix(b.dataset.fix); });
    document.querySelectorAll(".seg-b").forEach((b) => b.addEventListener("click", () => {
      mode = b.dataset.mode; document.querySelectorAll(".seg-b").forEach((x) => { x.classList.toggle("on", x === b); x.setAttribute("aria-checked", String(x === b)); });
      if (previewReady) frameWin().studioPreview.mode(mode);
      $("useBtn").classList.toggle("go", mode === "asgard"); $("useVBtn").classList.toggle("go", mode === "valhalla");
    }));
    $("freezeFx").onchange = (e) => { if (previewReady) frameWin().studioPreview.freeze(e.target.checked); };
    $("helpBtn").onclick = () => modal("How to make a theme", "<ol><li>Pick a <b>starting look</b> (✨ Starting looks).</li><li>Change things with the tabs on the left. The preview updates right away.</li>" +
      "<li>Made a mistake? Press <b>↶ Undo</b>. Feeling lucky? Press <b>🎲 Surprise me</b>.</li><li>Press <b>💾 Save theme</b> to keep it, or <b>🚀 Use in Asgard</b> to put it on.</li></ol>" +
      "<p class=\"muted\">Shortcuts: Ctrl+Z undo, Ctrl+Y redo, Ctrl+S save, Ctrl+O open. You can also drag a picture or a theme file onto this window.</p>");
    $("aboutBtn").onclick = () => modal("About Asgard Theme Studio", "<p><b>Asgard Theme Studio " + VERSION + "</b><br>Created November 22, 2026 by The_Mead_Maker &amp; Odin.<br>Copyright © 2026 The_Mead_Maker &amp; Odin. MIT License.</p>" +
      "<p>Makes themes for Asgard and Valhalla. It works offline: nothing is downloaded and nothing is sent anywhere, except to Asgard on this PC when you press Use in Asgard.</p>" +
      "<p class=\"muted\">Theme files hold only colors, choices from built-in lists, and your picture. They never contain code or links.</p>");
    document.addEventListener("keydown", (e) => {
      if (!$("modal").classList.contains("hidden")) return;
      const k = e.key.toLowerCase(), typing = /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName) && e.target.type !== "range" && e.target.type !== "checkbox";
      if (e.ctrlKey && k === "z" && !e.shiftKey && !typing) { e.preventDefault(); undo(); }
      else if (e.ctrlKey && (k === "y" || (k === "z" && e.shiftKey)) && !typing) { e.preventDefault(); redo(); }
      else if (e.ctrlKey && k === "s") { e.preventDefault(); save(); }
      else if (e.ctrlKey && k === "o") { e.preventDefault(); $("fileTheme").click(); }
      else if (k === "escape" && !$("start").classList.contains("hidden") && !$("startClose").classList.contains("hidden")) hideStart();
    });
    // Drag and drop: pictures go to Your Pictures, theme files open.
    let depth = 0;
    const hint = (on) => $("dropHint").classList.toggle("hidden", !on);
    document.addEventListener("dragenter", (e) => { if (e.dataTransfer && [...e.dataTransfer.types].includes("Files")) { depth++; hint(true); } });
    document.addEventListener("dragleave", () => { depth = Math.max(0, depth - 1); if (!depth) hint(false); });
    document.addEventListener("dragover", (e) => { e.preventDefault(); });
    document.addEventListener("drop", (e) => {
      e.preventDefault(); depth = 0; hint(false);
      const f = e.dataTransfer && e.dataTransfer.files[0]; if (!f) return;
      if (/^image\//.test(f.type)) { hideStart(); addPicture(f); }
      else if (/\.(asgard-theme|json)$/i.test(f.name)) openFile(f);
      else modal("That file can't be used here", "<p>Drop a <b>picture</b> (PNG, JPG, WebP) or a <b>.asgard-theme</b> file.</p>");
    });
    if (HAS_APP) {   // tell the Studio program the window is still open (it closes itself a little after the window closes)
      const ping = () => api("/api/ping", {}).catch(() => {});
      ping(); setInterval(ping, 10000);
      window.addEventListener("pagehide", () => { try { navigator.sendBeacon("/api/bye", ""); } catch (e) { /* closing anyway */ } });
    }
    state = normalize(STARTERS.find((s) => s.id === "blank").theme);
    refresh(true);
    showStart(true);
  }
  window.studio = { get state() { return state; }, openText, pickStarter, surprise, undo, redo, serialize: () => themeText(), addPicture, version: VERSION };
  start();
})();

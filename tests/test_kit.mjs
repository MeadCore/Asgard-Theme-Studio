// Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
// Checks theme-kit.js validate() against the same cases as theme_check.py (run test_theme_check.py first: it writes cases.json),
// plus save -> open round trips for every starter look.  node tests/test_kit.mjs
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import vm from "vm";
const require = createRequire(import.meta.url);
const here = path.dirname(new URL(import.meta.url).pathname);
const K = require(path.join(here, "..", "static", "theme-kit.js"));
let fails = 0;
const line = (ok, name, msg) => { if (!ok) fails++; console.log(`${ok ? "PASS" : "FAIL"} ${name.padEnd(36)} ${msg}`); };

for (const c of JSON.parse(fs.readFileSync(path.join(here, "cases.json"), "utf8"))) {
  const r = K.validate(c.text);
  line(!r.err === c.ok, c.name, r.err || "ok");
}
// Starter looks: serialize -> validate -> serialize gives the same file.
const sb = { window: {} }; vm.createContext(sb);
vm.runInContext(fs.readFileSync(path.join(here, "..", "static", "starters.js"), "utf8"), sb);
for (const s of sb.window.STUDIO_STARTERS) {
  const a = K.serialize(K.validate(JSON.stringify(s.theme)).theme || s.theme, true);
  const b = K.validate(a);
  const c = b.theme ? K.serialize(b.theme, true) : "";
  line(!b.err && a === c, "round trip: " + s.title, b.err || `${a.length} bytes, identical after save/open`);
}
// Python and JS agree on the normalized result for the trash-rain example.
const tr = K.validate(fs.readFileSync(path.join(here, "..", "themes", "trash-rain.asgard-theme"), "utf8"));
line(!tr.err && tr.theme.buttons === "sticker" && tr.theme.background.effect === "matrix-rain" && tr.theme.image.use === "sticker", "trash-rain normalized", JSON.stringify({ b: tr.theme.buttons, fx: tr.theme.background, img: tr.theme.image.use }));
console.log("\n" + (fails ? `${fails} FAILED` : "ALL PASSED"));
process.exit(fails ? 1 : 0);

<!-- Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License. -->
# The `.asgard-theme` file format (version 2)

A theme file is a small JSON text file. It describes a look using **only data**: colours, numbers and names picked from
built-in lists, plus at most one picture. It can never contain code, CSS, fonts, or links. Asgard, Valhalla and Asgard Theme
Studio all check every file with the same strict checker (`theme-kit.js` in the apps, `theme_check.py` on the Python side)
before anything is used, and anything unknown is rejected with a plain-words message.

Version 1 files (`"asgard_theme": 1`, colours only plus an optional `"effect"`) keep working everywhere. Version 2 adds
buttons and labels, logo, fonts, textures, more background effects and a picture.

## Example

```json
{
  "asgard_theme": 2,
  "name": "Trash Rain",
  "author": "Someone",
  "base": "custom",
  "palette": { "bg": "#0d0a07", "box": "#1f1710", "accent": "#e8261f", "accent2": "#ffd400", "text": "#f3e9d2" },
  "boxes": { "transparency": 45, "glow": 10, "corners": 4 },
  "buttons": "sticker",
  "logo": "sticker",
  "font": { "headings": "bold", "text": "clean" },
  "texture": { "kind": "grunge", "strength": 55, "boxes": false },
  "background": { "effect": "matrix-rain", "density": 70, "speed": 55, "opacity": 55 },
  "image": { "use": "sticker", "data": "data:image/png;base64,iVBORw0KGgo...", "corner": "bottom-right", "size": 150, "tilt": -8 }
}
```

## Settings

Only these top-level keys are allowed: `asgard_theme`, `name`, `author`, `base`, `palette`, `boxes`, `buttons`, `logo`,
`font`, `texture`, `background`, `image`. Missing optional settings use the default shown.

| Key | Allowed values | Default |
|---|---|---|
| `asgard_theme` | `2` (or `1` for the old format) | required |
| `name` | text, up to 40 characters (`< > { } \ ; ` " ` and control characters are removed) | required |
| `author` | text, up to 40 characters | empty |
| `base` | `custom`, or a built-in Asgard style: `asgard`, `cyberpunk`, `viking`, `gothic`, `mono`, `pop`, `gachi` | `custom` |
| `palette` | only with `base: "custom"` (then required): `bg`, `box`, `accent`, `accent2` as `#rrggbb`, optional `text` | – |
| `boxes` | only with `custom`: `transparency` 0–80, `glow` 0–100, `corners` 0–24 | 0 / 40 / 12 |
| `buttons` | `plain`, `pill`, `sticker` (tilted stickers and tape), `clipped` (cut corners, second colour on hover), `neon`, `rose-gold` | `plain` |
| `logo` | `plain`, `neon`, `glitch`, `sticker`, `gold`, `chrome`, `stencil` | `plain` |
| `font` | `{ "headings": id, "text": id }` (or one id for both). Ids: `clean`, `rounded`, `bold`, `techno`, `mono`, `typewriter`, `serif`, `fancy`, `gothic`, `marker`. All are fonts that ship with Windows; each falls back to a safe family. | `clean` |
| `texture` | `{ "kind": "none" \| "marble" \| "grunge" \| "paper" \| "carbon", "strength": 0–100, "boxes": true/false }` (or just the kind) | `none`, 50, false |
| `background` | `{ "effect": "none" \| "matrix-rain" \| "embers" \| "snow" \| "scanlines" \| "film-grain", "density": 10–100, "speed": 10–100, "opacity": 5–60 }` | `none`, 60, 50, 30 |
| `image` | `{ "use": "background" \| "sticker", "data": data URI, "dim": 0–90, "corner": "top-left" \| "top-right" \| "bottom-left" \| "bottom-right", "size": 60–360, "tilt": -20–20 }` | dim 45 (background) / 0, `bottom-right`, 180, 0 |

`buttons`, `logo`, `font` and `texture` need `base: "custom"` (the built-in styles have their own). A built-in base may still
add a `background` effect and an `image`.

Numbers outside a range are clamped in version 2 (version 1 keeps its stricter "whole number in range" rule). Unknown keys,
unknown names and wrong types are errors.

### Readability

If `palette.text` is given it must have a contrast of at least 4.5:1 with both `bg` and `box`. Version 1 rejects the file
otherwise; version 2 loads it with a readable text colour instead (and says so). Theme Studio warns while you edit
("Text may be hard to read…") and has a **Fix it for me** button.

### The picture

* Only `data:image/png;base64,…`, `data:image/jpeg;base64,…` or `data:image/webp;base64,…`.
* At most 1,500,000 characters of data URI (about 1.1 MB of picture). The whole file may be at most **1.5 MB**
  (1,572,864 bytes); version 1 files stay limited to 16,000 bytes.
* The first bytes must really be a PNG, JPEG or WebP picture of the declared type.
* Before use, the apps **re-draw the picture on a canvas** and keep only the new pixels, so nothing hidden in the original file
  survives. Theme Studio shrinks pictures (long side 1920 px for backgrounds, 640 px for stickers) to fit.
* Asgard and Valhalla keep pictures in the browser's IndexedDB (they are too big for localStorage).

### Always rejected

Any file containing `url(`, `expression(`, `javascript:`, `vbscript:`, `@import`, `<!--`, `\u003c`, or an HTML tag such as
`<script`, `<style`, `<svg`, `<iframe`, `<object`, `<embed`, `<link`, `<meta` anywhere in its text is refused before it is
even read as JSON.

## How the apps draw it

* `palette` + `boxes` become the same CSS variables as Asgard's Custom style (`AsgardThemeKit.vars`).
* `buttons`, `logo`, `font`, `texture` become `data-tk-*` attributes on `<html>`; the looks themselves live in
  `theme-kit.css`. Only whitelisted names ever reach the page.
* `background` effects are drawn by the apps' own code (`AsgardThemeKit.painter`) on one canvas behind everything. In Asgard
  they stop in Lite layout, in Game mode, when the tab is hidden, and (with Memory saver) when the window isn't focused.
  A theme that names an effect still animates when Windows "Animation effects" is off, because choosing the theme is
  asking for it.
* Asgard: 🎨 › **Import theme…** (or **Add it** after "Use in Asgard" in Theme Studio). Up to 30 imported themes.
* Valhalla: scene button › **Your themes** › **Import theme…**. The theme's colours also become the scene colours for the lights.

## "Use in Asgard" hand-off

Theme Studio checks the theme, then sends it from its own program (not the web page) to
`POST http://127.0.0.1:8777/api/themes/inbox` with header `X-Asgard-Studio: 1` and body `{"text": "<file text>"}`.
Asgard accepts this only from the PC itself (never from paired phones or other sites), checks it with `theme_check.py`,
and holds one theme in memory for 10 minutes. Nothing changes until you click **Add it** in Asgard; the page then fetches
it (`POST /api/themes/inbox/take {"id"}`) and checks it again like any imported file.

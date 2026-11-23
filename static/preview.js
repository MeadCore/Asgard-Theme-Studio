/* Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin.
   Copyright (c) 2026 The_Mead_Maker & Odin. MIT License, see LICENSE. Keep this notice.
   Draws a checked theme on the pretend screen. The Studio calls window.studioPreview.show(theme) on every change. */
(function () {
  "use strict";
  const K = window.AsgardThemeKit, root = document.documentElement;
  const fx = K.runner(document, {});
  let varKeys = [];
  window.studioPreview = {
    show(t) {
      varKeys.forEach((k) => root.style.removeProperty(k));
      const v = K.vars(t.palette, t.boxes);
      varKeys = Object.keys(v);
      for (const k of varKeys) root.style.setProperty(k, v[k]);
      K.applySkin(root, t);
      K.applyImage(document, t.image, t.image && t.image.data);
      const b = t.background || {};
      if (b.effect && b.effect !== "none") fx.set(b.effect, b, { accent: t.palette.accent, accent2: t.palette.accent2, text: v["--text"] });
      else fx.stop();
    },
    mode(m) { document.body.className = m === "valhalla" ? "mode-valhalla" : "mode-asgard"; },
    freeze(on) { fx.freeze(on); },
  };
  window.addEventListener("resize", () => fx.wake());
  // Clicks on the pretend buttons do nothing.
  document.addEventListener("click", (e) => e.preventDefault(), true);
  if (window.parent && window.parent !== window && window.parent.studioPreviewReady) window.parent.studioPreviewReady();
})();

// ------------------------------------------------------------------ v17 painted vistas: the bench rooms get their own view
// Each vista bench room (room.def.vista, a 'bench' with a view) can register a hand-painted backdrop that replaces its
// biome's parallax in that room only. Art: art/gen_vista_<room>.py → assets/vista_<room>_<layer>.png (+ .json, tag 'loop').
//   vistaRegister('R11', { tint: '#0b0a12', layers: [
//     { sheet: 'vista_r11_sky', fac: 0.02, vfac: 0.01 },              // far: barely moves
//     { sheet: 'vista_r11_far', fac: 0.08, vfac: 0.03 },
//     { sheet: 'vista_r11_mid', fac: 0.25, vfac: 0.08, wrap: false, x: 40 } ],   // wrap:false = one painting placed at x
//     fx(t, cam) {} });                                                  // optional: restrained motion over the layers
// Layer fields: fac / vfac (scroll factors like drawParallax's 0.08 / 0.02 far, 0.3 / 0.08 mid), wrap (default true:
// tiles horizontally), x (wrap:false: screen x of the painting's left edge at cam.x = 0), dy (extra vertical offset),
// fps (frame rate of the 'loop' tag, default 6), alpha. Layers taller than H rise into the sky a bench's pulled-back
// view opens up (43_systems.js sysDrawVista); they are bottom-anchored like the biome layers.
const VISTA_BG = {};
function vistaRegister(id, o) { VISTA_BG[id] = o; }
function vistaLayer(L) {
  const sh = sheet(L.sheet); if (!sh || !sh.ok) return;
  const t = sh.tag('loop'), n = t ? t.to - t.from + 1 : 1, fi = t ? t.from + Math.floor(time * (L.fps || 6)) % n : 0, f = sh.frames[fi];
  const oy = Math.round(clamp(-cam.y * (L.vfac || 0), -(f.h - H) - 20, 20)) + (H - f.h) + (L.dy || 0);
  const a = L.alpha === undefined ? 1 : L.alpha; if (a < 1) g.globalAlpha = a;
  if (L.wrap === false) g.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round((L.x || 0) - cam.x * (L.fac || 0)), oy, f.w, f.h);
  else { const ox = -((cam.x * (L.fac || 0)) % f.w + f.w) % f.w; for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy, f.w, f.h); }
  if (a < 1) g.globalAlpha = 1;
}
{ const _dp = drawParallax;
  drawParallax = function () {   // eslint-disable-line no-func-assign
    const V = room && room.def && VISTA_BG[room.id];
    if (!V || !V.layers.every(L => { const s = sheet(L.sheet); return s && s.ok; })) return _dp.apply(this, arguments);   // art missing: the biome's
    g.fillStyle = V.tint || (AREAS[room.def.biome] || AREAS.ramparts).tint; g.fillRect(0, 0, W, H);
    for (const L of V.layers) vistaLayer(L);
    if (V.fx) { g.save(); try { V.fx(time, cam); } catch (e) { console.error(e); } g.restore(); }
  }; }

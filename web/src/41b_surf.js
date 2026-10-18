// ------------------------------------------------------------------ v17 shading phase 2: surface normals (docs/v17/shading_phase2.md)
// Settings › Graphics › Surface lighting. Under Dynamic lighting every lit sprite (drawSprite) and the room's cached layers
// (room.back / room.front) also draw their *normals* into `lowN`, in the same order, so whatever is on top wins. The lighting
// pass (41_light.js) then lets a lamp wrap around the knight, foes, bosses, props and the bricks: the side facing the light
// takes more of it, the far side falls into shade, and the silhouette edge facing it catches a rim.
// No normal art ships: normals are derived at runtime from the art itself, cached per sheet frame / per room layer:
//   height = silhouette bevel (distance to the sprite's edge, a quarter-circle profile, width ~0.7 × its thickest part)
//            × inner relief (distance to its own dark outline / mortar lines: each plate, brick or fold gets a small bevel)
//   normal = gradient of that height, quantized to 8 directions × 3 tilts (light lands in a few clean steps, no plastic smear).
// lowN pixel: R,G = normal x,y (128 ± 127, y down), B = luminance of the art pixel it was made from, A = coverage. The pass only
// trusts a normal when the lit layer still shows that very pixel (|lum − B| small): fx, water, fog, flashes and decor painted
// over a sprite or wall without normals fall back to flat (exactly the phase-1 look) instead of borrowing what lies beneath.
const [lowN, gN] = lxCanvas(), [lowBg, gBg] = lxCanvas(), [lowBgM, gBgM] = lxCanvas();   // normals; the backdrop (parallax / vista: far, and the biome's mid layer)
const LXN = { on: false, sync: 0, q: [], qk: new Set(), rooms: new WeakMap(), ms: 0, gen: 0, px: 0, budget: 3, tick: 0,
  scr: null, sx: null, sheets: new Set(), dbg: null };
// look knobs (LX_TUNE-style, tests tweak live): bevel profile, inner relief, normal tilt scale, quantization
// inner: depth (px) of the dip along inner lines, over Bi px: kept shallow, so plates and bricks only ever reach the first tilt step
// (a gentle turn), while the silhouette's outer pixel reaches the steepest one, the only step that takes a rim (no embossed decals)
const LXN_TUNE = { inner: 1.1, Bi: 2, tiltK: 1.0, dirs: 8, tilts: 3, bMin: 2, bMax: 16, bK: 1.3, room: { B: 3, Bi: 2, inner: 1.0 }, back: { Bi: 2, inner: 1.0 } };

// two-pass 3×3 chamfer distance (1, √2): d holds 0 at seeds and a big value elsewhere; capped at cap
function lxnDist(d, w, h, cap) {
  const D = 1.4142;
  for (let y = 0; y < h; y++) for (let x = 0, i = y * w; x < w; x++, i++) {
    let v = d[i]; if (v === 0) continue;
    if (x > 0 && d[i - 1] + 1 < v) v = d[i - 1] + 1;
    if (y > 0) { const j = i - w; if (d[j] + 1 < v) v = d[j] + 1; if (x > 0 && d[j - 1] + D < v) v = d[j - 1] + D; if (x < w - 1 && d[j + 1] + D < v) v = d[j + 1] + D; }
    d[i] = v < cap ? v : cap;
  }
  for (let y = h - 1; y >= 0; y--) for (let x = w - 1, i = y * w + x; x >= 0; x--, i--) {
    let v = d[i]; if (v === 0) continue;
    if (x < w - 1 && d[i + 1] + 1 < v) v = d[i + 1] + 1;
    if (y < h - 1) { const j = i + w; if (d[j] + 1 < v) v = d[j] + 1; if (x < w - 1 && d[j + 1] + D < v) v = d[j + 1] + D; if (x > 0 && d[j - 1] + D < v) v = d[j - 1] + D; }
    d[i] = v;
  }
  return d;
}
// the normals of one RGBA image. o: { B: silhouette bevel (px; null = auto from the thickest part, 0 = no silhouette term),
//   Bi: inner-line bevel, inner: 0..1 how much the inner lines carve, cell: per-16px-cell line threshold (room layers),
//   open: the image border is open air (sprite frames) or continues (room bands), amin: alpha that counts as art }
function lxnBuild(src, w, h, o) {
  const n = w * h, T = LXN_TUNE, amin = o.amin ?? 100, al = new Uint8Array(n), L = new Float32Array(n);
  for (let i = 0; i < n; i++) { const k = i * 4; al[i] = src[k + 3] >= amin ? 1 : 0; L[i] = (0.299 * src[k] + 0.587 * src[k + 1] + 0.114 * src[k + 2]) / 255; }
  // inner lines: art pixels clearly darker than their surroundings (outlines, mortar, the gaps between plates)
  const line = new Uint8Array(n), hist = new Uint32Array(64);
  const median = (x0, y0, x1, y1) => {
    hist.fill(0); let c = 0;
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) { const i = y * w + x; if (al[i]) { hist[Math.min(63, (L[i] * 64) | 0)]++; c++; } }
    if (!c) return 0; let acc = 0; for (let b = 0; b < 64; b++) { acc += hist[b]; if (acc * 2 >= c) return (b + 0.5) / 64; } return 0;
  };
  const C = o.cell ? 16 : 0;
  if (C) for (let cy = 0; cy < h; cy += C) for (let cx = 0; cx < w; cx += C) {
    const x1 = Math.min(w, cx + C), y1 = Math.min(h, cy + C), th = Math.max(0.035, median(cx, cy, x1, y1) * 0.62);
    for (let y = cy; y < y1; y++) for (let x = cx; x < x1; x++) { const i = y * w + x; line[i] = al[i] && L[i] < th ? 1 : 0; }
  } else { const th = Math.max(0.035, median(0, 0, w, h) * 0.62); for (let i = 0; i < n; i++) line[i] = al[i] && L[i] < th ? 1 : 0; }
  // silhouette distance (to open air), inner distance (to air or a line)
  const BIG = 1e4, dS = new Float32Array(n), dI = new Float32Array(n);
  for (let i = 0; i < n; i++) { dS[i] = al[i] ? BIG : 0; dI[i] = al[i] && !line[i] ? BIG : 0; }
  const open = o.open !== false;
  let pw = w, ph = h, dSp = dS, dIp = dI;
  if (open) {   // pad by one pixel of air so art touching the frame edge still gets an edge there
    pw = w + 2; ph = h + 2; dSp = new Float32Array(pw * ph); dIp = new Float32Array(pw * ph);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { dSp[(y + 1) * pw + x + 1] = dS[y * w + x]; dIp[(y + 1) * pw + x + 1] = dI[y * w + x]; }
  }
  const sil = o.B !== 0;
  if (sil) lxnDist(dSp, pw, ph, BIG);
  lxnDist(dIp, pw, ph, (o.Bi ?? T.Bi) + 1);
  let B = o.B;
  if (sil && B == null) {   // auto: a dome over the thickest part (bodies), but boxy art (tombs, crates, plinths: it fills most of its
    let m = 0; for (let i = 0; i < dSp.length; i++) if (dSp[i] > m && dSp[i] < BIG) m = dSp[i];   // bounding box) keeps a flat face
    let x0 = w, y0 = h, x1 = -1, y1 = -1, c = 0;                   // with bevelled edges
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (al[y * w + x]) { c++; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    const fill = c / Math.max(1, (x1 - x0 + 1) * (y1 - y0 + 1));
    B = Math.max(T.bMin, Math.min(T.bMax, m * T.bK * (fill > 0.72 ? 0.35 : fill > 0.6 ? 0.7 : 1)));
  }
  const Bi = o.Bi ?? T.Bi, inner = o.inner ?? T.inner, Hh = new Float32Array(n);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x; if (!al[i]) continue;
    const p = open ? (y + 1) * pw + x + 1 : i;
    let hs = 1;
    if (sil) { const t = Math.min(1, dSp[p] / B); hs = Math.sqrt(1 - (1 - t) * (1 - t)); }
    const ti = Math.min(1, dIp[p] / Bi), hi = Math.sqrt(1 - (1 - ti) * (1 - ti));
    Hh[i] = (sil ? B * hs : inner) - inner * (1 - hi);
  }
  // gradient -> quantized normal
  const out = new Uint8ClampedArray(n * 4), dirs = T.dirs, tilts = T.tilts, step = Math.PI * 2 / dirs, tk = T.tiltK;
  const at = (x, y) => (x < 0 || y < 0 || x >= w || y >= h) ? (open ? 0 : Hh[Math.min(h - 1, Math.max(0, y)) * w + Math.min(w - 1, Math.max(0, x))]) : Hh[y * w + x];
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x, k = i * 4;
    out[k + 2] = Math.round(L[i] * 255); out[k + 3] = src[k + 3];
    if (!al[i]) { out[k] = out[k + 1] = 128; continue; }
    const gx = (at(x + 1, y) - at(x - 1, y)) * 0.5 * tk, gy = (at(x, y + 1) - at(x, y - 1)) * 0.5 * tk, gm = Math.hypot(gx, gy);
    let nx = 0, ny = 0;
    if (gm > 0.08) {
      const ang = Math.round(Math.atan2(-gy, -gx) / step) * step, th = Math.atan(gm), tq = Math.min(tilts, Math.round(th / (Math.PI / 2) * (tilts + 0.6))) / tilts * (Math.PI / 2) * 0.86;
      nx = Math.cos(ang) * Math.sin(tq); ny = Math.sin(ang) * Math.sin(tq);
    }
    out[k] = Math.round(128 + nx * 127); out[k + 1] = Math.round(128 + ny * 127);
  }
  return out;
}

// ---- sprite frames: generated lazily (a small time budget per frame), cached per sheet / frame / facing
function lxnScratch(w, h) {
  if (!LXN.scr) { LXN.scr = document.createElement('canvas'); LXN.sx = LXN.scr.getContext('2d', { willReadFrequently: true }); }
  if (LXN.scr.width < w || LXN.scr.height < h) { LXN.scr.width = Math.max(LXN.scr.width, w); LXN.scr.height = Math.max(LXN.scr.height, h); }
  LXN.sx.clearRect(0, 0, w, h); return LXN.sx;
}
function lxnCanvasOf(px, w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const x = c.getContext('2d'); x.putImageData(new ImageData(px, w, h), 0, 0); return c;
}
function lxnGenFrame(sh, fi) {
  const f = sh.frames[fi], img = sh.img; if (!f || !img.complete || !img.naturalWidth) return false;
  const x = lxnScratch(f.w, f.h); x.drawImage(img, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
  const src = x.getImageData(0, 0, f.w, f.h).data, nrm = lxnBuild(src, f.w, f.h, { open: true }), mir = new Uint8ClampedArray(nrm);
  for (let i = 0; i < mir.length; i += 4) mir[i] = 256 - mir[i];   // drawn mirrored (facing the other way): x flips sign
  const C = sh._lxn || (sh._lxn = { f: [], m: [] });
  C.f[fi] = lxnCanvasOf(nrm, f.w, f.h); C.m[fi] = lxnCanvasOf(mir, f.w, f.h);
  LXN.px += f.w * f.h * 2; LXN.gen++; LXN.sheets.add(sh);
  return true;
}
function lxnWant(sh, fi) {   // queue this frame and the next few of the same animation (the sheet is usually played in order)
  for (let k = 0; k < 6; k++) {
    const j = fi + k; if (!sh.frames[j] || (sh._lxn && sh._lxn.f[j])) continue;
    const key = sh.name + ':' + j; if (LXN.qk.has(key)) continue;
    LXN.qk.add(key); if (k === 0) LXN.q.unshift([sh, j, key]); else LXN.q.push([sh, j, key]);
  }
}
// ---- room layers: their normals are built in 32-row bands around the camera, a few per frame
const LXN_BAND = 32;
function lxnRoomEntry(cv, kind) {
  let E = LXN.rooms.get(cv);
  if (!E) {
    const c = document.createElement('canvas'); c.width = cv.width; c.height = cv.height;
    const bands = []; for (let y = 0; y < cv.height; y += LXN_BAND) bands.push(y);
    const cy = (LX.cy || 0) + H / 2; bands.sort((a, b) => Math.abs(a + 16 - cy) - Math.abs(b + 16 - cy));
    E = { c, x: c.getContext('2d'), bands, kind, done: false };
    LXN.rooms.set(cv, E); LXN.q.push([null, cv, E]);
  }
  return E;
}
function lxnGenBand(cv, E) {
  const y0 = E.bands.shift(); if (y0 === undefined) { E.done = true; return true; }
  const o = E.kind === 'back' ? LXN_TUNE.back : LXN_TUNE.room, M = 6, top = Math.max(0, y0 - M), bot = Math.min(cv.height, y0 + LXN_BAND + M), w = cv.width, h = bot - top;
  let src; try { src = cv.getContext('2d').getImageData(0, top, w, h).data; } catch (e) { E.done = true; E.bands.length = 0; return true; }
  const nrm = lxnBuild(src, w, h, { B: E.kind === 'back' ? 0 : o.B, Bi: o.Bi, inner: o.inner, cell: true, open: false, amin: E.kind === 'back' ? 40 : 100 });
  const r0 = y0 - top, rows = Math.min(LXN_BAND, cv.height - y0);
  E.x.putImageData(new ImageData(nrm.subarray(r0 * w * 4, (r0 + rows) * w * 4), w, rows), 0, y0);
  if (!E.bands.length) E.done = true;
  return true;
}
// called once per frame from lxBegin: spend the budget on queued frames / bands
function lxnTick() {
  const t0 = performance.now(), budget = LXN.budget * (typeof fadePhase !== 'undefined' && fadePhase ? 3 : 1);
  while (LXN.q.length && performance.now() - t0 < budget) {
    const j = LXN.q[0];
    if (j[0] === null) { lxnGenBand(j[1], j[2]); if (j[2].done) LXN.q.shift(); continue; }
    LXN.q.shift(); LXN.qk.delete(j[2]);
    if (!(j[0]._lxn && j[0]._lxn.f[j[1]])) lxnGenFrame(j[0], j[1]);
  }
  LXN.ms = performance.now() - t0;
  if (++LXN.tick % 600 === 0 && LXN.px > 16e6) {   // memory: drop the caches of sheets not drawn for a few rooms
    for (const s of LXN.sheets) if (s.name !== 'player' && !s.name.startsWith('wpn_') && SHEET_EPOCH - (s.used ?? 0) > 2) {
      for (const c of s._lxn.f) if (c) LXN.px -= c.width * c.height * 2;
      s._lxn = null; LXN.sheets.delete(s);
    }
  }
}
// ---- the mirror: called from drawSprite (00_core.js) with the lit layer's transform still applied
lxNHook = {
  g: null,   // the lit layer while surface lighting is on this frame, else null
  sprite(sh, fi, flip, dx, dy, w, h) {
    if (g.globalCompositeOperation !== 'source-over') return;
    let C = sh._lxn, c = C && (flip ? C.m : C.f)[fi];
    if (!c) {   // not cached yet: small frames (the knight, his weapon, most foes) are made on the spot, within ~1.5 ms a frame;
      const f = sh.frames[fi];   // big ones (bosses) are queued and show flat for a frame or two
      if (f && f.w * f.h <= 4096 && LXN.sync < 1.5) { const t0 = performance.now(); lxnGenFrame(sh, fi); LXN.sync += performance.now() - t0; C = sh._lxn; c = C && (flip ? C.m : C.f)[fi]; }
      if (!c) { lxnWant(sh, fi); return; }
    }
    if (sh._lxn.f[fi + 1] === undefined && sh.frames[fi + 1]) lxnWant(sh, fi + 1);
    gN.setTransform(g.getTransform()); gN.globalAlpha = g.globalAlpha;
    gN.drawImage(c, 0, 0, w, h, dx, dy, w, h);
  },
};
function lxnLayer(cv, kind) {   // a cached room layer was just drawn into the lit layer (renderWorld)
  if (!LXN.on || !cv) return;
  const E = lxnRoomEntry(cv, kind);
  gN.setTransform(g.getTransform()); gN.globalAlpha = 1; gN.drawImage(E.c, 0, 0);
}
function lxnBegin(on) {
  LXN.on = on; lxNHook.g = on ? gLow : null;
  if (!on) return;
  gN.setTransform(1, 0, 0, 1, 0, 0); gN.globalAlpha = 1; gN.clearRect(0, 0, W, H);
  LXN.sync = 0; lxnTick();
}
Object.assign(window.__game, { lxn: { LXN, LXN_TUNE, lxnBuild, lowN, lowBg } });   // headless tests

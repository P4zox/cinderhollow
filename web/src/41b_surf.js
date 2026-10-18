// ------------------------------------------------------------------ v17 shading phase 2: surface normals (docs/v17/shading_phase2.md)
// Settings › Graphics › Surface lighting. Under Dynamic lighting every lit sprite (drawSprite) and the room's cached layers
// (room.back / room.front) also draw their *normals* into `lowN`, in the same order, so whatever is on top wins. The lighting
// pass (41_light.js) then lets a lamp wrap around the knight, foes, bosses, props and the bricks: the side facing the light
// takes more of it, the far side falls into shade, and the silhouette edge facing it catches a rim.
// No normal art ships: normals are derived at runtime from the art itself, cached per sheet frame / per room layer:
//   height = silhouette bevel (distance to the sprite's edge, a quarter-circle profile, width ~0.7 × its thickest part)
//            × inner relief (distance to its own dark outline / mortar lines: each plate, brick or fold gets a small bevel)
//   normal = gradient of that height, quantized to 8 directions × 3 tilts (light lands in a few clean steps, no plastic smear).
// lowN pixel: R,G = normal x,y (128 ± 127, y down), B = luminance of the art pixel it was made from (6 bits) and, phase 3, its
// material (2 low bits: 0 matte, 1 metal highlight (glints), 2 sheen (wet stone, ice), 3 metal body), A = coverage. The pass only
// trusts a normal when the lit layer still shows that very pixel (|lum − B| small): fx, water, fog, flashes and decor painted
// over a sprite or wall without normals fall back to flat (exactly the phase-1 look) instead of borrowing what lies beneath.
const [lowN, gN] = lxCanvas(), [lowBg, gBg] = lxCanvas(), [lowBgM, gBgM] = lxCanvas();   // normals; the backdrop (parallax / vista: far, and the biome's mid layer)
const LXN = { on: false, sync: 0, q: [], wq: [], qk: new Set(), rooms: new WeakMap(), ms: 0, gen: 0, px: 0, budget: 3, tick: 0,
  scr: null, sx: null, sheets: new Set(), dbg: null };
// look knobs (LX_TUNE-style, tests tweak live): bevel profile, inner relief, normal tilt scale, quantization
// inner: depth (px) of the dip along inner lines, over Bi px: kept shallow, so plates and bricks only ever reach the first tilt step
// (a gentle turn), while the silhouette's outer pixel reaches the steepest one, the only step that takes a rim (no embossed decals)
const LXN_TUNE = { inner: 1.1, Bi: 2, tiltK: 1.0, dirs: 8, tilts: 3, bMin: 2, bMax: 16, bK: 1.3, room: { B: 3, Bi: 2, inner: 1.0 }, back: { Bi: 2, inner: 1.0 },
  // v17 phase 3 materials: metal pixels are greyish (chroma < mCh) and not inner lines; the ones the artist painted as highlights
  // (luminance >= max(mHi, median × mHk), or a local peak) take glints, the rest of the metal a faint broad sheen
  mCh: 0.36, mLo: 0.1, mHi: 0.4, mHk: 1.6, mPk: 0.07, iceV: 0.42 };
// v17 phase 3: a tiny material hint table (no new assets). Sheets listed as 'metal' let their greyish pixels be metal (armour, blades,
// the Hearthkeeper's hammer, iron props); coloured cloth, wood and skin in the same sheet stay matte. 'ice' sheets: pale blue-white
// pixels take a soft sheen. Everything else is matte. Room layers take the region's: ice in the Hoarfrost, wet stone under rain/water.
const LXN_MAT = [
  [/^(player|wpn_(?!fx_)|hearthkeeper_p|cf_unforged_|cf_smith|gilded_sentinel|grave_knight|enforcer|executioner_|champion|shield_warden|hollow_soldier|hollow_archer|du_soldier|dp_forge_sentry|vael_knight|vael_exec|warden|sf_golem|trn_dummy)/, 'metal'],
  [/^(prop_(anvil|bell|candelabra|gate|shelfcage|elevator|lever|lantern|chest)|hearthkeeper_props|cfa_(ganvil|rack|gate|guard|doors|furnace)|kit_(gate|parts|plat)|nv_bell|db_(bell|grate|lamp)|xrc_dp_(anvil|cage|gear|pipes|crucible|reliquary)|xrc_sp_(grate|winch|lantern)|xsa_(bell|chand)|cm_(chandelier|candelabra|sconce)|sp_lamp|dp_crucible)/, 'metal'],
  [/^(hf_icefall|hf_icicle|hf_golem|ice_warden|sf_glass|sf_lens|sf_shard)/, 'ice'],
];
const LXN_MAT_ROOM = { hoarfrost: 'ice', mire: 'wet', barrows: 'wet', spire: 'wet' };   // (lava is drawn as an emitter: no light to catch)
function lxnMatOf(name) { for (const [re, m] of LXN_MAT) if (re.test(name)) return m; return null; }

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
  let med = 0;
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
  } else { med = median(0, 0, w, h); const th = Math.max(0.035, med * 0.62); for (let i = 0; i < n; i++) line[i] = al[i] && L[i] < th ? 1 : 0; }
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
  // v17 phase 3: material per pixel (2 bits, packed under a 6-bit luminance in B)
  const mat = o.mat ? new Uint8Array(n) : null;
  if (mat) {
    const hi = Math.max(T.mHi, (med || median(0, 0, w, h)) * T.mHk);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = y * w + x; if (!al[i]) continue;
      const k = i * 4, r = src[k] / 255, gg = src[k + 1] / 255, b = src[k + 2] / 255, mx = Math.max(r, gg, b), ch = (mx - Math.min(r, gg, b)) / Math.max(mx, 0.02);
      if (o.mat === 'metal') {
        if (line[i] || ch >= T.mCh || mx < T.mLo) continue;
        let nb = 0, c = 0;
        for (const j of [i - 1, i + 1, i - w, i + w]) if (j >= 0 && j < n && al[j]) { nb += L[j]; c++; }
        mat[i] = L[i] >= hi || (c && L[i] - nb / c >= T.mPk && L[i] >= hi * 0.75) ? 1 : 3;
      } else if (o.mat === 'ice') { if (mx >= T.iceV && b >= r * 0.95 && ch < 0.55) mat[i] = 2; }
      else if (o.mat === 'wet') { if (!line[i] && mx >= 0.05) mat[i] = 2; }
    }
  }
  // gradient -> quantized normal
  const out = new Uint8ClampedArray(n * 4), dirs = T.dirs, tilts = T.tilts, step = Math.PI * 2 / dirs, tk = T.tiltK;
  const at = (x, y) => (x < 0 || y < 0 || x >= w || y >= h) ? (open ? 0 : Hh[Math.min(h - 1, Math.max(0, y)) * w + Math.min(w - 1, Math.max(0, x))]) : Hh[y * w + x];
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x, k = i * 4;
    out[k + 2] = Math.round(L[i] * 63) * 4 + (mat ? mat[i] : 0); out[k + 3] = src[k + 3];
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
  if (sh._mat === undefined) sh._mat = lxnMatOf(sh.name);
  const src = x.getImageData(0, 0, f.w, f.h).data, nrm = lxnBuild(src, f.w, f.h, { open: true, mat: sh._mat }), mir = new Uint8ClampedArray(nrm);
  for (let i = 0; i < mir.length; i += 4) mir[i] = 256 - mir[i];   // drawn mirrored (facing the other way): x flips sign
  const C = sh._lxn || (sh._lxn = { f: [], m: [], raw: [] });
  C.f[fi] = lxnCanvasOf(nrm, f.w, f.h); C.m[fi] = lxnCanvasOf(mir, f.w, f.h);
  if (f.w * f.h <= 4096) C.raw[fi] = nrm;   // phase 3: small frames keep their local normals for rotated draws (lxnRotOf)
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
    const rm = room && LXN_MAT_ROOM[room.def.biome], wetOut = rm === 'wet' && room.def.biome === 'spire' && room.def.indoor;   // the Spire is wet only under its rain
    E = { c, x: c.getContext('2d'), bands, kind, done: false, mat: wetOut ? null : kind === 'back' && rm === 'wet' ? null : rm || null };   // wet: the terrain, not the back wall
    LXN.rooms.set(cv, E); LXN.q.push([null, cv, E]);
  }
  return E;
}
function lxnGenBand(cv, E) {
  const y0 = E.bands.shift(); if (y0 === undefined) { E.done = true; return true; }
  const o = E.kind === 'back' ? LXN_TUNE.back : LXN_TUNE.room, M = 6, top = Math.max(0, y0 - M), bot = Math.min(cv.height, y0 + LXN_BAND + M), w = cv.width, h = bot - top;
  let src; try { src = cv.getContext('2d').getImageData(0, top, w, h).data; } catch (e) { E.done = true; E.bands.length = 0; return true; }
  const nrm = lxnBuild(src, w, h, { B: E.kind === 'back' ? 0 : o.B, Bi: o.Bi, inner: o.inner, cell: true, open: false, amin: E.kind === 'back' ? 40 : 100, mat: E.mat });
  const r0 = y0 - top, rows = Math.min(LXN_BAND, cv.height - y0);
  E.x.putImageData(new ImageData(nrm.subarray(r0 * w * 4, (r0 + rows) * w * 4), w, rows), 0, y0);
  if (!E.bands.length) E.done = true;
  return true;
}
// called once per frame from lxBegin: spend the budget on queued frames / bands
function lxnTick() {
  const busy = typeof state !== 'undefined' && state !== 'play';   // phase 3: intros, cutscenes and dialogue have frame time to spare
  const t0 = performance.now(), budget = LXN.budget * (typeof fadePhase !== 'undefined' && fadePhase ? 3 : busy ? 2 : 1);
  lxnPrewarm();
  let undec = 0;
  while (performance.now() - t0 < budget) {
    if (!LXN.q.length) {   // phase 3: nothing wanted right now: take a pre-warm job (they never hold up what is drawn)
      if (!LXN.wq.length) break;
      LXN.q.push(LXN.wq.shift());
    }
    const j = LXN.q[0];
    if (j[0] === null) { lxnGenBand(j[1], j[2]); if (j[2].done) LXN.q.shift(); continue; }
    LXN.q.shift();
    if (j[0]._lxn && j[0]._lxn.f[j[1]]) { LXN.qk.delete(j[2]); continue; }
    if (j[3] && !(j[0].img.complete && j[0].img.naturalWidth)) {   // a pre-warm job whose sheet is still decoding: try again later
      if ((j[4] = (j[4] || 0) + 1) < 900) { LXN.wq.push(j); if (++undec > 8) break; } else LXN.qk.delete(j[2]);
      continue;
    }
    LXN.qk.delete(j[2]);
    lxnGenFrame(j[0], j[1]);
  }
  LXN.ms = performance.now() - t0;
  if (++LXN.tick % 600 === 0 && LXN.px > 16e6) {   // memory: drop the caches of sheets not drawn for a few rooms
    for (const s of LXN.sheets) if (s.name !== 'player' && !s.name.startsWith('wpn_') && SHEET_EPOCH - (s.used ?? 0) > 2) {
      for (const c of s._lxn.f) if (c) LXN.px -= c.width * c.height * 2;
      s._lxn = null; LXN.sheets.delete(s);
    }
  }
}
// ---- v17 phase 3: pre-warm big sprites. A boss (and any big foe) gets the first frames of every animation of its current sheet
// family queued on room entry / when it appears / when its phase changes, behind whatever is being drawn right now, so the first
// frames of a new move are not flat. The rest of each animation follows as it plays (lxnWant). Family: the sheets sharing the
// name up to the phase (hearthkeeper_p1_1 … hearthkeeper_p1_12; cindervane, cindervane_p2 …).
const LXN_WARM = { per: 3, big: 4096 };
function lxnWarmSheet(sh, per = LXN_WARM.per) {
  if (!sh || !sh.ok || !sh.frames.length) return 0;
  let n = 0; sh.img;   // starts the decode of a lazily loaded sheet
  for (const t of Object.values(sh.tags).concat(sh.frames.length ? [{ from: 0, to: 0 }] : [])) for (let j = t.from; j <= Math.min(t.to, t.from + per - 1); j++) {
    if (sh._lxn && sh._lxn.f[j]) continue;
    const key = sh.name + ':' + j; if (LXN.qk.has(key)) continue;
    LXN.qk.add(key); LXN.wq.push([sh, j, key, 1]); n++;
  }
  return n;
}
function lxnFamily(sh) {
  const m = /^(.*?_p\d+)_\d+$/.exec(sh.name) || /^(.*?)(_p\d+[a-z]?)?$/.exec(sh.name), base = m[1];
  const out = [];
  for (const k of Object.keys(ASSETS)) if ((k === base || k.startsWith(base + '_')) && !k.endsWith('_meta') && ASSETS[k] && ASSETS[k].png && !/^(fx_|bg_)/.test(k)) out.push(sheet(k));
  return out.length > 40 ? out.slice(0, 40) : out;
}
function lxnPrewarm() {
  if (typeof room === 'undefined' || !room) return;
  if (LXN.wRoom !== room) {   // room entry: big foes (and the boss below)
    LXN.wRoom = room; LXN.wBoss = null;
    for (const j of LXN.wq) LXN.qk.delete(j[2]); LXN.wq.length = 0;   // the last room's pre-warm is moot
    for (const e of (typeof enemies !== 'undefined' ? enemies : [])) if (e.sh && e.sh.ok && e.sh.fw * e.sh.fh > LXN_WARM.big && !e.sh._warm) { e.sh._warm = 1; lxnWarmSheet(e.sh); }
  }
  const b = typeof boss !== 'undefined' ? boss : null;
  if (!LXN_WARM.per) return;
  if (b && b.sh && b.sh.ok && (LXN.wBoss !== b || LXN.wSh !== b.sh || LXN.wPh !== b.phase)) {
    LXN.wBoss = b; LXN.wSh = b.sh; LXN.wPh = b.phase;
    const fi = b.anim && b.anim.frame; if (fi !== undefined && !(b.sh._lxn && b.sh._lxn.f[fi])) lxnGenFrame(b.sh, fi);   // the frame on screen now, at once (it appears under the room fade / its intro)
    let n = lxnWarmSheet(b.sh, 6);
    for (const s of lxnFamily(b.sh)) if (s !== b.sh && !s._warm) { s._warm = 1; n += lxnWarmSheet(s, 2); }
    LXN.warmed = (LXN.warmed || 0) + n;
  }
}
// ---- phase 3: rotated draws (projectiles, spears, swinging bells and chandeliers, cranes). The normal image is drawn with the same
// transform as the art; its vectors are turned by the transform's own rotation / mirror, quantized to 16 angles (≤ 11°, under the
// 8-direction quantization of the normals themselves), cached per sheet / frame / angle.
function lxnRotOf(sh, fi, M) {
  const C = sh._lxn, base = C && C.f[fi]; if (!base) return null;
  const sa = Math.hypot(M.a, M.b) || 1, sc = Math.hypot(M.c, M.d) || 1, a = M.a / sa, b = M.b / sa, c = M.c / sc, d = M.d / sc;
  const q = ((Math.round(Math.atan2(b, a) / (Math.PI / 8)) % 16) + 16) % 16, fl = a * d - b * c < 0 ? 1 : 0, key = fi * 32 + q * 2 + fl;
  const R = C.r || (C.r = new Map()); let cv = R.get(key);
  if (cv) return cv;
  if (LXN.sync > 2.5) return null;
  const t0 = performance.now(), w = base.width, h = base.height;
  let raw = C.raw && C.raw[fi];
  if (!raw) { raw = base.getContext('2d').getImageData(0, 0, w, h).data; if (C.raw) C.raw[fi] = raw; }
  const qa = q * Math.PI / 8, ca = Math.cos(qa), sn = Math.sin(qa), m00 = ca, m10 = sn, m01 = fl ? sn : -sn, m11 = fl ? -ca : ca;
  const out = new Uint8ClampedArray(raw.length);
  for (let i = 0; i < raw.length; i += 4) {
    const nx = (raw[i] - 128) / 127, ny = (raw[i + 1] - 128) / 127;
    out[i] = Math.round(128 + (m00 * nx + m01 * ny) * 127); out[i + 1] = Math.round(128 + (m10 * nx + m11 * ny) * 127); out[i + 2] = raw[i + 2]; out[i + 3] = raw[i + 3];
  }
  cv = lxnCanvasOf(out, w, h); R.set(key, cv); LXN.px += w * h;
  LXN.sync += performance.now() - t0;
  return cv;
}
// ---- phase 3: the occluder / contact buffer (lowO). While renderWorld draws the knight, foes, the boss and big props (LXO.occ), every
// sprite also goes into lowO with the same transform; lxoFinish turns that into a flat silhouette (R) and adds soft contact pools
// under whatever stands on (or hovers over) the ground (alpha only, under the silhouettes). The lighting pass uploads it as
// LUMINANCE_ALPHA: silhouette = L × A, pool = A − L × A.
const [lowO, gO] = lxCanvas();
const LXO = { on: false, occ: false, n: 0, bb: [1e9, 1e9, -1e9, -1e9], pools: 0 };
const LXO_TUNE = { pool: 0.6, air: 88, propMin: 20, propMax: 160 };
function lxoBox(dx, dy, w, h) {
  const M = g.getTransform(), B = LXO.bb;
  for (const [x, y] of [[dx, dy], [dx + w, dy], [dx, dy + h], [dx + w, dy + h]]) {
    const X = M.a * x + M.c * y + M.e, Y = M.b * x + M.d * y + M.f;
    if (X < B[0]) B[0] = X; if (Y < B[1]) B[1] = Y; if (X > B[2]) B[2] = X; if (Y > B[3]) B[3] = Y;
  }
  LXO.n++;
}
function lxoDraw(img, sx, sy, w, h, dx, dy) {
  gO.setTransform(g.getTransform()); gO.globalAlpha = g.globalAlpha;
  gO.drawImage(img, sx, sy, w, h, dx, dy, w, h); lxoBox(dx, dy, w, h);
}
// ---- the mirror: called from drawSprite / drawRotated (00_core.js) with the lit layer's transform still applied
lxNHook = {
  g: null,   // the lit layer while Dynamic lighting is on this frame, else null
  sprite(sh, fi, flip, dx, dy, w, h, img, sx, sy) {
    if (g.globalCompositeOperation !== 'source-over') return;
    if (LXO.occ && img) lxoDraw(img, sx, sy, w, h, dx, dy);
    if (!LXN.on) return;
    let C = sh._lxn, c = C && (flip ? C.m : C.f)[fi];
    if (!c) {   // not cached yet: small frames (the knight, his weapon, most foes) are made on the spot, within ~1.5 ms a frame;
      const f = sh.frames[fi];   // big ones (bosses) are queued and show flat for a frame or two
      if (f && f.w * f.h <= 4096 && LXN.sync < 1.5) { const t0 = performance.now(); lxnGenFrame(sh, fi); LXN.sync += performance.now() - t0; C = sh._lxn; c = C && (flip ? C.m : C.f)[fi]; }
      if (!c) { lxnWant(sh, fi); LXN.miss = (LXN.miss || 0) + 1; return; }   // (counted: a big frame drawn flat)
    }
    if (sh._lxn.f[fi + 1] === undefined && sh.frames[fi + 1]) lxnWant(sh, fi + 1);
    gN.setTransform(g.getTransform()); gN.globalAlpha = g.globalAlpha;
    gN.drawImage(c, 0, 0, w, h, dx, dy, w, h);
  },
  rot(sh, fi, dx, dy, w, h, img, sx, sy) {   // phase 3: a rotated draw (the transform holds the rotation and any mirror)
    if (g.globalCompositeOperation !== 'source-over') return;
    if (LXO.occ && img) lxoDraw(img, sx, sy, w, h, dx, dy);
    if (!LXN.on) return;
    let C = sh._lxn;
    if (!(C && C.f[fi])) {
      const f = sh.frames[fi];
      if (f && f.w * f.h <= 4096 && LXN.sync < 1.5) { const t0 = performance.now(); lxnGenFrame(sh, fi); LXN.sync += performance.now() - t0; C = sh._lxn; }
      if (!(C && C.f[fi])) { lxnWant(sh, fi); return; }
    }
    const M = g.getTransform(), c = lxnRotOf(sh, fi, M); if (!c) return;
    gN.setTransform(M); gN.globalAlpha = g.globalAlpha;
    gN.drawImage(c, 0, 0, w, h, dx, dy, w, h);
  },
};
// phase 3: a frame drawn with a raw g.drawImage (unscaled, unflipped, e.g. moving platforms): draw its normals too
function lxnRaw(sh, fi, dx, dy) {
  if (!lxNHook.g || lxNHook.g !== g || !sh || !sh.ok) return;
  const f = sh.frames[fi]; if (!f) return;
  lxNHook.sprite(sh, fi, false, dx, dy, f.w, f.h, null);
}
function lxnLayer(cv, kind) {   // a cached room layer was just drawn into the lit layer (renderWorld)
  if (!LXN.on || !cv) return;
  const E = lxnRoomEntry(cv, kind);
  gN.setTransform(g.getTransform()); gN.globalAlpha = 1; gN.drawImage(E.c, 0, 0);
}
function lxnBegin(on, lit) {
  LXN.on = on; lxNHook.g = lit ? gLow : null;
  LXO.on = !!(lit && SETTINGS.csh > 0 && LX.ocOK); LXO.occ = false; LXO.n = 0; LXO.pools = 0; LXO.bb = [1e9, 1e9, -1e9, -1e9];
  if (LXO.on) { gO.setTransform(1, 0, 0, 1, 0, 0); gO.globalAlpha = 1; gO.globalCompositeOperation = 'source-over'; gO.clearRect(0, 0, W, H); }
  if (!on) return;
  gN.setTransform(1, 0, 0, 1, 0, 0); gN.globalAlpha = 1; gN.clearRect(0, 0, W, H);
  LXN.sync = 0; lxnTick();
}
// cast shadows: who goes into the silhouette buffer (renderWorld sets LXO.occ around these draws)
function lxoProp(p) {
  if (!LXO.on || SETTINGS.csh < 2 || !p.sh || !p.sh.ok || lxProp(p) || p.type === 'fog' || p.type === 'veil' || p.type === 'updraft' || p.type === 'npc') return false;
  const fw = p.sh.fw, fh = p.sh.fh;
  return fh >= LXO_TUNE.propMin && fw >= 12 && fw <= LXO_TUNE.propMax && fh <= LXO_TUNE.propMax;
}
// contact pools: a soft dark ellipse on the floor under x (feet at y). In the air it lies on the floor below, wider and fainter, and
// tightens as the body comes down. w: half-width of the body's footprint.
function lxoFloor(x, y) {
  const tx = Math.floor(x / TILE);
  for (let ty = Math.floor((y - 1) / TILE), k = 0; k < 7; ty++, k++) {
    const t = tileAt(tx, ty);
    if (isSolidT(t) || t === T_PLAT) { const top = ty * TILE; if (top >= y - 2) return top; }
  }
  return null;
}
function lxoPool(x, y, w, k = 1, grounded = false) {
  const fy = grounded ? y : lxoFloor(x, y); if (fy === null) return;
  const hgt = Math.max(0, fy - y), A = LXO_TUNE.air; if (hgt >= A) return;
  const f = 1 - hgt / A, a = LXO_TUNE.pool * k * f * f, rx = Math.max(3, w * (0.85 + hgt / 50)), ry = 2.6 + Math.min(3, hgt / 22);
  if (a < 0.02) return;
  gO.save(); gO.translate(Math.round(x), Math.round(fy)); gO.scale(rx, ry);
  const gr = gO.createRadialGradient(0, 0, 0, 0, 0, 1);
  gr.addColorStop(0, `rgba(0,0,0,${a.toFixed(3)})`); gr.addColorStop(0.55, `rgba(0,0,0,${(a * 0.7).toFixed(3)})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
  gO.fillStyle = gr; gO.beginPath(); gO.arc(0, 0, 1, 0, 6.2832); gO.fill(); gO.restore();
  LXO.pools++;
}
// end of the frame's world: silhouettes -> flat (R = 1), then the pools go under them
function lxoFinish(cx, cy) {
  if (!LXO.on) return;
  gO.setTransform(1, 0, 0, 1, 0, 0); gO.globalAlpha = 1;
  if (LXO.n) { gO.globalCompositeOperation = 'source-in'; gO.fillStyle = '#ff0000'; gO.fillRect(0, 0, W, H); }
  gO.globalCompositeOperation = 'destination-over'; gO.setTransform(1, 0, 0, 1, -cx, -cy);
  if (P && P.state !== 'dead' && !(P.x < -900)) lxoPool(P.x, P.y, 7, 1, P.ground);
  for (const e of enemies) if (e.alive !== false && !e.dead && e.hp > 0) lxoPool(e.x, e.y, Math.max(5, e.w * 0.55), e.cfg && e.cfg.flying ? 0.7 : 1, e.ground && !(e.cfg && e.cfg.flying));
  if (boss && boss.alive && boss.state !== 'dormant' && !boss.hidden && boss.visible !== false && boss.floor !== undefined) lxoPool(boss.x, boss.y, boss.kind === 'hound' ? 46 : 28, 1, Math.abs(boss.y - boss.floor) < 2);
  if (SETTINGS.csh >= 1) for (const p of props) if (p.sh && p.sh.ok && !lxProp(p) && p.type !== 'fog' && p.type !== 'veil' && p.type !== 'updraft' && p.type !== 'lantern' && p.type !== 'shelfcage' && p.type !== 'item' && p.type !== 'hookpoint' && p.sh.fw >= 14 && p.sh.fw <= 96) {
    if (Math.abs(p.x - cx - W / 2) > W / 2 + 60) continue;
    const t = tileAt(Math.floor(p.x / TILE), Math.floor((p.y + 2) / TILE)); if (!(isSolidT(t) || t === T_PLAT)) continue;
    lxoPool(p.x, Math.floor((p.y + 2) / TILE) * TILE, Math.min(26, p.sh.fw * 0.36), 0.55, true);
  }
  gO.setTransform(1, 0, 0, 1, 0, 0); gO.globalCompositeOperation = 'source-over';
}
Object.assign(window.__game, { lxn: { LXN, LXN_TUNE, LXO, LXO_TUNE, LXN_WARM, lxnBuild, lowN, lowBg, lowO } });   // headless tests

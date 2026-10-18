// ------------------------------------------------------------------ v17 shading phase 4 (docs/v17/shading_phase4.md)
// Five things on top of the phase 1-3 lighting pipeline (41_light.js, 41b_surf.js), all under Dynamic lighting only (Classic and
// shaders off never reach this file's code paths):
//   1. Reflections (Settings › Graphics › Reflections): water, ice and wet floors mirror what stands above them. Screen space: a
//      mask (lowR) says per pixel which surface it belongs to, where that surface's waterline is and how it reflects; a small pass
//      after the lighting (LX_RF) reads the lit frame at the mirrored pixel. Bodies (the silhouette buffer) and emitters (lowFx)
//      reflect strongly, lit world faintly, the painted backdrop barely (its own painted reflections are not mirrored twice);
//      the HUD and the overlays (lowTop) are laid on after the reflections, so they are never mirrored.
//   2. Lit particles: dust, ash, spores, motes, snow and rain go to their own layer (lowP) and are lit by the lamps as the air is
//      (shadowed, warm or cool by the lamp's colour, dark away from lights). Embers, sparks and spell motes stay emissive.
//   3. Light shafts: sunlight let into roofed air through openings (the SDF march toward the region's sun, GFX_SUN), and beams
//      from windows / vents; both cut by walls and by the bodies, dust drifting in them, in 3 clean steps (41_light.js shafts()).
//   4. Depth haze: the far backdrop fades toward the region's air colour, the mid layer less, the play layer not at all.
//   5. Effect light: spells, weapon arts, fatalities and boss attacks light the world in their own colour (lx4FxLight).
const [lowR, gR] = lxCanvas(), [lowP, gP] = lxCanvas();
const LX4 = { part: false, pn: 0, pDirty: false, rn: 0, rDirty: false, sh: false, rfOK: false, beams: 0, fxl: [] };
const LX4_NBM = 4;   // beams (windows, vents) per frame
// look knobs (tests tweak these live, like LX_TUNE)
//   reflections: env / body / bg how strongly lit world, bodies + emitters and the painted backdrop reflect; dark: the copy's
//   darkening; wD iD wetD pudD: how deep below the line each kind shows (px); wetS / pudS: the grazing compression of the floor
//   (one px of floor mirrors that many px of height: short streaks); wetT / wetK: what is bright enough to streak on wet stone, gain
//   particles: pAmb pLamp pShaft their share of the ambient, the lamps and the shafts
//   shafts: sun (× GFX_SUN strength), beam, gain per Light shafts setting (Soft, Strong), reach (px), roofN (tiles to a roof)
//   haze: far / mid (outdoors), farIn / midIn (indoors), farHall (halls whose far painting is the back wall), vista (× on benches)
const LX4_TUNE = { env: 0.4, body: 0.75, bg: 0.12, dark: 0.88, wD: 44, wDm: 84, gap0: 24, gap1: 56, lift: 1.35, iD: 10, wetD: 6, pudD: 5, wetS: 6, pudS: 2, wetT: 0.32, wetK: 0.6, sky: 0.3,
  fxMax: 0.8, fxK: 0.6, fxR: 0.95, fxMin: 22, fxMaxR: 170,
  pAmb: 0.9, pLamp: 1.0, pShaft: 6, sun: 0.22, open: 0, lamp: 0.12, lampOpen: 0.2, lampE0: 5, lampE1: 22, lampTop: 0.1, beam: 0.16, gain: [0, 1, 1.5], reach: 300, roofN: 10,
  far: 0.26, mid: 0.11, farIn: 0.16, midIn: 0.07, farHall: 0.1, vista: 0.45 };
// reflection tints: 0 rot water (~), 1 deep water ("), 2 the forge's cisterns, 3 freezing water (:), 4 dark pools (stairs, kit basins),
// 5 ice, 6 wet stone, 7 puddles
const LX4_RT = ['150,205,140', '140,215,210', '165,180,215', '185,215,250', '160,170,215', '210,232,255', '255,255,255', '190,210,250'].map(c => { const q = c.split(',').map(Number), m = Math.max(...q); return q.map(v => v / m); });
const LX4_K = { water: 1, ice: 2, wet: 3, puddle: 4 };
const LX4_WET = { mire: 1, barrows: 1, spire: 1 };   // wet stone (the materials' wet regions, 41b_surf.js LXN_MAT_ROOM; the Spire under its rain only)
// depth haze per region: [far, mid, 'r,g,b' air] (any may be null: defaults from LX4_TUNE and the region's tint + ambient)
const LX4_HAZE = { crown: [0.3, 0.12], lastfield: [0.3, 0.12], dunes: [0.3, 0.12], hoarfrost: [0.3, 0.13], ramparts: [0.28, 0.12] };

function lx4WantSil() { return !!((SETTINGS.refl && LX4.rfOK) || (SETTINGS.rays > 0 && SETTINGS.light >= 2)); }
function lx4Begin(on) {
  LX4.part = !!(on && SETTINGS.lpart && LX.partOK);
  LX4.sh = !!(on && SETTINGS.rays > 0 && SETTINGS.light >= 2);
  if (LX4.pDirty) { gP.setTransform(1, 0, 0, 1, 0, 0); gP.clearRect(0, 0, W, H); LX4.pDirty = false; }
  LX4.pn = 0; LX4.fxl.length = 0;
  lxFxHook.g = on && SETTINGS.light > 0 ? gFx : null;
}

// ---- 5. effect light: every effect sheet (fx_*, wpn_fx_*) drawn into the glow layer is one light in its own colour (the mean of its
// bright pixels), sized by its frame, fading as it plays; capped at k 0.8 (LX_FXL). Shadow-casting like any lamp (r ≤ 280: walls, and the
// bodies with Character shadows On), so big ones (slams, novas, a boss's bursts) throw brief shadows. Skipped when the effect already
// has a light of its own (an explicit addLight within 16 px, at least half the size): one main light per effect.
function lx4FxCol(sh, fi) {
  if (sh._fxL !== undefined) return sh._fxL;
  const f = sh.frames[Math.floor(sh.frames.length / 2)] || sh.frames[fi], img = sh.img;
  if (!f || !img.complete || !img.naturalWidth) return null;
  const x = lxnScratch(f.w, f.h); x.drawImage(img, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
  const d = x.getImageData(0, 0, f.w, f.h).data; let r = 0, gg = 0, b = 0, n = 0, cov = 0;
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] < 40) continue; cov++;
    const l = (0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]) / 255, w = l * l * d[i + 3] / 255;
    r += d[i] * w; gg += d[i + 1] * w; b += d[i + 2] * w; n += w;
  }
  const mean = n > 0.5 ? [r / n, gg / n, b / n] : null, lum = mean ? (0.299 * mean[0] + 0.587 * mean[1] + 0.114 * mean[2]) / 255 : 0;
  return (sh._fxL = mean && lum > 0.25 ? { c: mean.map(Math.round).join(','), cov: cov / (f.w * f.h) } : null);   // dark effects (smoke, ink) cast none
}
const LX4_FXSKIP = /^fx_(dust|wall_dust|blood|bleed|death_ash|ink|db_splash|dp_debris|ground_crack|g2_crack|shadow|smoke)/;
lxFxHook = {
  g: null,
  fx(sh, fi, x, y, f, opt) {
    const n = sh.name; if (!(n.startsWith('fx_') || n.startsWith('wpn_fx_')) || LX4_FXSKIP.test(n) || opt.blend === 'destination-out') return;
    if (Math.max(f.w, f.h) < 10) return;
    const C = lx4FxCol(sh, fi); if (!C) return;
    const M = g.getTransform(), wx = M.a * x + M.c * y + M.e + LX.cx, wy = M.b * x + M.d * y + M.f + LX.cy, T = LX4_TUNE;
    const r = clamp(Math.max(f.w, f.h) * T.fxR, T.fxMin, T.fxMaxR);
    for (const L of LX4.fxl) if (Math.abs(L.x - wx) < 12 && Math.abs(L.y - wy) < 12) return;   // the same effect drawn twice
    for (const L of lights) if (Math.abs(L.x - wx) < 16 && Math.abs(L.y - wy) < 16 && L.r >= r * 0.5) return;   // it has its own light
    const p = sh.frames.length > 1 ? fi / (sh.frames.length - 1) : 0, env = 1 - 0.65 * Math.min(1, p) ** 1.5;
    const k = T.fxK * env * Math.min(1, opt.alpha ?? 1) * (n.includes('telegraph') ? 0.35 : 1) * clamp(0.5 + C.cov * 2, 0.5, 1);
    if (k > 0.03) LX4.fxl.push({ x: wx, y: wy, r, color: C.c, k, o: LX_FXL });
  },
};

// ---- 2. lit particles
const LX4_AIR = new Set(['dust', 'ash', 'petal', 'sand', 'sandd', 'spore', 'tv_leaf', 'cfa_soot', 'cfa_ash', 'cfa_steam', 'ra_drop', 'db_foam', 'db_bubble', 'xrc_foam', 'ra_bone', 'x3_wheat', 'xrc_wheat', 'xrc_seed', 'x3_seed']);
function lx4AirP(p) {
  if (LX4_AIR.has(p.kind)) return true;
  if (p.kind === 'mote' && p.amb) { const a = room && AREAS[room.def.biome]; return !(a && a.amb === 'ember'); }   // the Deep's floating embers glow
  return false;
}
function lx4DrawAir(list) {   // the same pixels drawParticles makes, into the lit-particle layer (and no light of their own)
  if (!list.length) return;
  const g0 = g; gP.setTransform(g.getTransform()); g = gP;
  try {
    for (const p of list) {
      const a = p.amb ? Math.min(1, p.life / 2) * (p.kind === 'mote' ? 0.7 : 0.45) : Math.min(1, p.life * 2.5);
      g.fillStyle = `rgba(${PCOL[p.kind] || PCOL.gold},${a})`;
      const s = p.kind === 'rock' || (p.pet && Math.sin(p.sway * 2) > 0) ? 2 : 1;
      g.fillRect(Math.round(p.x), Math.round(p.y), s, s);
    }
  } finally { g = g0; gP.setTransform(1, 0, 0, 1, 0, 0); gP.globalAlpha = 1; }
  LX4.pn += list.length; LX4.pDirty = true;
}
// rain, snow and other air drawn by a region (world or screen space): into the lit-particle layer when it is on, else as before
function lxAir(fn) {
  if (!LX4.part || (g !== gLow && g !== gTop)) return fn();
  const g0 = g; gP.setTransform(g.getTransform()); gP.globalAlpha = 1; g = gP;
  try { return fn(); } finally { g = g0; gP.setTransform(1, 0, 0, 1, 0, 0); gP.globalAlpha = 1; gP.globalCompositeOperation = 'source-over'; LX4.pn++; LX4.pDirty = true; }
}

// ---- 1. reflections: the mask
const LX4_FS = new Map();
function lx4Rect(x, y, w, h, sy, kind, tint, str = 255) {
  if (w <= 0 || h <= 0) return;
  const G = Math.max(0, Math.min(255, Math.round(sy - LX.cy) + 40)), B = kind * 32 + tint, key = (str << 16) | (G << 8) | B;
  let fs = LX4_FS.get(key); if (!fs) { fs = `rgb(${str},${G},${B})`; LX4_FS.set(key, fs); }
  gR.fillStyle = fs; gR.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h)); LX4.rn++;
}
const lx4Water = t => t === T_WATER || t === T_FWATER_ || t === DB_T_WATER_;
let T_FWATER_ = -1, DB_T_WATER_ = -1, T_ICE_ = -1;
function lx4Mask() {
  if (LX4.rDirty) { gR.setTransform(1, 0, 0, 1, 0, 0); gR.clearRect(0, 0, W, H); LX4.rDirty = false; }
  LX4.rn = 0;
  if (!(SETTINGS.refl && LX4.rfOK && room)) return 0;
  if (T_FWATER_ < 0) { T_FWATER_ = typeof T_FWATER !== 'undefined' ? T_FWATER : -2; DB_T_WATER_ = typeof DB_T_WATER !== 'undefined' ? DB_T_WATER : -2; T_ICE_ = typeof T_ICE !== 'undefined' ? T_ICE : -2; }
  const T = LX4_TUNE, cx = LX.cx, cy = LX.cy, bio = room.def.biome, forge = bio === 'forge';
  gR.setTransform(1, 0, 0, 1, -cx, -cy);
  const tx0 = Math.floor(cx / TILE) - 1, tx1 = Math.floor((cx + W) / TILE) + 1, ty0 = Math.floor(cy / TILE) - 1, ty1 = Math.floor((cy + H) / TILE) + 1;
  const wet = LX4_WET[bio] && !(bio === 'spire' && room.def.indoor), skip = [];
  // basins that fill and drain (42_kit.js levels): their own waterline, not the grid's
  if (typeof KIT !== 'undefined' && KIT.objs) for (const o of KIT.objs) {
    if (!o.fluid || !o.F || o.F.fire || !(o.F === KIT_FLUID.water || o.F === KIT_FLUID.poison)) continue;
    const f = o.fluid(); skip.push([f.x0, f.x1]);
    const sy = Math.round(f.y + 2);
    for (let tx = Math.max(tx0, Math.floor(f.x0 / TILE)); tx <= tx1 && tx * TILE < f.x1; tx++) {
      if (isSolidT(tileAt(tx, Math.floor((sy + 1) / TILE)))) continue;
      let yb = sy; while (yb < sy + T.wDm && !isSolidT(tileAt(tx, Math.floor(yb / TILE)))) yb = (Math.floor(yb / TILE) + 1) * TILE;
      const x0 = Math.max(f.x0, tx * TILE), x1 = Math.min(f.x1, tx * TILE + TILE);
      lx4Rect(x0, sy, x1 - x0, Math.min(yb, f.y1) - sy, sy, LX4_K.water, o.F === KIT_FLUID.poison ? 0 : 4);
    }
  }
  for (let tx = tx0; tx <= tx1; tx++) {
    const px = tx * TILE, sk = skip.some(([a, b]) => px + 8 >= a && px + 8 < b);
    for (let ty = ty0; ty <= ty1; ty++) {
      const t = tileAt(tx, ty);
      if (lx4Water(t)) {
        let top = ty; while (top > ty - 40 && lx4Water(tileAt(tx, top - 1))) top--;
        let bot = ty; while (bot < ty1 && lx4Water(tileAt(tx, bot + 1))) bot++;
        const up = tileAt(tx, top - 1);
        if (!sk && !isSolidT(up)) {
          const sy = top * TILE, y1 = Math.min((bot + 1) * TILE, sy + T.wDm);
          if (y1 > ty * TILE) lx4Rect(px, Math.max(sy, ty * TILE), TILE, y1 - Math.max(sy, ty * TILE), sy, LX4_K.water, t === T_WATER ? 0 : t === T_FWATER_ ? 3 : forge ? 2 : 1);
        }
        ty = bot; continue;
      }
      if (ty <= ty0) continue;
      const ice = t === T_ICE_;
      if (!(ice || (wet && isSolidT(t) && t !== T_PLAT))) continue;
      const up = tileAt(tx, ty - 1); if (isSolidT(up) || lx4Water(up)) continue;
      lx4Rect(px, ty * TILE, TILE, ice ? T.iD : T.wetD, ty * TILE, ice ? LX4_K.ice : LX4_K.wet, ice ? 5 : 6);
    }
  }
  // the Barrows' arena tide, the cathedral stair's black water, the Spire's puddles
  if (typeof DBW !== 'undefined' && DBW.roomObj === room && DBW.tide) {
    const y = Math.round(DBW.tide.y);
    for (let tx = tx0; tx <= tx1; tx++) {
      const c = tileAt(tx, Math.floor(y / TILE)); if (isSolidT(c) && c !== T_PLAT) continue;
      lx4Rect(tx * TILE, y, TILE, T.wDm, y, LX4_K.water, 1);
    }
  }
  if (typeof RA !== 'undefined' && RA.roomObj === room && RA.waters) for (const w of RA.waters) lx4Rect(w.x0, w.y, w.x1 - w.x0, w.y1 - w.y + 1, w.y, LX4_K.water, 4);
  if (typeof SPR !== 'undefined' && SPR.puddles && typeof spIn === 'function' && spIn()) for (const pd of SPR.puddles) lx4Rect(pd.x0, Math.round(pd.y) - 1, pd.x1 - pd.x0, T.pudD, Math.round(pd.y) - 1, LX4_K.puddle, 7);
  if (LX4.rn) LX4.rDirty = true;
  return LX4.rn;
}

// ---- 3. light shafts: the sun / moon of the region (GFX_SUN) and the beams of windows, vents and painted shafts
function lx4SunDir() {
  if (!room || lxDark()) return null;
  const sun = GFX_SUN[room.def.biome]; if (!sun || (room.def.indoor && !sun[4])) return null;
  if (sun[6]) return null;   // a sun painted low on the far layer (dunes, ramparts): its light runs flat along the corridors; it keeps the screen-space bleed
  const x = sun[0], y = sun[1], dx = (x - 0.5) * W, dy = -(y - 0.5) * H, d = Math.hypot(dx, dy) || 1;
  if (dy / d > -0.5) return null;   // only a high sun / moon falls through holes in a roof as shafts
  return { x: dx / d, y: dy / d, k: sun[2], c: lxCol(sun[3]) };
}
const LX4_LANCET = { gold: '255,214,150', rose: '255,170,190', blue: '160,190,255' };
function lx4Beams(sun) {
  const out = [], cx = LX.cx + W / 2, cy = LX.cy + H / 2, T = LX4_TUNE;
  const add = (x, y, dx, dy, hw, len, k, col, spread) => {
    const d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    for (let s = 0; s < len * 0.6 && isSolidT(tileAt(Math.floor(x / TILE), Math.floor(y / TILE))); s += 3) { x += ux * 3; y += uy * 3; len -= 3; hw += spread * 3; }   // a vent / hole cut in rock: the beam starts where it leaves the rock
    const mx = x + ux * len * 0.5, my = y + uy * len * 0.5;   // on screen at all?
    if (Math.abs(mx - cx) > W / 2 + len * 0.6 + hw || Math.abs(my - cy) > H / 2 + len * 0.6 + hw) return;
    out.push({ x, y, ux, uy, hw, len, k, c: lxCol(col), sp: spread, dist: Math.hypot(mx - cx, my - cy) });
  };
  const sd = sun || { x: -0.2, y: -1 };
  for (const p of props) {
    if (p.type === 'ra_lancet') {   // the cathedral's stained glass: the moon through each window, in its glass colour
      const v = p.v || 'gold';
      add(p.x, p.y - 70, 0.7, 1, 7, 150, T.beam * 1.25, LX4_LANCET[v] || LX4_LANCET.gold, 0.16);   // (steeper than the moon: the beam clears the glass)
    } else if (p.type === 'cfa_ventlight') add(p.x + 2, p.y, 0.14, 1, 9, 175, T.beam * 0.9, '150,170,205', 0.12);   // the forge's cold vents
  }
  if (typeof SA !== 'undefined' && SA.roomObj === room && SA.shafts) for (const q of SA.shafts) add(q.x + q.w / 2, q.y, q.lean, 1, q.w * 0.4, q.h * Math.hypot(1, q.lean), T.beam * 0.8 * Math.min(2, q.a / 0.1), q.col, 0.08);
  out.sort((a, b) => a.dist - b.dist);
  return out.slice(0, LX4_NBM);
}

// ---- the uniforms of the lighting pass (called from lxPass); true when this frame has reflective surfaces on screen
const LX4_U = { bma: new Float32Array(LX4_NBM * 4), bmb: new Float32Array(LX4_NBM * 4), bmc: new Float32Array(LX4_NBM * 4) };
function lx4Uniforms(gl, u) {
  const T = LX4_TUNE, bio = room.def.biome, A = AREAS[bio] || {};
  gl.uniform4f(u.PQ, T.pAmb, T.pLamp, T.pShaft, LX4.part && LX4.pn ? 1 : 0);
  // depth haze
  let hz = [0, 0];
  if (SETTINGS.dhaze) {
    const H4 = LX4_HAZE[bio] || [], hall = (LX_BG_FAR[bio] || (A.lxBg && A.lxBg[0] > 0.2)) && room.def.indoor;
    hz = [H4[0] ?? (hall ? T.farHall : room.def.indoor ? T.farIn : T.far), H4[1] ?? (room.def.indoor ? T.midIn : T.mid)];
    if (typeof VISTA_BG !== 'undefined' && VISTA_BG[room.id]) hz = hz.map(q => q * T.vista);
  }
  gl.uniform2f(u.HZ, hz[0], hz[1]);
  const air = lx4Air(bio);
  gl.uniform3f(u.AIR, air[0], air[1], air[2]);
  // shafts
  const sk = LX4.sh ? T.gain[Math.min(2, SETTINGS.rays | 0)] || 0 : 0, sun = LX4.sh ? lx4SunDir() : null;
  gl.uniform4f(u.SHF, sk, 1, room.def.indoor ? 0 : T.open, sk ? T.lamp : 0);
  gl.uniform4f(u.SHL, T.lampOpen, T.lampE0, T.lampE1, T.lampTop);
  if (sun) { gl.uniform4f(u.SUN, sun.x, sun.y, sun.k * T.sun, T.reach); gl.uniform3f(u.SUNC, sun.c[0], sun.c[1], sun.c[2]); }
  else gl.uniform4f(u.SUN, 0, -1, 0, 0);
  const bm = sk ? lx4Beams(sun) : [], U = LX4_U; LX4.beams = bm.length;
  U.bmb.fill(0);
  bm.forEach((b, i) => { U.bma.set([b.x, b.y, b.ux, b.uy], i * 4); U.bmb.set([b.hw, b.len, b.k, b.sp], i * 4); U.bmc.set([b.c[0], b.c[1], b.c[2], 1], i * 4); });
  gl.uniform4fv(u.BMA, U.bma); gl.uniform4fv(u.BMB, U.bmb); gl.uniform4fv(u.BMC, U.bmc);
  // reflections: build the mask; the pass after this one lays the overlays (lowTop) on
  const rf = lx4Mask() > 0;
  gl.uniform1f(u.TOPK, rf ? 0 : 1);
  return rf;
}
const LX4_AIRC = {};
// the region's air: the colour of its far painting, weighted to its lit parts (the horizon / sky: aerial perspective pales the dark
// silhouettes toward it; the shader only ever lifts, never dims). Scene light × AMB in the shader, so it follows Brightness and the
// region's ambient. LX4_HAZE[b][2] overrides it.
function lx4Air(bio) {
  const key = bio;
  if (LX4_AIRC[key]) return LX4_AIRC[key];
  const H4 = LX4_HAZE[bio], A = AREAS[bio] || {};
  if (H4 && H4[2]) return (LX4_AIRC[key] = H4[2].split(',').map(v => v / 255));
  const far = sheet(`bg_${bio}_far`), k = 1;
  if (far.ok && far.frames[0] && far.img.complete && far.img.naturalWidth) {
    const f = far.frames[0], x = lxnScratch(32, 18); x.imageSmoothingEnabled = true; x.drawImage(far.img, f.x, f.y, f.w, f.h, 0, 0, 32, 18);
    const d = x.getImageData(0, 0, 32, 18).data; let r = 0, gg = 0, b = 0, n = 0;
    for (let i = 0; i < d.length; i += 4) { const a = d[i + 3] / 255 * (0.05 + (0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]) / 255); r += d[i] * a; gg += d[i + 1] * a; b += d[i + 2] * a; n += a; }
    if (n > 1) return (LX4_AIRC[key] = [r, gg, b].map(v => v / n / 255 * k));
  }
  const t = (A.tint || '#141018').replace('#', '');
  return [0, 2, 4].map(i => parseInt(t.slice(i, i + 2), 16) / 255 * k);   // (not cached: the far sheet may still be decoding)
}

// ---- per body: how strongly it reflects (whole or not at all). Its box's lowest point against the first water / ice / floor under it:
// full within RG.x px, none past RG.y; a body whose feet are already under the line wades (marked < 0: the shader keeps it only over
// bright water, which shows the part below). Bodies that cannot reflect are not sent; the rest, up to 16, nearest the water first.
function lx4Surf(x, y) {   // world px: the first water / solid surface at or below y (column x), within 5 tiles; { y, water }
  const tx = Math.floor(x / TILE);
  if (typeof DBW !== 'undefined' && DBW.roomObj === room && DBW.tide && y >= DBW.tide.y - LX4_TUNE.gap1 && y < DBW.tide.y + 80) return { y: DBW.tide.y, water: true };
  for (let ty = Math.floor((y - 1) / TILE), k = 0; k < 6; ty++, k++) {
    const t = tileAt(tx, ty);
    if (lx4Water(t)) { let top = ty; while (top > ty - 40 && lx4Water(tileAt(tx, top - 1))) top--; return { y: top * TILE, water: true }; }
    if (isSolidT(t) && ty * TILE >= y - 2) return { y: ty * TILE, water: false };
  }
  return null;
}
function lx4BodyK() {
  const T = LX4_TUNE, out = [];
  if (!LX4.rbx) { LX4.rbx = new Float32Array(64); LX4.rbk = new Float32Array(16); }
  LX4.rbx.fill(0); LX4.rbk.fill(0);
  for (const b of LXO.boxes) {
    if (b[2] - b[0] < 2 || b[3] - b[1] < 2) continue;
    const cx = (b[0] + b[2]) / 2 + LX.cx, bot = b[3] + LX.cy;
    let best = null;
    for (const fx of [0.3, 0.5, 0.7]) {   // the surface under three points of the body (a cloak over the edge of a basin)
      const S = lx4Surf(b[0] + (b[2] - b[0]) * fx + LX.cx, bot - 4); if (!S) continue;
      if (!best || S.y < best.y) best = S;   // the highest one: a body wading in one column wades
    }
    if (!best) continue;
    const gap = best.y - bot, wade = best.water && bot > best.y + 3;
    const k = wade ? -1 : 1 - clamp((gap - T.gap0) / (T.gap1 - T.gap0), 0, 1);
    if (k === 0) continue;
    out.push([b, k, Math.abs(gap)]);
  }
  out.sort((p, q) => p[2] - q[2]);
  out.slice(0, 16).forEach(([b, k], i) => { LX4.rbx.set([b[0] - 1, b[1] - 1, b[2] + 1, b[3] + 1], i * 4); LX4.rbk[i] = k; });
}

// ---- the reflection pass (after the lighting, before the post pass): reads the lit frame at the mirrored pixel
const LX_RF = GFX_HEAD.replace('uniform sampler2D T;\nuniform vec2 S;\n', '') + `
uniform sampler2D LT, RM, OC, WA, TP, FX;
uniform vec2 S, CAM;
uniform float TM, WPH, HOC;
uniform vec4 RK, RD, RW;
uniform vec3 RG;
uniform vec4 RBX[16], RBK[4];
uniform float RE, DBG;
vec3 dbg = vec3(0.0);
uniform vec3 RT[8], SKY;
vec2 uvp(vec2 p) { return vec2((p.x + 0.5) / S.x, 1.0 - (p.y + 0.5) / S.y); }
void main() {
  vec3 col = texture2D(LT, v).rgb;
  vec4 m = texture2D(RM, v);
  if (m.a > 0.5) {
    vec2 sp = floor(vec2(v.x, 1.0 - v.y) * S);                       // screen px, rows from the top
    float sy = floor(m.g * 255.0 + 0.5) - 40.0, d = sp.y - sy;       // the waterline (screen row) and how far below it this pixel is
    float bq = floor(m.b * 255.0 + 0.5), kind = floor(bq / 32.0 + 0.01), ti = bq - kind * 32.0;
    vec3 tint = vec3(1.0);
    for (int i = 0; i < 8; i++) if (abs(float(i) - ti) < 0.5) tint = mix(vec3(1.0), RT[i], 0.6);   // a hint of the water's colour
    float depth = kind < 1.5 ? RD.x : kind < 2.5 ? RD.y : kind < 3.5 ? RD.z : RD.w;
    if (d >= 0.0 && d < depth) {
      float de = kind < 1.5 ? RE : depth;                               // water: the surroundings fade over RE, bodies reach the whole mask
      float fd = clamp(1.0 - d / de, 0.0, 1.0);
      fd = floor(fd * 4.0 + 0.75) / 4.0;                               // fades with depth in 4 clean steps (pixel-art water strips)
      vec2 q;
      if (kind < 1.5) {                                                // water: rippled (whole-pixel shifts that grow with depth) and
        float amp = 0.6 + d / 16.0, band = floor(sp.y * 0.5);           // wobbling with the drawn surface (drawWater's wave); rows shift in pairs
        float dx = floor(sin(band * 1.9 + TM * 2.2 + (sp.x + CAM.x) * 0.03) * amp + 0.5);
        float wob = floor(sin(WPH + (sp.x + CAM.x) * 0.35) * 1.2 + 0.5);
        q = vec2(sp.x + dx, sy - 1.0 - d + wob);
      } else if (kind < 2.5) q = vec2(sp.x, sy - 1.0 - d);             // ice: sharp
      else if (kind < 3.5) q = vec2(sp.x, sy - 1.0 - d * RW.x);         // wet stone: the floor is seen at a grazing angle, so one px of it
      else q = vec2(sp.x + floor(sin(TM * 3.1 + (sp.x + CAM.x) * 0.5 + sp.y) * 0.6 + 0.5), sy - 1.0 - d * RW.y);   // mirrors several px of height
      if (q.y >= 0.0) {
        vec2 qu = uvp(q);
        vec3 r = texture2D(LT, qu).rgb;
        vec4 o = texture2D(OC, qu);
        float bo = HOC * o.r * o.a, bf = texture2D(FX, qu).a, top = clamp(q.y / 8.0, 0.0, 1.0);
        // a body reflects whole or not at all: one strength per body (lx4BodyK: how high its lowest point stands above the water under
        // it; none when it hovers high, or wades in dark water that hides the part below the line, so its mirror would float loose),
        // the same for every pixel of it: no depth steps cut it into pieces. The smallest box holding the mirrored pixel decides.
        float lc = dot(col, vec3(0.299, 0.587, 0.114)), fg = 0.0, ba = 1e9;
        if (bo > 0.05) for (int i = 0; i < 16; i++) {
          vec4 bx = RBX[i]; float bk = RBK[i / 4][0];
          if (i - 4 * (i / 4) == 1) bk = RBK[i / 4][1]; else if (i - 4 * (i / 4) == 2) bk = RBK[i / 4][2]; else if (i - 4 * (i / 4) == 3) bk = RBK[i / 4][3];
          if (q.x < bx.x || q.x > bx.z || q.y < bx.y || q.y > bx.w) continue;
          float ar = (bx.z - bx.x) * (bx.w - bx.y);
          if (ar < ba) { ba = ar; fg = bk < 0.0 ? -bk * smoothstep(0.08, 0.2, lc) : bk; }   // < 0: wading (only bright water shows it)
        }
        float kf = m.r * fd * top;                                     // the surroundings: lit world faintly, the painted backdrop barely
        float ke = mix(RK.z, RK.x, texture2D(WA, qu).a) * kf * (1.0 - step(0.05, bo));   // (its own painted reflections are not mirrored
                                                                       // twice); a body never shows through this path, only whole (kb)
        float kb = RK.y * m.r * top * max(bo * fg, bf * fd);           // bodies (silhouettes) whole; emitters (lamps, spells) by depth
        float body = max(bo, bf); dbg = vec3(bo, bf, fg * step(0.05, bo));
        if (kind > 2.5 && kind < 3.5) {                                // wet stone: only what is bright (lamps, flames, spells) streaks
          float br = max(r.r, max(r.g, r.b));
          col += r * (max(br - RW.z, 0.0) / max(br, 0.01)) * (RW.w * m.r * fd * mix(0.7, 1.0, body));
        } else {
          vec3 rr = r * tint * RK.w;
          col = max(col, mix(col, rr, ke));                            // the surroundings only lighten the water (it keeps its own colour)
          float lr = dot(rr, vec3(0.299, 0.587, 0.114));
          vec3 rb = mix(rr, rr * max(1.0, (lc * RG.z + 0.012) / max(lr, 0.004)), 1.0 - smoothstep(0.08, 0.2, lc));   // dark armour over dark water: a step above it, so the
          col = mix(col, rb, kb);                                      // silhouette reads as itself instead of vanishing (cloak left floating)
        }
      }
      col += SKY * tint * (m.r * fd * (kind > 2.5 && kind < 3.5 ? 0.3 : 1.0));   // lightning: the sky flashes in the surface
    }
  }
  vec4 tp = texture2D(TP, v);
  if (DBG > 15.5) { gl_FragColor = vec4(DBG < 16.5 ? dbg : m.rgb, 1.0); return; }   // test views: 16 the mirrored bodies (r silhouette, g emitter, b whole-body fade), 17 the mask
  gl_FragColor = vec4(clamp(mix(col, tp.rgb, tp.a), 0.0, 1.0), 1.0);
}`;
function lx4InitGL(gl, mk) {
  try {
    const P = gfxProg(gl, LX_RF), tR = mk(gl.NEAREST), tO2 = mk(gl.LINEAR);
    gl.bindTexture(gl.TEXTURE_2D, tO2); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, W, H, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    const fbo = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fbo); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tO2, 0);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    if (!ok) throw new Error('framebuffer incomplete');
    gl.useProgram(P.prog); [['LT', 0], ['RM', 1], ['OC', 2], ['WA', 3], ['TP', 4], ['FX', 5]].forEach(([n, i]) => gl.uniform1i(P.u[n], i));
    gl.useProgram(GFX.prog);
    Object.assign(LX4, { rf: P, tR, tO2, fbo2: fbo, rfOK: true });
  } catch (e) { console.warn('reflections unavailable:', e && e.message); LX4.rfOK = false; }
}
function lx4Reflect(gl) {
  const P = LX4.rf, u = P.u, T = LX4_TUNE;
  gl.useProgram(P.prog);
  const bind = (i, t) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); };
  bind(1, LX4.tR); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, lowR);
  bind(0, LX.tOut); bind(2, LX.tO); bind(3, LX.tA); bind(4, LX.tT); bind(5, LX.tF);
  gl.uniform2f(u.S, W, H); gl.uniform2f(u.CAM, LX.cx, LX.cy); gl.uniform1f(u.TM, time % 1000); gl.uniform1f(u.WPH, (time * 3) % (Math.PI * 2));
  gl.uniform1f(u.HOC, LXO.on && LXO.n ? 1 : 0);
  gl.uniform4f(u.RK, T.env, T.body, T.bg, T.dark); gl.uniform4f(u.RD, T.wDm, T.iD, T.wetD, T.pudD); gl.uniform1f(u.RE, T.wD); gl.uniform1f(u.DBG, LX.dbg || 0); gl.uniform3f(u.RG, T.gap0, T.gap1, T.lift); gl.uniform4f(u.RW, T.wetS, T.pudS, T.wetT, T.wetK);
  if (!LX4.rt) { LX4.rt = new Float32Array(24); LX4_RT.forEach((c, i) => LX4.rt.set(c, i * 3)); }
  gl.uniform3fv(u.RT, LX4.rt);
  lx4BodyK(); gl.uniform4fv(u.RBX, LX4.rbx); gl.uniform4fv(u.RBK, LX4.rbk);
  const s0 = LX.cand[0], sky = s0 && s0.o && s0.o.sky && LX.n ? s0 : null, c = sky ? lxCol(sky.color) : null, sk = sky ? Math.min(1.6, sky.k) * T.sky : 0;
  gl.uniform3f(u.SKY, sky ? c[0] * sk : 0, sky ? c[1] * sk : 0, sky ? c[2] * sk : 0);
  gl.bindFramebuffer(gl.FRAMEBUFFER, LX4.fbo2); gl.viewport(0, 0, W, H);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.activeTexture(gl.TEXTURE0);
  return LX4.tO2;
}

Object.assign(window.__game, { lx4: { LX4, LX4_TUNE, LX4_HAZE, lowR, lowP } });   // headless tests

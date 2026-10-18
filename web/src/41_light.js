// ------------------------------------------------------------------ dynamic lighting (agent LX, docs/EXPANSION3_CONTRACT.md §3)
// Shaders on + Lighting = Dynamic: renderWorld() (09_main.js) draws the lit scene into `low`, everything that emits light
// into `lowFx` (drawGlow) and the screen overlays into `lowTop`. lxPass() then lights `low` on the GPU at game resolution:
// albedo × (biome ambient × baked AO + Σ coloured lights), the summed light cut into a few soft steps (v17: no dither by
// default), shadowed by a rounded wall SDF, then tone-mapped once (GFX_TM, 40_gfx.js; docs/v17/shading_phase1.md). lowFx goes over the result unlit, lowTop over that, and the
// post shader in 40_gfx.js (bloom, grade, CRT…) runs on the composite. Classic / shaders off: one canvas + renderLighting().
const LX_DEFAULTS = { light: 3, lband: 0, rim: 0 };   // lband: 0 Stepped (v17), 1 Smooth, 2 Dithered (the pre-v17 Pixel look)
for (const [k, v] of Object.entries(LX_DEFAULTS)) if (SETTINGS[k] === undefined) SETTINGS[k] = v;
// v15: Lighting gained a 4th step, "Soft shadows" (SDF ray-marched penumbrae); saves that were on hard shadows move up once
if ((SETTINGS.lxv || 0) < 1) { if (SETTINGS.light === 2) SETTINGS.light = 3; SETTINGS.lxv = 1; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
// v17 shading: "Pixel" bands (Bayer-dithered rings) became "Stepped" (clean steps, same slot 0, so old Pixel saves move over by
// themselves); the luminance rim light is gone and the new edge-only rim starts off, so saves that had the old default (on) switch off once
if ((SETTINGS.lxv || 0) < 2) { if (SETTINGS.lband !== 1) SETTINGS.lband = 0; SETTINGS.rim = 0; SETTINGS.lxv = 2; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
const lxCanvas = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'); x.imageSmoothingEnabled = false; return [c, x]; };
const [lowFx, gFx] = lxCanvas(), [lowTop, gTop] = lxCanvas(), gLow = g;
const LX = { on: false, bad: false, prog: null, u: {}, NL: 48, SS: 12, SSD: 20, n: 0, LP: null, LC: null, cx: 0, cy: 0, amb: [0.5, 0.5, 0.5], pk: 1, room: null, sum: -1, fr: 0, cand: [] };
// look knobs (tests tweak these live): ambient gain, light gain, additive haze, emissive art, AO strength/cap, falloff power, wall depth
// v17 shading: lights no longer clip on their own (the scene is tone-mapped once, 40_gfx.js GFX_TM); knee/top/sat-shoulders are gone.
//   steps/bmax: light bands (count, the light level of the top step); lmax: most light dark stone takes (bright art takes ~1.3);
//   hcap: most haze a pixel gets; hard: penumbra size on Hard shadows; expo: scene exposure (× LX_EXPO[Brightness])
const LX_TUNE = { amb: 0.78, gain: 1.7, haze: 0, hazeRays: 0, hcap: 0.05, emi: 0.85, ao: 0.5, aoMax: 0.5, fall: 1.0, depth: 34, sat: 0.68,
  lmax: 2.2, player: 1.3, soft: 1.0, hard: 0.3, rim: 0.55, fog: 0.55, steps: 6, bmax: 2.6, bsoft: 0.25, desat: 0.4, expo: 1.2 };
// ambient light colour per biome. The level comes from AREAS[b].ambient (the old darkness) so darkT and boss rooms keep working.
// A region can override with AREAS[b].lx = { amb: 'r,g,b', lvl: 0.9 } from its own file.
// playtest pass: the darkest regions were hard to read under Dynamic lighting; lift their ambient a little
const LX_BOOST = { crown: 0.88, necropolis: 1.4, nv_void: 1.25, thornveil: 1.6, barrows: 1.4, crimson: 2.0, catacombs: 1.65, hoarfrost: 1.25, ember: 1.55, cathedral: 1.15, spire: 1.45, starfall: 1.5,
  deep: 1.25, archives: 1.3, neohallow: 1.4, hermit: 1.15, ramparts: 1.1 };   // v17 shading: re-measured (docs/v17/shading_phase1.md): the darkest regions sat at a mean of 8-15/255
const LX_BRIGHT = [0.8, 1, 1.25];   // Settings › Graphics › Brightness: Dark / Normal / Bright (ambient)
const LX_EXPO = [0.88, 1, 1.12];    // ... and the exposure of the whole lit scene, before the tone curve (nothing clips at Bright)
const LX_AMB = {
  ramparts: '175,150,205', catacombs: '125,150,195', cathedral: '165,150,200', mire: '130,180,130', crown: '235,238,248', archives: '185,165,140',
  deep: '220,130,95', spire: '140,160,210', hermit: '180,160,135', ember: '215,130,100', hoarfrost: '145,180,225', sov_void: '190,170,220',
  necropolis: '130,150,220', nv_void: '120,130,190', crimson: '195,120,135', barrows: '110,175,175', thornveil: '120,180,140', starfall: '150,160,225',
  dunes: '240,205,155', vn_dusk1: '225,218,238', vn_dusk2: '195,185,210', vn_dusk3: '165,155,190', neohallow: '165,125,220', neohallow_cyber: '235,240,250',
};
// what stays in the lit layer (everything else a draw routes through drawGlow is emissive)
const LX_GLOW_PROPS = new Set(['lantern', 'candelabra', 'item', 'remnant', 'hookpoint', 'fog']);
const LX_LIT_FX = new Set(['dust', 'wall_dust', 'blood', 'bleed', 'death_ash', 'ink_splash', 'ink_pool', 'ink_page', 'db_splash', 'dp_debris', 'petal',
  'g2_sandstorm', 'g2_chains', 'g2_bramble', 'du_coffin', 'tv_cloud', 'tv_thorn', 'tv_rootspike', 'root_spike', 'kd_pool', 'ground_crack', 'rotmist']);
const LX_LIT_P = new Set(['rock', 'ash', 'dust', 'blood', 'ink', 'petal', 'sand', 'sandd', 'db_foam', 'db_ink', 'db_bubble', 'tv_leaf', 'tv_thorn', 'glass', 'nh_dark', 'env', 'mat', 'wall', 'puddle', 'flood']);
const LX_LIT_PROJ = new Set(['arrow', 'mist', 'emist']);
const LX_PLAYER = { player: true }, LX_FLICKER = { flicker: true };   // shared option objects (lanterns, candles, torches, braziers pass LX_FLICKER)   // the personal light: always kept, never culled

// run a draw callback into the glow layer (unlit, stays bright in the dark and feeds the bloom). Classic: draws normally.
function drawGlow(fn) {
  if (!LX.on || g !== gLow) return fn();
  gFx.setTransform(g.getTransform()); g = gFx;
  try { return fn(); } finally { g = gLow; gFx.globalAlpha = 1; gFx.globalCompositeOperation = 'source-over'; }
}
// v17: a light-coloured hit flash (white, gold, cream) drawn into the lit layer got multiplied by strong lamps into a flat white
// shape. Under Dynamic lighting the sprite is drawn lit and the flash tint goes over it in the overlay layer, exactly as an
// unlit frame would mix it: lit sprite × (1 - flash) + colour × flash, the same at the forge as in the dark. Dark tints stay lit.
const LX_FLASH_L = {};
function lxFlashSplit(opt) {
  if (!LX.on || g !== gLow || opt.lxIn) return false;
  const c = opt.flashColor || '#fff';
  let l = LX_FLASH_L[c];
  if (l === undefined) {
    const h = c[0] === '#' ? (c.length === 4 ? c.slice(1).split('').map(z => z + z).join('') : c.slice(1, 7)) : 'ffffff';
    l = LX_FLASH_L[c] = (0.299 * parseInt(h.slice(0, 2), 16) + 0.587 * parseInt(h.slice(2, 4), 16) + 0.114 * parseInt(h.slice(4, 6), 16)) / 255 || 0;
  }
  return l >= 0.45;
}
function lxFlashOver(fn) {
  gTop.setTransform(g.getTransform()); g = gTop;
  try { fn(); } finally { g = gLow; gTop.setTransform(1, 0, 0, 1, 0, 0); gTop.globalAlpha = 1; gTop.globalCompositeOperation = 'source-over'; }
}
// called at the top of renderWorld: decides the path for this frame
function lxBegin() {
  g = gLow;
  LX.on = !!(room && SETTINGS.shaders && SETTINGS.light > 0 && !LX.bad && gfxReady() && (LX.prog || lxInitGL()));
  if (LX.on) for (const c of [gFx, gTop]) { c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.clearRect(0, 0, W, H); }
  return LX.on;
}
const lxProp = p => p.glow || LX_GLOW_PROPS.has(p.type);
const lxDark = () => typeof darkT !== 'undefined' && darkT > 0;   // snuffed: lanterns go out, so they stop glowing too
function lxDrawProp(p) { if (LX.on && lxProp(p) && !lxDark()) drawGlow(() => drawProp(p)); else drawProp(p); }
function lxDrawFx(f) { if (LX.on && !LX_LIT_FX.has(f.name)) drawGlow(() => drawFx(f)); else drawFx(f); }
function lxSplit(get, set, draw, lit) {   // draw a list in two passes: lit members, then emissive ones into lowFx
  if (!LX.on) return draw();
  const all = get(), a = [], b = [];
  for (const q of all) (lit(q) ? a : b).push(q);
  try { set(a); draw(); set(b); drawGlow(draw); } finally { set(all); }
}
function lxDrawParticles() { lxSplit(() => particles, v => { particles = v; }, drawParticles, p => LX_LIT_P.has(p.kind)); }
function lxDrawProjectiles() { lxSplit(() => projectiles, v => { projectiles = v; }, drawProjectiles, p => LX_LIT_PROJ.has(p.kind)); }

const LX_COL = {};
function lxCol(s) {   // 'r,g,b' or '#rrggbb' -> colour normalised so its brightest channel is 1 (k carries the strength)
  let c = LX_COL[s]; if (c) return c;
  let r = 255, gg = 190, b = 110;
  if (typeof s === 'string') {
    if (s[0] === '#') { const h = s.length === 4 ? s.slice(1).split('').map(q => q + q).join('') : s.slice(1, 7); r = parseInt(h.slice(0, 2), 16); gg = parseInt(h.slice(2, 4), 16); b = parseInt(h.slice(4, 6), 16); }
    else { const q = s.split(',').map(Number); if (q.length >= 3) [r, gg, b] = q; }
  }
  if (!(r >= 0 && gg >= 0 && b >= 0)) [r, gg, b] = [255, 190, 110];
  const m = Math.max(r, gg, b, 1), l = (0.299 * r + 0.587 * gg + 0.114 * b) / m, S = LX_TUNE.sat;
  return (LX_COL[s] = [r, gg, b].map(v => l + (v / m - l) * S));
}

// gather this frame's lights (after culling), strongest first, into the uniform arrays
function lxCollect(ls) {
  const bio = room.def.biome, A = AREAS[bio] || {}, O = A.lx || {};
  const a0 = A.ambient ?? 0.5, amb = typeof darkT !== 'undefined' && darkT > 0 ? Math.min(0.97, a0 + 0.4 * Math.min(1, darkT)) : a0;
  const c = lxCol(O.amb || LX_AMB[bio] || '150,155,180'), lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2], lvl = (1 - amb) * (O.lvl ?? LX_TUNE.amb) * (LX_BOOST[bio] || 1) * LX_BRIGHT[SETTINGS.bright ?? 1] / lum;
  LX.amb = c.map(v => v * lvl);
  // v17: the knight's fill light matters in dark regions and only there (by the region's darkness, AREAS[b].ambient): full from
  // 0.45 up, none in daylight rooms (crown, dunes, the Last Field), stronger while a boss has snuffed the lamps
  LX.pk = clamp((amb - 0.2) / 0.25, 0, 1) * (typeof darkT !== 'undefined' && darkT > 0 ? 1.6 : 1);
  const cx = LX.cx, cy = LX.cy, cand = LX.cand; cand.length = 0;
  for (const L of ls) {
    if (!(L.r > 1) || !(L.k > 0.01)) continue;
    const sx = L.x - cx, sy = L.y - cy;
    if (sx < -L.r || sx > W + L.r || sy < -L.r || sy > H + L.r) continue;
    L._s = L.o === LX_PLAYER ? 1e9 : L.k * Math.min(L.r, 220) * Math.min(L.r, 120);
    cand.push(L);
  }
  cand.sort((p, q) => q._s - p._s);
  const n = Math.min(cand.length, LX.NL), LP = LX.LP, LC = LX.LC, shOn = SETTINGS.light >= 2;
  for (let i = 0; i < n; i++) {
    const L = cand[i], o = L.o || {};
    let x = L.x, y = L.y, r = L.r, k = L.k;
    if (o.flicker) {   // smooth per-light noise, seeded by position so neighbours don't pulse together
      const s = hash2(Math.round(x / 4), Math.round(y / 4)) * 97, t = time;
      const f = 0.5 * Math.sin(t * 7.3 + s) + 0.3 * Math.sin(t * 12.9 + s * 1.7) + 0.2 * Math.sin(t * 23.1 + s * 2.9);
      k *= 1 + 0.14 * f; r *= 1 + 0.035 * f;
    }
    let sh = shOn && o.shadow !== false && r > 16 && r < 280;
    if (sh) {   // a light inside a wall (sconces, lava cells): cast from the nearest open spot, or not at all
      const tx = Math.floor(x / TILE), ty = Math.floor(y / TILE);
      if (isSolidT(tileAt(tx, ty))) {
        let best = null, bd = 1e9;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          if ((!dx && !dy) || isSolidT(tileAt(tx + dx, ty + dy))) continue;
          const qx = clamp(x, (tx + dx) * TILE + 2, (tx + dx + 1) * TILE - 2), qy = clamp(y, (ty + dy) * TILE + 2, (ty + dy + 1) * TILE - 2), d = (qx - x) ** 2 + (qy - y) ** 2;
          if (d < bd) { bd = d; best = [qx, qy]; }
        }
        if (best) [x, y] = best; else sh = false;
      }
    }
    const col = lxCol(L.color), gain = LX_TUNE.gain;
    LP[i * 4] = x; LP[i * 4 + 1] = y; LP[i * 4 + 2] = r; LP[i * 4 + 3] = Math.min(1.6, k) * gain * (L.o === LX_PLAYER ? LX_TUNE.player * LX.pk : 1);
    LC[i * 4] = col[0]; LC[i * 4 + 1] = col[1]; LC[i * 4 + 2] = col[2]; LC[i * 4 + 3] = (sh ? 1 : -1) * (1 + (o.height || 0));
  }
  LX.n = n;
}

// ---- per-room maps: occluder mask (1 texel per tile) and baked ambient occlusion (4 texels per tile), with an 8-tile border
const LX_B = 8, LX_Q = 4;
function lxBuildMaps(R) {
  const B = LX_B, w = R.w + 2 * B, h = R.h + 2 * B, sol = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) sol[y * w + x] = isSolidT(tileAtR(R, x - B, y - B)) ? 255 : 0;
  const Q = LX_Q, aw = w * Q, ah = h * Q, ao = new Uint8Array(aw * ah), sc = TILE / Q, rad = 12, str = LX_TUNE.ao * (R.def.indoor ? 1 : 0.5);
  for (let ay = 0; ay < ah; ay++) for (let ax = 0; ax < aw; ax++) {
    const tx = (ax / Q) | 0, ty = (ay / Q) | 0;
    if (sol[ty * w + tx]) { ao[ay * aw + ax] = 255; continue; }
    const px = (ax % Q + 0.5) * sc, py = (ay % Q + 0.5) * sc;
    let s = 0;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      if (!dx && !dy) continue;
      const nx = tx + dx, ny = ty + dy;
      if (nx < 0 || ny < 0 || nx >= w || ny >= h || !sol[ny * w + nx]) continue;
      const ex = dx < 0 ? px : dx > 0 ? TILE - px : 0, ey = dy < 0 ? py : dy > 0 ? TILE - py : 0, d = Math.hypot(ex, ey);
      if (d < rad) s += (1 - d / rad) ** 2 * (dx && dy ? 0.55 : dy > 0 ? 1.1 : dy < 0 ? 0.7 : 0.9);   // floor contact strongest
    }
    ao[ay * aw + ax] = Math.round(255 * (1 - Math.min(LX_TUNE.aoMax, s * str)));
  }
  lxBlurAO(ao, sol, w, aw, ah, Q);
  return { w, h, sol, aw, ah, ao, sdf: lxSdf(sol, w, h, Q, sc) };
}
// v17: separable gaussian (texel radius 3, sigma ~1.6 texels = ~6 px). AO: over open air only (walls keep 255 and don't bleed
// light into the contact shade), which melts the per-tile stair-steps into soft corners.
const LX_GK = [1, 0.82, 0.45, 0.17].map((q, i, a) => q / (a[0] + 2 * (a[1] + a[2] + a[3])));
function lxBlur(f, aw, ah, wt) {   // in place on a Float32Array; wt (optional): per-texel weight mask
  const tmp = new Float32Array(f.length), R = LX_GK.length - 1;
  for (let pass = 0; pass < 2; pass++) {
    const src = pass ? tmp : f, dst = pass ? f : tmp, sx = pass ? aw : 1, n = pass ? ah : aw, m = pass ? aw : ah, so = pass ? 1 : aw;
    for (let j = 0; j < m; j++) for (let i = 0; i < n; i++) {
      const o = j * so + i * sx;
      if (wt && !wt[o]) { dst[o] = src[o]; continue; }
      let acc = 0, ws = 0;
      for (let k = -R; k <= R; k++) {
        const ii = i + k < 0 ? 0 : i + k >= n ? n - 1 : i + k, q = j * so + ii * sx, w = LX_GK[k < 0 ? -k : k] * (wt ? wt[q] : 1);
        acc += src[q] * w; ws += w;
      }
      dst[o] = acc / ws;
    }
  }
  return f;
}
function lxBlurAO(ao, sol, w, aw, ah, Q) {
  const f = new Float32Array(ao.length), air = new Uint8Array(ao.length);
  for (let i = 0; i < ao.length; i++) { f[i] = ao[i]; air[i] = sol[(((i / aw) | 0) / Q | 0) * w + ((i % aw) / Q | 0)] ? 0 : 1; }
  lxBlur(f, aw, ah, air);
  for (let i = 0; i < ao.length; i++) if (air[i]) ao[i] = Math.round(f[i]);
}
// v15: signed distance (px) to the nearest wall edge at 4 texels per tile, 128 + d in a byte (±127 px; walls negative).
// Exact Euclidean transform (Felzenszwalb) on the texel grid, both ways; the soft-shadow march sphere-traces it.
function lxEdt(f, w, h) {   // f: squared-distance seeds (0 / 1e20), in place -> squared distances in texels
  const n = Math.max(w, h), d = new Float64Array(n), v = new Int32Array(n), z = new Float64Array(n + 1), g = new Float64Array(n);
  const pass = (len, o, st) => {   // one row / column: start offset o, stride st
    for (let q = 0; q < len; q++) g[q] = f[o + q * st];
    let k = 0; v[0] = 0; z[0] = -1e20; z[1] = 1e20;
    for (let q = 1; q < len; q++) {
      let sv;
      while ((sv = ((g[q] + q * q) - (g[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])) <= z[k]) k--;
      k++; v[k] = q; z[k] = sv; z[k + 1] = 1e20;
    }
    k = 0;
    for (let q = 0; q < len; q++) { while (z[k + 1] < q) k++; const r = q - v[k]; d[q] = r * r + g[v[k]]; }
    for (let q = 0; q < len; q++) f[o + q * st] = d[q];
  };
  for (let x = 0; x < w; x++) pass(h, x, w);
  for (let y = 0; y < h; y++) pass(w, y * w, 1);
  return f;
}
function lxSdf(sol, w, h, Q, sc) {
  const aw = w * Q, ah = h * Q, N = aw * ah, fo = new Float64Array(N), fi = new Float64Array(N), out = new Uint8Array(N);
  for (let ay = 0; ay < ah; ay++) for (let ax = 0; ax < aw; ax++) {
    const s = sol[((ay / Q) | 0) * w + ((ax / Q) | 0)], i = ay * aw + ax;
    fo[i] = s ? 0 : 1e20; fi[i] = s ? 1e20 : 0;
  }
  lxEdt(fo, aw, ah); lxEdt(fi, aw, ah);
  const df = new Float32Array(N);
  for (let i = 0; i < N; i++) df[i] = fo[i] > 0 ? Math.sqrt(fo[i]) * sc - sc * 0.5 : -(Math.sqrt(fi[i]) * sc - sc * 0.5);
  lxBlur(df, aw, ah);   // v17: blurring a distance field keeps straight walls where they are and rounds every corner (~6 px)
  for (let i = 0; i < N; i++) out[i] = Math.max(0, Math.min(255, Math.round(128 + df[i])));
  return out;
}
function lxGridSum(R) { let s = 0; const gr = R.grid; for (let i = 0; i < gr.length; i++) s = (s * 31 + gr[i]) | 0; return s; }
function lxMaps(gl) {
  if (LX.room === room && (LX.fr++ % 15 || lxGridSum(room) === LX.sum)) return;   // re-bake when a breakable wall opens
  LX.room = room; LX.sum = lxGridSum(room);
  const t0 = performance.now(), M = lxBuildMaps(room); LX.map = M; LX.mapMs = performance.now() - t0;
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
  gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, LX.tO); gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, M.w, M.h, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, M.sol);
  gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, LX.tAO); gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, M.aw, M.ah, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, M.ao);
  gl.activeTexture(gl.TEXTURE5); gl.bindTexture(gl.TEXTURE_2D, LX.tSD); gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, M.aw, M.ah, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, M.sdf);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 4);
}

// ---- the lighting pass (game resolution, into a texture the post shader samples)
const LX_FS = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
varying vec2 v;
uniform sampler2D A, F, TP, OC, AO, SD;
uniform vec2 S, CAM;
uniform vec4 OR;
uniform vec3 AMB;
uniform float NLt, SHAD, BANDS, NB, BMAX, BSOFT, DESAT, AOK, EMI, HAZE, HCAP, FALL, DEPTH, DBG, LMAX, SOFT, RIM, FOG, TM, PL, EXPO;
uniform vec4 LP[NL], LC[NL];
` + GFX_TM + `
float bayer2(vec2 a) { return fract(a.x * 0.5 + a.y * a.y * 0.75); }
float bayer4(vec2 a) { a = mod(a, 4.0); return bayer2(floor(a * 0.5)) * 0.25 + bayer2(mod(a, 2.0)); }
float occ(vec2 w) { return texture2D(OC, (w - OR.xy) / OR.zw).r; }
float sdf(vec2 w) { return texture2D(SD, (w - OR.xy) / OR.zw).r * 255.0 - 128.0; }   // px to the nearest wall edge, < 0 inside
float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y); }
// v17 light bands. The summed light (not each lamp) is cut into NB steps, evenly spaced in sqrt (roughly perceptual) space,
// so overlapping lamps share one set of steps. Stepped (default): each step edge is an anti-aliased ~1 px ramp, no dither;
// the dimmest step fades out smoothly so a light has no hard outer ring. Dithered (the old look): Bayer-checkered edges.
vec3 bands(vec3 L, float d) {
  if (BANDS < 0.5) return L;
  float m = max(L.r, max(L.g, L.b));
  if (m < 0.0005) return L;
  float n = sqrt(min(m, BMAX) / BMAX) * NB, f = floor(n), r = n - f, q;
  if (BANDS < 1.5) {
    float w = clamp(max(BSOFT, fwidth(n) * 0.75), 0.02, 0.5);   // BSOFT: how much of a step is ramp (0 = hard pixel edge)
    q = n < 1.0 ? n : f + smoothstep(0.5 - w, 0.5 + w, r);
  } else q = f + step(0.5 + (d - 0.5) * 0.7, r);
  q /= NB;
  return L * (m > BMAX ? 1.0 : q * q * BMAX / m);
}
void main() {
  vec2 sp = floor(vec2(v.x, 1.0 - v.y) * S), wp = sp + CAM + 0.5;
  float d = bayer4(sp + CAM);                                       // world-anchored (only the Dithered bands use it)
  vec3 al = texture2D(A, v).rgb;
  float sd0 = sdf(wp);
  float rimE = 0.0; vec2 sn = vec2(0.0);
  if (RIM > 0.0 && sd0 < 1.0 && sd0 > -6.0) {                       // v17 rim: only the lip of the terrain (the outer few px of a wall)
    sn = vec2(sdf(wp + vec2(2.0, 0.0)) - sdf(wp - vec2(2.0, 0.0)), sdf(wp + vec2(0.0, 2.0)) - sdf(wp - vec2(0.0, 2.0)));   // catches a light it faces
    sn /= max(length(sn), 0.001);
    rimE = RIM * smoothstep(-6.0, -1.5, sd0) * (1.0 - smoothstep(0.0, 1.0, sd0));
  }
  vec3 L = vec3(0.0), Lh = vec3(0.0), Lp = vec3(0.0);
  for (int i = 0; i < NL; i++) {
    if (float(i) >= NLt) break;
    vec4 lp = LP[i], lc = LC[i];
    vec2 dv = lp.xy - wp;
    float h = abs(lc.w) - 1.0, dist = length(dv), dh = sqrt(dist * dist + h * h);
    if (dh >= lp.z) continue;
    float x = dh / lp.z, s = 1.0 - x * x, a = s * sqrt(s);          // v17: windowed falloff, no slope at the rim (no visible disc edge)
    if (FALL != 1.0) a = pow(a, FALL);
    vec2 dir = dv / max(dist, 0.001);
    if (lc.w > 0.0 && SHAD > 0.5 && dist > 10.0) {                  // shadows: sphere-trace the (rounded) wall SDF toward the light; the
      float end = dist - 10.0, ls = SOFT * clamp(lp.z * 0.05, 2.0, 12.0);   // light is a disc of radius ls, so the penumbra
      float res = 1.0, t = 1.0, tex = sd0 > 0.0 ? 0.0 : -1.0;                // widens away from the wall that casts it
      for (int k = 0; k < SSD; k++) {
        if (t >= end) break;
        float hh = sdf(wp + dir * t);
        if (tex < 0.0) { if (hh > 0.0) tex = t; else { t += max(-hh, 1.5); continue; } }   // a wall pixel: walk out of its own wall first
        if (hh <= 0.0) { res = 0.0; break; }
        if (t - tex > 3.0) res = min(res, hh * dist / (ls * (t - tex)));   // the first px off a surface: no self-penumbra (it speckled)
        t += max(hh, 1.5);
      }
      a *= smoothstep(0.0, 1.0, res) * clamp(1.0 - (tex < 0.0 ? t : tex) / DEPTH, 0.12, 1.0);   // walls: lit from the surface, fading inward
    }
    vec3 c = lc.rgb * lp.w * a;
    if (float(i) < PL) { Lp += c * a; continue; }                   // the knight's own fill: smooth (a squared again: no disc), unbanded, no rim / haze
    L += c * (1.0 + rimE * max(dot(sn, dir), 0.0));
    if (lp.z > 24.0) Lh += c;                                       // sparks and motes light surfaces but add no haze
  }
  L = bands(L, d) + Lp * (1.0 - 0.75 * smoothstep(0.3, 0.7, max(al.r, max(al.g, al.b))));   // the fill reads the dark knight; pale walls behind him barely take it (no halo)
  float fogm = FOG > 0.0 ? mix(1.0, 0.35 + 1.3 * (0.65 * vn(wp * 0.028 + vec2(TM * 0.19, TM * 0.06)) + 0.35 * vn(wp * 0.07 - vec2(TM * 0.11, 0.0))), FOG) : 1.0;   // drifting dust in the light
  float ao = mix(1.0, texture2D(AO, (wp - OR.xy) / OR.zw).r, AOK);
  vec3 lit = AMB * ao + L * mix(1.0, ao, 0.5);
  float mx = max(al.r, max(al.g, al.b)), mn = min(al.r, min(al.g, al.b)), ch = (mx - mn) / max(mx, 0.02);
  float lm = max(lit.r, max(lit.g, lit.b));                         // bright or saturated art is already painted lit: it takes less light
  float lcap = mix(LMAX, 1.3, max(smoothstep(0.35, 0.75, mx), smoothstep(0.6, 0.92, ch) * step(0.25, mx)));   // (soft cap, so no flat plateau)
  if (lm > 1.0) lit *= (1.0 + (lm - 1.0) / (1.0 + (lm - 1.0) / max(lcap - 1.0, 0.01))) / lm;
  float em = smoothstep(0.84, 1.0, mx) * EMI;                       // the brightest art (lava, runes, eyes, sky) shows as painted
  vec3 hz = Lh * HAZE * fogm * (1.0 - em);
  float hm = max(hz.r, max(hz.g, hz.b));
  hz *= 1.0 / (1.0 + hm / HCAP);                                    // a little light in the air, capped where lamps pile up (lava)
  vec3 hdr = (al * lit + hz) * EXPO;
  vec3 col = tmap(hdr);                                             // scene light -> display (40_gfx.js GFX_TM); post adds glow in the same curve
  float cm = max(hdr.r, max(hdr.g, hdr.b));
  col = mix(col, vec3(max(col.r, max(col.g, col.b))), DESAT * smoothstep(0.7, 4.0, cm));   // hot light runs a little toward white (coloured lamps on stone don't go neon)
  col = mix(col, al, em);
  vec4 fx = texture2D(F, v);
  col = col * (1.0 - 0.85 * fx.a) + fx.rgb * fx.a;                  // emitters: unlit, over the lit scene, as painted
  vec4 tp = texture2D(TP, v);
  if (DBG > 0.5) { gl_FragColor = vec4(DBG < 1.5 ? vec3(occ(wp)) : DBG < 2.5 ? vec3(texture2D(AO, (wp - OR.xy) / OR.zw).r) : DBG < 3.5 ? L * 0.5 : DBG < 4.5 ? vec3(fx.a) : DBG < 5.5 ? vec3(tp.a) : DBG < 6.5 ? tmap(al * lit) : DBG < 7.5 ? vec3(clamp(sd0 / 64.0 + 0.5, 0.0, 1.0)) : vec3(sn * 0.5 + 0.5, rimE), 1.0); return; }   // test views
  gl_FragColor = vec4(clamp(mix(col, tp.rgb, tp.a), 0.0, 1.0), 1.0);
}`;
function lxInitGL() {
  const gl = GFX.gl; if (!gl || !GFX.prog) return false;
  try {
    const maxU = gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS) || 64;
    const NL = Math.max(8, Math.min(TOUCH_UI ? 16 : 48, Math.floor((maxU - 28) / 2))), SS = TOUCH_UI ? 8 : 12, SSD = TOUCH_UI ? 10 : 20;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, GFX_VS)); const ext = gl.getExtension('OES_standard_derivatives') ? '#extension GL_OES_standard_derivatives : enable\n' : '#define fwidth(x) 0.06\n';
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, ext + `#define NL ${NL}\n#define SS ${SS}\n#define SSD ${SSD}\n` + LX_FS));
    gl.bindAttribLocation(prog, Math.max(0, gl.getAttribLocation(GFX.prog, 'a')), 'a');   // shares the post pass's quad
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    const u = {};
    for (const n of ['A', 'F', 'TP', 'OC', 'AO', 'SD', 'S', 'CAM', 'OR', 'AMB', 'NLt', 'SHAD', 'BANDS', 'NB', 'BMAX', 'BSOFT', 'DESAT', 'AOK', 'EMI', 'HAZE', 'HCAP', 'FALL', 'DEPTH', 'DBG', 'LMAX', 'SOFT', 'RIM', 'FOG', 'TM', 'PL', 'EXPO', 'TMK', 'TMT', 'LP', 'LC']) u[n] = gl.getUniformLocation(prog, n);
    const mk = (filt) => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, filt], [gl.TEXTURE_MAG_FILTER, filt], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, p, v); return t; };
    gl.activeTexture(gl.TEXTURE0);
    const tA = mk(gl.NEAREST), tF = mk(gl.NEAREST), tT = mk(gl.NEAREST), tO = mk(gl.LINEAR), tAO = mk(gl.LINEAR), tSD = mk(gl.LINEAR), tOut = mk(gl.LINEAR);
    gl.bindTexture(gl.TEXTURE_2D, tOut); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, W, H, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    const fbo = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fbo); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tOut, 0);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    if (!ok) throw new Error('framebuffer incomplete');
    gl.useProgram(prog); [['A', 0], ['F', 1], ['TP', 2], ['OC', 3], ['AO', 4], ['SD', 5]].forEach(([n, i]) => gl.uniform1i(u[n], i));
    gl.useProgram(GFX.prog);
    Object.assign(LX, { prog, u, NL, SS, SSD, tA, tF, tT, tO, tAO, tSD, tOut, fbo, room: null, LP: new Float32Array(NL * 4), LC: new Float32Array(NL * 4) });
    return true;
  } catch (e) { console.warn('dynamic lighting unavailable:', e && e.message); LX.bad = true; return false; }
}
function lxPass(gl) {
  const u = LX.u;
  gl.useProgram(LX.prog);
  lxMaps(gl);
  const up = (i, t, src, fmt) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); if (src) gl.texImage2D(gl.TEXTURE_2D, 0, fmt, fmt, gl.UNSIGNED_BYTE, src); };
  up(0, LX.tA, low, gl.RGB); up(1, LX.tF, lowFx, gl.RGBA); up(2, LX.tT, lowTop, gl.RGBA); up(3, LX.tO); up(4, LX.tAO); up(5, LX.tSD);
  const T = LX_TUNE, map = LX.map;
  gl.uniform2f(u.S, W, H); gl.uniform2f(u.CAM, LX.cx, LX.cy);
  gl.uniform4f(u.OR, -LX_B * TILE, -LX_B * TILE, map.w * TILE, map.h * TILE);
  gl.uniform3f(u.AMB, LX.amb[0], LX.amb[1], LX.amb[2]);
  const rays = SETTINGS.rays > 0, br = SETTINGS.bright ?? 1;   // Graphics › Light shafts also thickens the haze and lets dust drift through it
  gl.uniform1f(u.NLt, LX.n); gl.uniform1f(u.SHAD, SETTINGS.light >= 2 ? 1 : 0); gl.uniform1f(u.BANDS, [1, 0, 2][SETTINGS.lband | 0] ?? 1);
  gl.uniform1f(u.NB, T.steps); gl.uniform1f(u.BMAX, T.bmax); gl.uniform1f(u.BSOFT, T.bsoft); gl.uniform1f(u.DESAT, T.desat);
  gl.uniform1f(u.SOFT, SETTINGS.light === 3 ? T.soft : T.hard); gl.uniform1f(u.RIM, SETTINGS.rim ? T.rim : 0); gl.uniform1f(u.FOG, rays ? T.fog : 0); gl.uniform1f(u.TM, time % 1000); gl.uniform1f(u.PL, LX.n && LX.cand[0] && LX.cand[0].o === LX_PLAYER ? 1 : 0);
  gl.uniform1f(u.AOK, 1); gl.uniform1f(u.EMI, T.emi * (lxDark() ? 0.35 : 1)); gl.uniform1f(u.HAZE, rays ? T.hazeRays : T.haze); gl.uniform1f(u.HCAP, T.hcap); gl.uniform1f(u.FALL, T.fall); gl.uniform1f(u.DEPTH, T.depth); gl.uniform1f(u.DBG, LX.dbg || 0);
  gl.uniform1f(u.LMAX, T.lmax); gl.uniform1f(u.EXPO, T.expo * LX_EXPO[br]); gl.uniform1f(u.TMK, GFX_TONE.k); gl.uniform1f(u.TMT, GFX_TONE.t);
  gl.uniform4fv(u.LP, LX.LP); gl.uniform4fv(u.LC, LX.LC);
  gl.bindFramebuffer(gl.FRAMEBUFFER, LX.fbo); gl.viewport(0, 0, W, H);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.activeTexture(gl.TEXTURE0);
  return LX.tOut;
}
// if the GL pass dies after the layers were split, flatten them so the plain blit still shows everything
function lxFlatten() { if (!LX.on) return; LX.on = false; gLow.setTransform(1, 0, 0, 1, 0, 0); gLow.drawImage(lowFx, 0, 0); gLow.drawImage(lowTop, 0, 0); }

Object.assign(window.__game, { lx: { LX, LX_TUNE, LX_AMB, setDark(t) { darkT = t; }, addLight, get light() { return lights; } } });   // headless tests

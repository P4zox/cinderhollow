// ------------------------------------------------------------------ dynamic lighting (agent LX, docs/EXPANSION3_CONTRACT.md §3)
// Shaders on + Lighting = Dynamic: renderWorld() (09_main.js) draws the lit scene into `low`, everything that emits light
// into `lowFx` (drawGlow) and the screen overlays into `lowTop`. lxPass() then lights `low` on the GPU at game resolution:
// albedo × (biome ambient × baked AO + Σ coloured lights), the summed light cut into a few soft steps (v17: no dither by
// default), shadowed by a rounded wall SDF, then tone-mapped once (GFX_TM, 40_gfx.js; docs/v17/shading_phase1.md). lowFx goes over the result unlit, lowTop over that, and the
// post shader in 40_gfx.js (bloom, grade, CRT…) runs on the composite. Classic / shaders off: one canvas + renderLighting().
// v17 phase 2 (docs/v17/shading_phase2.md): the far backdrop (drawParallax) goes to its own layer `lowBg` (+ a mask of the biome's
// mid layer, `lowBgM`) and takes the ambient plus only a depth-faded share of the lamps (no rings on painted skies); `low` keeps the
// world with alpha. Surface lighting (41b_surf.js) mirrors sprite / room-layer normals into `lowN`, so lamps wrap the forms and rim them.
// v17 phase 3 (docs/v17/shading_phase3.md): csh Character shadows (0 Off: the old ellipse, 1 Contact: soft pools under feet, 2 On: pools
// + bodies cast shadows from nearby lamps), mat Materials (metal glints, wet / ice sheen; needs Surface lighting), eyead Eye adaptation
const LX_DEFAULTS = { light: 3, lband: 0, rim: 1, surf: TOUCH_UI ? 0 : 1, csh: TOUCH_UI ? 0 : 2, mat: TOUCH_UI ? 0 : 1, eyead: 1 };   // phones: surface lighting starts off (one more layer to draw and upload)   // surf (v17 phase 2): Surface lighting, sprite and brick normals (41b_surf.js)   // lband: 0 Stepped (v17), 1 Smooth, 2 Dithered (the pre-v17 Pixel look)
for (const [k, v] of Object.entries(LX_DEFAULTS)) if (SETTINGS[k] === undefined) SETTINGS[k] = v;
// v15: Lighting gained a 4th step, "Soft shadows" (SDF ray-marched penumbrae); saves that were on hard shadows move up once
if ((SETTINGS.lxv || 0) < 1) { if (SETTINGS.light === 2) SETTINGS.light = 3; SETTINGS.lxv = 1; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
// v17 shading: "Pixel" bands (Bayer-dithered rings) became "Stepped" (clean steps, same slot 0, so old Pixel saves move over by
// themselves); the luminance rim light is gone and the new edge-only rim starts off, so saves that had the old default (on) switch off once
if ((SETTINGS.lxv || 0) < 2) { if (SETTINGS.lband !== 1) SETTINGS.lband = 0; SETTINGS.rim = 0; SETTINGS.lxv = 2; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
// v17 shading phase 2: the rim is rebuilt on the sprites' own silhouettes (41b_surf.js) and ships on; Surface lighting is new (on)
if ((SETTINGS.lxv || 0) < 3) { SETTINGS.rim = 1; SETTINGS.lxv = 3; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
const lxCanvas = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'); x.imageSmoothingEnabled = false; return [c, x]; };
const [lowFx, gFx] = lxCanvas(), [lowTop, gTop] = lxCanvas(), gLow = g;
const LX = { on: false, bad: false, prog: null, u: {}, NL: 48, SS: 12, SSD: 20, n: 0, LP: null, LC: null, cx: 0, cy: 0, amb: [0.5, 0.5, 0.5], pk: 1, room: null, sum: -1, fr: 0, cand: [] };
// look knobs (tests tweak these live): ambient gain, light gain, additive haze, emissive art, AO strength/cap, falloff power, wall depth
// v17 shading: lights no longer clip on their own (the scene is tone-mapped once, 40_gfx.js GFX_TM); knee/top/sat-shoulders are gone.
//   steps/bmax: light bands (count, the light level of the top step); lmax: most light dark stone takes (bright art takes ~1.3);
//   hcap: most haze a pixel gets; hard: penumbra size on Hard shadows; expo: scene exposure (× LX_EXPO[Brightness])
const LX_TUNE = { amb: 0.78, gain: 1.7, haze: 0, hazeRays: 0, hcap: 0.05, emi: 0.85, ao: 0.5, aoMax: 0.5, fall: 1.0, depth: 34, sat: 0.68,
  lmax: 2.2, player: 1.3, soft: 1.0, hard: 0.3, rim: 1.0, fog: 0.55, steps: 6, bmax: 2.6, bsoft: 0.25, desat: 0.4, expo: 1.2,
  // v17 phase 2 (surface lighting): sk how far a light wraps (1 + sk × facing), shz the height (px) a light sits in front of the
  // plane (right in front of a lamp nothing is side-lit), ambk the sky's top-down share on normals, bgk the share of lamp light the
  // far backdrop takes (soft, unshadowed, unbanded), ntol how far the lit pixel may differ from the one the normal was made from
  sk: 1.25, shz: 18, ambk: 0.3, ntol: 0.035,
  bgSky: 0.03, bgMid: 0.3,
  // v17 phase 3: csh how much light a body's shadow takes, con contact pool depth, ckz / cmx where the ray to a lamp crosses the bodies'
  // plane (its share of the way, at most cmx px: the shadow falls on the wall behind, offset away from the lamp), csk the same for the
  // sky; glk metal glints, shk wet / ice sheen, eyez the viewer's distance (px: glints slide a little as the view moves);
  // sky / skyFill / skyReach: lightning (lxSkyLight): the shadowed directional part, the unshadowed fill, how far its shadows reach
  csh: 0.72, con: 0.55, ckz: 0.32, cmx: 26, csk: 9, glk: 2.2, shk: 0.45, eyez: 420, sky: 0.95, skyFill: 0.35, skyReach: 170 };
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
// v17 phase 2: how much lamp light the painted backdrop takes. The far layer is a sky or a far view in most regions (next to
// nothing: a lamp no longer paints rings on it); in the halls whose far painting is the room's own back wall it takes a share.
// The mid layer (silhouettes of arches, pillars, ruins in between) takes LX_TUNE.bgMid. A room / region can override with
// AREAS[b].lxBg = [far, mid]. Vista benches (85_vistas.js) are views: sky share.
const LX_BG_FAR = { archives: 0.8, barrows: 0.75, catacombs: 0.85, cathedral: 0.6, deep: 0.6, forge: 0.8, thornveil: 0.4 };
function lxBgShare() {
  const b = room.def.biome, A = AREAS[b] || {}, T = LX_TUNE;
  if (A.lxBg) return A.lxBg;
  if (typeof VISTA_BG !== 'undefined' && VISTA_BG[room.id]) return [T.bgSky, T.bgSky];
  return [LX_BG_FAR[b] ?? T.bgSky, T.bgMid];
}
// what stays in the lit layer (everything else a draw routes through drawGlow is emissive)
const LX_GLOW_PROPS = new Set(['lantern', 'candelabra', 'item', 'remnant', 'hookpoint', 'fog']);
const LX_LIT_FX = new Set(['dust', 'wall_dust', 'blood', 'bleed', 'death_ash', 'ink_splash', 'ink_pool', 'ink_page', 'db_splash', 'dp_debris', 'petal',
  'g2_sandstorm', 'g2_chains', 'g2_bramble', 'du_coffin', 'tv_cloud', 'tv_thorn', 'tv_rootspike', 'root_spike', 'kd_pool', 'ground_crack', 'rotmist']);
const LX_LIT_P = new Set(['rock', 'ash', 'dust', 'blood', 'ink', 'petal', 'sand', 'sandd', 'db_foam', 'db_ink', 'db_bubble', 'tv_leaf', 'tv_thorn', 'glass', 'nh_dark', 'env', 'mat', 'wall', 'puddle', 'flood']);
const LX_LIT_PROJ = new Set(['arrow', 'mist', 'emist']);
const LX_PLAYER = { player: true }, LX_FLICKER = { flicker: true }, LX_SOFT = { soft: true };   // LX_SOFT: a small marker glow, drawn like the knight's fill (no band rings, no halo on pale art)
   // shared option objects (lanterns, candles, torches, braziers pass LX_FLICKER)   // the personal light: always kept, never culled

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
  if (LX.on) for (const c of [gFx, gTop, gBg]) { c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.clearRect(0, 0, W, H); }
  lxnBegin(LX.on && !!SETTINGS.surf, LX.on);
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

// v17 phase 3: lightning (the Spire's sky flashes and strikes, the Pharaoh's storm) as a directional light from the sky that casts
// real shadows: walls, ledges and bodies shade what lies under them for the length of the flash. Part of the flash stays an unshadowed
// fill so rooms under a roof still flicker. Classic (and Dynamic without shadows) keeps the old big point light.
function lxSkyLight(k, color, slant, classic) {
  if (!(LX.on && SETTINGS.light >= 2 && room)) return classic();
  const T = LX_TUNE;
  addLight(cam.x + W / 2, cam.y + H / 2, 420, color, k * T.skyFill);
  addLight(cam.x + W / 2, cam.y - 200, 9999, color, k * T.sky, { sky: true, dx: slant || 0 });
}
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
  // 0.45 up, none at 0.25 or less (crown, dunes, the Last Field, training), a trace at the Threshold (0.3), stronger while a boss has snuffed the lamps
  LX.pk = clamp((amb - 0.25) / 0.2, 0, 1) * (typeof darkT !== 'undefined' && darkT > 0 ? 1.6 : 1);
  const cx = LX.cx, cy = LX.cy, cand = LX.cand; cand.length = 0;
  for (const L of ls) {
    if (L.o && L.o.sky) { if (L.k > 0.01) { L._s = 2e9; cand.push(L); } continue; }   // lightning: always first
    if (!(L.r > 1) || !(L.k > 0.01)) continue;
    const sx = L.x - cx, sy = L.y - cy;
    if (sx < -L.r || sx > W + L.r || sy < -L.r || sy > H + L.r) continue;
    L._s = L.o === LX_PLAYER ? 1e9 : L.k * Math.min(L.r, 220) * Math.min(L.r, 120);
    cand.push(L);
  }
  cand.sort((p, q) => q._s - p._s);
  const n = Math.min(cand.length, LX.NL), LP = LX.LP, LC = LX.LC, shOn = SETTINGS.light >= 2, cs = SETTINGS.csh >= 2 ? 2048 : 0;
  for (let i = 0; i < n; i++) {
    const L = cand[i], o = L.o || {};
    if (o.sky) {   // directional: xy toward the sky (unit), z < 0: how far its shadows reach
      const col = lxCol(L.color), dl = Math.hypot(o.dx || 0, 1);
      LP[i * 4] = (o.dx || 0) / dl; LP[i * 4 + 1] = -1 / dl; LP[i * 4 + 2] = -LX_TUNE.skyReach; LP[i * 4 + 3] = Math.min(1.6, L.k) * LX_TUNE.gain;
      LC[i * 4] = col[0]; LC[i * 4 + 1] = col[1]; LC[i * 4 + 2] = col[2]; LC[i * 4 + 3] = shOn ? 1 + cs : -1;
      continue;
    }
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
    LP[i * 4] = x; LP[i * 4 + 1] = y; LP[i * 4 + 2] = r; LP[i * 4 + 3] = Math.min(1.6, k) * gain * (L.o === LX_PLAYER ? -LX_TUNE.player * LX.pk : o.soft ? -1 : 1);   // < 0: a soft fill (see LX_FS)
    LC[i * 4] = col[0]; LC[i * 4 + 1] = col[1]; LC[i * 4 + 2] = col[2]; LC[i * 4 + 3] = (sh ? 1 : -1) * (1 + (o.height || 0) + (sh && o.cast !== false ? cs : 0));   // phase 3: + 2048: bodies cast shadows from it
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
uniform sampler2D A, F, TP, BM, AO, SD, NM, BG;
uniform vec2 S, CAM;
uniform vec4 OR;
uniform vec3 AMB;
uniform float NLt, SHAD, BANDS, NB, BMAX, BSOFT, DESAT, AOK, EMI, HAZE, HCAP, FALL, DEPTH, DBG, LMAX, SOFT, RIM, FOG, TM, EXPO;
uniform float SURF, SK, SHZ, AMBK, BGF, BGM, NTOL;
uniform vec4 LP[NL], LC[NL];
uniform vec4 OBB;                                                   // v17 phase 3: the bodies' silhouettes this frame (world px box)
uniform float CSH, CON, CKZ, CMX, CSK, MAT, GLK, SHK, EYEZ;
#if OCC
uniform sampler2D OC;                                               // silhouettes (L × A) and contact pools (A − L × A), 41b_surf.js lowO
float occ(vec2 w) { vec4 o = texture2D(OC, vec2((w.x - CAM.x) / S.x, 1.0 - (w.y - CAM.y) / S.y)); return o.r * o.a; }
#endif
` + GFX_TM + `
float bayer2(vec2 a) { return fract(a.x * 0.5 + a.y * a.y * 0.75); }
float bayer4(vec2 a) { a = mod(a, 4.0); return bayer2(floor(a * 0.5)) * 0.25 + bayer2(mod(a, 2.0)); }
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
  vec4 wA = texture2D(A, v);                                        // the world (unpremultiplied; alpha = coverage over the backdrop)
  vec4 bm = texture2D(BM, v);                                       // v17 phase 2: the backdrop has its own layers (far, mid), lit by the
  vec3 al = wA.rgb, bgc = texture2D(BG, v).rgb;                    // sky / ambient and only a depth-faded share of the lamps (lxBgShare);
                                                                    // BM: where the biome's mid layer is (its alpha), which takes more
  float bgs = mix(BGF, BGM, bm.a);
  float wa = wA.a, lumW = dot(al, vec3(0.299, 0.587, 0.114));
  // surface normal (41b_surf.js): trusted only while the lit layer still shows the pixel it was made from. Phase 3: B holds that
  // pixel's luminance in 6 bits and its material in the 2 low bits (0 matte, 1 metal highlight, 2 sheen, 3 metal)
  vec4 nb = texture2D(NM, v);
  float bq = floor(nb.b * 255.0 + 0.5), mt = bq - 4.0 * floor(bq * 0.25 + 0.01), lumN = floor(bq * 0.25 + 0.01) / 63.0;
  float nk = SURF * step(0.5, nb.a) * step(0.5, wa) * (1.0 - step(NTOL + 0.008 + 0.04 * (1.0 - wa), abs(lumN - lumW)));
  vec2 nxy = (nb.rg * 255.0 - 128.0) / 127.0 * nk;
  float tilt = length(nxy);
  vec2 nd = nxy / max(tilt, 0.001);
  float rimE = RIM * smoothstep(0.86, 0.95, tilt);                  // rim: only the steepest tilt step, the outer pixel of a silhouette
  float mk = MAT * nk * step(0.97, nb.a);                           // phase 3 materials (opaque art only: a blend would mix the bits)
  float mG = mk * (1.0 - step(0.5, abs(mt - 1.0))), mS = mk * (1.0 - step(0.5, abs(mt - 2.0))), mD = mk * (1.0 - step(0.5, abs(mt - 3.0)));
  vec3 n3 = vec3(nxy, sqrt(max(0.0, 1.0 - tilt * tilt)));
  vec3 v3 = normalize(vec3(CAM + 0.5 * S - wp, EYEZ));              // toward the viewer (a little perspective: glints slide as the view moves)
  float occP = 0.0, con = 0.0;                                      // phase 3: is this pixel a body (it receives no body shadows), contact pool
#if OCC
  if (CSH + CON > 0.0) {
    vec4 o0 = texture2D(OC, v); occP = o0.r * o0.a;
    float cr = (o0.a - occP) * 3.0;                                 // the pool in 3 clean steps, like the light bands (smooth with Smooth bands)
    con = CON * (BANDS > 0.5 && BANDS < 1.5 ? (floor(cr) + smoothstep(0.3, 0.7, fract(cr))) / 3.0 : cr / 3.0);
  }
#endif
  float sd0 = sdf(wp);
  vec3 L = vec3(0.0), Lf = vec3(0.0), Lh = vec3(0.0), Lp = vec3(0.0), Lb = vec3(0.0), Lr = vec3(0.0), Ls = vec3(0.0);
  for (int i = 0; i < NL; i++) {
    if (float(i) >= NLt) break;
    vec4 lp = LP[i], lc = LC[i];
    float aw = abs(lc.w), cs = step(2047.5, aw), h = aw - 1.0 - 2048.0 * cs;   // phase 3: +2048 = bodies cast shadows from this light
    vec2 dv; float dist, a;
    if (lp.z < 0.0) { dist = 600.0; dv = lp.xy * dist; a = 1.0; }    // phase 3: lightning, a directional light from the sky (xy: toward it)
    else {
      dv = lp.xy - wp; dist = length(dv);
      float dh = sqrt(dist * dist + h * h);
      if (dh >= lp.z) continue;
      float x = dh / lp.z, s = 1.0 - x * x; a = s * sqrt(s);        // v17: windowed falloff, no slope at the rim (no visible disc edge)
      if (FALL != 1.0) a = pow(a, FALL);
    }
    if (lp.w > 0.0) Lb += lc.rgb * lp.w * a;                        // the backdrop's share (scaled by its depth below): unshadowed
    if (wa < 0.004) { if (lp.z > 24.0) Lh += lc.rgb * abs(lp.w) * a; continue; }   // pure backdrop: no shadow march
    vec2 dir = dv / max(dist, 0.001);
    if (lc.w > 0.0 && SHAD > 0.5 && dist > 10.0) {                  // shadows: sphere-trace the (rounded) wall SDF toward the light; the
      float end = lp.z < 0.0 ? -lp.z : dist - 10.0, ls = SOFT * (lp.z < 0.0 ? 18.0 : clamp(lp.z * 0.05, 2.0, 12.0));   // light is a disc of radius ls, so the penumbra
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
#if OCC
      if (cs > 0.5 && CSH > 0.0 && occP < 0.5 && a > 0.0) {         // phase 3: bodies cast shadows. The wall sits behind them, so the ray from a
        float off = lp.z < 0.0 ? CSK : min(dist * CKZ, CMX);        // pixel to the lamp crosses their plane a share of the way there (capped):
        vec2 q = wp + dir * off;                                    // the shadow lands behind the body, offset away from the lamp, and grows
        if (q.x > OBB.x && q.x < OBB.z && q.y > OBB.y && q.y < OBB.w) {   // softer with that offset
          vec2 pp = vec2(-dir.y, dir.x) * (0.75 + off * 0.07);
          float oc = 0.5 * occ(q) + 0.25 * (occ(q + pp) + occ(q - pp));
          vec2 ls2 = lp.xy - CAM;                                   // a lamp carried inside a silhouette (a lantern, a torch) casts none
          if (oc > 0.01 && lp.z > 0.0 && ls2.x > -6.0 && ls2.y > -6.0 && ls2.x < S.x + 6.0 && ls2.y < S.y + 6.0   // (within 6 px of it: a flame held
              && max(max(occ(lp.xy), occ(lp.xy + vec2(6.0, 0.0))), max(max(occ(lp.xy - vec2(6.0, 0.0)), occ(lp.xy + vec2(0.0, 6.0))), occ(lp.xy - vec2(0.0, 6.0)))) > 0.5) oc = 0.0;   // at a hammer's head)
          a *= 1.0 - CSH * oc;
        }
      }
#endif
    }
    vec3 c = lc.rgb * abs(lp.w) * a;
    if (lp.w < 0.0) { Lp += c * a; continue; }                      // soft fills (the knight's own, marker glows: strength < 0): smooth (a squared again,
                                                                    // no disc), unbanded, no rim / haze, and pale art barely takes them (below)
    if (lp.z > 24.0) Lh += c;                                       // sparks and motes light surfaces but add no haze
    Lf += c;                                                        // the same light on a flat surface (sets the art's soft cap, below)
    if (mk > 0.0 && (lp.z > 40.0 || lp.z < 0.0)) {                 // phase 3 materials: a highlight where the facet turns the lamp toward the eye
                                                                    // (lamps only: sparks and motes would make it sparkle)
      float ndh = dot(n3, normalize(normalize(vec3(dv, lp.z < 0.0 ? 0.8 * dist : SHZ)) + v3));   // The normals have 8 directions × 3 tilts,
      Ls += c * (mG * smoothstep(0.95, 0.98, ndh) * GLK            // so a glint jumps facet to facet as the lamp moves: small, sharp, stepped.
               + mD * smoothstep(0.93, 0.99, ndh) * GLK * 0.08     // metal away from the painted highlights: a faint sheen
               + mS * pow(max(ndh, 0.0), 6.0) * SHK * smoothstep(0.04, 0.3, lumW) * (lp.z < 0.0 ? 0.3 : 1.0));   // wet stone, ice: a soft broad
                                                                    // sheen, following the art's own value (dark mortar stays dark); lightning
                                                                    // would light every flat wet face alike, so it takes only a trace
    }
    if (tilt > 0.01) {                                              // v17 phase 2: the light wraps the form. facing: the normal's tilt toward
      float df = dist / (dist + SHZ), fc = dot(nxy, dir) * df;      // the light (0 right in front of the lamp, where it lights the face)
      c *= max(0.0, 1.0 + SK * fc);
      Lr += c * rimE * smoothstep(0.2, 0.75, dot(nd, dir) * df);    // the edge that faces it catches a rim
    }
    L += c;
  }
  float pa = 1.0 - lumW;                                            // the fill reads the dark knight; pale art behind him barely takes it (no halo):
  float nz = n3.z;
  vec3 Lpf = Lp * min(1.0, pa * pa * 1.4);                          // (1 - albedo luminance)^2, full on the knight's dark plate (lum <= ~0.15)
  Lf = bands(Lf, d) + Lpf;
  L = bands(L, d) + Lpf * mix(1.0, nz, 0.6);                        // phase 2: the fill comes from the front: a form's edges turn away from it
  float fogm = FOG > 0.0 ? mix(1.0, 0.35 + 1.3 * (0.65 * vn(wp * 0.028 + vec2(TM * 0.19, TM * 0.06)) + 0.35 * vn(wp * 0.07 - vec2(TM * 0.11, 0.0))), FOG) : 1.0;   // drifting dust in the light
  float ao = mix(1.0, texture2D(AO, (wp - OR.xy) / OR.zw).r, AOK) * (1.0 - con);   // phase 3: + the contact pools (a body's own AO on the floor)
  vec3 litF = AMB * ao + Lf * mix(1.0, ao, 0.5) * (1.0 - 0.6 * con);
  vec3 lit = AMB * ao * (1.0 - AMBK * nxy.y) + L * mix(1.0, ao, 0.5) * (1.0 - 0.6 * con);   // normals: the sky lights tops a little more than undersides
  float mx = max(al.r, max(al.g, al.b)), mn = min(al.r, min(al.g, al.b)), ch = (mx - mn) / max(mx, 0.02);
  float lm = max(litF.r, max(litF.g, litF.b));                      // bright or saturated art is already painted lit: it takes less light. Phase 2:
                                                                    // the cap is set by the flat light and scales the shaded light, so the form's
                                                                    // light and shade keep their ratio instead of being squeezed into the cap
  float lcap = mix(LMAX, 1.3, max(smoothstep(0.35, 0.75, mx), smoothstep(0.6, 0.92, ch) * step(0.25, mx)));   // (soft cap, so no flat plateau)
  if (lm > 1.0) lit *= (1.0 + (lm - 1.0) / (1.0 + (lm - 1.0) / max(lcap - 1.0, 0.01))) / lm;
  vec3 rim = Lr / (1.0 + max(Lr.r, max(Lr.g, Lr.b)) / 0.6);         // the rim adds light of its own (black outlines catch it too), capped
  vec3 spc = Ls / (1.0 + max(Ls.r, max(Ls.g, Ls.b)) / 0.5);        // phase 3: glints / sheen add light of their own, capped (accents, not
  spc *= mix(vec3(1.0), al / max(mx, 0.05), 0.35 * (mG + mD));      // flares); metal tints its glint a little
  vec3 alC = mix(bgc, al, wa);                                      // what the pixel shows, for the emitter test and the backdrop
  float mxC = max(alC.r, max(alC.g, alC.b));
  float em = smoothstep(0.84, 1.0, mxC) * EMI;                      // the brightest art (lava, runes, eyes, sky) shows as painted
  vec3 hz = Lh * HAZE * fogm * (1.0 - em);
  float hm = max(hz.r, max(hz.g, hz.b));
  hz *= 1.0 / (1.0 + hm / HCAP);                                    // a little light in the air, capped where lamps pile up (lava)
  vec3 hdrB = bgc * (AMB + bands(Lb * bgs, d));                     // the backdrop: sky light, plus its share of the lamps (a painted
                                                                    // hall wall takes some, a sky next to nothing: no rings on pale skies)
  float bl = dot(bgc, vec3(0.299, 0.587, 0.114));                   // seen through a back wall (the veil's fading steps) the backdrop is lit
  hdrB = mix(hdrB, bgc * lit, max(smoothstep(0.3, 0.8, wa), smoothstep(0.0, 0.3, wa) * (1.0 - smoothstep(0.12, 0.4, bl))));   // with the wall:
                                                                    // the pool of lamp light stays whole, except where a pale sky shows through
  vec3 hdr = (mix(hdrB, al * lit + rim + spc, wa) + hz) * EXPO;
  vec3 col = tmap(hdr);                                             // scene light -> display (40_gfx.js GFX_TM); post adds glow in the same curve
  float cm = max(hdr.r, max(hdr.g, hdr.b));
  col = mix(col, vec3(max(col.r, max(col.g, col.b))), DESAT * smoothstep(0.7, 4.0, cm));   // hot light runs a little toward white (coloured lamps on stone don't go neon)
  col = mix(col, alC, em);
  vec4 fx = texture2D(F, v);
  col = col * (1.0 - 0.85 * fx.a) + fx.rgb * fx.a;                  // emitters: unlit, over the lit scene, as painted
  vec4 tp = texture2D(TP, v);
  if (DBG > 0.5) { gl_FragColor = vec4(DBG < 1.5 ? vec3(texture2D(BM, v).a) : DBG < 2.5 ? vec3(texture2D(AO, (wp - OR.xy) / OR.zw).r) : DBG < 3.5 ? L * 0.5 : DBG < 4.5 ? vec3(fx.a) : DBG < 5.5 ? vec3(tp.a) : DBG < 6.5 ? tmap(al * lit) : DBG < 7.5 ? vec3(clamp(sd0 / 64.0 + 0.5, 0.0, 1.0)) : DBG < 8.5 ? vec3(nxy * 0.5 + 0.5, nk) : DBG < 9.5 ? vec3(wa) : DBG < 10.5 ? rim : DBG < 11.5 ? vec3(occP, con / max(CON, 0.01), 0.0) : DBG < 12.5 ? vec3(mG, mS, mD) : spc, 1.0); return; }   // test views (8 normals, 9 world coverage, 10 rim; phase 3: 11 silhouettes / pools, 12 materials, 13 glints)
  gl_FragColor = vec4(clamp(mix(col, tp.rgb, tp.a), 0.0, 1.0), 1.0);
}`;
function lxInitGL() {
  const gl = GFX.gl; if (!gl || !GFX.prog) return false;
  try {
    const maxU = gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS) || 64;
    const NL = Math.max(8, Math.min(TOUCH_UI ? 16 : 48, Math.floor((maxU - 40) / 2))), SS = TOUCH_UI ? 8 : 12, SSD = TOUCH_UI ? 10 : 20;
    const OCC = (gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS) || 8) >= 9 ? 1 : 0;   // phase 3: the silhouette / pool buffer takes a 9th texture unit
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, GFX_VS)); const ext = gl.getExtension('OES_standard_derivatives') ? '#extension GL_OES_standard_derivatives : enable\n' : '#define fwidth(x) 0.06\n';
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, ext + `#define NL ${NL}\n#define SS ${SS}\n#define SSD ${SSD}\n#define OCC ${OCC}\n` + LX_FS));
    gl.bindAttribLocation(prog, Math.max(0, gl.getAttribLocation(GFX.prog, 'a')), 'a');   // shares the post pass's quad
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    const u = {};
    for (const n of ['A', 'F', 'TP', 'BM', 'AO', 'SD', 'S', 'CAM', 'OR', 'AMB', 'NLt', 'SHAD', 'BANDS', 'NB', 'BMAX', 'BSOFT', 'DESAT', 'AOK', 'EMI', 'HAZE', 'HCAP', 'FALL', 'DEPTH', 'DBG', 'LMAX', 'SOFT', 'RIM', 'FOG', 'TM', 'EXPO', 'TMK', 'TMT', 'LP', 'LC', 'NM', 'BG', 'SURF', 'SK', 'SHZ', 'AMBK', 'BGF', 'BGM', 'NTOL', 'OC', 'OBB', 'CSH', 'CON', 'CKZ', 'CMX', 'CSK', 'MAT', 'GLK', 'SHK', 'EYEZ']) u[n] = gl.getUniformLocation(prog, n);
    const mk = (filt) => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, filt], [gl.TEXTURE_MAG_FILTER, filt], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, p, v); return t; };
    gl.activeTexture(gl.TEXTURE0);
    const tA = mk(gl.NEAREST), tF = mk(gl.NEAREST), tT = mk(gl.NEAREST), tN = mk(gl.NEAREST), tB = mk(gl.NEAREST), tBM = mk(gl.NEAREST), tAO = mk(gl.LINEAR), tSD = mk(gl.LINEAR), tOut = mk(gl.LINEAR);
    const tO = mk(gl.LINEAR); gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE_ALPHA, 1, 1, 0, gl.LUMINANCE_ALPHA, gl.UNSIGNED_BYTE, new Uint8Array(2));   // phase 3 (filtered: soft silhouette taps)
    gl.bindTexture(gl.TEXTURE_2D, tOut); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, W, H, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    const fbo = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fbo); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tOut, 0);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    if (!ok) throw new Error('framebuffer incomplete');
    gl.useProgram(prog); [['A', 0], ['F', 1], ['TP', 2], ['BM', 3], ['AO', 4], ['SD', 5], ['NM', 6], ['BG', 7]].concat(OCC ? [['OC', 8]] : []).forEach(([n, i]) => gl.uniform1i(u[n], i));
    gl.useProgram(GFX.prog);
    Object.assign(LX, { prog, u, NL, SS, SSD, tA, tF, tT, tN, tB, tBM, tAO, tSD, tOut, tO, fbo, ocOK: !!OCC, room: null, LP: new Float32Array(NL * 4), LC: new Float32Array(NL * 4) });
    return true;
  } catch (e) { console.warn('dynamic lighting unavailable:', e && e.message); LX.bad = true; return false; }
}
function lxPass(gl) {
  const u = LX.u;
  gl.useProgram(LX.prog);
  lxMaps(gl);
  const up = (i, t, src, fmt) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); if (src) gl.texImage2D(gl.TEXTURE_2D, 0, fmt, fmt, gl.UNSIGNED_BYTE, src); };
  up(0, LX.tA, low, gl.RGBA); up(1, LX.tF, lowFx, gl.RGBA); up(2, LX.tT, lowTop, gl.RGBA); up(3, LX.tBM, lowBgM, gl.ALPHA); up(4, LX.tAO); up(5, LX.tSD);
  up(6, LX.tN, LXN.on ? lowN : null, gl.RGBA); up(7, LX.tB, lowBg, gl.RGB);   // v17 phase 2: normals (only uploaded while on), the backdrop
  if (LX.ocOK) up(8, LX.tO, LXO.on ? lowO : null, gl.LUMINANCE_ALPHA);          // phase 3: silhouettes + contact pools (only while on)
  const T = LX_TUNE, map = LX.map;
  gl.uniform2f(u.S, W, H); gl.uniform2f(u.CAM, LX.cx, LX.cy);
  gl.uniform4f(u.OR, -LX_B * TILE, -LX_B * TILE, map.w * TILE, map.h * TILE);
  gl.uniform3f(u.AMB, LX.amb[0], LX.amb[1], LX.amb[2]);
  const rays = SETTINGS.rays > 0, br = SETTINGS.bright ?? 1;   // Graphics › Light shafts also thickens the haze and lets dust drift through it
  gl.uniform1f(u.NLt, LX.n); gl.uniform1f(u.SHAD, SETTINGS.light >= 2 ? 1 : 0); gl.uniform1f(u.BANDS, [1, 0, 2][SETTINGS.lband | 0] ?? 1);
  gl.uniform1f(u.NB, T.steps); gl.uniform1f(u.BMAX, T.bmax); gl.uniform1f(u.BSOFT, T.bsoft); gl.uniform1f(u.DESAT, T.desat);
  gl.uniform1f(u.SOFT, SETTINGS.light === 3 ? T.soft : T.hard); gl.uniform1f(u.RIM, SETTINGS.rim && LXN.on ? T.rim : 0); gl.uniform1f(u.FOG, rays ? T.fog : 0); gl.uniform1f(u.TM, time % 1000);
  gl.uniform1f(u.AOK, 1); gl.uniform1f(u.EMI, T.emi * (lxDark() ? 0.35 : 1)); gl.uniform1f(u.HAZE, rays ? T.hazeRays : T.haze); gl.uniform1f(u.HCAP, T.hcap); gl.uniform1f(u.FALL, T.fall); gl.uniform1f(u.DEPTH, T.depth); gl.uniform1f(u.DBG, LX.dbg || 0);
  gl.uniform1f(u.LMAX, T.lmax); gl.uniform1f(u.EXPO, T.expo * LX_EXPO[br]); gl.uniform1f(u.TMK, GFX_TONE.k); gl.uniform1f(u.TMT, GFX_TONE.t);
  gl.uniform1f(u.SURF, LXN.on ? 1 : 0); gl.uniform1f(u.SK, T.sk); gl.uniform1f(u.SHZ, T.shz); gl.uniform1f(u.AMBK, T.ambk); const bk = lxBgShare(); gl.uniform1f(u.BGF, bk[0]); gl.uniform1f(u.BGM, bk[1]); gl.uniform1f(u.NTOL, T.ntol);
  gl.uniform4fv(u.LP, LX.LP); gl.uniform4fv(u.LC, LX.LC);
  const cso = LXO.on, B = LXO.bb, hasO = cso && LXO.n > 0 && SETTINGS.csh >= 2;   // phase 3: character shadows, contact pools, materials
  gl.uniform1f(u.CSH, hasO ? T.csh : 0); gl.uniform1f(u.CON, cso ? T.con : 0);
  if (hasO) gl.uniform4f(u.OBB, B[0] + LX.cx - 2, B[1] + LX.cy - 2, B[2] + LX.cx + 2, B[3] + LX.cy + 2); else gl.uniform4f(u.OBB, 1e9, 1e9, -1e9, -1e9);
  gl.uniform1f(u.CKZ, T.ckz); gl.uniform1f(u.CMX, T.cmx); gl.uniform1f(u.CSK, T.csk);
  gl.uniform1f(u.MAT, SETTINGS.mat && LXN.on ? 1 : 0); gl.uniform1f(u.GLK, T.glk); gl.uniform1f(u.SHK, T.shk); gl.uniform1f(u.EYEZ, T.eyez);
  gl.bindFramebuffer(gl.FRAMEBUFFER, LX.fbo); gl.viewport(0, 0, W, H);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.activeTexture(gl.TEXTURE0);
  return LX.tOut;
}
// if the GL pass dies after the layers were split, flatten them so the plain blit still shows everything
function lxFlatten() {
  if (!LX.on) return; LX.on = false; lxnBegin(false, false); gLow.setTransform(1, 0, 0, 1, 0, 0);
  gLow.globalCompositeOperation = 'destination-over'; gLow.drawImage(lowBg, 0, 0); gLow.globalCompositeOperation = 'source-over';   // the backdrop goes back under
  gLow.drawImage(lowFx, 0, 0); gLow.drawImage(lowTop, 0, 0);
}
// v17 phase 2: under Dynamic lighting the far backdrop (drawParallax and its overrides: biome layers, vistas, forge…) is drawn
// into its own layer, so lamps light the world and not the painted sky behind it. Other code that needs the whole picture.
function lxDrawBackdrop() {
  if (!LX.on) return drawParallax();
  g = gBg; lxMidG = gBgM; gBgM.setTransform(1, 0, 0, 1, 0, 0); gBgM.clearRect(0, 0, W, H);   // the biome's mid layer goes to its own canvas (03_world.js)
  try { drawParallax(); } finally { g = gLow; lxMidG = null; for (const c of [gBg, gBgM]) { c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; } }
}
function lxWholeLow(ctx) { if (LX.on) ctx.drawImage(lowBg, 0, 0); ctx.drawImage(low, 0, 0); }

Object.assign(window.__game, { lx: { LX, LX_TUNE, LX_AMB, setDark(t) { darkT = t; }, addLight, get light() { return lights; } } });   // headless tests

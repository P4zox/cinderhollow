// ------------------------------------------------------------------ dynamic lighting (agent LX, docs/EXPANSION3_CONTRACT.md §3)
// Shaders on + Lighting = Dynamic: renderWorld() (09_main.js) draws the lit scene into `low`, everything that emits light
// into `lowFx` (drawGlow) and the screen overlays into `lowTop`. lxPass() then lights `low` on the GPU at game resolution:
// albedo × (biome ambient × baked AO + Σ coloured lights), each light banded into 5 steps with a 4×4 Bayer dither on the
// band edges, shadowed by a 1-texel-per-tile occluder mask. lowFx goes over the result unlit, lowTop over that, and the
// post shader in 40_gfx.js (bloom, grade, CRT…) runs on the composite. Classic / shaders off: one canvas + renderLighting().
const LX_DEFAULTS = { light: 2, lband: 0 };
for (const [k, v] of Object.entries(LX_DEFAULTS)) if (SETTINGS[k] === undefined) SETTINGS[k] = v;
const lxCanvas = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'); x.imageSmoothingEnabled = false; return [c, x]; };
const [lowFx, gFx] = lxCanvas(), [lowTop, gTop] = lxCanvas(), gLow = g;
const LX = { on: false, bad: false, prog: null, u: {}, NL: 48, SS: 12, n: 0, LP: null, LC: null, cx: 0, cy: 0, amb: [0.5, 0.5, 0.5], room: null, sum: -1, fr: 0, cand: [] };
// look knobs (tests tweak these live): ambient gain, light gain, additive haze, emissive art, AO strength/cap, falloff power, wall depth
const LX_TUNE = { amb: 0.78, gain: 2.0, haze: 0.09, emi: 0.65, ao: 0.42, aoMax: 0.46, fall: 1.0, depth: 34, sat: 0.85, knee: 1.0, top: 1.9, player: 0.85 };
// ambient light colour per biome. The level comes from AREAS[b].ambient (the old darkness) so darkT and boss rooms keep working.
// A region can override with AREAS[b].lx = { amb: 'r,g,b', lvl: 0.9 } from its own file.
// playtest pass: the darkest regions were hard to read under Dynamic lighting; lift their ambient a little
const LX_BOOST = { crown: 0.88, necropolis: 1.4, nv_void: 1.25, thornveil: 1.35, barrows: 1.4, crimson: 1.3, catacombs: 1.25, hoarfrost: 1.25, ember: 1.3, cathedral: 1.1, spire: 1.1, starfall: 1.1 };
const LX_BRIGHT = [0.8, 1, 1.3];   // Settings › Graphics › Brightness: Dark / Normal / Bright
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
  const cx = LX.cx, cy = LX.cy, cand = LX.cand; cand.length = 0;
  for (const L of ls) {
    if (!(L.r > 1) || !(L.k > 0.01)) continue;
    const sx = L.x - cx, sy = L.y - cy;
    if (sx < -L.r || sx > W + L.r || sy < -L.r || sy > H + L.r) continue;
    L._s = L.o === LX_PLAYER ? 1e9 : L.k * Math.min(L.r, 220) * Math.min(L.r, 120);
    cand.push(L);
  }
  cand.sort((p, q) => q._s - p._s);
  const n = Math.min(cand.length, LX.NL), LP = LX.LP, LC = LX.LC, shOn = SETTINGS.light === 2;
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
    LP[i * 4] = x; LP[i * 4 + 1] = y; LP[i * 4 + 2] = r; LP[i * 4 + 3] = Math.min(1.6, k) * gain * (L.o === LX_PLAYER ? LX_TUNE.player : 1);
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
  return { w, h, sol, aw, ah, ao };
}
function lxGridSum(R) { let s = 0; const gr = R.grid; for (let i = 0; i < gr.length; i++) s = (s * 31 + gr[i]) | 0; return s; }
function lxMaps(gl) {
  if (LX.room === room && (LX.fr++ % 15 || lxGridSum(room) === LX.sum)) return;   // re-bake when a breakable wall opens
  LX.room = room; LX.sum = lxGridSum(room);
  const t0 = performance.now(), M = lxBuildMaps(room); LX.map = M; LX.mapMs = performance.now() - t0;
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
  gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, LX.tO); gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, M.w, M.h, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, M.sol);
  gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, LX.tAO); gl.texImage2D(gl.TEXTURE_2D, 0, gl.LUMINANCE, M.aw, M.ah, 0, gl.LUMINANCE, gl.UNSIGNED_BYTE, M.ao);
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
uniform sampler2D A, F, TP, OC, AO;
uniform vec2 S, CAM;
uniform vec4 OR;
uniform vec3 AMB;
uniform float NLt, STEPS, SMOOTH, AOK, EMI, HAZE, FALL, DEPTH, DBG, KNEE, TOP;
uniform vec4 LP[NL], LC[NL];
float bayer2(vec2 a) { return fract(a.x * 0.5 + a.y * a.y * 0.75); }
float bayer4(vec2 a) { a = mod(a, 4.0); return bayer2(floor(a * 0.5)) * 0.25 + bayer2(mod(a, 2.0)); }
float occ(vec2 w) { return texture2D(OC, (w - OR.xy) / OR.zw).r; }
float band(float x, float d) {                                     // 5 flat bands, Bayer-dithered across each edge
  if (SMOOTH > 0.5) return x;
  float n = x * 5.0, f = floor(n);
  return (f + step(0.5 + (d - 0.5) * 0.7, n - f)) * 0.2;
}
void main() {
  vec2 sp = floor(vec2(v.x, 1.0 - v.y) * S), wp = sp + CAM + 0.5;
  float d = bayer4(sp + CAM);                                       // world-anchored: the dither doesn't swim as the camera moves
  vec3 al = texture2D(A, v).rgb;
  float inside = step(0.5, occ(wp));
  vec3 L = vec3(0.0), Lh = vec3(0.0);
  for (int i = 0; i < NL; i++) {
    if (float(i) >= NLt) break;
    vec4 lp = LP[i], lc = LC[i];
    vec2 dv = lp.xy - wp;
    float h = abs(lc.w) - 1.0, dist = length(dv), dh = sqrt(dist * dist + h * h);
    if (dh >= lp.z) continue;
    float a = pow(1.0 - dh / lp.z, FALL);
    if (lc.w > 0.0 && STEPS > 0.5 && dist > 10.0) {               // march toward the light; the last 10px (its own wall) never shadow
      float end = (dist - 10.0) / dist, lit = 1.0, ins = inside, depth = 0.0;
      for (int s = 0; s < SS; s++) {
        if (float(s) >= STEPS) break;
        float k = (float(s) + d) / STEPS * end;
        float o = smoothstep(0.3, 0.7, occ(wp + dv * k));
        if (ins > 0.5) { if (o < 0.5) ins = 0.0; else depth = k * dist; }   // inside a wall: lit from its surface, fading inward
        else lit *= 1.0 - o;
      }
      a *= lit * clamp(1.0 - depth / DEPTH, 0.12, 1.0);
    }
    vec3 c = lc.rgb * lp.w * band(a, d);
    L += c; if (lp.z > 24.0) Lh += c;                                // sparks and motes light surfaces but add no haze
  }
  float ao = texture2D(AO, (wp - OR.xy) / OR.zw).r;
  if (SMOOTH < 0.5) ao = floor(ao * 10.0 + d) * 0.1;
  ao = mix(1.0, ao, AOK);
  vec3 lit = AMB * ao + L * mix(1.0, ao, 0.5);
  float mx = max(al.r, max(al.g, al.b)), em = smoothstep(0.84, 1.0, mx) * EMI;
  vec3 over = max(lit - KNEE, 0.0);
  lit = min(lit, vec3(KNEE)) + over / (1.0 + over / (TOP - KNEE));  // soft shoulder: hot spots saturate gently, never flat white
  float mn = min(al.r, min(al.g, al.b)), ch = (mx - mn) / max(mx, 0.02);
  float cap = mix(TOP, 1.15, max(smoothstep(0.35, 0.75, mx), smoothstep(0.6, 0.92, ch) * step(0.25, mx))), lm = max(lit.r, max(lit.g, lit.b));   // dark stone can take a lot of light;
  if (lm > cap) lit *= cap / lm;                                                                // bright art is already painted lit
  lit = mix(lit, max(lit, vec3(1.0)) / max(1.0, max(lit.r, max(lit.g, lit.b))) * 1.08, em);   // bright art (lava, runes, eyes, sky) shows as painted
  vec3 col = al * lit + Lh * HAZE * (1.0 - em) / (1.0 + 0.5 * max(Lh.r, max(Lh.g, Lh.b)));   // a little light in the air; saturates where lights pile up (lava)
  vec3 hi = max(col - 0.75, 0.0); col = mix(min(col, vec3(0.75)) + hi / (1.0 + hi * 4.0), col, em);   // highlight shoulder: lit stone keeps its texture
  vec4 fx = texture2D(F, v);
  col = col * (1.0 - 0.85 * fx.a) + fx.rgb * fx.a;                  // emitters: unlit, over the lit scene
  vec4 tp = texture2D(TP, v);
  if (DBG > 0.5) { gl_FragColor = vec4(DBG < 1.5 ? vec3(occ(wp)) : DBG < 2.5 ? vec3(texture2D(AO, (wp - OR.xy) / OR.zw).r) : DBG < 3.5 ? L * 0.5 : DBG < 4.5 ? vec3(fx.a) : DBG < 5.5 ? vec3(tp.a) : al * lit, 1.0); return; }   // test views
  gl_FragColor = vec4(clamp(mix(col, tp.rgb, tp.a), 0.0, 1.0), 1.0);
}`;
function lxInitGL() {
  const gl = GFX.gl; if (!gl || !GFX.prog) return false;
  try {
    const maxU = gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS) || 64;
    const NL = Math.max(8, Math.min(TOUCH_UI ? 16 : 48, Math.floor((maxU - 24) / 2))), SS = TOUCH_UI ? 8 : 12;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, GFX_VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, `#define NL ${NL}\n#define SS ${SS}\n` + LX_FS));
    gl.bindAttribLocation(prog, Math.max(0, gl.getAttribLocation(GFX.prog, 'a')), 'a');   // shares the post pass's quad
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    const u = {};
    for (const n of ['A', 'F', 'TP', 'OC', 'AO', 'S', 'CAM', 'OR', 'AMB', 'NLt', 'STEPS', 'SMOOTH', 'AOK', 'EMI', 'HAZE', 'FALL', 'DEPTH', 'DBG', 'KNEE', 'TOP', 'LP', 'LC']) u[n] = gl.getUniformLocation(prog, n);
    const mk = (filt) => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, filt], [gl.TEXTURE_MAG_FILTER, filt], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, p, v); return t; };
    gl.activeTexture(gl.TEXTURE0);
    const tA = mk(gl.NEAREST), tF = mk(gl.NEAREST), tT = mk(gl.NEAREST), tO = mk(gl.LINEAR), tAO = mk(gl.LINEAR), tOut = mk(gl.LINEAR);
    gl.bindTexture(gl.TEXTURE_2D, tOut); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, W, H, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    const fbo = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fbo); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tOut, 0);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    if (!ok) throw new Error('framebuffer incomplete');
    gl.useProgram(prog); [['A', 0], ['F', 1], ['TP', 2], ['OC', 3], ['AO', 4]].forEach(([n, i]) => gl.uniform1i(u[n], i));
    gl.useProgram(GFX.prog);
    Object.assign(LX, { prog, u, NL, SS, tA, tF, tT, tO, tAO, tOut, fbo, room: null, LP: new Float32Array(NL * 4), LC: new Float32Array(NL * 4) });
    return true;
  } catch (e) { console.warn('dynamic lighting unavailable:', e && e.message); LX.bad = true; return false; }
}
function lxPass(gl) {
  const u = LX.u;
  gl.useProgram(LX.prog);
  lxMaps(gl);
  const up = (i, t, src, fmt) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); if (src) gl.texImage2D(gl.TEXTURE_2D, 0, fmt, fmt, gl.UNSIGNED_BYTE, src); };
  up(0, LX.tA, low, gl.RGB); up(1, LX.tF, lowFx, gl.RGBA); up(2, LX.tT, lowTop, gl.RGBA); up(3, LX.tO); up(4, LX.tAO);
  const T = LX_TUNE, map = LX.map;
  gl.uniform2f(u.S, W, H); gl.uniform2f(u.CAM, LX.cx, LX.cy);
  gl.uniform4f(u.OR, -LX_B * TILE, -LX_B * TILE, map.w * TILE, map.h * TILE);
  gl.uniform3f(u.AMB, LX.amb[0], LX.amb[1], LX.amb[2]);
  gl.uniform1f(u.NLt, LX.n); gl.uniform1f(u.STEPS, SETTINGS.light === 2 ? LX.SS : 0); gl.uniform1f(u.SMOOTH, SETTINGS.lband ? 1 : 0);
  gl.uniform1f(u.AOK, 1); gl.uniform1f(u.EMI, T.emi * (lxDark() ? 0.35 : 1)); gl.uniform1f(u.HAZE, T.haze); gl.uniform1f(u.FALL, T.fall); gl.uniform1f(u.DEPTH, T.depth); gl.uniform1f(u.DBG, LX.dbg || 0); gl.uniform1f(u.KNEE, T.knee); gl.uniform1f(u.TOP, T.top);
  gl.uniform4fv(u.LP, LX.LP); gl.uniform4fv(u.LC, LX.LC);
  gl.bindFramebuffer(gl.FRAMEBUFFER, LX.fbo); gl.viewport(0, 0, W, H);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.activeTexture(gl.TEXTURE0);
  return LX.tOut;
}
// if the GL pass dies after the layers were split, flatten them so the plain blit still shows everything
function lxFlatten() { if (!LX.on) return; LX.on = false; gLow.setTransform(1, 0, 0, 1, 0, 0); gLow.drawImage(lowFx, 0, 0); gLow.drawImage(lowTop, 0, 0); }

Object.assign(window.__game, { lx: { LX, LX_TUNE, LX_AMB, setDark(t) { darkT = t; }, addLight, get light() { return lights; } } });   // headless tests

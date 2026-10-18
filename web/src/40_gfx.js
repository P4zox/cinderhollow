// ------------------------------------------------------------------ Graphics: texture filter + post-process shaders
// The world renders to the 384x216 `low` canvas. presentWorld() (called from render() in 09_main.js) either blits it
// straight onto the view, or uploads it to a WebGL canvas and runs one fragment shader over it (texture filter, bloom,
// colour grade, scanlines/CRT, chromatic aberration, vignette, grain) before the HUD and menus draw on top, crisp.
// If WebGL is missing or the context is lost, the plain blit takes over and the shader rows say so.
const GFX_DEFAULTS = { bright: 1, shaders: 0, tex: 0, bloom: 1, vig: 1, scan: 0, grain: 0, ca: 0, grade: 0, rays: 1, mood: 1 };
for (const [k, v] of Object.entries(GFX_DEFAULTS)) if (SETTINGS[k] === undefined) SETTINGS[k] = v;
// (pre-v15) shaders were opt-in: switch them off once for saves from when they were on by default, then respect the player's choice
if ((SETTINGS.gfxv || 0) < 2) { SETTINGS.shaders = 0; SETTINGS.gfxv = 2; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
// v15 (runs after the old opt-in switch, so it wins on fresh profiles too): the new pipeline (soft shadows, light shafts, rim light, region mood) costs less than the old one, so shaders are
// on by default on desktop -- and switched on once for existing players too (they can turn them off in Graphics)
if (!SETTINGS.gfxV15) { SETTINGS.gfxV15 = 1; if (!(typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches)) SETTINGS.shaders = 1; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
const GFX_KEYS = ['tex', 'bloom', 'vig', 'scan', 'grain', 'ca', 'grade'];
const GFX_PRESETS = [
  ['Cinematic', { tex: 0, bloom: 1, vig: 1, scan: 0, grain: 0, ca: 0, grade: 0 }],
  ['Ember glow', { tex: 1, bloom: 2, vig: 1, scan: 0, grain: 0, ca: 0, grade: 1 }],
  ['Moonlit', { tex: 0, bloom: 1, vig: 1, scan: 0, grain: 1, ca: 0, grade: 2 }],
  ['Noir', { tex: 0, bloom: 1, vig: 1, scan: 0, grain: 1, ca: 0, grade: 3 }],
  ['Vivid', { tex: 0, bloom: 2, vig: 0, scan: 0, grain: 0, ca: 0, grade: 4 }],
  ['Retro CRT', { tex: 0, bloom: 1, vig: 1, scan: 2, grain: 1, ca: 1, grade: 0 }],
  ['Clean', { tex: 0, bloom: 0, vig: 0, scan: 0, grain: 0, ca: 0, grade: 0 }],
];
const GFX = { ok: null, cv: null, gl: null, prog: null, tex: null, u: {}, lost: false };

const GFX_VS = `attribute vec2 a; varying vec2 v; void main() { v = a * 0.5 + 0.5; gl_Position = vec4(a, 0.0, 1.0); }`;
// v17 shading: THE tone curve, shared by the lighting pass (41_light.js) and the post pass. It works on the brightest channel and
// scales the other two with it, so a hue never drifts to cream: linear up to the knee TMK, a Reinhard shoulder from there
// to 1.0 (never reached, so lit stone can't clip), and a small toe TMT that deepens the last few % of black. tmapInv is its
// exact inverse: the post pass lifts the display image back to scene light, adds bloom and shafts there, and maps once more,
// so glow piles up into the shoulder instead of clipping, and an image with nothing added comes back unchanged.
const GFX_TM = `
uniform float TMK, TMT;
float tmC(float x) {
  float y = x > TMK ? TMK + (x - TMK) / (1.0 + (x - TMK) / (1.0 - TMK)) : x;
  return y * y / (y + TMT) * (1.0 + TMT);
}
float tmCi(float z) {
  z = clamp(z, 0.0, 0.996) / (1.0 + TMT);
  float y = 0.5 * (z + sqrt(z * z + 4.0 * z * TMT));
  return y > TMK ? TMK + (y - TMK) / max(1.0 - (y - TMK) / (1.0 - TMK), 0.004) : y;
}
vec3 tmap(vec3 c) { float m = max(c.r, max(c.g, c.b)); return m > 0.00001 ? c * (tmC(m) / m) : vec3(0.0); }
vec3 tmapInv(vec3 c) { float m = max(c.r, max(c.g, c.b)); return m > 0.00001 ? c * (tmCi(m) / m) : vec3(0.0); }
`;
// knee + toe of the curve; bloom/shafts: the most they can add to a pixel (soft cap, scene light), and their strengths per setting
const GFX_TONE = { k: 0.6, t: 0.004, cap: 0.45, bloom: [0, 0.3, 0.45], rays: [0, 0.7, 1.05], expo: [0.86, 1, 1.12] };
const GFX_FS = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
varying vec2 v;
uniform sampler2D T, B1, B2, GR;
uniform vec2 S, O;
uniform float tm, bloom, vig, scan, grain, ca, filt, grade, expo, chain, rays, mood, gSat, gCon, bloomK, raysK, addCap;
uniform vec3 gS, gH;
` + GFX_TM + `
float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
vec3 tap(vec2 uv) {
  vec2 t = uv * S;
  if (filt < 0.5) t = floor(t) + 0.5;                               // crisp: nearest texel
  else if (filt < 1.5) {                                            // smooth pixels: sharp-bilinear (pixel art, soft seams)
    float k = max(1.0, floor(O.x / S.x + 0.01)), r = 0.5 - 0.5 / k;
    vec2 fl = floor(t), c = fract(t) - 0.5;
    t = fl + (c - clamp(c, -r, r)) * k + 0.5;
  }
  return texture2D(T, t / S).rgb;
}
void main() {
  vec2 uv = v;
  if (scan > 1.5) {                                                 // CRT: barrel curve
    vec2 c = uv * 2.0 - 1.0; c *= 1.0 + vec2(0.028, 0.045) * dot(c, c); uv = c * 0.5 + 0.5;
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
  }
  vec3 col;
  if (ca > 0.5) { vec2 o = (uv - 0.5) * vec2(1.6, 1.2) / S; col = vec3(tap(uv + o).r, tap(uv).g, tap(uv - o).b); }
  else col = tap(uv);
  float bl = dot(col, vec3(0.299, 0.587, 0.114));
  vec3 add = vec3(0.0);                                             // v17: everything the post pass adds, in scene light
  if (bloom > 0.5 && chain > 0.5) {                                 // v15: soft-knee bright pass, blurred at 1/2 and 1/4 res (gfxChain)
    add += (texture2D(B1, uv).rgb * 0.6 + texture2D(B2, uv).rgb * 0.9) * bloomK * (1.0 - 0.6 * bl);
  } else if (bloom > 0.5) {                                         // fallback: bright-pass ring taps around the texel
    vec3 b = vec3(0.0);
    for (float i = 0.0; i < 12.0; i += 1.0) {
      float a = i * 0.5236 + 0.26, r = mod(i, 2.0) < 0.5 ? 1.7 : 3.8;
      vec3 s = texture2D(T, uv + vec2(cos(a), sin(a)) * r / S).rgb;
      b += max(s - 0.6, 0.0) * (r < 2.0 ? 1.0 : 0.6);
    }
    add += b * bloomK * 0.45 * (1.0 - 0.6 * bl);                    // glow lifts the dark around a light, not what's already bright
  }
  if (rays > 8.5) { gl_FragColor = vec4((rays > 9.5 ? texture2D(B1, uv).rgb : texture2D(GR, uv).rgb) * 2.0, 1.0); return; }   // test views (SETTINGS.rays 9 / 10)
  if (rays > 0.5) add += texture2D(GR, uv).rgb * raysK;             // light shafts (gfxChain)
  float am = max(add.r, max(add.g, add.b));
  add *= 1.0 / (1.0 + am / addCap);                                 // soft cap: glow and shafts together never add more than addCap
  col = tmap(tmapInv(col) * expo + add);                            // the one tone map: the scene comes back as it was, the glow rolls off
  if (mood > 0.0) {                                                 // v15 biome mood: saturation, contrast about a low pivot, split-tone
    float ml = dot(col, vec3(0.299, 0.587, 0.114));
    vec3 m = mix(vec3(ml), col, gSat);
    m = max((m - 0.3) * gCon + 0.3, 0.0);
    m *= mix(gS, gH, smoothstep(0.04, 0.6, ml));
    col = mix(col, m, mood);
  }
  float l = dot(col, vec3(0.299, 0.587, 0.114));
  if (grade > 0.5 && grade < 1.5) { col *= vec3(1.07, 0.98, 0.86); col += vec3(0.025, 0.012, 0.0) * (1.0 - l); }          // ember
  else if (grade > 1.5 && grade < 2.5) { col = mix(vec3(l), col, 0.8) * vec3(0.88, 0.98, 1.12); col += vec3(0.0, 0.006, 0.02); }  // moonlit
  else if (grade > 2.5 && grade < 3.5) { col = vec3(l) * vec3(1.03, 1.0, 0.94); col = (col - 0.5) * 1.22 + 0.5; }       // noir
  else if (grade > 3.5) { col = mix(vec3(l), col, 1.32); col = (col - 0.5) * 1.07 + 0.5; }                                 // vivid
  // (no second shoulder here: lit stone leaves the tone map at <= ~0.93, so only painted emitters can reach 1 after the mood, and they clip as painted)
  if (scan > 0.5) {                                                 // one scanline per game pixel row
    float y = fract(uv.y * S.y), sl = 0.5 - 0.5 * cos(6.2832 * y);
    col *= mix(1.0, 0.5 + 0.5 * sl, scan > 1.5 ? 0.55 : 0.32);
    if (scan > 1.5) { float m = mod(gl_FragCoord.x, 3.0); col *= (m < 1.0 ? vec3(1.08, 0.9, 0.9) : m < 2.0 ? vec3(0.9, 1.08, 0.9) : vec3(0.9, 0.9, 1.08)) * 1.12; }
  }
  if (vig > 0.5) { vec2 c = (uv - 0.5) * vec2(1.0, 0.85); col *= 1.0 - 0.32 * smoothstep(0.3, 0.75, length(c)); }
  if (grain > 0.5) col += (hash(gl_FragCoord.xy + fract(tm * 7.13) * 311.0) - 0.5) * 0.07;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

// ---- v15 bloom + light-shaft chain: small passes at 1/2 and 1/4 of game resolution (192x108, 96x54), so the full-res
// post shader reads 3 bilinear taps instead of 12 ring taps. BP: soft-knee bright pass (th < 0: plain 4x4 box downsample).
// BLR: 9-tap gaussian in 5 bilinear fetches. RAY: radial blur of the bright pass toward up to 3 sources (the sun / moon of an
// outdoor biome, the strongest lights in view): light bleeds out of lamps and through gaps, cut by whatever stands in front.
const GFX_HEAD = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
varying vec2 v;
uniform sampler2D T;
uniform vec2 S;
`;
const GFX_BP = GFX_HEAD + `uniform float th, knee;
void main() {
  vec2 o = 1.0 / S;
  vec3 c = 0.25 * (texture2D(T, v + vec2(-o.x, -o.y)).rgb + texture2D(T, v + vec2(o.x, -o.y)).rgb + texture2D(T, v + vec2(-o.x, o.y)).rgb + texture2D(T, v + o).rgb);
  if (th >= 0.0) {
    float br = max(c.r, max(c.g, c.b)), sk = clamp(br - th + knee, 0.0, 2.0 * knee);
    c *= max(sk * sk / (4.0 * knee + 0.0001), br - th) / max(br, 0.0001);
  }
  gl_FragColor = vec4(c, 1.0);
}`;
const GFX_BLR = GFX_HEAD + `uniform vec2 D;
void main() {
  vec2 a = D * 1.3846153846 / S, b = D * 3.2307692308 / S;
  vec3 c = texture2D(T, v).rgb * 0.2270270270 + (texture2D(T, v + a).rgb + texture2D(T, v - a).rgb) * 0.3162162162
         + (texture2D(T, v + b).rgb + texture2D(T, v - b).rgb) * 0.0702702703;
  gl_FragColor = vec4(c, 1.0);
}`;
const GFX_RAY = GFX_HEAD + `uniform vec4 SP[3];
uniform vec4 SC[3];   // rgb tint, a = brightness threshold of what feeds this source's shafts
uniform float GAIN;
vec3 bright(vec2 p, float th) { vec3 c = texture2D(T, p).rgb; float m = max(c.r, max(c.g, c.b)); return c * (max(m - th, 0.0) / max(m, 0.001)); }
void main() {
  vec3 acc = vec3(0.0);
  float j = fract(52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715))));   // interleaved-gradient jitter
  for (int k = 0; k < 3; k++) {
    vec4 sp = SP[k];
    if (sp.z <= 0.0) continue;
    vec2 dl = (v - sp.xy) * vec2(S.x / S.y, 1.0);
    float dist = length(dl);
    vec2 st = (v - sp.xy) * sp.w / 22.0;
    vec2 p = v - st * j;
    vec3 s = vec3(0.0); float w = 1.0, ws = 0.0;
    for (int i = 0; i < 22; i++) { p -= st; s += bright(p, SC[k].a) * w; ws += w; w *= 0.95; }
    acc += s / ws * SC[k].rgb * sp.z * GAIN * (1.0 - smoothstep(0.2, 1.4, dist));
  }
  gl_FragColor = vec4(acc, 1.0);
}`;
function gfxProg(gl, fs) {
  const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
  const prog = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, GFX_VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, fs));
  gl.bindAttribLocation(prog, Math.max(0, gl.getAttribLocation(GFX.prog, 'a')), 'a'); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  const u = {}, n = gl.getProgramParameter(prog, gl.ACTIVE_UNIFORMS);
  for (let i = 0; i < n; i++) { const nm = gl.getActiveUniform(prog, i).name.replace(/\[0\]$/, ''); u[nm] = gl.getUniformLocation(prog, nm); }
  return { prog, u };
}
function gfxChainInit() {
  const gl = GFX.gl; GFX.chain = false;
  try {
    const rt = (w, h) => {
      const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, p, v);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
      const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE; gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      if (!ok) throw new Error('framebuffer incomplete');
      return { t, f, w, h };
    };
    const w2 = W >> 1, h2 = H >> 1, w4 = W >> 2, h4 = H >> 2;
    Object.assign(GFX, { pBP: gfxProg(gl, GFX_BP), pBL: gfxProg(gl, GFX_BLR), pRY: gfxProg(gl, GFX_RAY),
      rA: rt(w2, h2), rB: rt(w2, h2), rC: rt(w4, h4), rD: rt(w4, h4), rG: rt(w2, h2), rM: rt(W >> 3, H >> 3), chain: true });   // rM: the exposure meter (phase 3)
  } catch (e) { console.warn('bloom chain unavailable, using the single-pass bloom:', e && e.message); GFX.chain = false; }
  gl.useProgram(GFX.prog); gl.activeTexture(gl.TEXTURE0);
  return GFX.chain;
}
function gfxPass(P, src, dst, sw, sh, set) {   // one full-screen draw of program P reading src (sw x sh) into render target dst
  const gl = GFX.gl;
  gl.useProgram(P.prog); gl.bindFramebuffer(gl.FRAMEBUFFER, dst.f); gl.viewport(0, 0, dst.w, dst.h);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, src); gl.uniform1i(P.u.T, 0); gl.uniform2f(P.u.S, sw, sh);
  if (set) set(P.u);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
// light-shaft sources for this frame: [x, y (uv, y up), strength, reach] + colour. Outdoor biomes get a sun / moon above the
// view; the strongest big lights on screen bleed too. Slots fade in and out so a source never pops.
const GFX_SUN = {   // biome: [uv x, uv y (1 = top edge), strength, colour, indoors too, threshold, far-layer sun {x, y, w} (px in bg_<b>_far)]
  crown: [0.68, 1.35, 0.55, '255,246,226'], dunes: [0.6, 1.3, 0.6, '255,226,170', 0, 0.42, { x: 294, y: 31, w: 512 }],
  ramparts: [0.3, 1.25, 0.5, '255,170,120', 0, 0.42, { x: 243, y: 111, w: 512 }],
  hoarfrost: [0.55, 1.3, 0.4, '210,232,255'], spire: [0.45, 1.3, 0.35, '200,214,255'], starfall: [0.62, 1.25, 0.32, '190,200,255'],
  lastfield: [0.7, 1.3, 0.5, '255,220,170'], neohallow: [0.5, 1.25, 0.25, '230,170,255'], crimson: [0.4, 1.25, 0.3, '255,150,150'],
  vn_dusk1: [0.6, 1.3, 0.4, '255,214,190'], vn_dusk2: [0.6, 1.3, 0.3, '235,200,220'], sov_void: [0.5, 1.3, 0.3, '220,200,255'],
  cathedral: [0.38, 1.4, 0.6, '205,218,255', 1, 0.2],   // 5th = also indoors (moonlight through the tall windows), 6th = threshold
};
const GFX_RAYSRC = [];   // { key, x, y, k, c: [r,g,b], tk (target), seen }
function gfxRaySources(dt) {
  const want = [];
  if (room && !(typeof darkT !== 'undefined' && darkT > 0)) {
    const bio = room.def.biome, sun = GFX_SUN[bio];
    if (sun && (!room.def.indoor || sun[4])) {
      let x = sun[0], y = sun[1];
      const F = sun[6];
      if (F) {   // the sun painted in the far parallax layer: follow it (drawParallax: x factor 0.08, y factor 0.02)
        const ox = -((cam.x * 0.08) % F.w + F.w) % F.w, oy = Math.round(clamp(-cam.y * 0.02, -20, 20));
        let sx = ox + F.x; while (sx < W / 2 - F.w / 2) sx += F.w;
        x = sx / W; y = 1 - (oy + F.y) / H;
      }
      // phase 4: indoors, a moon above the view (the cathedral's) shines through holes and windows as real shafts (41c_atmos.js); a sun
      // painted on screen (vistas, the far layer's) and the sun / moon over an open sky keep this screen-space bleed past the silhouettes
      if (!(LX4.sh && room.def.indoor && y > 1)) want.push({ key: 'sun', x, y, k: sun[2], c: lxCol(sun[3]), th: sun[5] ?? 0.42 });
    }
    if (LX.on) for (const L of LX.cand) {
      if (want.length >= 3) break;
      if (L.o === LX_PLAYER || !(L.r >= 56) || !(L.k >= 0.45) || L._sl) continue;   // (phase 4: a shaft lamp lights the air itself, 41_light.js)
      const sx = (L.x - LX.cx) / W, sy = 1 - (L.y - LX.cy) / H;
      if (sx < 0.02 || sx > 0.98 || sy < 0.02 || sy > 0.98) continue;
      want.push({ key: Math.round(L.x / 24) + ',' + Math.round(L.y / 24), x: sx, y: sy, k: 0.42 * Math.min(1.2, L.k) * Math.min(1, L.r / 120), c: lxCol(L.color), th: 0.5 });
    }
  }
  for (const s of GFX_RAYSRC) s.seen = false;
  for (const w of want) {
    let s = GFX_RAYSRC.find(q => q.key === w.key);
    if (!s) { s = { key: w.key, k: 0 }; GFX_RAYSRC.push(s); }
    Object.assign(s, { x: w.x, y: w.y, c: w.c, th: w.th, tk: w.k, seen: true });
  }
  const f = 1 - Math.exp(-dt * 6);
  for (const s of GFX_RAYSRC) s.k += ((s.seen ? s.tk : 0) - s.k) * f;
  for (let i = GFX_RAYSRC.length - 1; i >= 0; i--) if (!GFX_RAYSRC[i].seen && GFX_RAYSRC[i].k < 0.01) GFX_RAYSRC.splice(i, 1);
  return GFX_RAYSRC.slice().sort((a, b) => b.k - a.k).slice(0, 3);
}
// v17 phase 3: eye adaptation. Not an auto-exposure: every region keeps its calibrated look (LX_BOOST, LX_EXPO). When the room changes,
// the new room's first lit frame is metered (mean luminance, 48×27 box-filtered, one readback) against the last room's, and the
// exposure starts from where the eye was, A0 = (new / old)^s (clamped: a dark hall looks darker for a moment, a bright one glares a
// little), then settles to exactly 1 with time constant tau (≈ 0.9 s to 95 %). Small differences (|ln| < dead) do nothing.
const GFX_EYE = { s: 0.5, lo: 0.72, hi: 1.35, tau: 0.3, dead: 0.1, every: 2 };
function gfxMeter(src) {
  const gl = GFX.gl, M = GFX.rM;
  gfxPass(GFX.pBP, src, M, W, H, q => { gl.uniform1f(q.th, -1); gl.uniform1f(q.knee, 0); });
  const buf = GFX.mBuf || (GFX.mBuf = new Uint8Array(M.w * M.h * 4));
  gl.readPixels(0, 0, M.w, M.h, gl.RGBA, gl.UNSIGNED_BYTE, buf);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  let s = 0; for (let i = 0; i < buf.length; i += 4) s += 0.299 * buf[i] + 0.587 * buf[i + 1] + 0.114 * buf[i + 2];
  return Math.max(2, s / (buf.length / 4));
}
function gfxEye(lit, dt) {
  const E = GFX.eye || (GFX.eye = { room: null, key: 0, A: 1, A0: 1, t: 0, m: 0, wait: 0 });
  if (!lit || !SETTINGS.eyead || !GFX.chain || !room) { E.room = room; E.key = 0; E.A = E.A0 = 1; return 1; }
  const T = GFX_EYE;
  if (room !== E.room) { E.room = room; E.wait = 3; E.t = 0; }   // the new room's first frames still lack its lamps (and sit under the fade): meter the 3rd
  if (E.wait > 0) {
    if (--E.wait > 0) return E.A;
    const k = gfxMeter(lit);
    if (E.key > 0) { const r = Math.log(k / E.key); E.A0 = Math.abs(r) < T.dead ? 1 : clamp(Math.exp(r * T.s), T.lo, T.hi); } else E.A0 = 1;
    E.key = k; E.t = 0; E.m = 0;
  } else {
    E.t += dt; E.m += dt;
    if (E.m > T.every && E.t > 1.5) { E.m = 0; E.key = 0.5 * E.key + 0.5 * gfxMeter(lit); }   // follow the room as the view moves (where the eye is when it leaves)
  }
  E.A = E.A0 === 1 ? 1 : Math.pow(E.A0, Math.exp(-E.t / T.tau));
  return E.A;
}
// biome mood: [shadow tint, highlight tint, saturation, contrast]; blended over ~0.5 s when the biome changes
const GFX_MOOD_DEF = [[1, 1, 1], [1, 1, 1], 1, 1];
const GFX_MOOD = {
  ramparts: [[0.96, 0.94, 1.08], [1.07, 1.0, 0.92], 1.0, 1.06], catacombs: [[0.9, 0.98, 1.1], [1.06, 1.0, 0.9], 0.95, 1.08],
  cathedral: [[0.95, 0.94, 1.08], [1.08, 1.02, 0.9], 1.0, 1.05], mire: [[0.92, 1.04, 0.98], [1.02, 1.04, 0.9], 0.94, 1.05],
  crown: [[0.95, 0.98, 1.06], [1.04, 1.02, 0.98], 0.95, 1.03], archives: [[0.98, 0.94, 1.02], [1.08, 1.0, 0.86], 0.96, 1.06],
  deep: [[1.04, 0.92, 0.94], [1.08, 0.98, 0.88], 1.06, 1.08], spire: [[0.92, 0.96, 1.1], [1.0, 1.02, 1.04], 0.94, 1.06],
  hermit: [[0.98, 0.95, 1.0], [1.06, 1.01, 0.92], 0.96, 1.04], ember: [[1.04, 0.92, 0.94], [1.08, 0.98, 0.88], 1.05, 1.07],
  hoarfrost: [[0.9, 0.98, 1.12], [1.0, 1.02, 1.05], 0.9, 1.05], necropolis: [[0.9, 0.94, 1.12], [1.02, 1.0, 1.0], 0.9, 1.08],
  nv_void: [[0.92, 0.9, 1.12], [1.02, 0.98, 1.04], 0.92, 1.08], crimson: [[1.04, 0.9, 0.96], [1.06, 0.98, 0.94], 1.02, 1.08],
  barrows: [[0.88, 1.02, 1.04], [1.0, 1.04, 0.98], 0.92, 1.06], thornveil: [[0.92, 1.03, 0.96], [1.05, 1.04, 0.9], 0.96, 1.06],
  starfall: [[0.9, 0.94, 1.14], [1.02, 1.0, 1.04], 0.94, 1.06], dunes: [[1.0, 0.95, 0.96], [1.06, 1.01, 0.9], 1.02, 1.04],
  neohallow: [[0.96, 0.9, 1.12], [1.02, 1.0, 1.06], 1.06, 1.06], neohallow_cyber: [[0.92, 0.96, 1.1], [1.02, 1.02, 1.04], 1.05, 1.06],
};
function gfxMood(dt) {
  const T = (room && GFX_MOOD[room.def.biome]) || GFX_MOOD_DEF, M = GFX.mood || (GFX.mood = JSON.parse(JSON.stringify(T)));
  const f = 1 - Math.exp(-dt * 4);
  for (let i = 0; i < 2; i++) for (let c = 0; c < 3; c++) M[i][c] += (T[i][c] - M[i][c]) * f;
  M[2] += (T[2] - M[2]) * f; M[3] += (T[3] - M[3]) * f;
  return M;
}

function gfxInit() {
  GFX.ok = false;
  try {
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const gl = cv.getContext('webgl', { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false, preserveDrawingBuffer: false, powerPreference: 'high-performance' });
    if (!gl) return false;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const prog = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, GFX_VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, GFX_FS)); gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    gl.useProgram(prog);
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'a'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
    for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, p, v);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    for (const n of ['T', 'B1', 'B2', 'GR', 'S', 'O', 'tm', 'bloom', 'vig', 'scan', 'grain', 'ca', 'filt', 'grade', 'expo', 'chain', 'rays', 'mood', 'gSat', 'gCon', 'gS', 'gH', 'bloomK', 'raysK', 'addCap', 'TMK', 'TMT']) GFX.u[n] = gl.getUniformLocation(prog, n);
    cv.addEventListener('webglcontextlost', e => { e.preventDefault(); GFX.ok = false; GFX.lost = true; });
    Object.assign(GFX, { cv, gl, prog, tex, ok: true });
    gfxChainInit();
  } catch (e) { console.warn('shaders unavailable:', e && e.message); GFX.ok = false; }
  return GFX.ok;
}
function gfxReady() { return GFX.ok === null ? gfxInit() : GFX.ok; }
function gfxRender(w, h) {
  const { gl, cv, u } = GFX;
  const k = Math.min(1, 2560 / w), ow = Math.max(W, Math.round(w * k)), oh = Math.max(H, Math.round(h * k));
  if (cv.width !== ow || cv.height !== oh) { cv.width = ow; cv.height = oh; }
  const lit = LX.on ? lxPass(gl) : null;   // Dynamic lighting (41_light.js): the lit composite at 384x216, else the raw canvas
  gl.activeTexture(gl.TEXTURE0);
  if (!lit) { gl.bindTexture(gl.TEXTURE_2D, GFX.tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, low); }
  const src = lit || GFX.tex, dt = clamp(time - (GFX.lastT ?? time), 0, 0.1); GFX.lastT = time;   // game time: fades hold while paused
  const eye = gfxEye(lit, dt);   // v17 phase 3: eye adaptation after a room change (1 when settled, and always 1 unlit)
  const bl = SETTINGS.bloom > 0, rs = SETTINGS.rays > 0 && GFX.chain ? gfxRaySources(dt) : [], ry = rs.some(q => q.k > 0.01);
  if (GFX.chain && (bl || ry)) {
    const { pBP, pBL, rA, rB, rC, rD, rG } = GFX;
    gfxPass(pBP, src, rA, W, H, q => { gl.uniform1f(q.th, 0.6); gl.uniform1f(q.knee, 0.2); });
    gfxPass(pBL, rA.t, rB, rA.w, rA.h, q => gl.uniform2f(q.D, 1, 0)); gfxPass(pBL, rB.t, rA, rA.w, rA.h, q => gl.uniform2f(q.D, 0, 1));
    if (bl) {
      gfxPass(pBP, rA.t, rC, rA.w, rA.h, q => { gl.uniform1f(q.th, -1); gl.uniform1f(q.knee, 0); });
      gfxPass(pBL, rC.t, rD, rC.w, rC.h, q => gl.uniform2f(q.D, 1, 0)); gfxPass(pBL, rD.t, rC, rC.w, rC.h, q => gl.uniform2f(q.D, 0, 1));
    }
    if (ry) {
      const SP = new Float32Array(12), SC = new Float32Array(12);
      rs.forEach((q, i) => { SP.set([q.x, q.y, q.k, q.key === 'sun' ? 0.85 : 0.6], i * 4); SC.set([...q.c, q.th], i * 4); });
      gfxPass(GFX.pRY, src, rG, W, H, q => { gl.uniform4fv(q.SP, SP); gl.uniform4fv(q.SC, SC); gl.uniform1f(q.GAIN, 2.6); });
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }
  gl.useProgram(GFX.prog); gl.viewport(0, 0, ow, oh);
  const ch = GFX.chain && bl ? 1 : 0;
  gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, GFX.chain ? GFX.rA.t : src);
  gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, GFX.chain ? GFX.rC.t : src);
  gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, GFX.chain ? GFX.rG.t : src);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, src);
  gl.uniform1i(u.T, 0); gl.uniform1i(u.B1, 1); gl.uniform1i(u.B2, 2); gl.uniform1i(u.GR, 3);
  const M = gfxMood(dt);
  gl.uniform1f(u.chain, ch); gl.uniform1f(u.rays, ry ? SETTINGS.rays : 0); gl.uniform1f(u.mood, SETTINGS.mood && room ? 1 : 0);
  gl.uniform3fv(u.gS, M[0]); gl.uniform3fv(u.gH, M[1]); gl.uniform1f(u.gSat, M[2]); gl.uniform1f(u.gCon, M[3]);
  gl.uniform2f(u.S, W, H); gl.uniform2f(u.O, ow, oh); gl.uniform1f(u.tm, time % 1000);
  const TN = GFX_TONE;   // Brightness: the lighting pass exposes the scene itself (41_light.js), so the post pass only exposes unlit frames
  gl.uniform1f(u.expo, lit ? eye : TN.expo[SETTINGS.bright ?? 1]); gl.uniform1f(u.TMK, TN.k); gl.uniform1f(u.TMT, TN.t); gl.uniform1f(u.addCap, TN.cap);
  gl.uniform1f(u.bloomK, TN.bloom[SETTINGS.bloom] || 0); gl.uniform1f(u.raysK, TN.rays[Math.min(2, SETTINGS.rays | 0)] || 0); gl.uniform1f(u.bloom, SETTINGS.bloom); gl.uniform1f(u.vig, SETTINGS.vig); gl.uniform1f(u.scan, SETTINGS.scan); gl.uniform1f(u.grain, SETTINGS.grain);
  gl.uniform1f(u.ca, SETTINGS.ca); gl.uniform1f(u.filt, SETTINGS.tex); gl.uniform1f(u.grade, SETTINGS.grade);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
// test probe (GFX.sync): read one pixel back so the GL passes and the canvas composite really finish inside the timing
// (gl.finish() returns early in Chrome, so the old probe mostly timed command submission)
function gfxSync() { try { vctx.getImageData(ox | 0, oy | 0, 1, 1); } catch (e) { GFX.gl.finish(); } }
function presentWorld() {
  const t0 = performance.now(); presentBody(); const dt = performance.now() - t0;
  GFX.pt = (GFX.pt || 0) + dt; GFX.pn = (GFX.pn || 0) + 1;   // frame-time probe for tools/shots/lx (reset both to measure)
}
function presentBody() {
  const w = W * scale, h = H * scale;
  if (SETTINGS.shaders && gfxReady()) {
    try { gfxRender(w, h); vctx.imageSmoothingEnabled = true; vctx.drawImage(GFX.cv, ox, oy, w, h); if (GFX.sync) gfxSync(); return; }
    catch (e) { console.warn('shader pass failed, falling back:', e && e.message); GFX.ok = false; }
  }
  lxFlatten();
  vctx.imageSmoothingEnabled = SETTINGS.tex === 2; if (vctx.imageSmoothingEnabled) vctx.imageSmoothingQuality = 'high';
  vctx.drawImage(low, ox, oy, w, h);
  vctx.imageSmoothingEnabled = false;
  if (GFX.sync) gfxSync();
}

// ---- Settings › Graphics & shaders
const GFX_ROWS = [
  { k: 'shaders', label: 'Shaders', opts: ['Off', 'On'], desc: 'Post-processing on the game world (the HUD stays sharp). Turn off on slow devices.' },
  { k: 'bright', label: 'Brightness', opts: ['Dark', 'Normal', 'Bright'], desc: 'How much of the dark you can see into. Bright helps on dim screens and in daylight.' },
  { k: 'light', label: 'Lighting', opts: ['Classic', 'Dynamic', 'Hard shadows', 'Soft shadows'], shader: true, desc: 'Dynamic: lanterns, fire and spells light the stone in pixel-art bands. Shadows: walls block the light; soft shadows blur wider the farther they fall.' },
  { k: 'lband', label: 'Light bands', opts: ['Stepped', 'Smooth', 'Dithered'], shader: true, desc: 'Stepped: light falls off in a few clean pixel-art steps. Smooth: a soft gradient. Dithered: steps with a checkered retro edge.' },
  { k: 'surf', label: 'Surface lighting', opts: ['Off', 'On'], shader: true, desc: 'Needs Dynamic lighting. Light wraps around the knight, foes and stone: the side facing a lamp catches it, the far side falls into shade.' },
  { k: 'rim', label: 'Rim light', opts: ['Off', 'On'], shader: true, desc: 'Needs Surface lighting. The edge of a silhouette that faces a lamp catches a thin bright rim.' },
  { k: 'csh', label: 'Character shadows', opts: ['Off', 'Contact', 'On'], shader: true, desc: 'Needs Dynamic lighting. Contact: a soft shadow pools under feet. On: the knight, foes and bosses also throw shadows from nearby lamps (needs shadows).' },
  { k: 'mat', label: 'Materials', opts: ['Off', 'On'], shader: true, desc: 'Needs Surface lighting. Armour, blades and iron catch small glints from lamps; wet stone and ice a soft sheen.' },
  { k: 'eyead', label: 'Eye adaptation', opts: ['Off', 'On'], shader: true, desc: 'Needs Dynamic lighting. Stepping from a bright room into a dark one, your eyes take a moment to adjust (and back).' },
  { k: 'refl', label: 'Reflections', opts: ['Off', 'On'], shader: true, desc: 'Needs Dynamic lighting. Water, ice and wet stone mirror the knight, foes, lamps and spells above them.' },
  { k: 'lpart', label: 'Lit particles', opts: ['Off', 'On'], shader: true, desc: 'Needs Dynamic lighting. Dust, ash, spores, snow and rain catch the light of nearby lamps and fall dark away from them. Embers and sparks still glow.' },
  { k: 'dhaze', label: 'Depth haze', opts: ['Off', 'On'], shader: true, desc: 'Needs Dynamic lighting. Far backdrops fade into the air of each region, the near ones less, so distance reads.' },
  { k: 'preset', label: 'Look', desc: 'A ready-made mix of the options below. Change any of them to make your own.' },
  { k: 'tex', label: 'Texture filter', opts: ['Crisp pixels', 'Smooth pixels', 'Soft'], desc: 'Crisp: hard pixel edges. Smooth pixels: clean anti-aliased pixel art (needs shaders). Soft: blurred.' },
  { k: 'bloom', label: 'Bloom', opts: ['Off', 'Low', 'High'], shader: true, desc: 'Embers, fire, spells and light sources glow and bleed into the dark.' },
  { k: 'rays', label: 'Light shafts', opts: ['Off', 'Soft', 'Strong'], shader: true, desc: 'Sun, moon and windows throw shafts through openings, cut by walls and passing bodies, with dust drifting in them. Strong lamps bleed light.' },
  { k: 'grade', label: 'Colour grade', opts: ['Natural', 'Ember', 'Moonlit', 'Noir', 'Vivid'], shader: true, desc: 'Tints the whole world: warm ember, cold moonlight, black-and-white noir, or richer colour.' },
  { k: 'mood', label: 'Region mood', opts: ['Off', 'On'], shader: true, desc: 'Each region keeps its own colour: cold catacomb shadows, a molten Deep, sun-bleached dunes. Under the colour grade.' },
  { k: 'vig', label: 'Lens vignette', opts: ['Off', 'On'], shader: true, desc: 'Darkens the corners a little more, like an old lens.' },
  { k: 'scan', label: 'Scanlines', opts: ['Off', 'Soft', 'CRT'], shader: true, desc: 'Soft: faint lines between pixel rows. CRT: a curved old monitor with a phosphor mask.' },
  { k: 'grain', label: 'Film grain', opts: ['Off', 'On'], shader: true, desc: 'A fine moving grain over the picture.' },
  { k: 'ca', label: 'Chromatic aberration', opts: ['Off', 'On'], shader: true, desc: 'Red and blue split slightly toward the edges of the screen.' },
  { k: 'shakeLvl', label: 'Screen shake', opts: ['Off', 'Low', 'Full'], desc: 'How hard the view jolts on heavy blows, finishers and landings. Same as Settings › Screen shake.' },
  { k: 'wtrail', label: 'Weapon trail', opts: ['Off', 'On'], desc: 'A faint streak of light follows the blade tip during a cut, in the weapon’s own colour.' },
];
function gfxPresetIdx() { return GFX_PRESETS.findIndex(([, v]) => GFX_KEYS.every(k => (SETTINGS[k] || 0) === v[k])); }
function gfxSubInput(M, a) {
  const S = M.sub, n = GFX_ROWS.length, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  if (['pause', 'back', 'heavy'].includes(a)) { M.sub = null; sfx.menu(); return; }
  if (a === 'up') { S.sel = (S.sel + n - 1) % n; sfx.menu(); return; }
  if (a === 'down') { S.sel = (S.sel + 1) % n; sfx.menu(); return; }
  if (!(a === 'left' || a === 'right' || conf)) return;
  const R = GFX_ROWS[S.sel], d = a === 'left' ? -1 : 1;
  if (R.k === 'preset') {
    const i = gfxPresetIdx(), ni = ((i < 0 ? (d > 0 ? -1 : 0) : i) + d + GFX_PRESETS.length) % GFX_PRESETS.length;
    Object.assign(SETTINGS, GFX_PRESETS[ni][1]); if (!SETTINGS.shaders) SETTINGS.shaders = 1;
  } else {
    if (R.k === 'shaders' && !SETTINGS.shaders && !gfxReady()) { sfx.deny(); toast('This browser can’t run the shaders (no WebGL)', 2.5); return; }
    SETTINGS[R.k] = ((SETTINGS[R.k] || 0) + d + R.opts.length) % R.opts.length;
    if (R.shader && !SETTINGS.shaders) SETTINGS.shaders = 1;
  }
  saveSettings(); sfx.menu();
}
function renderGfxSub(M) {
  const S = M.sub;
  uiBackdrop(0.12);
  vctx.fillStyle = 'rgba(6,4,10,0.86)'; vctx.fillRect(ox, oy, 214 * scale, H * scale);   // the right side stays clear: a live preview
  uiTitle('GRAPHICS', 17, 9);
  const px = 12, pw = 196, top = 24, VIS = Math.min(GFX_ROWS.length, 13), rh = 10.8, on = !!SETTINGS.shaders, bad = GFX.ok === false;
  const first = clamp(S.sel - 6, 0, GFX_ROWS.length - VIS);   // the list scrolls with the selection
  panel(px, top, pw, 10 + VIS * rh);
  if (first > 0) text('▲', px + pw / 2, top + 6, 5, '#b8ab90', 'center', { weight: 400, alpha: 0.8 });
  if (first + VIS < GFX_ROWS.length) text('▼', px + pw / 2, top + 13 + VIS * rh, 5, '#b8ab90', 'center', { weight: 400, alpha: 0.8 });
  GFX_ROWS.forEach((R, i) => {
    if (i < first || i >= first + VIS) return;
    const y = top + 15 + (i - first) * rh, sel = i === S.sel, dim = (R.shader && !on);
    uiHit(px + 4, y - 9, pw - 8, rh - 1, () => { S.sel = i; }, () => { S.sel = i; uiAct('right'); });
    uiHit(px + pw - 76, y - 9, 34, rh - 1, () => { S.sel = i; }, () => { S.sel = i; uiAct('left'); });
    if (sel) uiSel(px + 4, y - 9, pw - 8, rh - 1);
    text(R.label, px + 12, y, 6.2, sel ? '#f5e3b0' : dim ? '#7f745f' : '#d8cdb4', 'left', { weight: sel ? 600 : 400 });
    let val;
    if (R.k === 'preset') { const pi = gfxPresetIdx(); val = pi < 0 ? 'Custom' : GFX_PRESETS[pi][0]; }
    else if (R.k === 'shaders' && bad) val = 'Unavailable';
    else val = R.opts[SETTINGS[R.k] || 0];
    if (R.k === 'tex' && SETTINGS.tex === 1 && !on) val += ' (off)';
    text((sel ? '◂ ' : '') + val + (sel ? ' ▸' : ''), px + pw - 10, y, 6.2, dim ? '#6f6656' : (R.k === 'shaders' ? (on ? '#ffd070' : '#8a7f6a') : '#f1e6c8'), 'right', { weight: 600 });
  });
  const R = GFX_ROWS[S.sel];
  wrap(R.desc, pw - 16, 5.4).slice(0, 3).forEach((ln, i) => text(ln, px + 8, top + 23 + VIS * rh + i * 7.5, 5.4, '#b8ab90', 'left', { weight: 400 }));
  text('Preview →', 300, 30, 5.6, '#b8ab90', 'center', { weight: 400, alpha: 0.8 });
  uiFooter([['↑↓', 'select'], ['←→', 'change'], ['Esc', 'back']]);
}

Object.assign(window.__game, { pad: padPoll, PAD, GFX, GFX_PRESETS, GFX_TONE });   // headless tests

// ------------------------------------------------------------------ Graphics: texture filter + post-process shaders
// The world renders to the 384x216 `low` canvas. presentWorld() (called from render() in 09_main.js) either blits it
// straight onto the view, or uploads it to a WebGL canvas and runs one fragment shader over it (texture filter, bloom,
// colour grade, scanlines/CRT, chromatic aberration, vignette, grain) before the HUD and menus draw on top, crisp.
// If WebGL is missing or the context is lost, the plain blit takes over and the shader rows say so.
const GFX_DEFAULTS = { bright: 1, shaders: 0, tex: 0, bloom: 1, vig: 1, scan: 0, grain: 0, ca: 0, grade: 0 };
for (const [k, v] of Object.entries(GFX_DEFAULTS)) if (SETTINGS[k] === undefined) SETTINGS[k] = v;
// shaders are opt-in now: switch them off once for saves from when they were on by default, then respect the player's choice
if ((SETTINGS.gfxv || 0) < 2) { SETTINGS.shaders = 0; SETTINGS.gfxv = 2; try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} }
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
const GFX_FS = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
varying vec2 v;
uniform sampler2D T;
uniform vec2 S, O;
uniform float tm, bloom, vig, scan, grain, ca, filt, grade, expo;
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
  if (bloom > 0.5) {                                                // bright-pass ring taps around the texel
    vec3 b = vec3(0.0);
    for (float i = 0.0; i < 12.0; i += 1.0) {
      float a = i * 0.5236 + 0.26, r = mod(i, 2.0) < 0.5 ? 1.7 : 3.8;
      vec3 s = texture2D(T, uv + vec2(cos(a), sin(a)) * r / S).rgb;
      b += max(s - 0.6, 0.0) * (r < 2.0 ? 1.0 : 0.6);
    }
    float bl = dot(col, vec3(0.299, 0.587, 0.114));
    col += b * (bloom > 1.5 ? 0.24 : 0.13) * (1.0 - 0.7 * bl);   // glow lifts the dark around a light, not what's already bright
  }
  col *= expo;
  vec3 hi = max(col - 0.72, 0.0); col = min(col, 0.72) + hi / (1.0 + hi * 3.6);   // highlight shoulder: bright skies roll off instead of clipping to white
  float l = dot(col, vec3(0.299, 0.587, 0.114));
  if (grade > 0.5 && grade < 1.5) { col *= vec3(1.07, 0.98, 0.86); col += vec3(0.025, 0.012, 0.0) * (1.0 - l); }          // ember
  else if (grade > 1.5 && grade < 2.5) { col = mix(vec3(l), col, 0.8) * vec3(0.88, 0.98, 1.12); col += vec3(0.0, 0.006, 0.02); }  // moonlit
  else if (grade > 2.5 && grade < 3.5) { col = vec3(l) * vec3(1.03, 1.0, 0.94); col = (col - 0.5) * 1.22 + 0.5; }       // noir
  else if (grade > 3.5) { col = mix(vec3(l), col, 1.32); col = (col - 0.5) * 1.07 + 0.5; }                                 // vivid
  if (scan > 0.5) {                                                 // one scanline per game pixel row
    float y = fract(uv.y * S.y), sl = 0.5 - 0.5 * cos(6.2832 * y);
    col *= mix(1.0, 0.5 + 0.5 * sl, scan > 1.5 ? 0.55 : 0.32);
    if (scan > 1.5) { float m = mod(gl_FragCoord.x, 3.0); col *= (m < 1.0 ? vec3(1.08, 0.9, 0.9) : m < 2.0 ? vec3(0.9, 1.08, 0.9) : vec3(0.9, 0.9, 1.08)) * 1.12; }
  }
  if (vig > 0.5) { vec2 c = (uv - 0.5) * vec2(1.0, 0.85); col *= 1.0 - 0.42 * smoothstep(0.28, 0.72, length(c)); }
  if (grain > 0.5) col += (hash(gl_FragCoord.xy + fract(tm * 7.13) * 311.0) - 0.5) * 0.07;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

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
    for (const n of ['T', 'S', 'O', 'tm', 'bloom', 'vig', 'scan', 'grain', 'ca', 'filt', 'grade', 'expo']) GFX.u[n] = gl.getUniformLocation(prog, n);
    cv.addEventListener('webglcontextlost', e => { e.preventDefault(); GFX.ok = false; GFX.lost = true; });
    Object.assign(GFX, { cv, gl, prog, tex, ok: true });
  } catch (e) { console.warn('shaders unavailable:', e && e.message); GFX.ok = false; }
  return GFX.ok;
}
function gfxReady() { return GFX.ok === null ? gfxInit() : GFX.ok; }
function gfxRender(w, h) {
  const { gl, cv, u } = GFX;
  const k = Math.min(1, 2560 / w), ow = Math.max(W, Math.round(w * k)), oh = Math.max(H, Math.round(h * k));
  if (cv.width !== ow || cv.height !== oh) { cv.width = ow; cv.height = oh; }
  const lit = LX.on ? lxPass(gl) : null;   // Dynamic lighting (41_light.js): the lit composite at 384x216, else the raw canvas
  gl.useProgram(GFX.prog); gl.viewport(0, 0, ow, oh); gl.activeTexture(gl.TEXTURE0);
  if (lit) gl.bindTexture(gl.TEXTURE_2D, lit);
  else { gl.bindTexture(gl.TEXTURE_2D, GFX.tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, low); }
  gl.uniform1i(u.T, 0); gl.uniform2f(u.S, W, H); gl.uniform2f(u.O, ow, oh); gl.uniform1f(u.tm, time % 1000);
  gl.uniform1f(u.expo, [0.86, 1, 1.08][SETTINGS.bright ?? 1]); gl.uniform1f(u.bloom, SETTINGS.bloom); gl.uniform1f(u.vig, SETTINGS.vig); gl.uniform1f(u.scan, SETTINGS.scan); gl.uniform1f(u.grain, SETTINGS.grain);
  gl.uniform1f(u.ca, SETTINGS.ca); gl.uniform1f(u.filt, SETTINGS.tex); gl.uniform1f(u.grade, SETTINGS.grade);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
function presentWorld() {
  const t0 = performance.now(); presentBody(); const dt = performance.now() - t0;
  GFX.pt = (GFX.pt || 0) + dt; GFX.pn = (GFX.pn || 0) + 1;   // frame-time probe for tools/shots/lx (reset both to measure)
}
function presentBody() {
  const w = W * scale, h = H * scale;
  if (SETTINGS.shaders && gfxReady()) {
    try { gfxRender(w, h); vctx.imageSmoothingEnabled = true; vctx.drawImage(GFX.cv, ox, oy, w, h); if (GFX.sync) GFX.gl.finish(); return; }
    catch (e) { console.warn('shader pass failed, falling back:', e && e.message); GFX.ok = false; }
  }
  lxFlatten();
  vctx.imageSmoothingEnabled = SETTINGS.tex === 2; if (vctx.imageSmoothingEnabled) vctx.imageSmoothingQuality = 'high';
  vctx.drawImage(low, ox, oy, w, h);
  vctx.imageSmoothingEnabled = false;
}

// ---- Settings › Graphics & shaders
const GFX_ROWS = [
  { k: 'shaders', label: 'Shaders', opts: ['Off', 'On'], desc: 'Post-processing on the game world (the HUD stays sharp). Turn off on slow devices.' },
  { k: 'bright', label: 'Brightness', opts: ['Dark', 'Normal', 'Bright'], desc: 'How much of the dark you can see into. Bright helps on dim screens and in daylight.' },
  { k: 'light', label: 'Lighting', opts: ['Classic', 'Dynamic', 'Dynamic + shadows'], shader: true, desc: 'Dynamic: lanterns, fire and spells light the stone in pixel-art bands. Shadows: walls block the light.' },
  { k: 'lband', label: 'Light bands', opts: ['Pixel', 'Smooth'], shader: true, desc: 'Pixel: light falls off in hand-drawn steps with a dithered edge. Smooth: a soft gradient.' },
  { k: 'preset', label: 'Look', desc: 'A ready-made mix of the options below. Change any of them to make your own.' },
  { k: 'tex', label: 'Texture filter', opts: ['Crisp pixels', 'Smooth pixels', 'Soft'], desc: 'Crisp: hard pixel edges. Smooth pixels: clean anti-aliased pixel art (needs shaders). Soft: blurred.' },
  { k: 'bloom', label: 'Bloom', opts: ['Off', 'Low', 'High'], shader: true, desc: 'Embers, fire, spells and light sources glow and bleed into the dark.' },
  { k: 'grade', label: 'Colour grade', opts: ['Natural', 'Ember', 'Moonlit', 'Noir', 'Vivid'], shader: true, desc: 'Tints the whole world: warm ember, cold moonlight, black-and-white noir, or richer colour.' },
  { k: 'vig', label: 'Lens vignette', opts: ['Off', 'On'], shader: true, desc: 'Darkens the corners a little more, like an old lens.' },
  { k: 'scan', label: 'Scanlines', opts: ['Off', 'Soft', 'CRT'], shader: true, desc: 'Soft: faint lines between pixel rows. CRT: a curved old monitor with a phosphor mask.' },
  { k: 'grain', label: 'Film grain', opts: ['Off', 'On'], shader: true, desc: 'A fine moving grain over the picture.' },
  { k: 'ca', label: 'Chromatic aberration', opts: ['Off', 'On'], shader: true, desc: 'Red and blue split slightly toward the edges of the screen.' },
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
  const px = 12, pw = 196, top = 26, rh = 13, on = !!SETTINGS.shaders, bad = GFX.ok === false;
  panel(px, top, pw, 10 + GFX_ROWS.length * rh);
  GFX_ROWS.forEach((R, i) => {
    const y = top + 15 + i * rh, sel = i === S.sel, dim = (R.shader && !on);
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
  wrap(R.desc, pw - 16, 5.4).forEach((ln, i) => text(ln, px + 8, top + 21 + GFX_ROWS.length * rh + i * 7.5, 5.4, '#b8ab90', 'left', { weight: 400 }));
  text('Preview →', 300, 30, 5.6, '#b8ab90', 'center', { weight: 400, alpha: 0.8 });
  uiFooter([['↑↓', 'select'], ['←→', 'change'], ['Esc', 'back']]);
}

Object.assign(window.__game, { pad: padPoll, PAD, GFX, GFX_PRESETS });   // headless tests

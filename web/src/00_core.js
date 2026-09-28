// Cinderhollow — core: canvas, sprites, animation, audio, input. All art = Aseprite exports in ASSETS.
'use strict';
const W = 384, H = 216, TILE = 16;
const view = document.getElementById('game');
const vctx = view.getContext('2d');
const low = document.createElement('canvas'); low.width = W; low.height = H;
let g = low.getContext('2d'); g.imageSmoothingEnabled = false;   // let: drawGlow() (41_light.js) points it at the glow layer while emitters draw
const lightC = document.createElement('canvas'); lightC.width = W; lightC.height = H;
const lg = lightC.getContext('2d');
const tint = document.createElement('canvas'); tint.width = 256; tint.height = 160;
const tctx = tint.getContext('2d');
const FONT = "'Cinzel', 'Trajan Pro', 'Cormorant Garamond', Georgia, serif";
const rand = (a, b) => a + Math.random() * (b - a);
const irand = (a, b) => Math.floor(rand(a, b + 1));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const approach = (v, t, d) => v < t ? Math.min(t, v + d) : Math.max(t, v - d);
const lerp = (a, b, t) => a + (b - a) * t;
const sign = v => v < 0 ? -1 : 1;
function rect(x0, y0, x1, y1) { return { x0: Math.min(x0, x1), x1: Math.max(x0, x1), y0: Math.min(y0, y1), y1: Math.max(y0, y1) }; }
function overlap(a, b) { return a.x0 < b.x1 && a.x1 > b.x0 && a.y0 < b.y1 && a.y1 > b.y0; }
function hash2(x, y) { let h = (x * 374761393 + y * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }

// ------------------------------------------------------------------ sprites
class Sheet {
  constructor(name, opt = {}) {
    const a = ASSETS[name];
    this.name = name; this.tags = {}; this.frames = []; this.meta = null; this.fw = this.fh = 16; this.ax = 8; this.ay = 16; this.native = opt.native ?? 1;
    this.ok = !!(a && a.png && a.json);
    if (!this.ok) return;
    this.frames = a.json.frames.map(f => ({ x: f.frame.x, y: f.frame.y, w: f.frame.w, h: f.frame.h, ms: f.duration }));
    this.tags = {};
    for (const t of a.json.meta.frameTags) this.tags[t.name] = { from: t.from, to: t.to };
    this.fw = this.frames[0].w; this.fh = this.frames[0].h;
    this.configure(opt);
  }
  // meta/anchor/facing can arrive after a bare preload of the same sheet (phase-2 sheets borrow phase-1 meta)
  configure(opt = {}) {
    if (!this.ok) return this;
    this.meta = ASSETS[this.name + '_meta'] || opt.meta || this.meta || null;
    this.native = opt.native ?? (this.meta && this.meta.native) ?? 1;
    const an = this.meta && this.meta.anchor;
    this.ax = opt.ax ?? (an ? an[0] : this.fw / 2);
    this.ay = opt.ay ?? (an ? an[1] : this.fh);
    return this;
  }
  // images are created on first use and big ones are dropped again a few rooms later (phones can't hold every sheet decoded)
  get img() {
    if (!this._img) { this._img = new Image(); this._img.src = ASSETS[this.name].png; }
    this.used = SHEET_EPOCH; return this._img;
  }
  get big() { return this.fw * this.fh * this.frames.length > 600000; }
  evict() { if (this._img) { this._img.src = ''; this._img = null; } }
  tag(name) { return this.tags[name] || Object.values(this.tags)[0]; }
  has(name) { return !!this.tags[name]; }
  first(name) { const t = this.tag(name); return t ? t.from : 0; }
}
const SHEETS = {};
let SHEET_EPOCH = 0;   // bumped on every room change
// warm up sheets created while a room was built; free big ones unused for a few rooms (never the player/weapon)
function sheetHousekeeping(keep) {
  SHEET_EPOCH++;
  for (const s of Object.values(SHEETS)) {
    if (!s.ok || !s._img) continue;
    if (s.big && !keep(s.name) && SHEET_EPOCH - (s.used ?? 0) > 3) s.evict();
  }
}
function warmSheets() { for (const s of Object.values(SHEETS)) if (s.ok && s._img && !s._img.complete && s._img.decode) s._img.decode().catch(() => {}); }
function sheet(name, opt) { const s = SHEETS[name]; if (!s) return (SHEETS[name] = new Sheet(name, opt)); if (opt && !s.cfgd) { s.cfgd = true; s.configure(opt); } return s; }

class Anim {
  constructor(sh, tag, loop = true, speed = 1) { this.s = sh; this.set(tag, loop, speed); }
  set(tag, loop = true, speed = 1) {
    const t = (this.s.ok && this.s.tag(tag)) || { from: 0, to: 0 };
    Object.assign(this, { tag, from: t.from, n: t.to - t.from + 1, i: 0, t: 0, loop, speed, done: false, changed: true, entered: true });
    return this;
  }
  ms(i = this.i) { return this.s.ok ? this.s.frames[this.from + i].ms : 100; }
  total() { let s = 0; for (let i = 0; i < this.n; i++) s += this.ms(i); return s / 1000 / this.speed; }
  update(dt) {
    this.changed = this.entered; this.entered = false;
    if (this.done) return;
    this.t += dt * 1000 * this.speed;
    let guard = 0;
    while (this.t >= this.ms() && guard++ < 32) {
      this.t -= this.ms();
      if (this.i < this.n - 1) { this.i++; this.changed = true; }
      else if (this.loop) { this.i = 0; this.changed = true; }
      else { this.done = true; this.t = 0; break; }
    }
  }
  hold() { this.t = Math.min(this.t, 1); }
  get frame() { return this.from + this.i; }
}

// draws with the sheet anchor at (x,y) in the current transform (world coords)
function drawSprite(sh, frame, x, y, face, opt = {}) {
  if (!sh || !sh.ok) return;
  const f = sh.frames[frame];
  if (!f) return;
  const flip = face !== sh.native;
  let img = sh.img, sx = f.x, sy = f.y;
  if (opt.flash) {
    if (tint.width < f.w || tint.height < f.h) { tint.width = Math.max(tint.width, f.w); tint.height = Math.max(tint.height, f.h); }
    tctx.clearRect(0, 0, f.w, f.h);
    tctx.globalCompositeOperation = 'source-over'; tctx.globalAlpha = 1;
    tctx.drawImage(img, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
    tctx.globalCompositeOperation = 'source-atop'; tctx.globalAlpha = Math.min(1, opt.flash);
    tctx.fillStyle = opt.flashColor || '#fff'; tctx.fillRect(0, 0, f.w, f.h);
    tctx.globalCompositeOperation = 'source-over'; tctx.globalAlpha = 1;
    img = tint; sx = 0; sy = 0;
  }
  const X = Math.round(x), Y = Math.round(y);
  let ax, ay;
  if (opt.pivot) [ax, ay] = opt.pivot;
  else if (opt.center) { ax = Math.floor(f.w / 2); ay = Math.floor(f.h / 2); }
  else if (opt.bottom) { ax = Math.floor(f.w / 2); ay = f.h; }
  else { ax = sh.ax; ay = sh.ay; }
  g.save();
  g.globalAlpha = opt.alpha ?? 1;
  if (opt.blend) g.globalCompositeOperation = opt.blend;
  if (opt.rot) {
    g.translate(X, Y); if (flip) g.scale(-1, 1); g.rotate(opt.rot);
    g.drawImage(img, sx, sy, f.w, f.h, -ax, -ay, f.w, f.h); g.restore(); return;
  }
  if (flip) { g.translate(X, 0); g.scale(-1, 1); g.drawImage(img, sx, sy, f.w, f.h, -ax, Y - ay, f.w, f.h); }
  else g.drawImage(img, sx, sy, f.w, f.h, X - ax, Y - ay, f.w, f.h);
  g.restore();
}
function drawRotated(sh, frame, x, y, angle, alpha = 1) {
  if (!sh || !sh.ok) return;
  const f = sh.frames[frame];
  g.save(); g.globalAlpha = alpha;
  g.translate(Math.round(x), Math.round(y));
  g.rotate(angle - (sh.native === -1 ? Math.PI : 0));
  g.drawImage(sh.img, f.x, f.y, f.w, f.h, -Math.floor(f.w / 2), -Math.floor(f.h / 2), f.w, f.h);
  g.restore();
}
// meta rect (frame coords, native facing) -> world rect for an entity {x,y,face} drawn with sheet sh
function metaRect(sh, e, r) {
  const x0 = r[0] - sh.ax, x1 = r[0] + r[2] - sh.ax, y0 = e.y - sh.ay + r[1], y1 = y0 + r[3];
  return (e.face === sh.native) ? rect(e.x + x0, y0, e.x + x1, y1) : rect(e.x - x1, y0, e.x - x0, y1);
}
function metaPoint(sh, e, p) {
  const dx = p[0] - sh.ax;
  return { x: e.face === sh.native ? e.x + dx : e.x - dx, y: e.y - sh.ay + p[1] };
}

// ------------------------------------------------------------------ audio (tiny synth)
let AC = null, muted = false, master = null;
function audio() {
  if (!AC) { try { AC = new (window.AudioContext || window.webkitAudioContext)(); master = AC.createGain(); master.gain.value = SETTINGS.sfx; master.connect(AC.destination); } catch (e) {} }
  if (AC && AC.state === 'suspended') AC.resume();
  return AC;
}
function noise(dur, freq, q, vol, type = 'bandpass', slide = 0) {
  const ac = audio(); if (!ac || muted) return;
  const len = Math.max(1, Math.floor(ac.sampleRate * dur)), buf = ac.createBuffer(1, len, ac.sampleRate), d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
  const src = ac.createBufferSource(); src.buffer = buf;
  const f = ac.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
  if (slide) f.frequency.exponentialRampToValueAtTime(Math.max(40, freq * slide), ac.currentTime + dur);
  const gn = ac.createGain(); gn.gain.value = vol;
  src.connect(f).connect(gn).connect(master); src.start();
}
function tone(freq, dur, vol, type = 'sine', slide = 1, delay = 0, dest = null) {
  const ac = audio(); if (!ac || muted) return;
  const o = ac.createOscillator(), gn = ac.createGain(), t0 = ac.currentTime + delay;
  o.type = type; o.frequency.setValueAtTime(freq, t0);
  o.frequency.exponentialRampToValueAtTime(Math.max(20, freq * slide), t0 + dur);
  gn.gain.setValueAtTime(0.0001, ac.currentTime); gn.gain.setValueAtTime(vol, t0); gn.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
  o.connect(gn).connect(dest || master); o.start(t0); o.stop(t0 + dur + 0.05);
}
const sfx = {
  swing: () => noise(0.12, 2000, 0.8, 0.22, 'bandpass', 0.4),
  heavySwing: () => noise(0.25, 900, 0.7, 0.35, 'bandpass', 0.3),
  hit: () => { noise(0.1, 600, 1, 0.45, 'lowpass'); tone(120, 0.12, 0.2, 'square', 0.5); },
  bigHit: () => { noise(0.2, 400, 1, 0.6, 'lowpass'); tone(80, 0.25, 0.3, 'square', 0.4); },
  block: () => { tone(900, 0.1, 0.12, 'square', 0.6); noise(0.08, 3000, 2, 0.2, 'highpass'); },
  parry: () => { tone(1320, 0.3, 0.16, 'triangle', 1.2); tone(1980, 0.25, 0.1, 'sine'); noise(0.1, 4000, 2, 0.25, 'highpass'); },
  crit: () => { noise(0.35, 300, 1, 0.8, 'lowpass', 0.3); tone(60, 0.4, 0.4, 'sawtooth', 0.4); },
  hurt: () => { noise(0.2, 300, 1, 0.6, 'lowpass'); tone(70, 0.25, 0.3, 'sawtooth', 0.6); },
  roll: () => noise(0.18, 400, 0.5, 0.16, 'lowpass'),
  jump: () => noise(0.08, 700, 0.6, 0.1, 'bandpass'),
  land: () => noise(0.1, 250, 0.6, 0.18, 'lowpass'),
  step: () => noise(0.04, 180, 0.6, 0.05, 'lowpass'),
  boom: () => { noise(0.7, 160, 0.8, 0.9, 'lowpass', 0.3); tone(44, 0.7, 0.5, 'sine', 0.5); },
  bossSwing: () => noise(0.32, 500, 0.6, 0.45, 'bandpass', 0.25),
  glint: () => { tone(1760, 0.18, 0.08, 'triangle', 1.5); tone(2637, 0.12, 0.05, 'sine'); },
  charge: () => tone(220, 0.8, 0.08, 'sawtooth', 3),
  spear: () => noise(0.2, 2500, 2, 0.15, 'bandpass', 0.5),
  pillar: () => { noise(0.4, 300, 0.7, 0.35, 'lowpass', 2); tone(90, 0.4, 0.15, 'sawtooth', 1.6); },
  heal: () => { tone(523, 0.5, 0.12, 'triangle'); tone(784, 0.6, 0.1, 'triangle', 1, 0.12); },
  mana: () => { tone(659, 0.5, 0.1, 'sine'); tone(988, 0.6, 0.08, 'sine', 1, 0.12); },
  died: () => { tone(98, 2.2, 0.35, 'sawtooth', 0.5); tone(73, 2.4, 0.3, 'sine', 0.6); },
  felled: () => [392, 494, 587, 784].forEach((f, i) => tone(f, 1.4, 0.12, 'triangle', 1, i * 0.16)),
  roar: () => { noise(1.4, 200, 0.6, 0.8, 'lowpass', 0.5); tone(58, 1.4, 0.45, 'sawtooth', 0.7); },
  howl: () => { tone(220, 1.4, 0.2, 'sawtooth', 1.8); tone(330, 1.2, 0.12, 'triangle', 1.6); noise(1.2, 700, 0.8, 0.3, 'bandpass', 0.5); },
  bolt: () => { tone(880, 0.25, 0.08, 'triangle', 0.5); noise(0.2, 3000, 1, 0.12, 'bandpass', 0.4); },
  fire: () => { noise(0.5, 600, 0.6, 0.4, 'lowpass', 1.8); tone(110, 0.4, 0.15, 'sawtooth', 0.6); },
  cinders: () => { tone(1568, 0.1, 0.05, 'triangle'); tone(2093, 0.12, 0.04, 'triangle', 1, 0.05); },
  pickup: () => [659, 880, 1175].forEach((f, i) => tone(f, 0.4, 0.09, 'triangle', 1, i * 0.08)),
  levelup: () => [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.9, 0.1, 'triangle', 1, i * 0.1)),
  kindle: () => { noise(0.8, 500, 0.6, 0.3, 'lowpass', 2); [392, 587, 784].forEach((f, i) => tone(f, 1.6, 0.08, 'sine', 1, 0.2 + i * 0.15)); },
  menu: () => tone(1046, 0.06, 0.05, 'triangle'),
  deny: () => tone(160, 0.15, 0.1, 'square', 0.8),
  shoot: () => noise(0.12, 1800, 2, 0.15, 'bandpass', 0.6),
  crumble: () => { noise(0.6, 250, 0.5, 0.5, 'lowpass', 0.4); noise(0.3, 900, 0.5, 0.2, 'bandpass'); },
  gate: () => { noise(1.0, 150, 0.8, 0.4, 'lowpass'); tone(55, 1.0, 0.2, 'square', 1.1); },
  bleed: () => { noise(0.3, 1200, 0.7, 0.4, 'bandpass', 0.3); tone(200, 0.2, 0.15, 'sawtooth', 0.5); },
  urn: () => { noise(0.25, 1500, 1, 0.3, 'bandpass', 0.5); tone(700, 0.08, 0.06, 'square', 0.5); },
};

// ------------------------------------------------------------------ input
const held = new Set(), buffered = new Map();
const DEFAULT_KEYMAP = {
  ArrowLeft: 'left', KeyA: 'left', ArrowRight: 'right', KeyD: 'right', ArrowUp: 'up', KeyW: 'up', ArrowDown: 'down', KeyS: 'down',
  Space: 'jump', KeyJ: 'attack', KeyK: 'heavy', KeyL: 'roll', ShiftLeft: 'roll', ShiftRight: 'roll',
  KeyU: 'cast', KeyI: 'parry', KeyO: 'art', KeyH: 'hook', KeyC: 'hook', KeyQ: 'spell', KeyF: 'heal', KeyR: 'mana', KeyE: 'interact',
  Tab: 'map', KeyM: 'map', Escape: 'pause', KeyP: 'pause', Enter: 'confirm', KeyN: 'mute', Backspace: 'back',
};
// ---- rebindable keys (Settings › Key bindings). Two key slots per action, saved per browser.
const KEYMAP = {};
const FIXED_KEYS = { Escape: 'pause', Enter: 'confirm', Backspace: 'back' };   // always work, so menus can never be locked out
const BINDABLE = [['left', 'Move left'], ['right', 'Move right'], ['up', 'Aim up / look up'], ['down', 'Aim down / drop'], ['jump', 'Jump'],
  ['attack', 'Attack'], ['heavy', 'Heavy attack'], ['roll', 'Roll / air dash'], ['parry', 'Parry / shield block'], ['art', 'Weapon art'],
  ['cast', 'Cast spell'], ['spell', 'Switch spell'], ['heal', 'Crimson flask (HP)'], ['mana', 'Azure flask (FP)'], ['hook', 'Root Hook'],
  ['interact', 'Interact / rest'], ['map', 'Map'], ['pause', 'Menu'], ['mute', 'Mute sound']];
const KEYS_STORE = 'cinderhollow_keys';
let BINDINGS = {}, KEY_CAPTURE = null;
function defaultBindings() {
  const b = {}; for (const [a] of BINDABLE) b[a] = [];
  for (const [code, a] of Object.entries(DEFAULT_KEYMAP)) if (b[a] && b[a].length < 2 && !FIXED_KEYS[code]) b[a].push(code);
  return b;
}
function applyBindings() {
  for (const k of Object.keys(KEYMAP)) delete KEYMAP[k];
  for (const [a, codes] of Object.entries(BINDINGS)) for (const c of codes) if (c) KEYMAP[c] = a;
  Object.assign(KEYMAP, FIXED_KEYS);
}
function loadBindings() {
  BINDINGS = defaultBindings();
  try { const s = JSON.parse(localStorage.getItem(KEYS_STORE) || 'null'); if (s) for (const [a] of BINDABLE) if (Array.isArray(s[a])) BINDINGS[a] = s[a].slice(0, 2).filter(c => typeof c === 'string' && !FIXED_KEYS[c]); } catch (e) {}
  applyBindings();
}
function saveBindings() { try { localStorage.setItem(KEYS_STORE, JSON.stringify(BINDINGS)); } catch (e) {} applyBindings(); }
function bindKey(action, slot, code) {   // code === null clears the slot; a key moves away from any other action
  for (const [a, codes] of Object.entries(BINDINGS)) BINDINGS[a] = codes.filter(c => c !== code);
  const L = [...(BINDINGS[action] || [])]; if (code) L[slot] = code; else L.splice(slot, 1);
  BINDINGS[action] = L.filter(Boolean).slice(0, 2); saveBindings();
}
const KEY_NAMES = { ArrowLeft: '←', ArrowRight: '→', ArrowUp: '↑', ArrowDown: '↓', Space: 'Space', ShiftLeft: 'Shift', ShiftRight: 'R-Shift', ControlLeft: 'Ctrl',
  ControlRight: 'R-Ctrl', AltLeft: 'Alt', AltRight: 'R-Alt', MetaLeft: 'Cmd', MetaRight: 'R-Cmd', Tab: 'Tab', Enter: 'Enter', Escape: 'Esc', Backspace: 'Bksp',
  CapsLock: 'Caps', Semicolon: ';', Quote: "'", Comma: ',', Period: '.', Slash: '/', Backslash: '\\', BracketLeft: '[', BracketRight: ']', Minus: '-', Equal: '=', Backquote: '`' };
function keyLabel(code) {
  if (!code) return '—';
  if (KEY_NAMES[code]) return KEY_NAMES[code];
  if (/^Key[A-Z]$/.test(code)) return code.slice(3);
  if (/^Digit\d$/.test(code)) return code.slice(5);
  if (/^Numpad/.test(code)) return 'Num' + code.slice(6);
  if (/^F\d+$/.test(code)) return code;
  return code;
}
function keysOf(action) { return (BINDINGS[action] || []).filter(Boolean).map(keyLabel); }
loadBindings();
let onPressHook = () => {};
function press(a) { if (!held.has(a)) buffered.set(a, performance.now()); held.add(a); onPressHook(a); }
function release(a) { held.delete(a); }
addEventListener('keydown', e => { if (KEY_CAPTURE) { e.preventDefault(); if (!e.repeat) { const f = KEY_CAPTURE; KEY_CAPTURE = null; f(e.code); } return; } const a = KEYMAP[e.code]; if (!a) return; e.preventDefault(); if (!e.repeat) press(a); else if (['left', 'right', 'up', 'down'].includes(a)) onPressHook(a, true); });
addEventListener('keyup', e => { const a = KEYMAP[e.code]; if (a) release(a); });
function grabFocus() { try { window.focus(); view.focus({ preventScroll: true }); } catch (e) {} }
view.addEventListener('mousedown', e => {
  const hadFocus = document.hasFocus();
  grabFocus();
  if (!hadFocus) return;
  if (typeof uiEatsClick === 'function' && uiEatsClick()) return;   // 63_mouse.js: menu clicks select, they don't swing
  press(e.button === 2 ? 'heavy' : 'attack');
});
view.addEventListener('pointerdown', grabFocus);
addEventListener('mouseup', e => release(e.button === 2 ? 'heavy' : 'attack'));
addEventListener('blur', () => held.clear());
view.addEventListener('contextmenu', e => e.preventDefault());
function take(a, win = 180) { const t = buffered.get(a); if (t !== undefined && performance.now() - t < win) { buffered.delete(a); return true; } return false; }
function peek(a, win = 180) { const t = buffered.get(a); return t !== undefined && performance.now() - t < win; }
function clearBuffer() { buffered.clear(); }
document.querySelectorAll('[data-act]').forEach(b => {
  const a = b.dataset.act;
  b.addEventListener('pointerdown', e => { e.preventDefault(); b.setPointerCapture(e.pointerId); press(a); });
  const up = e => { e.preventDefault(); release(a); };
  b.addEventListener('pointerup', up); b.addEventListener('pointercancel', up);
});

// ------------------------------------------------------------------ extension points (see docs/EXPANSION_CONTRACT.md)
// hook lists: update(dt) render() renderTop() hud() enter(def) rest(shrineProp) derive(D) playerHurt(dmg, opt) -> dmg,
// strike(target, info, A) after each player melee hit, parry(src), cast(id), death()
const HOOKS = { update: [], render: [], renderTop: [], hud: [], enter: [], rest: [], derive: [], playerHurt: [], strike: [], parry: [], cast: [], death: [] };
const runHooks = (k, ...a) => { for (const f of HOOKS[k]) f(...a); };
const SPELL_CAST = {};   // spell id -> (spellPower) => void
const ART_IMPL = {};     // art id -> { fallback: [animTag, speed], release: frameIndex, start(), update(dt, grav) }

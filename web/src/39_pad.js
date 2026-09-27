// ------------------------------------------------------------------ Controller support (Gamepad API, "standard" layout)
// Polled once per frame from frame() in 09_main.js. In play the buttons map through PAD.binds (Settings › Controller);
// everywhere else (menus, title, dialog, cutscenes, map) a fixed layout drives the UI so a menu can never be locked out:
// A confirm · B back · Start menu · View/RB map/next tab · LB previous tab · D-pad or left stick to move the cursor.
// Buttons still held when the mode flips are latched until released, so the A that closed a menu doesn't also jump.
const PAD_STORE = 'cinderhollow_pad';
const PAD_NAMES = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'LT', 'RT', 'View', 'Start', 'L3', 'R3', 'D-pad ↑', 'D-pad ↓', 'D-pad ←', 'D-pad →', 'Home'];
const PAD_SHORT = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'LT', 'RT', 'View', 'Start', 'L3', 'R3', 'D↑', 'D↓', 'D←', 'D→', 'Home'];
const PAD_DEFAULT = { jump: 0, roll: 1, attack: 2, interact: 3, parry: 4, art: 5, cast: 6, heavy: 7, map: 8, mana: 12, heal: 13, spell: 14, hook: 15 };
const PAD_FIXED = 9;   // Start always opens the menu
const PAD_BINDABLE = BINDABLE.filter(([a]) => a !== 'pause' && a !== 'mute');
const PAD_UI = { 0: 'confirm', 1: 'back', 9: 'pause', 8: 'map', 5: 'map', 4: 'spell', 12: 'up', 13: 'down', 14: 'left', 15: 'right' };
const PAD = { active: false, name: '', mode: 'play', prev: new Set(), raw: new Set(), latch: new Set(), rep: {}, binds: {}, capture: null, rumble: 1, seen: false };

function padDefaults() { return { ...PAD_DEFAULT }; }
function padLoad() {
  PAD.binds = padDefaults();
  try {
    const s = JSON.parse(localStorage.getItem(PAD_STORE) || 'null');
    if (s && s.binds) { PAD.binds = {}; for (const [a] of PAD_BINDABLE) if (Number.isInteger(s.binds[a]) && s.binds[a] !== PAD_FIXED) PAD.binds[a] = s.binds[a]; }
    if (s && s.rumble !== undefined) PAD.rumble = s.rumble ? 1 : 0;
  } catch (e) {}
}
function padSave() { try { localStorage.setItem(PAD_STORE, JSON.stringify({ binds: PAD.binds, rumble: PAD.rumble })); } catch (e) {} }
function padBind(action, btn) {   // btn === null clears; a button moves away from any other action
  for (const a of Object.keys(PAD.binds)) if (PAD.binds[a] === btn) delete PAD.binds[a];
  if (btn === null) delete PAD.binds[action]; else PAD.binds[action] = btn;
  padSave();
}
function padActionOf(i) { if (i === PAD_FIXED) return 'pause'; for (const a in PAD.binds) if (PAD.binds[a] === i) return a; return null; }
padLoad();

function padFind() {
  let pads = []; try { pads = navigator.getGamepads ? navigator.getGamepads() : []; } catch (e) {}
  for (const p of pads) if (p && p.connected && p.buttons && p.buttons.length >= 4) return p;
  return null;
}
function padPoll(dt) {
  const gp = padFind();
  if (!gp) { if (PAD.prev.size) { for (const a of PAD.prev) release(a); PAD.prev = new Set(); } PAD.raw = new Set(); return; }
  if (!PAD.seen) { PAD.seen = true; PAD.name = gp.id.replace(/\s*\(.*$/, '').slice(0, 34) || 'Controller'; toast(`Controller connected: ${PAD.name}`, 2.5); }
  const down = new Set();
  gp.buttons.forEach((b, i) => { if (i !== 16 && (b.pressed || b.value > 0.35)) down.add(i); });
  const ax = gp.axes[0] || 0, ay = gp.axes[1] || 0;
  if (ax < -0.4) down.add('s:left'); if (ax > 0.4) down.add('s:right');
  if (ay < -0.55) down.add('s:up'); if (ay > 0.55) down.add('s:down');
  const fresh = [...down].filter(k => !PAD.raw.has(k));
  if (fresh.length) PAD.active = true;
  // rebinding: the next fresh button goes to the capture callback (the stick doesn't count)
  if (PAD.capture) {
    const b = fresh.find(k => typeof k === 'number');
    if (b !== undefined) { const f = PAD.capture; PAD.capture = null; for (const k of down) PAD.latch.add(k); f(b); }
    PAD.raw = down; return;
  }
  const mode = state === 'play' ? 'play' : 'ui';
  if (mode !== PAD.mode) { PAD.mode = mode; for (const k of down) PAD.latch.add(k); }
  for (const k of [...PAD.latch]) if (!down.has(k)) PAD.latch.delete(k);
  const want = new Set();
  for (const k of down) {
    if (PAD.latch.has(k)) continue;
    const a = typeof k === 'string' ? k.slice(2) : mode === 'play' ? padActionOf(k) : PAD_UI[k];
    if (a) want.add(a);
  }
  for (const a of want) if (!PAD.prev.has(a)) press(a);
  for (const a of PAD.prev) if (!want.has(a)) release(a);
  // held directions repeat in menus, like a held arrow key
  for (const d of ['left', 'right', 'up', 'down']) {
    if (mode !== 'ui' || !want.has(d)) { PAD.rep[d] = 0; continue; }
    const t0 = PAD.rep[d] || 0, t1 = t0 + dt; PAD.rep[d] = t1;
    if (t1 > 0.38 && Math.floor((t1 - 0.38) / 0.09) !== Math.floor(Math.max(0, t0 - 0.38) / 0.09)) onPressHook(d, true);
  }
  PAD.prev = want; PAD.raw = down;
}
// keyboard or mouse use hands the on-screen prompts back to the keyboard
addEventListener('keydown', () => { PAD.active = false; }, true);
addEventListener('mousedown', () => { PAD.active = false; }, true);
addEventListener('gamepaddisconnected', () => { PAD.seen = false; PAD.active = false; toast('Controller disconnected', 2); });

// ---- rumble
function padRumble(strong, weak, ms) {
  if (!PAD.rumble || !PAD.active) return;
  const gp = padFind(); const va = gp && gp.vibrationActuator;
  try { if (va && va.playEffect) va.playEffect('dual-rumble', { duration: ms, strongMagnitude: strong, weakMagnitude: weak }); } catch (e) {}
}
{ const _hurt = hurtPlayer; hurtPlayer = function (...args) { const hp0 = P ? P.hp : 0, r = _hurt.apply(this, args); if (r && P && P.hp < hp0) padRumble(P.hp <= 0 ? 1 : 0.55, 0.35, P.hp <= 0 ? 420 : 170); return r; }; }
HOOKS.parry.push(() => padRumble(0.2, 0.6, 90));

// ---- prompts follow the last device you touched
const PAD_TEXT = [[/\bPress E\b/g, 'Press Y'], [/\bpress E\b/g, 'press Y'], [/\(Esc\)/g, '(Start)'], [/\bEsc\b/g, 'Start'], [/\bPress Enter\b/g, 'Press A'], [/\bPress Q\b/g, 'Press D-pad ←']];
function padText(s) { if (!PAD.active || typeof s !== 'string') return s; for (const [re, r] of PAD_TEXT) s = s.replace(re, r); return s; }
const PAD_KL = { Enter: 'A', Esc: 'B', Tab: 'View', Q: 'LB', Bksp: 'X', '↑↓': 'D-pad', '←→': 'D-pad', '↑↓←→': 'D-pad' };
{
  const _keysOf = keysOf;
  keysOf = function (action) {
    if (!PAD.active) return _keysOf(action);
    if (['left', 'right', 'up', 'down'].includes(action)) { const b = PAD.binds[action]; return [...(b !== undefined ? [PAD_SHORT[b]] : []), 'L-stick']; }
    if (action === 'pause') return ['Start'];
    const b = PAD.binds[action]; return b !== undefined ? [PAD_SHORT[b]] : [];
  };
}

// ---- Settings › Controller
const PAD_ROWS = () => [...PAD_BINDABLE, ['__rumble', 'Vibration'], ['__reset', 'Reset to defaults']];
function padSubInput(M, a) {
  const S = M.sub, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a), rows = PAD_ROWS(), n = rows.length;
  if (S.capture) return;
  if (['pause', 'back', 'heavy'].includes(a)) { M.sub = null; sfx.menu(); return; }
  if (a === 'up') { S.sel = (S.sel + n - 1) % n; sfx.menu(); return; }
  if (a === 'down') { S.sel = (S.sel + 1) % n; sfx.menu(); return; }
  const [act] = rows[S.sel];
  if (act === '__rumble') { if (conf || a === 'left' || a === 'right') { PAD.rumble = PAD.rumble ? 0 : 1; padSave(); sfx.menu(); if (PAD.rumble) padRumble(0.4, 0.4, 150); } return; }
  if (act === '__reset') { if (conf) { PAD.binds = padDefaults(); padSave(); sfx.kindle(); toast('Controller reset to defaults', 2.5); } return; }
  if (!conf) return;
  if (!padFind()) { sfx.deny(); toast('Connect a controller and press any button on it', 2.5); return; }
  S.capture = true; sfx.glint();
  const cancel = code => { if (!S.capture) return; S.capture = false; PAD.capture = null; clearBuffer(); if (code === 'Backspace') { padBind(act, null); sfx.menu(); } else sfx.menu(); };
  KEY_CAPTURE = cancel;   // keyboard: Esc cancels, Backspace clears
  PAD.capture = btn => {
    S.capture = false; KEY_CAPTURE = null; clearBuffer();
    if (btn === PAD_FIXED) { sfx.deny(); toast('Start is reserved for the menu', 2.5); return; }
    const was = padActionOf(btn);
    padBind(act, btn); sfx.kindle();
    if (was && was !== act) toast(`${PAD_NAMES[btn]} moved from ${(BINDABLE.find(b => b[0] === was) || [0, was])[1]}`, 3);
  };
}
function renderPadSub(M) {
  const S = M.sub, rows = PAD_ROWS(), vis = 10, n = rows.length, gp = padFind();
  uiBackdrop(0.9); uiStrips();
  uiTitle('CONTROLLER', 17, 9);
  text(gp ? `Connected: ${PAD.name || 'controller'}` : 'No controller found. Plug one in and press any button on it.', W / 2, 28, 5.4, gp ? '#8fd89a' : '#9a8f78', 'center', { weight: 400 });
  S.off = clamp(S.off || 0, Math.max(0, S.sel - vis + 1), Math.min(S.sel, n - vis));
  const px = 60, pw = 264, top = 34, rh = 14;
  panel(px, top, pw, 12 + vis * rh);
  text('ACTION', px + 12, top + 10, 5, '#8a7f6a', 'left', { spacing: 1 });
  text('BUTTON', px + 214, top + 10, 5, '#8a7f6a', 'center', { spacing: 1 });
  for (let r = 0; r < vis && S.off + r < n; r++) {
    const i = S.off + r, [act, label] = rows[i], y = top + 24 + r * rh, sel = i === S.sel;
    if (sel) uiSel(px + 4, y - 10, pw - 8, rh - 1);
    if (act === '__reset') { text(label, px + pw / 2, y, 6.4, sel ? '#f5e3b0' : UIC.gold, 'center', { weight: 600 }); continue; }
    text(label, px + 12, y, 6.2, sel ? '#f5e3b0' : '#d8cdb4', 'left', { weight: sel ? 600 : 400 });
    let lbl, lit;
    if (act === '__rumble') { lbl = PAD.rumble ? 'On' : 'Off'; lit = !!PAD.rumble; }
    else { const b = PAD.binds[act], cap = sel && S.capture; lbl = cap ? '…' : b !== undefined ? PAD_NAMES[b] : ['left', 'right', 'up', 'down'].includes(act) ? 'L-stick' : '—'; lit = cap || b !== undefined; }
    const cx = px + 214, w = Math.max(30, textW(lbl, 6, 600) + 10);
    vctx.fillStyle = sel ? 'rgba(176,138,58,0.35)' : 'rgba(255,255,255,0.05)';
    vctx.fillRect(ox + (cx - w / 2) * scale, oy + (y - 8) * scale, w * scale, 11 * scale);
    text(lbl, cx, y, 6, lit ? '#f1e6c8' : '#6f6656', 'center', { weight: 600 });
  }
  if (S.off > 0) text('▲', px + pw - 10, top + 16, 5, '#9a8f78', 'center');
  if (S.off + vis < n) text('▼', px + pw - 10, top + 12 + vis * rh, 5, '#9a8f78', 'center');
  text('Move with the left stick. Start always opens the menu. In menus: A confirm, B back, LB/RB switch tabs.', W / 2, top + 24 + vis * rh, 5, '#8a7f6a', 'center', { weight: 400 });
  if (S.capture) {
    const act = rows[S.sel];
    vctx.fillStyle = 'rgba(0,0,0,0.55)'; vctx.fillRect(ox, oy, W * scale, H * scale);
    vctx.fillStyle = 'rgb(12,9,16)'; vctx.fillRect(ox + 92 * scale, oy + 84 * scale, 200 * scale, 44 * scale);
    vctx.strokeStyle = '#b08a3a'; vctx.strokeRect(ox + 92 * scale, oy + 84 * scale, 200 * scale, 44 * scale);
    text(`Press a button for “${act[1]}”`, W / 2, 101, 7, '#f5e3b0', 'center', { weight: 600 });
    text('Keyboard: Esc cancel  ·  Backspace clear', W / 2, 116, 5.6, '#b8ab90', 'center', { weight: 400 });
  }
  uiFooter([['↑↓', 'select'], ['Enter', rows[S.sel][0] === '__reset' ? 'reset' : rows[S.sel][0] === '__rumble' ? 'toggle' : 'rebind'], ['Esc', 'back']]);
}

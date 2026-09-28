// ------------------------------------------------------------------ WC: hit feel (engine-side impact polish, shared by every weapon)
// Pure feel: nothing here changes damage, reach or timing windows. Hitstop freezes both sides equally.
// Everything hooks in from this file: wrappers around playerStrike / pogo / hurtPlayer / updatePlayer / updateCamera /
// drawSprite, plus HOOKS.update / strike / render. Sounds live in 62_wsfx.js (WSFX). Keyed on ATK fields, never tag names.
//   hitstop by weapon weight · directional camera kick (scaled by Settings › Screen shake) · impact sparks by material and
//   element · a thin tip ribbon tinted by the weapon's glow · landing dust, thud and squash after air/down attacks
const FEEL = { off: false, hs: true, kx: 0, ky: 0, ax: 0, ay: 0, clock: 0, sq: 0, sparks: [], flashes: [], puffs: [], trail: [], sid: 0, tipPrev: null,
  inPlayer: false, strikeA: null, strikeN: 0, strikeBoss: false, swingHit: 0, airAtk: null, wasGround: true, lastSwing: null };
if (SETTINGS.wtrail === undefined) SETTINGS.wtrail = 1;   // Graphics › Weapon trail (row: see NEEDS in the WC report)
// Settings › Graphics › Screen shake mirror: an index view (0 Off / 1 Low / 2 Full) of the existing SETTINGS.shake (0 / 0.5 / 1).
// Not enumerable, so it never lands in the saved settings JSON; lets a GFX_ROWS entry drive the same value.
if (!Object.getOwnPropertyDescriptor(SETTINGS, 'shakeLvl')) Object.defineProperty(SETTINGS, 'shakeLvl', { enumerable: false, configurable: true,
  get() { return Math.round(clamp(SETTINGS.shake ?? 1, 0, 1) * 2); }, set(v) { SETTINGS.shake = clamp(v, 0, 2) / 2; } });
// WC's own random stream: feel effects never draw from Math.random, so the fight itself (damage rolls, AI) plays out identically with feel on or off
let feelSeed = 0x9e3779b9;
function frand(a, b) { feelSeed = (feelSeed * 1664525 + 1013904223) >>> 0; return a + (b - a) * (feelSeed / 4294967296); }
const feelShake = () => clamp(SETTINGS.shake ?? 1, 0, 1);

// ---- weight: 0 (dagger) .. 1 (hammer); the class sets the band, the weapon's own speed nudges it
const FEEL_CLS_W = { dagger: 0.08, whip: 0.14, twin: 0.14, katana: 0.36, spear: 0.4, staff: 0.36, sword: 0.46, shield: 0.5, scythe: 0.6, great: 0.9 };
function feelCls(A) { const c = A && A.cls && A.cls !== 'tech' ? A.cls : wcls(); return c === 'mirror' ? 'sword' : c; }
function feelWeight(A) {
  const Wd = WEAPONS[SAVE.weapon] || {};
  return clamp((FEEL_CLS_W[feelCls(A)] ?? 0.46) + clamp((1 - (Wd.speed || 1)) * 0.5, -0.12, 0.12), 0, 1);
}
function feelFinisher(A) { return A.kind === 'heavy' || A.counter || (typeof isFinisher === 'function' && isFinisher(P.state)) || (A.cls === 'tech'); }

// ---- element / glow of the equipped weapon: sparks, lights, the tip ribbon
const FEEL_EL = {
  fire: { pk: 'fire', pk2: 'ember', light: '255,140,60', glow: '#ffb070' },
  frost: { pk: 'frost', pk2: 'spark', light: '160,210,255', glow: '#bfe4ff' },
  holy: { pk: 'mote', pk2: 'gold', light: '255,240,200', glow: '#fff0c8' },
  rot: { pk: 'spore', pk2: 'ember', light: '150,210,90', glow: '#b8e890' },
  steel: { pk: 'spark', pk2: 'spark', light: '255,236,200', glow: '#dfe8f5' },
};
function feelElement(fire) {
  const sg = SIGS[SAVE.weapon]; if (sg && sg.glow) return { pk: sg.pk || 'spark', pk2: sg.pk2 || sg.pk || 'spark', light: sg.light || '255,220,160', glow: sg.glow, sig: true };
  const Wd = WEAPONS[SAVE.weapon] || {};
  if (fire || Wd.fire) return FEEL_EL.fire;
  if (Wd.frost) return FEEL_EL.frost;
  if (Wd.holy) return FEEL_EL.holy;
  if (Wd.rot) return FEEL_EL.rot;
  return FEEL_EL.steel;
}

// ---- what did we hit: metal rings and throws sparks, stone puffs dust, flesh bleeds, spirits scatter ink / frost
const FEEL_MAT_RX = [
  ['frost', /^hf_|ice_warden|vael|frost|rime/],
  ['stone', /golem|gargoyle|colossus|scarab|barnacle|magma_crawler|vessel|statue|stone|astrel/],
  ['metal', /knight|soldier|warden|sentinel|sentry|drone|cyborg|turret|kalden|champion|executioner|enforcer|overseer|bellringer|ringer|orrery|saint0|butler|pharaoh|foreman|twins|oswin/],
  ['ink', /wisp|wraith|grimoire|ink_|librarian|unwritten|coven|ferryman|choir|scarecrow|nv_hound|ghost|shade/],
];
const FEEL_MAT_CACHE = {};
function feelMat(t) {
  if (!t || t === 'brk') return 'stone';
  if (t.feelMat) return t.feelMat;
  if (t.prop) return 'stone';
  const id = t.boss ? (t.kind || (typeof boss !== 'undefined' && boss && boss.kind) || '') : (t.type || '');
  if (id in FEEL_MAT_CACHE) return FEEL_MAT_CACHE[id];
  let m = 'flesh';
  for (const [k, rx] of FEEL_MAT_RX) if (rx.test(id)) { m = k; break; }
  if (m === 'flesh' && t.cfg && t.cfg.guard) m = 'metal';
  return (FEEL_MAT_CACHE[id] = m);
}

// ---- short-lived streak sparks + flash lights (own pool, drawn as additive lines into the glow layer)
function feelSpark(x, y, vx, vy, col, life = 0.22, g = 420, len = 0.028) {
  if (FEEL.sparks.length > 90) FEEL.sparks.shift();
  FEEL.sparks.push({ x, y, vx, vy, col, life, max: life, g, len });
}
// soft dust / ink puffs that swell and fade (drawn lit, not glowing)
function feelPuff(x, y, vx, vy, r0, r1, col, a = 0.4, life = 0.4) { if (FEEL.puffs.length > 40) FEEL.puffs.shift(); FEEL.puffs.push({ x, y, vx, vy, r0, r1, col, a, life, max: life }); }
function feelFlash(x, y, r, col, k = 1, life = 0.09) { if (FEEL.flashes.length > 12) FEEL.flashes.shift(); FEEL.flashes.push({ x, y, r, col, k, life, max: life }); }
function feelKick(dx, dy) {
  FEEL.kx = clamp(FEEL.kx + dx, -5, 5); FEEL.ky = clamp(FEEL.ky + dy, -5, 5);
}
// direction of the swing: side swings kick along the facing, up/down attacks and slams kick vertically
function feelDir(A) { return A.down || A.slam ? [0, 1] : A.up ? [0, -1] : [P.face, 0]; }

// ---- impact: sparks by material, a tint by element, a light, a kick on heavies/finishers (per swing, not per target)
function feelImpact(t, x, y, A, heavy, fire) {
  const mat = feelMat(t), el = feelElement(fire), w = feelWeight(A);
  const dir = (t && t.x !== undefined ? Math.sign(t.x - P.x) : P.face) || P.face, big = heavy || (A && feelFinisher(A));
  const n = Math.round(3 + w * 3 + (big ? 2 : 0));
  if (mat === 'metal') {
    for (let i = 0; i < n + 2; i++) { const a = frand(-1.25, 0.35), s = frand(120, 260); feelSpark(x, y, dir * Math.cos(a) * s, Math.sin(a) * s, i % 3 ? '255,236,190' : '255,255,245', frand(0.12, 0.26)); }
    feelFlash(x, y, 30 + w * 14, '255,230,170', 1.1);
  } else if (mat === 'stone') {
    for (let i = 0; i < n; i++) particles.push({ x: x + frand(-3, 3), y: y + frand(-3, 3), vx: dir * frand(10, 70), vy: -frand(10, 60), g: 120, life: frand(0.35, 0.6), kind: 'dust' });
    for (let i = 0; i < 2 + (big ? 1 : 0); i++) feelPuff(x + frand(-3, 3), y + frand(-3, 3), dir * frand(10, 40), -frand(5, 20), 2, frand(6, 9), '150,140,125', 0.38, frand(0.35, 0.5));
    for (let i = 0; i < 2 + (big ? 2 : 0); i++) particles.push({ x, y, vx: dir * frand(30, 110), vy: -frand(40, 120), g: 460, life: frand(0.4, 0.7), kind: 'rock' });
    feelFlash(x, y, 22, '220,200,170', 0.6);
  } else if (mat === 'frost') {
    for (let i = 0; i < n; i++) { const a = frand(-1.4, 0.6), s = frand(70, 170); feelSpark(x, y, dir * Math.cos(a) * s, Math.sin(a) * s, '190,230,255', frand(0.14, 0.28), 300, 0.02); }
    for (let i = 0; i < 3; i++) particles.push({ x, y, vx: dir * frand(10, 60), vy: -frand(10, 50), g: 60, life: frand(0.4, 0.7), kind: 'frost' });
    feelFlash(x, y, 28, '170,215,255', 0.9);
  } else if (mat === 'ink') {
    for (let i = 0; i < n; i++) particles.push({ x: x + frand(-4, 4), y: y + frand(-4, 4), vx: dir * frand(10, 60), vy: -frand(0, 40), life: frand(0.35, 0.65), kind: 'ink' });
    feelPuff(x, y, dir * 20, -8, 2, 8, '60,30,95', 0.45, 0.35);
    feelFlash(x, y, 24, '170,120,240', 0.7);
  } else {   // flesh: a few dark drops that fall, never a fountain
    for (let i = 0; i < Math.min(6, n); i++) particles.push({ x: x + frand(-2, 2), y: y + frand(-2, 2), vx: dir * frand(20, 90), vy: -frand(20, 80), g: 420, life: frand(0.3, 0.55), kind: 'blood' });
  }
  // element / signature tint: a small burst in the weapon's own colour, and its light
  if (el !== FEEL_EL.steel) {
    for (let i = 0; i < 3 + (big ? 3 : 0); i++) particles.push({ x: x + frand(-4, 4), y: y + frand(-6, 6), vx: dir * frand(10, 70), vy: -frand(10, 60), g: 90, life: frand(0.25, 0.5), kind: frand(0, 1) < 0.7 ? el.pk : el.pk2 });
    feelFlash(x, y, 34 + (big ? 10 : 0), el.light, 1);
  }
  if (typeof WSFX !== 'undefined') WSFX.mat(mat, w);
}

// ---- hitstop by weight: tiny for daggers/whips/twins, medium for swords/katanas/spears/staves, heavy for hammers.
// Finishers, heavies and charged heavies get more; bosses slightly less; never above 0.12 s.
function feelHitstop(A) {
  const w = feelWeight(A);
  let h = 0.03 + w * 0.045;
  if (A.down) h = Math.max(h, 0.045);
  if (feelFinisher(A)) h += 0.015;
  if (A.kind === 'heavy') h += 0.02;
  if (A.kind === 'heavy' && P.charged) h += 0.025;
  if (FEEL.strikeBoss) h *= 0.8;
  return clamp(h, 0.02, 0.12);
}

// ---- wrappers
{
  // the player's own update: lets the sound wrappers tell the player's swing from a foe's in the same frame
  const _up = updatePlayer;
  updatePlayer = function (dt) { FEEL.inPlayer = true; try { return _up(dt); } finally { FEEL.inPlayer = false; } };
  // melee strikes: weight-based hitstop replaces the flat 0.05 / 0.09 set by the target (special beats above 0.1 s are kept)
  const _ps = playerStrike;
  playerStrike = function (A) {
    if (FEEL.off) return _ps.apply(this, arguments);
    const h0 = hitstop; FEEL.strikeA = A; FEEL.strikeN = 0; FEEL.strikeBoss = false;
    try { _ps.apply(this, arguments); } finally { FEEL.strikeA = null; }
    if (FEEL.hs && FEEL.strikeN > 0 && hitstop > h0 && hitstop <= 0.1001) hitstop = Math.max(h0, feelHitstop(A));
  };
  // pogo: a short vertical kick, a stretch as you spring, sparks under your feet
  const _pogo = pogo;
  pogo = function () {
    _pogo.apply(this, arguments);
    if (FEEL.off) return;
    feelKick(0, 2.6); FEEL.sq = -0.8;
    for (let i = 0; i < 6; i++) { const a = frand(0.3, Math.PI - 0.3); feelSpark(P.x, P.y + 8, Math.cos(a) * 150, Math.sin(a) * 90, '255,236,190', frand(0.1, 0.2), 300); }
    feelFlash(P.x, P.y + 8, 26, '255,230,170', 0.8);
    if (typeof WSFX !== 'undefined') WSFX.pogo();
  };
  // taking a blow: the view jolts away from it (shake itself is unchanged)
  const _hurt = hurtPlayer;
  hurtPlayer = function (dmg, dir) {
    const r = _hurt.apply(this, arguments);
    if (r === true && !FEEL.off) feelKick((dir || 0) * 2.2, -0.6);
    return r;
  };
  // camera: apply the kick on top of the normal follow; remove it before the follow so the lerp never sees it
  const _cam = updateCamera;
  updateCamera = function (dt, snap) {
    cam.x -= FEEL.ax; cam.y -= FEEL.ay; FEEL.ax = FEEL.ay = 0;
    _cam.apply(this, arguments);
    if (snap) { FEEL.kx = FEEL.ky = 0; return; }
    if (FEEL.off || state !== 'play') return;
    const s = feelShake(); FEEL.ax = FEEL.kx * s; FEEL.ay = FEEL.ky * s;
    cam.x += FEEL.ax; cam.y += FEEL.ay;
  };
  // landing squash: scale the player + weapon overlay about the feet for a few frames
  const _ds = drawSprite;
  drawSprite = function (sh, frame, x, y, face, opt) {
    if (FEEL.sq === 0 || x !== P.x || y !== P.y || !sh || !(sh.name === 'player' || sh.name.startsWith('wpn_'))) return _ds(sh, frame, x, y, face, opt);
    const k = FEEL.sq, X = Math.round(x), Y = Math.round(y);
    g.save(); g.translate(X, Y); g.scale(1 + 0.12 * k, 1 - 0.13 * k); g.translate(-X, -Y);
    try { return _ds(sh, frame, x, y, face, opt); } finally { g.restore(); }
  };
}

// ---- the swing itself (called by WSFX's swing wrapper at the exact frame the engine plays its whoosh)
function feelOnSwing(A) {
  FEEL.lastSwing = A; FEEL.swingHit = 0;
  const heavy = A.kind === 'heavy', fin = feelFinisher(A), w = feelWeight(A);
  if (heavy || fin || (A.slam)) {
    const [dx, dy] = feelDir(A), amt = (heavy ? 1.4 : 0.9) + w * 1.0 + (heavy && P.charged ? 1.2 : 0);
    feelKick(dx * amt, dy * amt);
  }
  if (heavy && P.charged) {   // charged release: a flare at the blade
    const sg = feelElement(false);
    feelFlash(P.x + P.face * 18, P.y - 18, 56, sg.light, 1.3, 0.16);
    for (let i = 0; i < 8; i++) { const a = frand(-0.9, 0.9); feelSpark(P.x + P.face * 14, P.y - 18, P.face * Math.cos(a) * frand(120, 220), Math.sin(a) * 140, i % 2 ? '255,245,220' : sg.light, frand(0.12, 0.24), 120); }
  }
}

// ---- the tip ribbon: where is the weapon's tip in this frame? (farthest solid pixel of the overlay from the shoulder; cached)
const FEEL_TIP = {};
let feelTipCv = null, feelTipCx = null;
// mode: 'a' any pixel · 'f' in front of the body · 'u' above the shoulder · 'd' below it. During the cut the blade is where
// the hitbox is, so this keeps a scabbard, a shield rim or a trailing chain from being taken for the tip.
function feelTip(ws, fi, mode = 'a') {
  const k = ws.name + ':' + fi + mode;
  if (k in FEEL_TIP) return FEEL_TIP[k];
  const img = ws.img, f = ws.frames[fi];
  if (!f) return (FEEL_TIP[k] = null);
  if (!img || !img.complete || !img.naturalWidth) return null;   // not decoded yet: try again next frame
  try {
    if (!feelTipCv) { feelTipCv = document.createElement('canvas'); feelTipCx = feelTipCv.getContext('2d', { willReadFrequently: true }); }
    if (feelTipCv.width < f.w || feelTipCv.height < f.h) { feelTipCv.width = Math.max(feelTipCv.width, f.w); feelTipCv.height = Math.max(feelTipCv.height, f.h); }
    feelTipCx.clearRect(0, 0, f.w, f.h); feelTipCx.drawImage(img, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h);
    const d = feelTipCx.getImageData(0, 0, f.w, f.h).data, cx = ws.ax, cy = ws.ay - 18;
    let best = 0, bx = 0, by = 0;
    for (let y = 0; y < f.h; y++) for (let x = 0; x < f.w; x++) {
      if (d[(y * f.w + x) * 4 + 3] < 200) continue;   // solid blade only: baked smears are translucent and never count
      if (mode === 'f' ? (x - cx) * ws.native < -2 : mode === 'u' ? y > cy : mode === 'd' ? y < cy - 4 : false) continue;
      const q = (x - cx) * (x - cx) + (y - cy) * (y - cy); if (q > best) { best = q; bx = x; by = y; }
    }
    return (FEEL_TIP[k] = best < 14 * 14 ? null : { dx: bx + 0.5 - ws.ax, dy: by + 0.5 - ws.ay });
  } catch (e) { return (FEEL_TIP[k] = null); }
}
function feelWsheet() { const ws = sheet('wpn_' + (SAVE.weapon || 'longsword')); return ws.ok ? ws : sheet('wpn_longsword'); }
function feelTrailTick() {
  const A = ATK[P.state];
  if (!A || !SETTINGS.wtrail || P.anim.i < A.active[0] - 1 || P.anim.i > A.active[1]) { FEEL.tipPrev = null; return; }
  const mode = P.anim.i < A.active[0] || A.spin || A.staffSpin ? 'a' : A.up ? 'u' : A.down ? 'd' : 'f';
  const ws = feelWsheet(), tp = feelTip(ws, P.anim.frame, mode); if (!tp) return;
  const x = ws.native === P.face ? P.x + tp.dx : P.x - tp.dx, y = P.y + tp.dy, prev = FEEL.tipPrev;
  let same = prev && prev.hs === P.hitSet;   // startAttack() makes a new hitSet: a repeated tag is still a new swing
  if (same && prev.f === P.anim.frame) return;
  const col = feelElement(P.fireT > 0).glow, px = P.x - P.face * 2, py = P.y - 18;
  const a0 = same ? Math.atan2(prev.y - py, prev.x - px) : 0, a1 = Math.atan2(y - py, x - px);
  let da = a1 - a0; while (da > Math.PI) da -= 2 * Math.PI; while (da < -Math.PI) da += 2 * Math.PI;
  // only the cut itself: no ribbon for a wind-up behind the back or a pose change that jumps more than ~110 degrees
  if (same && (Math.abs(da) > 1.9 || ((prev.x - P.x) * P.face < -6 && P.anim.i <= A.active[0]))) same = false;
  if (!same) FEEL.sid++;
  if (same) {   // sweep an arc about the shoulder between the two tips, not a straight chord
    const r0 = Math.hypot(prev.x - px, prev.y - py), r1 = Math.hypot(x - px, y - py);
    const n = Math.max(1, Math.min(6, Math.ceil(Math.abs(da) / 0.28)));
    for (let i = 1; i <= n; i++) {
      const k = i / n, a = a0 + da * k, r = r0 + (r1 - r0) * k;
      FEEL.trail.push({ x: i === n ? x : px + Math.cos(a) * r, y: i === n ? y : py + Math.sin(a) * r, t: FEEL.clock - (1 - k) * 0.03, sid: FEEL.sid, col, act: P.anim.i >= A.active[0] });
    }
  } else FEEL.trail.push({ x, y, t: FEEL.clock, sid: FEEL.sid, col, act: false });
  if (FEEL.trail.length > 64) FEEL.trail.splice(0, FEEL.trail.length - 64);
  FEEL.tipPrev = { x, y, hs: P.hitSet, f: P.anim.frame };
}
const FEEL_TRAIL_LIFE = 0.12;
const feelRGB = {};
function feelHexRGB(h) {
  if (feelRGB[h]) return feelRGB[h];
  if (h[0] !== '#') return (feelRGB[h] = h);
  const s = h.length === 4 ? h.slice(1).split('').map(q => q + q).join('') : h.slice(1, 7);
  return (feelRGB[h] = [0, 2, 4].map(i => parseInt(s.slice(i, i + 2), 16)).join(','));
}
function feelDrawTrail() {
  const T = FEEL.trail; if (T.length < 2) return;
  g.save(); g.globalCompositeOperation = 'lighter'; g.lineCap = 'round';
  for (let i = 1; i < T.length; i++) {
    const a = T[i - 1], b = T[i]; if (a.sid !== b.sid || !b.act) continue;
    const age = FEEL.clock - b.t, k = 1 - age / FEEL_TRAIL_LIFE; if (k <= 0) continue;
    const rgb = feelHexRGB(b.col);
    g.strokeStyle = `rgba(${rgb},${0.16 * k})`; g.lineWidth = 3; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    g.strokeStyle = `rgba(255,255,255,${0.42 * k * k})`; g.lineWidth = 1; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
  }
  g.restore();
}
function feelDrawSparks() {
  if (!FEEL.sparks.length) return;
  g.save(); g.globalCompositeOperation = 'lighter'; g.lineWidth = 1;
  for (const s of FEEL.sparks) {
    const k = s.life / s.max;
    g.strokeStyle = `rgba(${s.col},${Math.min(1, 0.35 + k)})`;
    g.beginPath(); g.moveTo(Math.round(s.x) + 0.5, Math.round(s.y) + 0.5); g.lineTo(Math.round(s.x - s.vx * s.len * (0.4 + k)) + 0.5, Math.round(s.y - s.vy * s.len * (0.4 + k)) + 0.5); g.stroke();
  }
  g.restore();
}

const feelDrawFx = () => { feelDrawTrail(); feelDrawSparks(); };
// ---- per frame
HOOKS.update.push(dt => {
  if (FEEL.off || !P) return;
  FEEL.clock += dt;
  // kick: snaps out, eases home (~0.15 s); squash eases back to 1
  const dk = Math.pow(0.0006, dt); FEEL.kx *= dk; FEEL.ky *= dk; if (Math.abs(FEEL.kx) < 0.05) FEEL.kx = 0; if (Math.abs(FEEL.ky) < 0.05) FEEL.ky = 0;
  if (FEEL.sq) { FEEL.sq = FEEL.sq > 0 ? Math.max(0, FEEL.sq - dt / 0.14) : Math.min(0, FEEL.sq + dt / 0.16); }
  for (const s of FEEL.sparks) { s.life -= dt; s.vy += s.g * dt; s.vx *= Math.pow(0.08, dt); s.x += s.vx * dt; s.y += s.vy * dt; }
  if (FEEL.sparks.length) FEEL.sparks = FEEL.sparks.filter(s => s.life > 0);
  for (const f of FEEL.puffs) { f.life -= dt; f.x += f.vx * dt; f.y += f.vy * dt; f.vx *= Math.pow(0.05, dt); }
  if (FEEL.puffs.length) FEEL.puffs = FEEL.puffs.filter(f => f.life > 0);
  for (const f of FEEL.flashes) f.life -= dt;
  if (FEEL.flashes.length) FEEL.flashes = FEEL.flashes.filter(f => f.life > 0);
  if (FEEL.trail.length && FEEL.clock - FEEL.trail[FEEL.trail.length - 1].t > FEEL_TRAIL_LIFE) FEEL.trail.length = 0;
  feelTrailTick();
  // airborne attacks arm the landing (plunge and the spear dive have their own impacts)
  const A = ATK[P.state];
  if (A && !P.ground) FEEL.airAtk = { down: !!A.down, w: feelWeight(A) };
  if (P.ground && !FEEL.wasGround && FEEL.airAtk && P.state !== 'dead') {
    const L = FEEL.airAtk, k = L.down ? 1 : 0.7;
    FEEL.sq = Math.max(FEEL.sq, k * (0.7 + L.w * 0.3));
    for (let i = 0; i < 8; i++) { const s = i % 2 ? 1 : -1; particles.push({ x: P.x + s * frand(2, 8), y: P.y - 1, vx: s * frand(30, 80), vy: -frand(4, 22), g: 60, life: frand(0.35, 0.6), kind: 'dust' }); }
    for (let i = 0; i < 4; i++) { const s = i % 2 ? 1 : -1; feelPuff(P.x + s * frand(3, 6), P.y - 3, s * frand(25, 55) * (i < 2 ? 1 : 0.5), -frand(2, 8), 2, frand(5, 8) * (L.down ? 1.2 : 1), '140,130,115', 0.26, frand(0.3, 0.45)); }
    if (L.down) feelKick(0, 1.6);
    if (typeof WSFX !== 'undefined') WSFX.land(L.down, L.w);
  }
  if (P.ground) FEEL.airAtk = null;
  FEEL.wasGround = P.ground;
});
// every melee hit that lands (strikes, plunge, spear dive): sparks, light, a kick on the first hit of a heavy swing
HOOKS.strike.push((t, info, A) => {
  if (FEEL.off || !A) return;
  if (FEEL.strikeA) { FEEL.strikeN++; if (t && t.boss) FEEL.strikeBoss = true; }
  feelImpact(t, info.x, info.y, A, !!info.heavy, P.fireT > 0);
  if (FEEL.swingHit++ === 0 && FEEL.strikeA && (A.kind === 'heavy' || feelFinisher(A))) {
    const [dx, dy] = feelDir(A), amt = (0.9 + feelWeight(A) * 1.4) * (t && t.boss ? 0.8 : 1);
    feelKick(dx * amt, dy * amt);
  }
});
HOOKS.render.push(() => {
  if (FEEL.off || !P) return;
  for (const f of FEEL.puffs) {
    const k = 1 - f.life / f.max, r = f.r0 + (f.r1 - f.r0) * Math.sqrt(k);
    g.fillStyle = `rgba(${f.col},${f.a * (1 - k)})`; g.beginPath(); g.arc(Math.round(f.x), Math.round(f.y), r, 0, 6.2832); g.fill();
  }
  if (FEEL.trail.length > 1 || FEEL.sparks.length) drawGlow(feelDrawFx);
  for (const f of FEEL.flashes) addLight(f.x, f.y, f.r, f.col, f.k * (f.life / f.max));
});
HOOKS.enter.push(() => { FEEL.sparks = []; FEEL.puffs = []; FEEL.flashes = []; FEEL.trail = []; FEEL.tipPrev = null; FEEL.kx = FEEL.ky = 0; FEEL.sq = 0; FEEL.airAtk = null; FEEL.wasGround = true; });
if (typeof window !== 'undefined' && window.__game) window.__game.feel = { FEEL, feelTip, feelMat, feelWeight, feelHitstop, ev: s => eval(s) };   // headless tests (tools/shots/wc)

// ------------------------------------------------------------------ WM: Staff (A9) + Whip (A10)   (v14 reach pass: docs/revamp2/reach.md)
// ================================================================== Staff: master of the air
// I vaults (350 ms, ~2.5 tiles up and forward, invulnerable 0.2 s, 15 stam) -- not an attack. J / K pressed at any time
// during the vault are kept and played the moment it can be left (0.22 s): I -> J is the vault kick, I -> K the aerial spin,
// I -> down J the dive kick. Combo hits strike in front and slightly behind. Each air hit adds a momentum stack (max 3,
// +8% each), kept until 0.5 s after landing (the first ground swing keeps them). The staff's spinning air moves glide
// (the fall is slowed while the staff turns), so a vault string fits in one trip. Air K = aerial spin; air down J = dive
// kick (its bounce refunds one air attack, once per trip through the air).
// New in v14: J J K pole launcher (into the air), I -> J vault kick, air J J cartwheel, dive kick -> K pole drop (II).
// (air down K is the Cinder Slam technique for every weapon, so the pole drop hangs off the dive kick instead)
// Mastery: roll vault (II), pole drop (II), spin finisher (III), double vault (IV), gale (V).
const ST_SPIN_STAM = 24;
function stSpinStam() { return ST_SPIN_STAM * ((typeof skillOn === 'function' && skillOn('m_staff')) ? 55 / 80 : 1); }   // Whirling Staff: cheaper
function stVault(fromAir) {
  if (P.st <= 0) return false;
  spend(15); P.mvInv = 0.2; P.vaultT = 0; P.vaultAir = !!fromAir; P.vaultUp = false; P.vaultQ = null; P.mvQ = null;
  setP('vault', pHas('st_vault') ? 'st_vault' : 'double_jump', false, pHas('st_vault') ? 1 : 0.8);
  if (!fromAir) spawnFx('dust', P.x, P.y, P.face);
  else { P.vy = -240; P.vx = P.face * 110; P.ground = false; mvSpark(P.x, P.y + 4, 6, '255,236,190', 120); }
  sfx.jump(); return true;
}
// what a press kept during the vault plays (q: { b, up, down } from the moment it was pressed, or held now)
function stVaultGo(q) {
  const ax = inputX(); if (ax) P.face = ax;
  const dn = q.down || held.has('down'), up = q.up || held.has('up');
  return mvStart(q.b === 'J' ? (dn ? 'st_down' : up ? 'st_up' : 'st_vkick') : 'st_aspin');
}
MV_STATES.vault = (dt, ax, grav) => {
  P.vaultT += dt;
  if (!P.vaultQ) {   // latch J / K for the whole vault (a press in the plant used to be lost)
    if (peek('attack')) { take('attack'); P.vaultQ = { b: 'J', up: held.has('up'), down: held.has('down') }; }
    else if (peek('heavy')) { take('heavy'); P.vaultQ = { b: 'K', down: held.has('down') }; }
  }
  if (!P.vaultAir && P.vaultT < 0.13) { P.vx = approach(P.vx, 0, 900 * dt); grav(); return; }   // the staff plants first
  if (!P.vaultAir && !P.vaultUp) { P.vaultUp = true; P.vy = -235; P.vx = P.face * 115; P.ground = false; }
  if (ax) P.vx = approach(P.vx, ax * 125, 400 * dt);
  grav();
  if (P.vaultQ && P.vaultT >= 0.22) {
    const q = P.vaultQ; P.vaultQ = null; P.vaultUp = false;
    setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground);
    if (!P.ground && stVaultGo(q)) return;
    if (P.ground) { buffered.set(q.b === 'J' ? 'attack' : 'heavy', performance.now()); return; }
  }
  if (P.vaultT >= 0.35) { P.vaultUp = false; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
};
MV_STATES.vault.inv = () => false;
function stMomentumHit(A) {   // +1 stack per airborne move that connects (once per move)
  if (P.ground) return;   // only hits while airborne build momentum
  if (P.momMove === P.hitSet) return; P.momMove = P.hitSet;
  if ((P.mom || 0) < 3) { P.mom = (P.mom || 0) + 1; tone(880 + P.mom * 220, 0.12, 0.04, 'triangle', 1.4); }
  P.momLand = null;
}
// IV: the foe (or boss) whose head the double vault can push off
function stDvFoe() {
  return targets().find(t => !t.prop && !t.boss && t.alive !== false && Math.abs(t.x - P.x) < 34 && P.y < t.y + 4 && P.y > t.y - 70)
    || (boss && boss.active && boss.alive && Math.abs(boss.x - P.x) < 50 && P.y < boss.y ? boss : null);
}
function stDoubleVault() {
  if (!mvHas(4) || P.dvUsed || P.st <= 0 || P.ground || !stDvFoe()) return false;
  P.dvUsed = true; P.airN = 0; P.airLock = false; return stVault(true);
}
// the staff's air moves: a glide (the fall is capped at `cap` px/s while the staff turns) and, at IV, the double vault
// cancels them once their hit is out (the I press used to be lost inside an air move)
function stAir(d, cap) {
  const on = d.on || {}, up0 = on.update;
  d.on = { ...on, update(dt, A, ax, grav) {
    if (up0) { const r = up0(dt, A, ax, grav); if (r === 'stop') return r; }
    if (!P.ground && P.mvT >= d.wind + 40 && mvHas(4) && !P.dvUsed && peek('parry') && stDvFoe()) { take('parry'); P.mvQ = null; if (stDoubleVault()) return 'stop'; }
  } };
  if (cap) d.move = (dt, A, ax, grav) => {
    const t = P.mvT;
    if (d.drive && t >= d.wind - 90 && t < d.wind + 60) P.vx = P.face * d.drive;   // the vault kick drives forward through the hit
    else P.vx = approach(P.vx, ax * MAXV * 0.8, 500 * dt);
    grav();
    if (t < d.total - 80 && P.vy > cap) P.vy = approach(P.vy, cap, 1800 * dt);
  };
  return d;
}
// II: the pole drop (dive kick -> K) -- a short hang, then straight down on the staff's point; a two-sided shock where it lands (or on a
// foe's head, bouncing off). Uses the smash limit like every plunge, not the air-attack limit.
function stPdropImpact(A, midair) {
  const d = A.mv; P.pdLand = true; P.mvT = d.wind; smashLanded();
  const box = rect(P.x - 36, P.y - (midair ? 30 : 32), P.x + 36, P.y + (midair ? 26 : 2));
  P.hitSet = new Set(); P.mvHitK = 0;
  mvStrikeAt(box, d.dmg, d.poise, { A, kind: 'heavy', big: true, onHit: (t, info) => { if (!t.prop) mvOnHit(t, info, A, { tip: false }); } });
  shake = Math.max(shake, 6); sfx.boom(); hitstop = Math.max(hitstop, 0.06);
  if (!midair) { spawnFx('shockwave', P.x, P.y, 1); for (const s of [-1, 1]) spawnFx('dust', P.x + s * 18, P.y, s); for (let i = 0; i < 14; i++) particles.push({ x: P.x + rand(-34, 34), y: P.y - 2, vx: rand(-90, 90), vy: -rand(30, 120), g: 320, life: 0.6, kind: 'dust' }); }
  else { P.vy = -210; P.ground = false; spawnFx(fxOr('pogo', 'hit'), P.x, P.y + 6, P.face); }
}
mvRegister('staff', {
  light: ['st_1', 'st_2', 'st_3', 'st_4'], K: 'st_heavy', up: 'st_up', air: 'st_air', down: 'st_down',
  plunge: { dmg: 1.4, poise: 40, stam: 16 },
  rollJ: 'st_lowsweep',
  onK(ax) {
    if (mvHas(5) && (P.mom || 0) >= 3) return mvStart('st_gale');
    return mvStart('st_heavy');
  },
  onAirK(ax) {   // the aerial spin replaces the plunge (and counts toward the air limit like any air attack)
    take('heavy'); if (ax) P.face = ax;
    return mvStart('st_aspin');
  },
  onI(ax) {
    if (P.ground) { take('parry'); if (ax) P.face = ax; return stVault(false); }
    // IV: double vault -- off a foe's head in the air, once per jump; refunds the air attacks
    if (mvHas(4) && !P.dvUsed && P.st > 0 && stDvFoe()) { take('parry'); return stDoubleVault(); }
    return false;
  },
  dodgeUpdate(dt, g) { if (mvHas(2) && P.ground && peek('parry') && g.t >= 80) { take('parry'); P.dg = null; stVault(false); return true; } },   // II: roll vault
  hitMod(c) { if (P.mom > 0) c.mul *= 1 + 0.08 * P.mom; },
  onHit(t, info, A) {
    if (!t || t.prop) return; stMomentumHit(A);
    // the dive kick's bounce refunds one air attack -- once per trip through the air (it used to refund every bounce: an endless pogo)
    if (A.mv && A.mv.id === 'st_down' && !P.stRefund && !P.stRefTrip) { P.stRefund = true; P.stRefTrip = true; airRefund(); }
  },
  started(A) {
    P.stRefund = false;
    if (P.ground && P.mom > 0) { if (P.momLand !== null && P.momLand !== undefined && P.clk - P.momLand <= 0.5) P.momKeep = A.mv.id; }
  },
  landed() { P.dvUsed = false; P.stRefTrip = false; if (P.mom > 0) P.momLand = P.clk; },
  tick(dt) {
    if (P.mom > 0 && P.ground && P.momLand != null && P.clk - P.momLand > 0.5) {
      const A = ATK[P.state]; if (!(A && A.mv && P.momKeep === A.mv.id)) { P.mom = 0; P.momKeep = null; P.momLand = null; }
    }
  },
  interrupted() { P.vaultQ = null; },
  render() {
    for (let i = 0; i < (P.mom || 0); i++) {   // momentum: up to 3 motes orbiting the staff hand
      const a = P.clk * 5 + i * 2.094, x = P.x + Math.cos(a) * 11, y = P.y - 18 + Math.sin(a) * 5;
      addLight(x, y, 9, '160,220,255', 0.7);
      drawGlow(() => { g.fillStyle = 'rgba(190,230,255,0.95)'; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2); });
      if (Math.random() < 0.35) particles.push({ x, y, vx: 0, vy: -10, life: 0.25, kind: 'mote' });
    }
    if (P.state === 'vault' && P.vaultT < 0.2) addLight(P.x, P.y - 14, 20, '220,240,255', 0.4);
    if (P.state === 'st_pdrop' && !P.pdLand && P.mvT > 100) addLight(P.x, P.y + 4, 16, '200,230,255', 0.5);
  },
  hud(x) { for (let i = 0; i < 3; i++) mvHudPip(x + 3 + i * 5, 22, i < (P.mom || 0), '#a8dcff'); },
  unlocks: [
    { rank: 2, id: 'st_rollvault', name: 'Roll vault', input: 'L → I', desc: 'Vault straight out of a roll.' },
    { rank: 2, id: 'st_pdrop', name: 'Pole drop', input: 'air ↓J → K', desc: 'Off the dive kick, drop on the staff point: 1.4, a shock on both sides.' },
    { rank: 3, id: 'st_aspin2', name: 'Spin finisher', input: 'air K → K', desc: 'A second aerial spin: 1.8 dmg, uses one air attack.' },
    { rank: 4, id: 'st_doublevault', name: 'Double vault', input: 'I in the air near a foe', desc: "Vault off the foe's head; refunds the air attacks once per jump." },
    { rank: 5, id: 'st_gale', name: 'Gale', input: 'K with 3 momentum stacks', desc: 'The spin becomes a slow tornado: 3 hits of 0.6 on what stands in it.' },
  ],
  combos: [
    { rank: 1, name: 'Strike · Butt strike · Low sweep · Overhead', input: 'J J J J', desc: 'Both ends: every step also hits just behind you. The sweep trips.' },
    { rank: 1, name: 'Pole launcher', input: 'J J K', desc: 'Upswing that launches small foes and carries you into the air.' },
    { rank: 1, name: 'Spin', input: 'K', desc: 'Two full turns at the waist, front and back. 24 stamina.' },
    { rank: 1, name: 'Vault', input: 'I', desc: 'Spring off the staff, up and forward. Invulnerable at the start.' },
    { rank: 1, name: 'Vault kick', input: 'I → J', desc: 'A flying kick off the planted staff at the top of the vault.' },
    { rank: 1, name: 'Vault spin', input: 'I → K', desc: 'The aerial spin straight out of the vault.' },
    { rank: 1, name: 'Low sweep', input: 'L → J', desc: 'Out of a roll: a spinning sweep at the ankles, both sides.' },
    { rank: 1, name: 'Aerial strike', input: 'air J', desc: 'An air wheel. Each air hit adds a momentum stack (+8%, max 3).' },
    { rank: 1, name: 'Cartwheel', input: 'air J J', desc: 'Turn over the staff: the butt behind you, then the head in front.' },
    { rank: 1, name: 'Aerial spin', input: 'air K', desc: 'A gliding spin round the waist, front and back.' },
    { rank: 1, name: 'Rising twirl', input: '↑J', desc: 'The staff wheels overhead: for fliers.' },
    { rank: 1, name: 'Dive kick', input: 'air ↓J', desc: 'Pogo off a foe. The first bounce of a jump refunds an air attack.' },
    { rank: 2, name: 'Roll vault', input: 'L → I', desc: 'Vault straight out of a roll.' },
    { rank: 2, name: 'Pole drop', input: 'air ↓J → K', desc: 'Off the dive kick, drop on the staff point: a shock on both sides.' },
    { rank: 3, name: 'Spin finisher', input: 'air K → K', desc: 'A second, wider aerial spin ending in a chop.' },
    { rank: 4, name: 'Double vault', input: 'I in the air near a foe', desc: 'Vault off its head (cancels an air move); refunds the air attacks.' },
    { rank: 5, name: 'Gale', input: 'K with 3 momentum', desc: 'Spend the momentum: a slow tornado strikes 3 times.' },
  ],
}, {
  st_1: { tags: ['st_1'], dmg: 0.9, poise: 12, stam: 10, wind: 140, total: 360, step: 0, back: 14, fx: 'slash_air', next: { J: 'st_2' } },
  st_2: { tags: ['st_2'], dmg: 0.9, poise: 12, stam: 10, wind: 140, total: 360, step: 1, back: 30,
    next: { J: 'st_3', K: () => (mvHas(5) && (P.mom || 0) >= 3 ? '@K' : 'st_rise') } },
  st_3: { tags: ['st_3'], dmg: 0.9, poise: 16, stam: 11, wind: 160, total: 380, step: 2, back: 14, reel: true, ys: [-14, 0], next: { J: 'st_4' } },
  st_4: { tags: ['st_4'], dmg: 1.5, poise: 40, stam: 14, wind: 240, total: 560, step: 3, back: 14, fin: true, fx: 'heavy' },
  st_heavy: { tags: ['st_heavy'], kind: 'heavy', staffSpin: true, hits: [0.8, 0.8], gap: 180, poise: 60, stam: () => stSpinStam(), wind: 220, total: 640, spin: true, reach: 40, backReach: 40, fin: true },
  st_gale: { tags: ['st_gale', 'st_heavy'], kind: 'heavy', rank: 5, noHit: true, dmg: 0.6, poise: 20, stam: 16, wind: 220, total: 640,
    on: { swing() { P.mom = 0; stGale(); } } },
  st_lowsweep: { tags: ['st_lowsweep', 'st_3'], dmg: 1.1, poise: 20, stam: 10, wind: 140, total: 380, back: 14, reel: true, ys: [-14, 0], next: { J: 'st_4' } },
  // v14: J J K -- plant and heave upward: small foes are launched, and you ride the staff up into the air
  st_rise: { tags: ['st_rise', 'st_up'], dmg: 1.0, poise: 28, stam: 12, wind: 170, total: 470, airOk: true, launch: 220, reach: 32, back: 10, ys: [-50, -2],
    on: { start() { P.stHop = false; }, update() { if (!P.stHop && P.mvT >= 200 && P.ground) { P.stHop = true; P.vy = -255; P.vx = P.face * 35; P.ground = false; spawnFx('dust', P.x, P.y, P.face); } } } },
  st_air: stAir({ tags: ['st_air'], air: true, dmg: 0.9, poise: 14, stam: 10, wind: 120, total: 320,
    next: { J: q => (held.has('down') ? 'st_down' : q.up ? 'st_up' : 'st_air2') } }, 0),
  // v14: air J J -- the cartwheel: turn over the staff, the butt strikes behind, then the head in front
  st_air2: stAir({ tags: ['st_air2', 'st_air'], air: true, hits: [0.5, 0.6], gap: 120, poise: 18, stam: 11, wind: 120, total: 400, spin: true, reach: 34, backReach: 30 }, 90),
  // v14: I -> J -- the vault kick: both legs swung through off the planted pole
  st_vkick: stAir({ tags: ['st_vkick', 'st_air'], air: true, dmg: 1.1, poise: 24, stam: 10, wind: 110, total: 360, drive: 150, reach: 30, ys: [-30, 4] }, 50),
  st_aspin: stAir({ tags: ['st_aspin', 'st_air'], air: true, kind: 'heavy', dmg: 1.4, poise: 40, stam: 16, wind: 180, total: 460, spin: true, reach: 38, ys: [-38, 2],
    next: { K: () => (mvHas(3) && !P.ground ? 'st_aspin2' : null) } }, 60),
  st_aspin2: stAir({ tags: ['st_aspin2', 'st_aspin', 'st_air'], air: true, kind: 'heavy', rank: 3, dmg: 1.8, poise: 45, stam: 16, wind: 120, total: 540, spin: true, reach: 40, ys: [-38, 2], fin: true,
    can: () => !P.airLock }, 60),
  st_up: stAir({ tags: ['st_twirl_up', 'st_up'], up: true, dmg: 0.9, poise: 14, stam: 10, wind: 140, total: 340 }, 0),
  st_down: stAir({ tags: ['st_divekick', 'st_down'], down: true, dmg: 1.0, poise: 30, stam: 10, wind: 100, total: 300,
    next: { K: () => (mvHas(2) && !P.ground ? 'st_pdrop' : null) } }, 0),
  // v14 (II): dive kick -> K -- the pole drop
  st_pdrop: { tags: ['st_pdrop', 'st_down'], kind: 'heavy', rank: 2, noHit: true, commit: true, dmg: 1.4, poise: 40, stam: 16, wind: 150, total: 520, fin: true, keepFace: true,
    can: () => !P.ground && smashReady(),
    on: { start() { smashStart(); P.pdLand = false; },
      update(dt, A) { if (!P.pdLand && P.mvT >= 110) { P.mvT = Math.min(P.mvT, A.mv.wind - 1); P.mvHitK = 0; } } },   // hold the dive pose until it lands
    move(dt, A, ax, grav) {
      const d = A.mv;
      if (P.pdLand) { if (P.ground) { P.vx *= Math.pow(0.0002, dt); } else P.vx = approach(P.vx, ax * MAXV * 0.5, 400 * dt); grav(); return; }
      if (P.mvT < 110) { P.vx *= Math.pow(0.02, dt); P.vy = approach(Math.min(P.vy, 40), 0, 1600 * dt); return; }   // the hang: raise the staff
      P.vx = 0; P.vy = 430;
      if (P.ground) return stPdropImpact(A, false);
      const r = rect(P.x - 9, P.y - 6, P.x + 9, P.y + 10);
      if (targets().some(t => { const hb = hbOf(t); return hb && !t.prop && t.alive !== false && overlap(r, hb); })) stPdropImpact(A, true);
    } },
});
// V: gale -- a slow tornado that drifts forward and strikes 3 times (0.6 each): a foe standing in front takes all three
const ST_GALES = [];
function stGale() {
  ST_GALES.push({ x: P.x + P.face * 20, y: P.y, d: P.face, t: 0, n: 0 });
  sfx.heavySwing(); shake = Math.max(shake, 4);
}
HOOKS.enter.push(() => { ST_GALES.length = 0; });
HOOKS.update.push(dt => {
  for (const gl of ST_GALES) {
    gl.t += dt; gl.x += gl.d * 50 * dt;
    if (gl.t >= 0.12 + gl.n * 0.26 && gl.n < 3) { gl.n++; mvStrikeAt(rect(gl.x - 18, gl.y - 42, gl.x + 18, gl.y + 2), 0.6, 20, { A: ATK.st_gale, kind: 'heavy' }); tone(300 + gl.n * 80, 0.15, 0.04, 'sawtooth', 0.4); }
    if (Math.random() < 0.9) { const a = rand(0, 6.283); particles.push({ x: gl.x + Math.cos(a) * rand(4, 14), y: gl.y - rand(0, 38), vx: -Math.sin(a) * 60, vy: -rand(10, 40), life: 0.3, kind: 'dust' }); }
  }
  for (let i = ST_GALES.length - 1; i >= 0; i--) if (ST_GALES[i].t > 0.95) ST_GALES.splice(i, 1);
});
HOOKS.render.push(() => { for (const gl of ST_GALES) { const k = Math.min(1, gl.t / 0.1, (0.95 - gl.t) / 0.2); addLight(gl.x, gl.y - 20, 30, '200,230,255', 0.6 * k); g.strokeStyle = `rgba(210,235,255,${0.45 * k})`; g.lineWidth = 1; for (let j = 0; j < 4; j++) { const r = 5 + j * 3, a = gl.t * 14 + j; g.beginPath(); g.ellipse(Math.round(gl.x), Math.round(gl.y - 6 - j * 9), r + 2, 2.5, 0, a, a + 4.2); g.stroke(); } } });

// ================================================================== Whip: control the space
// The tip: the last 30% of a lash's reach deals x1.3 and fills the crack meter (+10 light, +20 heavy). The lash past the
// sprite's own reach is drawn by the engine (whLashFx), its tip zone bright, so you can see where the tip lands. At 100 the
// next K is a thunderclap (2.5, x1.3 at the tip, 90 poise, a small blast and a stagger). I grapples (64 px, 2 s cooldown):
// small foes are pulled in and stunned briefly, large foes and hook rings pull you; never bosses.
// New in v14: J J K trip lash, L -> K coil spin (the close-range answer: shoves small foes out to the tip), air J J skyfall
// crack, grapple -> J reel kick (II). Mastery: snap counter (II), reel kick (II), grapple slam (III), double crack (IV),
// thousand lashes (V).
const WH_REACH = MV_SR * 2;   // 80 px
const WH_TIP = 0.7;           // the tip zone: the last 30% of the reach
function whTip(c) {
  const d = c.d, hb = c.hb;
  if (!d.tip) return;
  let dist, front;
  if (c.A.up) { dist = P.y - hb.y1; front = -c.A.ys[0]; }
  else { dist = P.face > 0 ? hb.x0 - P.x : P.x - hb.x1; front = c.A.reach[1]; }
  if (dist >= front * WH_TIP) { c.tip = true; c.mul *= 1.3; }
  else if (d.tipOnly) c.skip = true;
}
function whTipFx(x, y, big) {   // the tip spark: a bright crack of light where the lash snaps
  sfx.parry(); if (typeof feelFlash === 'function') feelFlash(x, y, big ? 40 : 28, '255,245,220', 1.3, 0.1);
  mvSpark(x, y, big ? 12 : 7, '255,245,220', big ? 220 : 160);
  for (let i = 0; i < 4; i++) particles.push({ x, y, vx: P.face * rand(20, 90), vy: -rand(10, 70), g: 200, life: 0.3, kind: 'spark' });
}
function whSmall(t) { return t && !t.prop && !t.boss && t !== boss && t.alive !== false && !(t.cfg && (t.cfg.elite || t.cfg.flying)) && !whLarge(t); }
// shove a small foe out along the floor to `to` px from you (the coil spin and the reel kick put it back at the tip)
function whShove(t, to) {
  if (!whSmall(t)) return;
  const dir = t.x >= P.x ? 1 : -1, x0 = t.x, goal = P.x + dir * to;
  if ((goal - x0) * dir <= 0) return;
  let gx = x0; for (let x = x0; (goal - x) * dir > 0; x += dir * 4) { if (solidAtPx(x + dir * 6, t.y - 6) || solidAtPx(x + dir * 6, t.y - 20)) break; gx = x; }
  wfx({ life: 0.2, update() { if (t.alive === false) return false; t.x = x0 + (gx - x0) * Math.min(1, this.t / 0.18); if (t.vx !== undefined) t.vx = 0; } });
  for (let i = 0; i < 6; i++) particles.push({ x: t.x, y: t.y - 2, vx: dir * rand(30, 90), vy: -rand(10, 50), g: 300, life: 0.4, kind: 'dust' });
}
// hold checks: the hold has to be continuous from the move's start (a mash tap used to fall inside the check's 50 ms window)
function whHoldStart(btn) { P.whHold = held.has(btn); }
function whHolding(btn) { if (!held.has(btn)) P.whHold = false; return !!P.whHold; }
mvRegister('whip', {
  light: ['wh_1', 'wh_2', 'wh_3'], K: 'wh_heavy', up: 'wh_up', air: 'wh_air', down: 'wh_down',
  plunge: { dmg: 1.3, poise: 50, stam: 16 },
  rollJ: 'wh_retreat',
  rollK: () => mvStart('wh_coil'),
  onJ(ax) {   // II: grapple -> J, the reel kick (right after a pull, or on arriving at a large foe)
    if (mvHas(2) && P.whPull && P.clk - P.whPull.t < 0.7) { take('attack'); if (ax) P.face = ax; P.whPull = null; return mvStart('wh_reelkick'); }
    return false;
  },
  onK(ax) {
    if ((P.crack || 0) >= 100) return mvStart('wh_thunder');
    if (P.whPull && P.whPull.small && P.clk - P.whPull.t < 0.7 && mvHas(3) && P.whPull.t2 && P.whPull.t2.alive !== false) { P.whPull = null; return mvStart('wh_slam'); }   // III: grapple -> K
    return mvStart('wh_heavy');
  },
  onI(ax) {
    if (P.st <= 0) return false;
    take('parry'); if (ax) P.face = ax;
    const grap = !((P.whCd || 0) > 0);
    // II: a blow within 150 ms of the press is snapped away. Arming it without a grapple costs 6 stamina and it can't
    // be re-armed for 0.5 s (mashing I used to keep it armed all the time, for free)
    if (mvHas(2) && !(P.snapCd > 0)) { P.snapT = 0.15; P.snapCd = 0.5; if (!grap) { spend(6); mvStar(P.x + P.face * 8, P.y - 18, 3, '235,240,255', 0.9); sfx.swing(); } }
    if (!grap) { if (!(P.snapT > 0)) sfx.deny(); return true; }
    spend(14); P.whCd = 2; whGrapple(); return true;
  },
  hurt(c) {
    if (P.snapT > 0 && !c.negate && c.opt && (c.opt.src || c.id !== undefined)) {
      c.negate = true; P.snapT = 0; mvGain('counter');
      const s = c.opt.src; if (c.dir) P.face = -c.dir;
      sfx.parry(); hitstop = Math.max(hitstop, 0.1); whTipFx(P.x + P.face * 40, P.y - 18, true);
      if (s && s.alive !== false) {
        if (s.boss || s === boss) { if (typeof s.stance === 'number' && !(s.stanceImmune > 0) && s.state !== 'stagger') { s.stance += 60; if (s.stance >= s.stanceMax && s.stagger && (!s.canStagger || s.canStagger())) s.stagger(); } }
        else if (s.breakStance && !(s.cfg && s.cfg.elite) && s.state !== 'stagger') s.breakStance();
      }
      mvStart('wh_snap');
    }
  },
  hitMod(c) { whTip(c); },
  onHit(t, info, A, c) {
    if (!c || !c.tip || !t || t.prop) return;
    const big = A.kind === 'heavy';
    whTipFx(info.x, info.y, big);
    if (A.mv.id !== 'wh_thunder') {
      const was = P.crack || 0; P.crack = Math.min(100, was + (big ? 20 : 10));
      if (was < 100 && P.crack >= 100) { tone(1568, 0.3, 0.06, 'triangle', 1.6); sfx.glint(); }
    }
  },
  tick(dt) { P.whCd = Math.max(0, (P.whCd || 0) - dt); P.snapT = Math.max(0, (P.snapT || 0) - dt); P.snapCd = Math.max(0, (P.snapCd || 0) - dt); },
  render() {
    if ((P.crack || 0) >= 100) { mvStar(P.x + P.face * 9, P.y - 17, 2 + 1.5 * Math.abs(Math.sin(P.clk * 9)), '210,225,255', 0.9); addLight(P.x + P.face * 8, P.y - 18, 20, '200,220,255', 0.6 + 0.3 * Math.sin(P.clk * 16)); if (Math.random() < 0.3) particles.push({ x: P.x + P.face * rand(4, 16), y: P.y - rand(10, 26), vx: 0, vy: -rand(10, 30), life: 0.25, kind: 'spark' }); }
    const gp = P.whGrap;
    if (gp && (P.state === 'grapple' || P.clk - gp.t < 0.2)) {   // the chain beyond the frame
      const tx = gp.x, ty = gp.y; g.strokeStyle = 'rgba(190,190,205,0.9)'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(Math.round(P.x + P.face * 8) + 0.5, Math.round(P.y - 18) + 0.5); g.lineTo(Math.round(tx) + 0.5, Math.round(ty) + 0.5); g.stroke();
      addLight(tx, ty, 10, '255,240,210', 0.6);
    }
    whLashFx();
  },
  hud(x) {
    mvHudBar(x, 21, 34, 2.5, (P.crack || 0) / 100, (P.crack || 0) >= 100 ? '#cfe2ff' : '#8aa0c8');
    if ((P.whCd || 0) > 0) mvHudBar(x, 25, 34 * P.whCd / 2, 1, 1, 'rgba(200,200,215,0.5)', 'rgba(0,0,0,0)');
  },
  unlocks: [
    { rank: 2, id: 'wh_snap', name: 'Snap counter', input: 'I within 150 ms of a hit', desc: 'Lashes the attacker out of its move: the hit is negated, small foes stagger, a boss takes +60 stance.' },
    { rank: 2, id: 'wh_reelkick', name: 'Reel kick', input: 'grapple → J', desc: 'Kick the foe you just reeled in back out to the tip: 1.2 dmg.' },
    { rank: 3, id: 'wh_slam', name: 'Grapple slam', input: 'grapple → K', desc: 'Pull a small foe in and slam it: 1.6 dmg, stunned.' },
    { rank: 4, id: 'wh_double', name: 'Double crack', input: 'K → K', desc: 'A follow-up crack: 1.4 then 1.8, both with tip bonuses.' },
    { rank: 5, id: 'wh_thousand', name: 'Thousand lashes', input: 'hold J', desc: "A held flurry: 8 × 0.45, tip-only, so it's a spacing test." },
  ],
  combos: [
    { rank: 1, name: 'Lash · Lash II · Whirl lash', input: 'J J J', desc: 'Twice sword reach. The last 30% of the lash is the tip: ×1.3.' },
    { rank: 1, name: 'Trip lash', input: 'J J K', desc: 'A low crack along the floor. Tipped, it trips small foes.' },
    { rank: 1, name: 'Heavy crack', input: 'K', desc: 'Fling the chain straight out. A tip hit fills the crack meter.' },
    { rank: 1, name: 'Overhead crack', input: 'hold K', desc: 'Whirl it overhead, release at full: 2.4× sword reach.' },
    { rank: 1, name: 'Thunderclap', input: 'K at 100 crack', desc: '2.5 (3.25 at the tip), 90 poise, a blast and a stagger.' },
    { rank: 1, name: 'Grapple', input: 'I', desc: 'Small foes are reeled in; large foes and hook rings pull you. 2 s.' },
    { rank: 1, name: 'Retreat lash', input: 'L → J', desc: 'Back off 40 px and crack forward: the tip lands where you were.' },
    { rank: 1, name: 'Coil spin', input: 'L → K', desc: 'Out of a roll, the chain whirls round you: shoves small foes to the tip.' },
    { rank: 1, name: 'Circular lash', input: 'air J', desc: 'A full circle round the body, front and back.' },
    { rank: 1, name: 'Skyfall crack', input: 'air J J', desc: 'From the circle, a long crack down to the floor ahead.' },
    { rank: 1, name: 'Vertical crack', input: '↑J', desc: 'The tip cracks straight overhead: for fliers.' },
    { rank: 1, name: 'Down crack', input: 'air ↓J', desc: 'Pogo off a foe on a long box below.' },
    { rank: 2, name: 'Snap counter', input: 'I just before a hit', desc: 'Negate it and lash the attacker out of its move. 6 stamina.' },
    { rank: 2, name: 'Reel kick', input: 'grapple → J', desc: 'Kick the foe you reeled in back out to the tip.' },
    { rank: 3, name: 'Grapple slam', input: 'grapple → K', desc: 'Haul the catch overhead and slam it: 1.6 dmg, stunned.' },
    { rank: 4, name: 'Double crack', input: 'K → K', desc: 'A rising backhand into a second, harder crack.' },
    { rank: 5, name: 'Thousand lashes', input: 'hold J', desc: 'Keep J held through the lash: 8 tip-only cracks.' },
  ],
}, {
  wh_1: { tags: ['wh_1'], dmg: 0.8, poise: 8, stam: 9, wind: 160, total: 400, step: 0, reach: WH_REACH, tip: true, next: { J: 'wh_2' },
    on: { start() { whHoldStart('attack'); }, update() { if (whHolding('attack') && mvHas(5) && P.mvT >= 240) { mvStart('wh_thousand'); return 'stop'; } } } },
  wh_2: { tags: ['wh_2'], dmg: 0.8, poise: 8, stam: 9, wind: 160, total: 400, step: 1, reach: WH_REACH, tip: true,
    next: { J: 'wh_3', K: () => ((P.crack || 0) >= 100 ? '@K' : 'wh_trip') } },
  wh_3: { tags: ['wh_3'], dmg: 1.1, poise: 20, stam: 14, wind: 260, total: 620, step: 2, fin: true, spin: true, reach: WH_REACH },   // the whirl spans the whole lash, front and back
  wh_heavy: { tags: ['wh_heavy'], kind: 'heavy', dmg: 1.4, poise: 30, stam: 18, wind: 300, total: 680, reach: WH_REACH, tip: true,
    next: { K: () => (mvHas(4) ? 'wh_double' : '@K') },
    on: { start() { whHoldStart('heavy'); }, update() { if (whHolding('heavy') && P.mvT >= 180 && P.mvT < 285 && !P.mvO.noHold) { mvStart('wh_overhead_hold', { cost: 0 }); return 'stop'; } } } },
  wh_overhead_hold: { tags: ['wh_overhead_hold', 'wh_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    on: { update(dt) {
      P.vx *= Math.pow(0.05, dt); P.charge = P.mvT / 1000;
      if (P.mvT >= 380 && !P.whFull) { P.whFull = true; sfx.glint(); spawnFx('telegraph', P.x, P.y - 36, P.face); }
      if (!held.has('heavy') || P.mvT > 1800) { const f = P.whFull; P.whFull = false; if (f) mvStart('wh_overhead', { cost: 6, charged: true }); else mvStart('wh_heavy', { cost: 0, t0: 180, noHold: true }); return 'stop'; }
    }, start() { P.whFull = false; } } },
  wh_overhead: { tags: ['wh_overhead', 'wh_heavy'], kind: 'heavy', dmg: 2.0, poise: 45, stam: 24, wind: 300, total: 600, reach: MV_SR * 2.4, tip: true, fin: true },
  // the thunderclap pays for spacing now: 2.5, x1.3 at the tip (it was 3.2 from anywhere, the top sustained route in the game)
  wh_thunder: { tags: ['wh_thunder', 'wh_heavy'], kind: 'heavy', dmg: 2.5, poise: 90, stam: 20, wind: 300, total: 700, reach: WH_REACH, tip: true, fin: true,
    on: {
      start() { P.crack = 0; },
      swing(A) {   // the blast at the tip
        const tx = P.x + P.face * (WH_REACH - 10), ty = P.y - 18;
        whTipFx(tx, ty, true); flashScreen = Math.max(flashScreen, 0.12); shake = Math.max(shake, 6); sfx.boom();
        spawnFx('shockwave', tx, P.y, 1);
      },
      hit(t) { if (!t.boss && t.breakStance && !(t.cfg && t.cfg.elite) && t.state !== 'stagger') t.breakStance(); },
    } },
  wh_double: { tags: ['wh_double', 'wh_heavy'], kind: 'heavy', rank: 4, dmg: 1.8, poise: 35, stam: 18, wind: 220, total: 550, reach: WH_REACH, tip: true, fin: true },
  wh_thousand: { tags: ['wh_thousand', 'wh_1'], rank: 5, hits: [0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45], gap: 110, poise: 32, stam: 20, wind: 80, total: 1000, reach: WH_REACH, tip: true, tipOnly: true, fxEach: false, animLoop: true },
  wh_retreat: { tags: ['wh_retreat', 'wh_1'], dmg: 1.0, poise: 10, stam: 10, wind: 160, total: 420, lunge: -40, lungeLead: 160, lungeTail: 200, reach: WH_REACH, tip: true },
  wh_snap: { tags: ['wh_snap', 'wh_1'], rank: 2, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 80, total: 320, inv: [0, 200] },
  wh_slam: { tags: ['wh_slam', 'wh_heavy'], kind: 'heavy', rank: 3, dmg: 1.6, poise: 60, stam: 16, wind: 250, total: 600, reach: 34, fin: true, slam: true, reel: true },
  // v14: J J K -- the trip lash: a low crack skimming the floor at full length; tipped, it takes a small foe's legs
  wh_trip: { tags: ['wh_trip', 'wh_2'], dmg: 1.0, poise: 22, stam: 12, wind: 200, total: 560, step: 2, fin: true, reach: WH_REACH, tip: true, ys: [-16, 0],
    on: { hit(t, info, A, c) { if (c && c.tip && whSmall(t) && t.breakStance && t.state !== 'stagger') t.breakStance(); } } },
  // v14: L -> K -- the coil spin: the chain whirls tight round you, both sides; small foes are flung out to the tip
  wh_coil: { tags: ['wh_coil', 'wh_3'], hits: [0.6, 0.7], gap: 140, poise: 26, stam: 14, wind: 140, total: 520, spin: true, reach: 46, backReach: 40, lashExt: false,
    on: { hit(t) { if (P.mvHitK === 1) whShove(t, 64); } } },
  // v14 (II): grapple -> J -- the reel kick: the chain wrapped round the boot, a spinning heel kick back out to the tip
  wh_reelkick: { tags: ['wh_reelkick', 'wh_retreat'], rank: 2, dmg: 1.2, poise: 30, stam: 12, wind: 150, total: 460, reach: 32, back: 4, airOk: true, lashExt: false,
    on: { hit(t) { whShove(t, 64); } } },
  wh_air: { tags: ['wh_air'], air: true, dmg: 0.9, poise: 12, stam: 10, wind: 160, total: 380, spin: true, reach: MV_SR * 1.4,
    next: { J: q => (held.has('down') ? 'wh_down' : q.up ? 'wh_up' : 'wh_air2') } },
  // v14: air J J -- the skyfall crack: out of the circle, a long crack down to the floor ahead
  wh_air2: { tags: ['wh_air2', 'wh_air'], air: true, dmg: 1.0, poise: 16, stam: 10, wind: 150, total: 400, reach: WH_REACH, tip: true, ys: [-22, 34], lashDown: true },
  wh_up: { tags: ['wh_up'], up: true, dmg: 0.9, poise: 14, stam: 10, wind: 160, total: 380, tip: true, ys: [-70, -14] },
  wh_down: { tags: ['wh_down'], down: true, dmg: 0.9, poise: 12, stam: 10, wind: 120, total: 320, box: [-8, 14, -10, 44] },
});
// ---- the lash beyond the sprite: the drawn chain reaches ~36 px, the hit reaches 80 (96 overhead). While a lash is
// out, the engine draws the rest of it: grey links swinging out to the real reach, the tip zone (last 30%) hot, a glint
// at the tip. Both sides for the spins.
function whLashFx() {
  const A = ATK[P.state]; if (!A || !A.mv || A.cls !== 'whip') return;
  const d = A.mv, R = A._r; if (!R || d.noHit || d.lashExt === false || A.up || A.down || P.mvHitK < 0) return;
  const reach = A.reach[1]; if (reach <= 40) return;
  const kT = R.hitT ? R.hitT[P.mvHitK] : d.wind + P.mvHitK * (d.gap || 70), e = P.mvT - kT, act = R.actMs;
  if (e < -10 || e > act + 110) return;
  const out = e < 50 ? Math.max(0, (e + 10) / 60) : e <= act ? 1 : Math.max(0, 1 - (e - act) / 110);   // unfurl, hold, recoil
  const yc = clamp((A.ys[0] + A.ys[1]) / 2, -30, -4);
  for (const s of (A.spin ? [1, -1] : [1])) {
    const dir = P.face * s, x0 = P.x + dir * 34, y0 = P.y + yc + (s < 0 ? 2 : 0), len = (reach - 34) * out;
    if (len < 2) continue;
    const yEnd = d.lashDown ? P.y + 18 : y0 + 1, n = Math.max(2, Math.round(len / 3));
    const pts = []; for (let i = 0; i <= n; i++) { const u = i / n; pts.push([x0 + dir * len * u, y0 + (yEnd - y0) * u + Math.sin(u * Math.PI) * (1 - out) * 6 + Math.sin(u * 9 + P.mvT * 0.04) * 0.6 * u]); }
    const tipFrom = (reach * WH_TIP - 34) / Math.max(1, reach - 34);
    for (let i = 0; i < n; i++) {
      const u = (i + 0.5) / n, hot = u * (len / Math.max(1, reach - 34)) >= tipFrom;
      g.fillStyle = hot ? `rgba(255,240,205,${0.95 * out})` : (i % 2 ? `rgba(120,118,138,${0.9 * out})` : `rgba(196,196,212,${0.9 * out})`);
      g.fillRect(Math.round(pts[i][0]), Math.round(pts[i][1]), 1, 1);
      if (i % 2 === 0) g.fillRect(Math.round((pts[i][0] + pts[i + 1][0]) / 2), Math.round((pts[i][1] + pts[i + 1][1]) / 2), 1, 1);
    }
    const tp = pts[n];
    if (out > 0.85) { mvStar(tp[0], tp[1], 2.5, '255,245,220', 0.9 * out); addLight(tp[0], tp[1], 14, '255,236,200', 0.5 * out); }
    else drawGlow(() => { g.fillStyle = `rgba(255,236,200,${0.7 * out})`; g.fillRect(Math.round(tp[0]), Math.round(tp[1]), 1, 1); });
  }
}
// ---- the grapple: a thrown chain (64 px). Small foes come to you (stunned 0.6 s); large foes and hook rings pull you.
function whLarge(t) { const hb = t.hurtbox && t.hurtbox(); return !!(t.cfg && t.cfg.elite) || (hb && (hb.x1 - hb.x0 > 28 || hb.y1 - hb.y0 > 44)); }
function whGrapple() {
  const R = 64;
  let best = null, bd = 1e9;
  for (const h of (room.hooks || [])) {
    const dx = h.x - P.x, dy = h.y - (P.y - 20), d = Math.hypot(dx, dy);
    if (d > R + 16 || dx * P.face < -8) continue;
    if (d < bd && lineOfSight(P.x, P.y - 22, h.x, h.y + 6)) { bd = d; best = { ring: h, x: h.x, y: h.y }; }
  }
  for (const t of targets()) {
    if (t.prop || t.alive === false || t.boss || (boss && t === boss) || (boss && boss.parts && boss.parts.includes(t))) continue;   // never bosses
    const hb = hbOf(t); if (!hb) continue;
    const near = P.face > 0 ? hb.x0 - P.x : P.x - hb.x1, dy = (hb.y0 + hb.y1) / 2 - (P.y - 14);
    if (near < -6 || near > R || Math.abs(dy) > 40) continue;
    if (near < bd) { bd = near; best = { foe: t, x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2 }; }
  }
  P.whGrap = { t: P.clk, x: P.x + P.face * R, y: P.y - 18 };
  setP('grapple', pHas('wh_grapple') ? 'wh_grapple' : 'wh_1', false);
  P.grT = 0; P.grTarget = best; P.whZipJ = false; sfx.shoot && sfx.shoot();
  if (best) { P.whGrap.x = best.x; P.whGrap.y = best.y; }
}
// a J / K pressed in the grapple's tail leaves it at once (the follow-ups used to need the press to land after it)
function whGrapExit(after) {
  if (P.grT < after || !(peek('attack') || peek('heavy'))) return false;
  setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); return true;
}
MV_STATES.grapple = (dt, ax, grav) => {
  P.grT += dt; const b = P.grTarget;
  if (!b) { P.vx = approach(P.vx, 0, 900 * dt); grav(); if (P.grT >= 0.3 || whGrapExit(0.16)) setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); return; }
  if (b.foe && !whLarge(b.foe) && !b.done) {   // a small foe: reel it in, stunned (a short stagger: the long one let the grapple lock a foe down)
    b.done = true; const t = b.foe;
    P.whPull = { t: P.clk, t2: t, small: true };
    weaponPull(t, { chain: true });
    if (t.breakStance && t.state !== 'stagger') { t.breakStance(); if (t.state === 'stagger' && typeof t.t === 'number') t.t = Math.min(t.t, 0.6); }
    t._whStun = 0.6; whTipFx(b.x, b.y, false);
    if (pHas('wh_grapple_pull')) P.anim.set('wh_grapple_pull', false);
  }
  if (b.foe && !whLarge(b.foe)) { P.vx = approach(P.vx, 0, 900 * dt); grav(); if (P.grT >= 0.3 || whGrapExit(0.16)) setP('idle', 'idle', true); return; }
  // a large foe or a hook ring: the chain hauls you in (J pressed on the way is kept: the reel kick on arrival, II)
  if (peek('attack') && mvHas(2) && b.foe) { take('attack'); P.whZipJ = true; }
  if (P.grT < 0.08) { P.vx = 0; grav(); return; }
  if (pHas('wh_grapple_zip') && P.anim.tag !== 'wh_grapple_zip') P.anim.set('wh_grapple_zip', true);
  if (b.foe && b.foe.alive !== false) { const hb = hbOf(b.foe); if (hb) { b.x = P.x < b.x ? hb.x0 - 6 : hb.x1 + 6; b.y = P.y - 14; } }
  P.whGrap.x = b.x; P.whGrap.y = b.y;
  const dx = b.x - P.x, dy = (b.ring ? b.y + 30 : b.y + 14) - P.y, d = Math.hypot(dx, dy);
  if (d < 10 || P.grT > 0.7) {
    P.vy = b.ring ? -200 : -80; P.vx = Math.sign(dx || P.face) * 90; P.ground = false; setP('air', 'jump_up');
    if (b.foe) { P.whPull = { t: P.clk, t2: b.foe, small: false }; if (P.whZipJ) { P.whZipJ = false; P.face = Math.sign(dx || P.face); P.whPull = null; mvStart('wh_reelkick'); } }
    return;
  }
  P.vx = dx / d * 360; P.vy = dy / d * 360; P.ground = false;
};
HOOKS.update.push(dt => { for (const e of enemies) if (e._whStun > 0) { e._whStun -= dt; if (e.vx !== undefined) e.vx = 0; } });

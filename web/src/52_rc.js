// ------------------------------------------------------------------ EXPANSION 3 — agent RC: Stormward Spire, The Deep, The Crown
// Rooms: tools/regions/82_rc.py (SP8-SP17, LF1, D9-D17, X6-X12). This file adds: the `lastfield` biome (The Last Field: five
// parallax layers, wheat that sways and parts around you, her nest and egg, a warm variation of the Spire music), the Ember
// Hatchling spell (a drake cub that fights beside you for 10 s), the three trial charms (c_x3_storm, c_x3_slag,
// c_x3_crown), the region set pieces and mechanics used by the new rooms (xrc spawns: ore carts, lava geysers, belts that
// reverse on a beat, storm-drain waves, the Gale Trial's bolt columns, the Slag Sluices puzzle, petals that carry you…),
// three elite variants for the gauntlets, and lore pages rc_1…rc_12. Every top-level name is prefixed xrc / XRC.
// Art: art/gen_xrc_lastfield.py (xrc_lf_*, tiles_lastfield), art/gen_xrc_cub.py (xrc_cub, xrc_icons), art/gen_xrc_spire.py
// (xrc_sp_*), art/gen_xrc_deep.py (xrc_dp_*), art/gen_xrc_crown.py (xrc_cr_*).
const XRC = { roomObj: null, props: [], front: [], wheat: null, cub: null, shots: [], lfT: 0, mus: 0, musI: 0, carts: [], belts: null,
              bolts: null, sluice: null, t: 0, hint: {} };
const xrcIn = id => room && room.id === id;
const xrcSh = n => sheet(n);
function xrcEnsure() { if (XRC.roomObj !== room) Object.assign(XRC, { roomObj: room, props: [], front: [], wheat: null, shots: [], carts: [], belts: null, bolts: null, sluice: null, t: 0 }); }
const xrcSfx = {
  chime: (k = 1) => [523, 784, 1046, 1318].forEach((f, i) => tone(f * k, 1.8, 0.05, 'sine', 1, i * 0.16)),
  crack: () => { noise(0.3, 1800, 1.2, 0.2, 'highpass'); tone(1400, 0.2, 0.04, 'triangle', 0.7); },
  hatch: () => { [392, 494, 587, 784, 988].forEach((f, i) => tone(f, 1.6, 0.06, 'triangle', 1, i * 0.12)); noise(0.6, 900, 0.6, 0.12, 'bandpass', 1.5); },
  spit: () => { noise(0.18, 1400, 1, 0.12, 'bandpass', 0.6); tone(520, 0.12, 0.04, 'sawtooth', 1.4); },
  chirp: () => { tone(1320, 0.08, 0.04, 'triangle', 1.3); tone(1760, 0.1, 0.03, 'sine', 1.2, 0.07); },
  rumble: (v = 1) => { noise(1.0, 140, 0.6, 0.3 * v, 'lowpass', 0.6); tone(46, 0.9, 0.12 * v, 'sine', 0.8); },
  klaxon: () => { tone(330, 0.18, 0.06, 'square', 1); tone(247, 0.18, 0.06, 'square', 1, 0.2); },
  gush: () => { noise(0.9, 800, 0.5, 0.35, 'bandpass', 0.4); noise(0.5, 2600, 0.8, 0.12, 'highpass'); },
  pour: () => { noise(1.2, 300, 0.6, 0.25, 'lowpass', 0.7); tone(90, 1.0, 0.08, 'sawtooth', 0.8); },
  hiss: () => { noise(1.4, 3200, 0.6, 0.18, 'highpass', 0.5); },
  wrong: () => { tone(185, 0.5, 0.09, 'sawtooth', 0.8); tone(196, 0.5, 0.09, 'sawtooth', 0.8); },
};

// ================================================================== the Last Field biome
Object.assign(AREAS, { lastfield: { name: 'The Last Field', ambient: 0.2, amb: 'mote', tint: '#3a2448', map: '#c8983a',
  lx: { amb: '255,200,160', lvl: 0.7 } } });
Object.assign(SCALES, { lastfield: [0, 2, 4, 7, 9] });           // the Spire's minor mode turned warm: the same root, a major pentatonic
Object.assign(ROOTS, { lastfield: ROOTS.spire || 46.25 });
if (typeof MAP_COLS !== 'undefined') Object.assign(MAP_COLS, { lastfield: '#c8983a' });
Object.assign(PCOL, { xrc_seed: '250,230,170', xrc_wheat: '236,196,100', xrc_foam: '210,235,245', xrc_slag: '255,140,50', xrc_petal: '255,248,232' });

// ================================================================== lore (Hallow Chronicle)
Object.assign(LORE_PAGES, {
  rc_1: { region: 'spire', title: 'The Fishers\' Last Tally', text: 'Chalked on a hut door, the strokes going on long after the boats stopped coming home:\nNine boats out. Four back. The storm does not end. It only draws breath.\nWe were told the drake keeps the sky. We never asked whose sky.' },
  rc_2: { region: 'spire', title: 'The Keeper\'s Log', text: 'The last entry, the ink run with rain:\nThe lamp is lit, though no ship has come in a hundred years. I keep it for the ones still out there.\nWhen lightning takes the sea, for one breath I can see all the way to the edge of the world. It is only more storm.' },
  rc_3: { region: 'spire', title: 'A Crow-Picked Pilgrim', text: 'He climbed the stack for the crows\' hoard. The note is still in his fist:\nThey bring the shining things of the drowned up here. Rings, buckles, one small crown.\nI have held the crown. Now I cannot find the way down, and the crows are patient.' },
  rc_4: { region: 'lastfield', title: 'The Last Field', text: 'Before the Pale Root, all of the Hallow was fields like this, and the long evening never ended.\nThe drakes kept the sky over them. The farmers left the first sheaf of every harvest on the stones, and the drakes let the sun go down slowly.' },
  rc_5: { region: 'lastfield', title: 'The Drake Stone', text: 'Carved deep, the edges worn soft by weather:\nWhen the Root rose, the sky went grey. The drakes flew into the grey to tear it down, and one by one they did not come back.\nThe last of them came here, where the light still fell. She would not leave it. She called the storm down around this field and let the world believe she had become the storm.' },
  rc_6: { region: 'lastfield', title: 'Her Last Egg', text: 'In the hollow of the nest, among her shed scales, the egg is still warm.\n"The sky was ours before the Root. It will be ours after." She did not mean herself.\nShe meant this.' },
  rc_7: { region: 'deep', title: 'The Forgemaster\'s Ledger', text: 'The Root wants iron for its crown and fire for its roots, and the Deep gives both.\nWe no longer count the shifts. The furnace does not go out, and neither do we. Those who fall into the slag are poured with the rest. The Overseer says nothing down here is wasted.' },
  rc_8: { region: 'deep', title: 'A Thief in the Vault', text: 'He broke the floor with a hammer he could barely lift and found the Overseer\'s hoard.\nHe never found the way out. His last words are scratched into a sheet of gold leaf:\nWorth it. Almost.' },
  rc_9: { region: 'deep', title: 'The Smiths\' Stair', text: 'Stamped into an iron plate on the gallery rail:\nThree measures cast the Stair of the Smiths: the Ox below, the Hammer above it, the Flame on top. Pour from the floor up; hot iron will not set on nothing.\nThe fourth mould is the Grave. What is poured there is not given back.\nFollow the pipes from each valve to its mould.' },
  rc_10: { region: 'crown', title: 'The Crown Overlook', text: 'From here the whole Hallow lies under a sea of cloud: the Ramparts, the drowned Cathedral, the Spire in its storm, the red breath of the Deep.\nThe Sovereign sat here once, before the crown grew into her. She looked down at all of it and loved it, and could not let any of it go.\nThat was the beginning.' },
  rc_11: { region: 'crown', title: 'Graven in the Heartwood', text: 'The Root does not grow toward the light. It grows toward whatever it can keep.\nEvery bough here was a road once. Every petal is a name.' },
  rc_12: { region: 'crown', title: 'The Singing Pilgrims', text: 'Pilgrims came up the Root in the early days, singing. The Root took them in.\nYou can still hear them if you press an ear to the bark. The song is very slow now.' },
});

// ================================================================== gear: Ember Hatchling + the three trial charms
if (typeof ICON_SHEETS !== 'undefined' && !ICON_SHEETS.includes('xrc_icons')) ICON_SHEETS.push('xrc_icons');
registerGear({
  spells: {
    ember_hatchling: { name: 'Ember Hatchling', fp: 30, cd: 25, icon: 's_ember_hatchling', sheet: 'xrc_icons',
      desc: 'Cindervane\'s last egg, hatched in your hands. A drake cub fights beside you for 10 seconds, spitting embers at the nearest foe and diving in to bite and burn, then scatters into sparks. Scales with Faith.' },
  },
  charms: {
    c_x3_storm: { name: 'Stormglass Feather', iconSheet: 'xrc_icons', desc: 'A feather of glass the storm grew over an old drake\'s quill. You glide 25% faster, and updrafts carry you harder.' },
    c_x3_slag: { name: 'Slagwalker\'s Sole', iconSheet: 'xrc_icons', desc: 'The iron sole of a forge-walker who never burned. The first touch of lava in ten seconds throws you back out unharmed.' },
    c_x3_crown: { name: 'Sovereign\'s Sigil', iconSheet: 'xrc_icons', desc: 'The seal she pressed into every bough. Cinder Slams cost no stamina, and every blow lands 8% harder.' },
  },
}, 'xrc_icons');

// ---- charms. Stormglass Feather: faster glides, stronger draughts (wraps the Gale Cloak's glide)
{
  const base = updateGlide;
  updateGlide = function (dt) {
    const v0 = P.vx, w0 = P.vy;
    base(dt);
    if (!charmOn('c_x3_storm') || P.state !== 'glide') return;
    const ax = inputX(), vx = (charmOn('c_feather') ? 150 : 135) * 1.25;
    if (ax) P.vx = approach(v0, ax * vx, 520 * dt);
    if (inUpdraft(P)) P.vy = approach(w0, -170 * 1.35, 900 * dt);
  };
}
// Slagwalker's Sole: the first lava touch in 10 s bounces you out unharmed (Deep lava tiles, and KM rising/level lava)
function xrcSlagBounce() {
  if (!charmOn('c_x3_slag') || P.state === 'dead' || time - (P.xrcSlagT ?? -99) < 10) return false;
  P.xrcSlagT = time; P.vy = -400; P.ground = false; P.inv = Math.max(P.inv, 0.6); setP('air', 'jump_up', false);
  sfx.fire(); tone(660, 0.3, 0.06, 'triangle', 1.5); shake = Math.max(shake, 3);
  for (let i = 0; i < 16; i++) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(0, 6), vx: rand(-60, 60), vy: -rand(60, 160), g: 420, life: rand(0.4, 0.8), kind: 'ember' });
  if (!XRC.hint.slag) { XRC.hint.slag = 1; toast('The sole throws you clear of the lava.', 2.4); }
  return true;
}
if (typeof lavaHurt === 'function') {
  const base = lavaHurt;
  lavaHurt = function () { if (xrcSlagBounce()) return; return base.apply(this, arguments); };
}
HOOKS.playerHurt.push((dmg, opt) => (dmg > 0 && opt && opt.hazard && opt.fire && xrcSlagBounce()) ? 0 : dmg);
// Sovereign's Sigil: slams are free, every blow +8%
{
  const og = outgoing;
  outgoing = function (base, mult, kind) { const d = og(base, mult, kind); return charmOn('c_x3_crown') ? d * 1.08 : d; };
  const ss = startSlam;
  startSlam = function () { const st = P.st; ss(); if (charmOn('c_x3_crown')) P.st = st; };
}

// ================================================================== Ember Hatchling: a drake cub fights at your side for 10 s
const XRC_CUB = { life: 10, spitEvery: 1.05, diveEvery: 3.2, range: 175 };
function xrcFoes() { return targets().filter(t => !t.prop && (t.alive === undefined || t.alive)); }
function xrcHb(t) { const hb = hbOf(t); return hb ? { x: (hb.x0 + hb.x1) / 2, y: (hb.y0 + hb.y1) / 2, hb } : null; }
function xrcHit(t, dmg, o = {}) {
  const c = xrcHb(t); if (!c) return;
  t.hit(Object.assign({ dmg: outgoing(dmg, 1, 'spell'), poise: 18, dir: t.x >= (o.from ?? P.x) ? 1 : -1, kind: 'spell', x: c.x, y: c.y, fire: true }, o));
  if (o.burn && typeof WSTATUS !== 'undefined') WSTATUS.burn(t, o.burn[0], o.burn[1]);
}
function xrcCubAnim(c, tag, loop = false) { const sh = xrcSh('xrc_cub'); if (!c.anim || c.anim.tag !== tag) c.anim = new Anim(sh, sh.has(tag) ? tag : 'fly', loop); }
SPELL_CAST.ember_hatchling = sp => {
  const old = XRC.cub; if (old && old.state !== 'vanish') { old.state = 'vanish'; xrcCubAnim(old, 'vanish'); }
  const c = { x: P.x - P.face * 16, y: P.y - 40, vx: 0, vy: 0, face: P.face, t: 0, life: XRC_CUB.life, sp, state: 'appear', spitT: 0.7, diveT: 2.2, tgt: null, bite: new Set() };
  xrcCubAnim(c, 'appear'); XRC.cub = c; xrcSfx.hatch(); xrcSfx.chirp();
  for (let i = 0; i < 18; i++) particles.push({ x: c.x + rand(-8, 8), y: c.y + rand(-8, 8), vx: rand(-60, 60), vy: rand(-60, 40), life: rand(0.4, 0.9), kind: 'ember' });
};
function xrcCubTarget(c) {
  let best = null, bd = XRC_CUB.range;
  for (const t of xrcFoes()) { const q = xrcHb(t); if (!q) continue; const d = Math.hypot(q.x - c.x, q.y - c.y); if (d < bd && lineOfSight(c.x, c.y, q.x, q.y)) { bd = d; best = t; } }
  return best;
}
function xrcUpdateCub(dt) {
  const c = XRC.cub; if (!c) return;
  c.t += dt; c.anim.update(dt);
  const sh = xrcSh('xrc_cub');
  if (c.state !== 'vanish' && c.t >= c.life) { c.state = 'vanish'; xrcCubAnim(c, 'vanish'); tone(880, 0.6, 0.04, 'sine', 0.5); }
  if (c.state === 'vanish') {
    if (Math.random() < 0.6) particles.push({ x: c.x + rand(-8, 8), y: c.y + rand(-6, 6), vx: rand(-30, 30), vy: -rand(10, 50), life: rand(0.4, 0.9), kind: 'ember' });
    if (c.anim.done || !sh.ok) XRC.cub = null;
    return;
  }
  if (c.state === 'appear' && (c.anim.done || !sh.ok)) { c.state = 'fly'; xrcCubAnim(c, 'fly', true); }
  // hover beside you, a little behind and above; bob
  const hx = P.x - P.face * 18, hy = P.y - 38 + Math.sin(c.t * 3.2) * 3;
  if (c.state === 'dive') {
    const q = c.tgt && (c.tgt.alive === undefined || c.tgt.alive) ? xrcHb(c.tgt) : null;
    c.diveK += dt;
    if (!q || c.diveK > 0.9) { c.state = 'fly'; xrcCubAnim(c, 'fly', true); }
    else {
      const dx = q.x - c.x, dy = q.y - c.y, d = Math.hypot(dx, dy) || 1;
      c.vx = approach(c.vx, dx / d * 300, 1600 * dt); c.vy = approach(c.vy, dy / d * 300, 1600 * dt);
      c.face = dx >= 0 ? 1 : -1;
      if (d < 14 && !c.bite.has(c.tgt)) {
        c.bite.add(c.tgt); xrcHit(c.tgt, 38 * c.sp, { poise: 30, burn: [4, 7 * c.sp], from: c.x }); sfx.hit(); sfx.fire();
        for (let i = 0; i < 10; i++) particles.push({ x: q.x, y: q.y, vx: rand(-80, 80), vy: -rand(30, 120), g: 300, life: 0.5, kind: 'fire' });
        c.state = 'fly'; xrcCubAnim(c, 'fly', true); c.vy = -160; c.vx = -c.face * 90;
      }
    }
  } else {
    c.vx = approach(c.vx, (hx - c.x) * 5, 900 * dt); c.vy = approach(c.vy, (hy - c.y) * 5, 900 * dt);
    c.tgt = xrcCubTarget(c);
    if (c.tgt) { const q = xrcHb(c.tgt); if (q) c.face = q.x >= c.x ? 1 : -1; } else if (Math.abs(c.vx) > 20) c.face = sign(c.vx);
    c.spitT -= dt; c.diveT -= dt;
    if (c.state === 'fly' && c.tgt) {
      const q = xrcHb(c.tgt), d = q ? Math.hypot(q.x - c.x, q.y - c.y) : 999;
      if (c.diveT <= 0 && d < 130) { c.state = 'dive'; c.diveK = 0; c.bite = new Set(); xrcCubAnim(c, 'dive'); c.diveT = XRC_CUB.diveEvery; xrcSfx.chirp(); }
      else if (c.spitT <= 0) { c.state = 'spit'; c.spitK = 0; c.spat = false; xrcCubAnim(c, 'spit'); c.spitT = XRC_CUB.spitEvery; }
    }
    if (c.state === 'spit') {
      c.spitK += dt;
      if (!c.spat && (c.anim.i >= 2 || c.spitK > 0.25)) {
        c.spat = true; const q = c.tgt && xrcHb(c.tgt);
        const mx = c.x + c.face * 14, my = c.y, ang = q ? Math.atan2(q.y - my, q.x - mx) : (c.face > 0 ? 0 : Math.PI);
        XRC.shots.push({ x: mx, y: my, vx: Math.cos(ang) * 220, vy: Math.sin(ang) * 220, t: 0, tgt: c.tgt, dmg: 24 * c.sp, id: ++hazardId });
        xrcSfx.spit();
      }
      if (c.anim.done || c.spitK > 0.6) { c.state = 'fly'; xrcCubAnim(c, 'fly', true); }
    }
  }
  c.x += c.vx * dt; c.y += c.vy * dt;
  addLight(c.x, c.y, 34, '255,150,70', 0.7);
  if (Math.random() < 0.25) particles.push({ x: c.x - c.face * 6 + rand(-3, 3), y: c.y + rand(-2, 4), vx: -c.face * rand(5, 25), vy: rand(-10, 10), life: rand(0.3, 0.6), kind: 'ember' });
}
function xrcUpdateShots(dt) {
  for (const s of XRC.shots) {
    s.t += dt;
    if (s.tgt && (s.tgt.alive === undefined || s.tgt.alive)) {   // a little homing
      const q = xrcHb(s.tgt); if (q) { const a = Math.atan2(q.y - s.y, q.x - s.x), sp = Math.hypot(s.vx, s.vy); s.vx = approach(s.vx, Math.cos(a) * sp, 500 * dt); s.vy = approach(s.vy, Math.sin(a) * sp, 500 * dt); }
    }
    s.x += s.vx * dt; s.y += s.vy * dt;
    addLight(s.x, s.y, 26, '255,150,60', 0.8);
    if (Math.random() < 0.5) particles.push({ x: s.x, y: s.y, vx: -s.vx * 0.1, vy: rand(-10, 10), life: 0.3, kind: 'fire' });
    let hit = solidAtPx(s.x, s.y) || s.t > 1.6;
    if (!hit) for (const t of xrcFoes()) { const hb = hbOf(t); if (hb && overlap(hb, rect(s.x - 4, s.y - 4, s.x + 4, s.y + 4))) { xrcHit(t, s.dmg, { burn: [2.5, 4 * (XRC.cub ? XRC.cub.sp : 1)], from: s.x }); hit = true; break; } }
    if (hit) { s.dead = true; for (let i = 0; i < 7; i++) particles.push({ x: s.x, y: s.y, vx: rand(-60, 60), vy: rand(-80, 20), g: 300, life: rand(0.2, 0.5), kind: 'ember' }); }
  }
  XRC.shots = XRC.shots.filter(s => !s.dead);
}
function xrcDrawCub() {
  const c = XRC.cub, sh = xrcSh('xrc_cub');
  if (c) {
    if (sh.ok) drawSprite(sh, c.anim.frame, c.x, c.y, c.face, { center: true });
    else { g.fillStyle = '#2a2530'; g.fillRect(Math.round(c.x) - 6, Math.round(c.y) - 3, 12, 6); }
  }
  if (!XRC.shots.length) return;
  drawGlow(() => {
    const fb = sh.ok && sh.has('fireball') ? sh.tag('fireball') : null;
    for (const s of XRC.shots) {
      if (fb) drawSprite(sh, fb.from + (Math.floor(s.t * 14) % (fb.to - fb.from + 1)), s.x, s.y, 1, { center: true, rot: Math.atan2(s.vy, s.vx) });
      else { g.fillStyle = '#ffc060'; g.fillRect(Math.round(s.x) - 2, Math.round(s.y) - 2, 4, 4); }
    }
  });
}
HOOKS.enter.push(() => { if (XRC.cub) XRC.cub = null; XRC.shots = []; });
HOOKS.death.push(() => { XRC.cub = null; XRC.shots = []; });

// ================================================================== elites for the gauntlets (existing foes, burning brighter)
// xrc_slag_foreman / xrc_slag_golem: forge sentries run hot; xrc_sentinel_echo: a gilded sentinel's pale echo.
const XRC_ELITE = {
  xrc_slag_foreman: { base: 'dp_forge_sentry', hp: 1.9, filter: 'sepia(0.6) saturate(2.2) hue-rotate(-12deg) brightness(1.08)', glow: '255,130,50', name: 'Slag Foreman' },
  xrc_slag_golem: { base: 'dp_forge_sentry', hp: 2.8, filter: 'sepia(0.9) saturate(3) hue-rotate(-22deg) brightness(1.15)', glow: '255,110,40', name: 'Slag Golem' },
  xrc_sentinel_echo: { base: 'gilded_sentinel', hp: 1.5, filter: 'grayscale(0.7) brightness(1.5) contrast(0.9)', glow: '235,240,255', name: 'Sentinel\'s Echo', alpha: 0.82 },
};
for (const [id, E] of Object.entries(XRC_ELITE)) {
  const b = ENEMY[E.base]; if (!b) continue;
  ENEMY[id] = { ...b, hp: Math.round(b.hp * E.hp), cinders: Math.round((b.cinders || 100) * 3), elite: true, stance: Math.round((b.stance || 100) * 1.4) };
  if (ATTACK_TAGS[E.base]) ATTACK_TAGS[id] = ATTACK_TAGS[E.base];
  if (typeof FLYING_TYPES !== 'undefined' && FLYING_TYPES.has && FLYING_TYPES.has(E.base)) FLYING_TYPES.add(id);
  const Base = ENEMY_CLASSES[E.base] || Enemy;
  ENEMY_CLASSES[id] = class extends Base {
    constructor(type, x, y, key) {
      SHEETS[type] = sheet(E.base);             // the elite wears its base's sheet (and meta)
      super(type, x, y, key); this.xrcE = E;
    }
    update(dt) {
      super.update(dt);
      if (this.alive) {
        const hb = this.hurtbox && this.hurtbox(); const cx = hb ? (hb.x0 + hb.x1) / 2 : this.x, cy = hb ? (hb.y0 + hb.y1) / 2 : this.y - 16;
        addLight(cx, cy, 60, E.glow, 0.7);
        if (Math.random() < 0.3) particles.push({ x: cx + rand(-10, 10), y: cy + rand(-14, 14), vx: rand(-8, 8), vy: -rand(14, 40), life: rand(0.4, 0.9), kind: E.base === 'gilded_sentinel' ? 'mote' : 'ember' });
      }
    }
    draw() {
      const f = g.filter, a = g.globalAlpha;
      try { g.filter = E.filter; if (E.alpha) g.globalAlpha = E.alpha; super.draw(); } finally { g.filter = f; g.globalAlpha = a; }
    }
  };
}

// ================================================================== decor props (xrc spawns): sheet, tag, anchor, extras
// anchor: 'bottom' = bottom-centre on the cell's floor; 'top' = hung from the cell's top; 'center' = the cell's centre.
const XRC_DECO = {
  hut: ['xrc_sp_hut', 'idle', 'bottom'], nets: ['xrc_sp_nets', 'sway', 'bottom'], boat: ['xrc_sp_boat', 'bob', 'bottom', { dy: 10 }],
  crates: ['xrc_sp_crates', 'idle', 'bottom'], pipe: ['xrc_sp_pipe', 'idle', 'top'], pennant: ['xrc_sp_pennant', 'loop', 'bottom'],
  winch: ['xrc_sp_winch', 'idle', 'bottom'], bignest: ['xrc_sp_bignest', 'idle', 'bottom'], railing: ['xrc_sp_railing', 'idle', 'bottom'],
  lantern_room: ['xrc_sp_lantern', 'loop', 'bottom'],
  gear: ['xrc_dp_gear', 'spin', 'center'], pipes: ['xrc_dp_pipes', 'idle', 'bottom'], cage: ['xrc_dp_cage', 'idle', 'top'],
  timbers: ['xrc_dp_timbers', 'idle', 'bottom'], ore: ['xrc_dp_ore', 'idle', 'bottom'], anvil_big: ['xrc_dp_anvil', 'idle', 'bottom'],
  overseer_seat: ['xrc_dp_seat', 'idle', 'bottom'], hoard: ['xrc_dp_hoard', 'idle', 'bottom'], furnace: ['xrc_dp_furnace', 'idle', 'bottom'],
  sapvein: ['xrc_cr_sapvein', 'loop', 'top'], rootknot: ['xrc_cr_rootknot', 'idle', 'bottom'], portrait: ['xrc_cr_portrait', 'idle', 'center'],
  thornbrazier: ['xrc_cr_brazier', 'loop', 'bottom'], blossom: ['xrc_cr_blossom', 'loop', 'bottom'], heartbloom: ['xrc_cr_heartbloom', 'loop', 'bottom'],
  lorestone: ['xrc_lf_stone', 'idle', 'bottom'], deadtree: ['xrc_lf_tree', 'idle', 'bottom', { dy: 2 }], stones: ['xrc_lf_stones', 'idle', 'bottom', { dy: 1 }],
  fence: ['xrc_lf_fence', 'idle', 'bottom', { dy: 1 }], plough: ['xrc_lf_plough', 'idle', 'bottom', { dy: 1 }], nest: ['xrc_lf_nest', 'idle', 'bottom', { dy: 3 }],
};
// per-kind life: lights, particles, wind reactions
const XRC_LIFE = {
  hut: p => { const w = typeof SPR !== 'undefined' && SPR.wind; const gust = w && w.st === 'gust';
    if (gust && p.anim.tag !== 'rattle' && p.sh.has('rattle')) p.anim.set('rattle', true); else if (!gust && p.anim.tag === 'rattle') p.anim.set('idle', true);
    addLight(p.x - p.face * 18, p.y - 40, 44, '255,178,96', 0.7, LX_FLICKER); },
  nets: p => addLight(p.x + p.face * 20, p.y - 30, 34, '255,180,100', 0.6, LX_FLICKER),
  boat: p => { p.oy = Math.round(Math.sin(time * 1.6 + p.x) * 1.5); },
  lantern_room: p => { addLight(p.x, p.y - 52, 130 + Math.sin(time * 3) * 6, '255,214,140', 1.1, LX_FLICKER); addLight(p.x, p.y - 52, 40, '255,240,200', 1); },
  furnace: p => { addLight(p.x, p.y - 44, 170 + Math.sin(time * 4) * 10, '255,120,40', 1.2, LX_FLICKER); addLight(p.x, p.y - 44, 60, '255,210,120', 1); addLight(p.x - 4, p.y - 103, 16, '255,90,40', 0.8);
    if (Math.random() < 0.5) particles.push({ x: p.x + rand(-30, 30), y: p.y - rand(40, 110), vx: rand(-10, 10), vy: -rand(20, 60), life: rand(0.8, 1.6), kind: 'ember' }); },
  heartbloom: p => {
    if (Math.random() < 0.35) particles.push({ x: p.x + rand(-70, 70), y: p.y - rand(60, 150), vx: rand(4, 18), vy: rand(6, 18), life: rand(3, 6), kind: 'petal', pet: true }); },
  thornbrazier: p => addLight(p.x, p.y - 30, 56, '255,236,200', 0.8, LX_FLICKER),
  sapvein: p => addLight(p.x, p.y + 30, 30, '255,210,110', 0.45),
  pipes: p => { if (Math.random() < 0.02) particles.push({ x: p.x + rand(-8, 8), y: p.y - rand(20, 50), vx: rand(-10, 10), vy: -rand(10, 30), life: 1.2, kind: 'dust' }); },
  ore: p => addLight(p.x, p.y - 4, 22, '255,120,50', 0.4),
  hoard: p => { addLight(p.x, p.y - 6, 30, '255,210,120', 0.45); if (Math.random() < 0.03) particles.push({ x: p.x + rand(-10, 10), y: p.y - rand(2, 10), vx: 0, vy: -8, life: 0.8, kind: 'gold' }); },
  lorestone: p => { if (!x3().lore.rc_5) addLight(p.x, p.y - 26, 26, '255,210,140', 0.45); },
  pipe: p => { if (Math.random() < 0.03) particles.push({ x: p.x + rand(-2, 2), y: p.y + 44, vx: 0, vy: 40, g: 400, life: 0.6, kind: 'xrc_foam' }); },
};
function xrcDecoProp(s, c) {
  const d = XRC_DECO[s.kind]; if (!d) return null;
  const sh = xrcSh(d[0]), o = d[3] || {};
  const y = d[2] === 'top' ? c.fy - TILE : d[2] === 'center' ? c.fy - TILE / 2 : c.fy + (o.dy || 0);
  const p = { type: 'xrc_' + s.kind, x: c.cx + (s.dx || 0), y, face: s.flip ? -1 : 1, sh, anchor: d[2], oy: 0, s,
              anim: new Anim(sh, sh.has(d[1]) ? d[1] : (Object.keys(sh.tags)[0] || d[1]), true) };
  p.anim.t = rand(0, 400);
  const life = XRC_LIFE[s.kind];
  p.update = dt => { if (life) life(p, dt); };
  p.draw = () => {
    if (!p.sh.ok) return;
    const fr = p.anim.frame, y0 = p.y + p.oy;
    if (p.anchor === 'top') drawSprite(p.sh, fr, p.x, y0, p.face, { pivot: [Math.floor(p.sh.fw / 2), 0] });
    else drawSprite(p.sh, fr, p.x, y0, p.face, p.anchor === 'center' ? { center: true } : { bottom: true });
  };
  return p;
}

// ================================================================== the xrc spawn dispatcher
const XRC_KIND = {};
SPAWNS.xrc = (s, c) => {
  xrcEnsure();
  const f = XRC_KIND[s.kind];
  if (f) return f(s, c);
  const p = xrcDecoProp(s, c); if (p) props.push(p);
};

// ---- the lighthouse lantern, the furnace and the heartbloom glow (drawn emissive where they burn)
XRC_KIND.lantern_room = XRC_KIND.furnace = XRC_KIND.heartbloom = (s, c) => { const p = xrcDecoProp(s, c); if (!p) return; p.glowParts = true; props.push(p); };
{ const base = XRC_KIND.heartbloom;   // ivory against a white sky: deepen it so its gold core and petal edges read
  XRC_KIND.heartbloom = (s, c) => { base(s, c); const p = props[props.length - 1]; if (!p || p.type !== 'xrc_heartbloom') return; const d = p.draw;
    p.draw = () => { const f = g.filter; try { g.filter = 'brightness(0.74) contrast(1.2) saturate(1.35)'; d(); } finally { g.filter = f; } }; }; }

// ================================================================== Spire: storm-drain waves (SP10): a gout of sea through the grates
XRC_KIND.grate = (s, c) => {
  const p = xrcDecoProp({ ...s, kind: 'grate' }, c) || {};
  const sh = xrcSh('xrc_sp_grate'), A = s.area || [0, 0, 0, 0], ar = rect(A[0] * TILE, A[1] * TILE, (A[0] + A[2]) * TILE, (A[1] + A[3]) * TILE);
  Object.assign(p, { type: 'xrc_grate', x: c.cx, y: c.fy - 8, face: (s.push || 0) < 0 ? -1 : 1, sh, anchor: 'center', oy: 0, st: 'calm', k: 0,
    anim: new Anim(sh, sh.has('idle') ? 'idle' : Object.keys(sh.tags)[0] || 'idle', true) });
  const per = s.period || 5, off = s.off || 0;
  p.draw = () => { if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y, p.face, { center: true }); };
  p.update = dt => {
    const t = ((time + off) % per + per) % per, st = t > per - 0.9 ? 'warn' : t < 1.0 ? 'burst' : 'calm';
    if (st !== p.st) {
      p.st = st;
      if (sh.ok) p.anim.set(sh.has(st) ? st : 'idle', st !== 'burst');
      const near = Math.abs(P.x - p.x) < 260 && Math.abs(P.y - p.y) < 160;
      if (st === 'warn' && near) noise(0.9, 400, 0.6, 0.12, 'lowpass', 1.6);
      if (st === 'burst' && near) { xrcSfx.gush(); shake = Math.max(shake, 2); }
    }
    if (p.st === 'burst') {
      for (let i = 0; i < 3; i++) particles.push({ x: p.x + p.face * rand(6, 20), y: p.y + rand(-8, 8), vx: p.face * rand(120, 260), vy: rand(-40, 60), g: 260, life: rand(0.4, 0.9), kind: 'xrc_foam' });
      if (s.push && !XRC.noPush && overlap(playerHurtbox(), ar) && !['hook', 'rest', 'dead'].includes(P.state)) P.pushVx = (P.pushVx || 0) + s.push * (P.ground ? 1 : 1.2);
    } else if (p.st === 'warn' && Math.random() < 0.3) particles.push({ x: p.x + rand(-8, 8), y: p.y + 6, vx: 0, vy: 30, g: 300, life: 0.5, kind: 'xrc_foam' });
  };
  props.push(p);
};

// ---- kites over the gorge (SP14): drawn at their line's anchor, tugging in the wind
XRC_KIND.kite = (s, c) => {
  const sh = xrcSh('xrc_sp_kite'), tag = 'kite' + (s.c || 0);
  const p = { type: 'xrc_kite', x: c.cx, y: c.fy - TILE - 15, face: s.face || -1, sh, anim: new Anim(sh, sh.has(tag) ? tag : Object.keys(sh.tags)[0] || tag, true), seed: rand(0, 9) };
  p.update = () => {};
  p.draw = () => { if (!sh.ok) return; drawSprite(sh, p.anim.frame, p.x + Math.sin(time * 1.3 + p.seed) * 2, p.y + Math.sin(time * 2.1 + p.seed) * 1, p.face, { center: true }); };
  props.push(p);
};

// ---- the Stormwarden (SP8): painted into the room's back layer so the causeway passes in front of it
XRC_KIND.colossus = (s, c) => { props.push({ type: 'xrc_colossus', x: c.cx, y: c.fy + 6, anim: { update() {} }, draw() {},
  update() { addLight(this.x + 76, this.y - 230, 60, '150,190,255', 0.3 + 0.2 * Math.max(0, Math.sin(time * 0.7))); } }); };
XRC_KIND.beam = () => { XRC.lighthouse = true; };
XRC_KIND.panorama = () => { XRC.panorama = true; };
XRC_KIND.petals = () => { XRC.petals = true; };

// ---- the Gale Trial's bolt columns (SP16): full-height strikes on a beat, marked a breath before they fall
XRC_KIND.bolts = s => { XRC.bolts = { cols: (s.cols || []).map(([x, per, off]) => ({ x: x * TILE + 8, per, off, st: 'calm', id: 0 })), warn: s.warn || 0.8, t0: time }; };
function xrcUpdateBolts() {
  const B = XRC.bolts; if (!B) return;
  const t = SYS.trial ? SYS.trial.t : time - B.t0;
  for (const c of B.cols) {
    const k = ((t + c.off) % c.per + c.per) % c.per, st = k > c.per - B.warn ? 'warn' : k < 0.22 ? 'strike' : 'calm';
    if (st !== c.st) {
      c.st = st;
      if (st === 'strike') { c.id = ++hazardId; if (Math.abs(P.x - c.x) < 300) { (typeof spSfx !== 'undefined' ? spSfx.strike : xrcSfx.crack)(); shake = Math.max(shake, 3); } if (typeof SPR !== 'undefined') SPR.flash = Math.max(SPR.flash || 0, 0.25); }
      if (st === 'warn' && Math.abs(P.x - c.x) < 220 && typeof spSfx !== 'undefined') spSfx.crackle();
    }
    if (c.st === 'strike') {
      addLight(c.x, P.y - 20, 120, '200,225,255', 1, { shadow: false });
      if (Math.abs(P.x - c.x) < 9 && P.state !== 'dead') hurtPlayer(34 * NGP.dmg, sign(P.x - c.x) || 1, c.id, {});
    } else if (c.st === 'warn') addLight(c.x, room.ph - 30, 30 + 40 * (1 - (c.per - k) / B.warn), '120,180,255', 0.6);
  }
}
function xrcDrawBolts() {
  const B = XRC.bolts; if (!B) return;
  const t = SYS.trial ? SYS.trial.t : time - B.t0;
  drawGlow(() => {
    for (const c of B.cols) {
      const k = ((t + c.off) % c.per + c.per) % c.per;
      if (c.st === 'warn') {
        const w = 1 - (c.per - k) / B.warn, a = 0.12 + 0.3 * w * (0.5 + 0.5 * Math.sin(time * 40));
        g.fillStyle = `rgba(140,190,255,${a})`;
        for (let y = cam.y - 8; y < cam.y + H + 8; y += 6) g.fillRect(Math.round(c.x + Math.sin(y * 0.3 + time * 20) * 1.5), Math.round(y), 1, 3);
      } else if (c.st === 'strike') {
        const a = 1 - k / 0.22;
        let x = c.x;
        for (let y = cam.y - 8; y < cam.y + H + 8; y += 4) {
          x = c.x + (hash2(Math.floor(y / 4), Math.floor(time * 30)) - 0.5) * 6;
          g.fillStyle = `rgba(230,245,255,${a})`; g.fillRect(Math.round(x) - 1, Math.round(y), 3, 4);
          g.fillStyle = `rgba(120,170,255,${0.5 * a})`; g.fillRect(Math.round(x) - 4, Math.round(y), 9, 4);
        }
      }
    }
  });
}

// ================================================================== Deep: runaway ore carts (D10)
XRC_KIND.cart = (s, c) => { XRC.carts.push({ x0: c.cx, y: c.fy, dir: s.dir || -1, per: s.period || 7, off: s.off || 0, speed: s.speed || 230, st: 'idle', x: -999, id: 0 }); };
function xrcUpdateCarts(dt) {
  for (const k of XRC.carts) {
    const t = ((time + k.off) % k.per + k.per) % k.per;
    if (k.st === 'idle' && t > k.per - 1.4) { k.st = 'warn'; if (Math.abs(P.y - k.y) < 120) { xrcSfx.rumble(0.8); if (!XRC.hint.cart) { XRC.hint.cart = 1; toast('The rails are singing. Get off the track.', 2.6); } } }
    if (k.st === 'warn') {
      if (Math.random() < 0.5) particles.push({ x: k.x0 + rand(-6, 6), y: k.y - rand(0, 6), vx: k.dir * rand(20, 80), vy: -rand(20, 80), g: 300, life: 0.4, kind: 'spark' });
      addLight(k.x0, k.y - 16, 50, '255,140,60', 0.6);
      if (t < 1) { k.st = 'run'; k.x = k.x0 + (k.dir < 0 ? 24 : -24); k.id = ++hazardId; xrcSfx.rumble(1.2); }
    }
    if (k.st === 'run') {
      k.x += k.dir * k.speed * dt;
      addLight(k.x, k.y - 14, 50, '255,130,50', 0.8);
      if (Math.random() < 0.6) particles.push({ x: k.x - k.dir * 14, y: k.y - 2, vx: -k.dir * rand(20, 80), vy: -rand(20, 90), g: 400, life: 0.35, kind: 'spark' });
      const r = rect(k.x - 16, k.y - 24, k.x + 16, k.y);
      if (overlap(r, playerHurtbox()) && P.state !== 'dead') { if (hurtPlayer(46 * NGP.dmg, k.dir, k.id, {})) { P.vx = k.dir * 180; P.vy = -200; } }
      for (const e of enemies) if (e.alive && !e.cfg.flying && e.hurtbox && e.hurtbox() && overlap(r, e.hurtbox()) && !e.xrcCart) { e.xrcCart = k.id; e.hit({ dmg: 200, poise: 200, dir: k.dir, kind: 'env', x: e.x, y: e.y - 10 }); }
      if (k.x < -40 || k.x > room.pw + 40) { k.st = 'idle'; k.x = -999; }
    }
  }
}
function xrcDrawCarts() {
  const sh = xrcSh('xrc_dp_cart');
  for (const k of XRC.carts) if (k.st === 'run') {
    if (sh.ok) drawSprite(sh, sh.first('roll') + Math.floor(time * 16) % 4, k.x, k.y, k.dir, { bottom: true });
    else { g.fillStyle = '#3a302c'; g.fillRect(Math.round(k.x) - 14, Math.round(k.y) - 20, 28, 16); g.fillStyle = '#ff9040'; g.fillRect(Math.round(k.x) - 12, Math.round(k.y) - 22, 24, 3); }
  }
}
// rails along the tunnel floor + the Forge's crane rail: drawn once into the back layer (see xrcPaintBack)
XRC_KIND.rails = (s, c) => { (XRC.backRails = XRC.backRails || []).push({ x0: s.x * TILE, x1: (s.x + (s.w || 10)) * TILE, y: c.fy }); };
XRC_KIND.crane_rail = (s, c) => { (XRC.backRails = XRC.backRails || []).push({ x0: s.x * TILE, x1: (s.x + (s.w || 10)) * TILE, y: s.y * TILE, crane: true }); };

// ---- lava geysers (D11): a vent in a slag pool bulges, then throws a column of lava
XRC_KIND.geyser = (s, c) => {
  const sh = xrcSh('xrc_dp_vent');
  const p = { type: 'xrc_geyser', x: c.cx, y: c.fy + TILE, face: 1, sh, anim: new Anim(sh, sh.has('idle') ? 'idle' : Object.keys(sh.tags)[0] || 'idle', true),
              per: s.period || 4, off: s.off || 0, h: (s.h || 6) * TILE, st: 'calm', id: 0, glow: true };
  p.update = () => {
    const t = ((time + p.off) % p.per + p.per) % p.per, st = t > p.per - 0.9 ? 'warn' : t < 1.0 ? 'erupt' : 'calm';
    if (st !== p.st) {
      p.st = st; if (sh.ok) p.anim.set(sh.has(st) ? st : 'idle', true);
      if (st === 'erupt') { p.id = ++hazardId; if (Math.abs(P.x - p.x) < 240) { sfx.fire(); noise(0.8, 300, 0.6, 0.3, 'lowpass', 0.6); } }
    }
    if (p.st === 'warn') { addLight(p.x, p.y - 6, 30, '255,120,40', 0.7); if (Math.random() < 0.4) particles.push({ x: p.x + rand(-5, 5), y: p.y - 4, vx: rand(-20, 20), vy: -rand(40, 110), g: 300, life: 0.5, kind: 'ember' }); }
    if (p.st === 'erupt') {
      const t2 = t / 1.0, hh = p.h * Math.min(1, t2 * 4) * (t2 > 0.8 ? (1 - t2) * 5 : 1);
      p.hh = hh;
      addLight(p.x, p.y - hh / 2, 60 + hh * 0.3, '255,130,50', 1);
      if (Math.random() < 0.8) particles.push({ x: p.x + rand(-6, 6), y: p.y - hh, vx: rand(-50, 50), vy: -rand(20, 80), g: 420, life: rand(0.4, 0.8), kind: 'fire' });
      if (overlap(playerHurtbox(), rect(p.x - 8, p.y - hh, p.x + 8, p.y)) && P.state !== 'dead') {
        if (!xrcSlagBounce() && hurtPlayer(52 * NGP.dmg, sign(P.x - p.x) || 1, p.id, { fire: true }) && typeof addBurn === 'function') addBurn(40);
      }
    } else p.hh = 0;
  };
  p.draw = () => {
    if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y + 2, 1, { bottom: true });
    if (p.hh > 2) {
      const x = Math.round(p.x), top = Math.round(p.y - 8 - p.hh);
      for (let y = top; y < p.y - 8; y += 2) {
        const w = 5 + Math.sin(y * 0.4 + time * 20) * 1.5 + (p.y - y < 10 ? 3 : 0);
        g.fillStyle = y - top < 6 ? '#ffe9a0' : (y + Math.floor(time * 30)) % 6 < 3 ? '#ff9a30' : '#e0501a';
        g.fillRect(Math.round(x - w / 2), y, Math.round(w), 2);
      }
      g.fillStyle = '#fff6d0'; g.fillRect(x - 1, top, 2, Math.round(p.hh * 0.7));
    }
  };
  props.push(p);
};

// ---- belts that reverse on a beat (D12, D14, D15): every belt tile in the room flips; a klaxon and chevrons warn first
XRC_KIND.beltflip = s => { XRC.belts = { per: s.period || 3, warn: s.warn || 0.9, t0: time, st: 'run', n: 0 }; };
function xrcUpdateBelts() {
  const B = XRC.belts; if (!B) return;
  const t = time - B.t0, k = t % B.per, st = k > B.per - B.warn ? 'warn' : 'run', cyc = Math.floor(t / B.per);
  if (st === 'warn' && B.st !== 'warn' && Math.abs(P.y - room.ph / 2) < room.ph) xrcSfx.klaxon();
  B.st = st;
  if (cyc !== B.n) {
    B.n = cyc;
    for (let i = 0; i < room.grid.length; i++) { const v = room.grid[i]; if (v === T_BELT_L) room.grid[i] = T_BELT_R; else if (v === T_BELT_R) room.grid[i] = T_BELT_L; }
    noise(0.25, 500, 0.8, 0.14, 'bandpass', 0.6);
  }
}
function xrcDrawBeltWarn() {
  const B = XRC.belts; if (!B || B.st !== 'warn' || Math.floor(time * 8) % 2) return;
  const tx0 = Math.max(0, Math.floor(cam.x / TILE)), tx1 = Math.min(room.w - 1, Math.floor((cam.x + W) / TILE) + 1);
  const ty0 = Math.max(0, Math.floor(cam.y / TILE)), ty1 = Math.min(room.h - 1, Math.floor((cam.y + H) / TILE) + 1);
  drawGlow(() => {
    for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
      const v = room.grid[ty * room.w + tx]; if (v !== T_BELT_L && v !== T_BELT_R) continue;
      const d = v === T_BELT_L ? 1 : -1, x = tx * TILE + 8, y = ty * TILE - 5;   // chevrons point the way it is about to run
      g.fillStyle = 'rgba(255,190,80,0.85)';
      for (let i = 0; i < 3; i++) g.fillRect(Math.round(x + d * (i - 1) * 1), y - 1 + i, 1, 1), g.fillRect(Math.round(x + d * (i - 1)), y + 3 - i, 1, 1);
    }
  });
}

// ================================================================== D13 Slag Sluices: pour the Smiths' Stair (puzzle)
// Four valves on the gallery; each pipe runs (visibly, crossing the others) from the hanging crucible to one mould. The Ox, the
// Hammer and the Flame moulds cast a stair up to the reliquary, but only from the floor up; the Grave swallows a measure.
// The crucible holds three measures; the quench lever melts everything down again. A solved stair stays cast.
const XRC_T_SLAG = 197;
SOLID_EXT.add(XRC_T_SLAG);
const XRC_SLUICE_ROUTE = [13.5, 8, 11, 9.5];     // the height each valve's pipe runs west at (by valve index)
XRC_KIND.sluice = (s, c) => {
  const key = 'x3:' + room.id + ':sluice', solved = !!SAVE.flags[key];
  const S = XRC.sluice = { s, key, molds: s.molds.map(m => ({ x0: m[0], y0: m[1], x1: m[2], y1: m[3], fill: 0, st: 'empty', heat: 0 })),
    measures: 3, wrong: 0, pour: null, solved, got: !!SAVE.flags['x3:' + room.id + ':shard'] };
  if (solved) for (let i = 0; i < 3; i++) xrcCast(S.molds[i], true);
  // valves and the quench lever: props you strike or use
  s.valves.forEach(([vx, vy, m], i) => {
    const p = { type: 'xrc_valve', x: vx * TILE + 8, y: (vy + 1) * TILE, face: 1, anim: { update() {} }, i, m, turn: 0 };
    p.prompt = () => S.pour ? null : 'Open the valve';
    p.interact = () => xrcPour(i);
    p.hurtbox = () => rect(p.x - 6, p.y - 16, p.x + 6, p.y);
    p.onHit = () => { if ((p.hitT || 0) < time) { p.hitT = time + 0.4; xrcPour(i); } };
    p.update = dt => { p.turn = approach(p.turn, S.pour && S.pour.i === i ? 1 : 0, dt * 3); };
    p.draw = () => xrcDrawValve(p.x, p.y, p.turn, i + 1);
    props.push(p);
  });
  const [rx, ry] = s.reset;
  const q = { type: 'xrc_quench', x: rx * TILE + 8, y: (ry + 1) * TILE, face: 1, anim: { update() {} }, down: 0 };
  q.prompt = () => S.solved || S.pour ? null : 'Pull the quench lever';
  q.interact = () => xrcQuench();
  q.update = dt => { q.down = approach(q.down, 0, dt * 1.5); };
  q.draw = () => {
    const x = Math.round(q.x), y = Math.round(q.y), a = -0.9 + q.down * 1.8;
    g.fillStyle = '#26262c'; g.fillRect(x - 5, y - 4, 10, 4); g.fillStyle = '#44444e'; g.fillRect(x - 4, y - 5, 8, 2);
    g.fillStyle = '#6c6c78'; for (let k = 0; k < 11; k++) g.fillRect(Math.round(x + Math.sin(a) * k), Math.round(y - 4 - Math.cos(a) * k), 1, 1);
    g.fillStyle = '#5ab0e0'; g.fillRect(Math.round(x + Math.sin(a) * 11) - 1, Math.round(y - 4 - Math.cos(a) * 11) - 1, 3, 3);
  };
  props.push(q);
  // the pillars live in a prop (drawn behind you); the reliquary on its ledge
  props.push({ type: 'xrc_molds', x: 0, y: 0, anim: { update() {} }, update: dt => xrcUpdateSluice(dt), draw: () => xrcDrawMolds() });
  const [gx, gy] = s.reward, rs = xrcSh('xrc_dp_reliquary');
  const r = { type: 'xrc_reliquary', x: gx * TILE + 8, y: (gy + 1) * TILE, face: 1, sh: rs, anim: new Anim(rs, S.got ? 'open' : 'closed', false) };
  if (S.got && rs.ok) { r.anim.i = r.anim.n - 1; r.anim.done = true; }
  r.prompt = () => S.got ? null : 'Open the reliquary';
  r.interact = () => { if (S.got) return; S.got = true; SAVE.flags['x3:' + room.id + ':shard'] = 1; if (rs.ok) r.anim.set('open', false); sfx.chest && sfx.chest(); grantItem('shard', r.x, r.y - 20); };
  r.update = () => { if (!S.got) addLight(r.x, r.y - 14, 34, '255,200,120', 0.6); };
  r.draw = () => { if (rs.ok) drawSprite(rs, r.anim.frame, r.x, r.y, 1, { bottom: true }); else { g.fillStyle = '#4a3c38'; g.fillRect(Math.round(r.x) - 7, Math.round(r.y) - 14, 14, 14); } };
  props.push(r);
};
function xrcMoldCells(m) { const out = []; for (let y = m.y0; y <= m.y1; y++) for (let x = m.x0; x <= m.x1; x++) out.push([x, y]); return out; }
function xrcCast(m, instant) {
  m.st = 'set'; m.fill = 1; m.heat = instant ? 0 : 1;
  for (const [x, y] of xrcMoldCells(m)) room.grid[y * room.w + x] = XRC_T_SLAG;
}
function xrcUncast(m) { m.st = 'empty'; m.fill = 0; m.heat = 0; for (const [x, y] of xrcMoldCells(m)) room.grid[y * room.w + x] = T_EMPTY; }
function xrcPipePath(i) {   // valve i's pipe, in px: crucible spout → the valve → west along its route → down into its mould
  const S = XRC.sluice, [vx, vy, mi] = S.s.valves[i], m = S.molds[mi], [cx, cy] = S.s.crucible;
  const ry = XRC_SLUICE_ROUTE[i] * TILE, mx = ((m.x0 + m.x1 + 1) / 2) * TILE, px = vx * TILE + 8;
  const sx = cx * TILE + 8 - 32 + 61, sy = TILE + 19;          // the crucible's spout tip (xrc_dp_crucible, hung from the ceiling)
  const hy = 22 + i * 7, bx0 = sx + 4 + i * 5;                    // each pipe leaves the spout at its own height
  return [[sx, sy], [bx0, sy], [bx0, hy], [px, hy], [px, (vy + 1) * TILE + 4], [px, ry], [mx, ry], [mx, m.y0 * TILE - 2]];
}
function xrcPour(i) {
  const S = XRC.sluice; if (!S || S.pour) return;
  const mi = S.s.valves[i][2], m = S.molds[mi];
  if (S.solved) { toast('The stair is cast. The valves are cold.'); return; }
  if (S.measures <= 0) { sfx.deny(); toast('The crucible is spent. The quench lever will melt it all down.', 3); return; }
  if (m.st === 'set') { sfx.deny(); toast('That mould is already cast.'); return; }
  S.measures--; S.pour = { i, mi, t: 0 }; xrcSfx.pour(); kitSfx && kitSfx.clunk && kitSfx.clunk();
}
function xrcQuench() {
  const S = XRC.sluice; if (!S || S.solved || S.pour) return;
  for (const m of S.molds) if (m.st !== 'empty') xrcUncast(m);
  S.measures = 3; xrcSfx.hiss(); shake = Math.max(shake, 2);
  const q = props.find(p => p.type === 'xrc_quench'); if (q) q.down = 1;
  for (let i = 0; i < 30; i++) particles.push({ x: rand(4, 20) * TILE, y: rand(10, 19) * TILE, vx: rand(-10, 10), vy: -rand(20, 50), life: rand(0.8, 1.6), kind: 'dust' });
  toast('The quench floods the moulds. The crucible fills again.', 2.6);
}
function xrcUpdateSluice(dt) {
  const S = XRC.sluice; if (!S) return;
  for (const m of S.molds) if (m.heat > 0) m.heat = Math.max(0, m.heat - dt / 3);
  const Pq = S.pour; if (!Pq) return;
  Pq.t += dt;
  const m = S.molds[Pq.mi], path = xrcPipePath(Pq.i);
  let len = 0; for (let k = 1; k < path.length; k++) len += Math.hypot(path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1]);
  Pq.len = len; Pq.run = Math.min(1, Pq.t / 1.2);
  if (Pq.t > 1.2 && !Pq.landed) {
    Pq.landed = true;
    if (Pq.mi === 3) { S.wrong++; m.st = 'grave'; m.fill = 0; toast('The Grave drinks the measure and gives nothing back.', 2.6); xrcSfx.wrong(); }
    else if (Pq.mi > 0 && S.molds[Pq.mi - 1].st !== 'set') { S.wrong++; m.st = 'crack'; toast('The mould cracks. The slag runs off hissing: nothing beneath it has set.', 3); xrcSfx.wrong(); xrcSfx.hiss(); }
    else { m.st = 'filling'; m.fill = 0; }
    if (S.wrong >= 3 && !S.hinted) { S.hinted = true; sysLater(2.5, () => toast('Trace each valve\'s pipe to its mould. The Ox first, then the Hammer, then the Flame. Leave the Grave dry.', 5)); }
  }
  if (Pq.landed) {
    const mx = ((m.x0 + m.x1 + 1) / 2) * TILE;
    if (m.st === 'filling') {
      m.fill = Math.min(1, m.fill + dt / 1.0);
      const topY = (m.y1 + 1) * TILE - (m.y1 - m.y0 + 1) * TILE * m.fill;
      // the rising slag carries anything standing in the mould up with it
      if (P.x > m.x0 * TILE - 4 && P.x < (m.x1 + 1) * TILE + 4 && P.y > topY && P.y - 20 < (m.y1 + 1) * TILE) { P.y = topY; P.vy = Math.min(P.vy, 0); P.ground = true; }
      addLight(mx, topY, 50, '255,130,50', 1);
      if (m.fill >= 1) { xrcCast(m); Pq.done = true; xrcSfx.hiss(); }
    } else if (Pq.t > 2.2) {
      if (m.st === 'crack' || m.st === 'grave') m.st = 'empty';
      Pq.done = true;
    }
  }
  if (Pq.done) {
    S.pour = null;
    if ([0, 1, 2].every(k => S.molds[k].st === 'set')) {
      S.solved = true; SAVE.flags[S.key] = 1; saveGame();
      sysLater(0.6, () => { if (typeof kitSfx !== 'undefined') kitSfx.chime(); toast('The Smiths\' Stair stands, cooling.', 3); });
    } else if (S.measures <= 0) sysLater(0.8, () => toast('The crucible is spent. The quench lever will melt it all down.', 3));
  }
}
function xrcPolyPt(path, u) {   // point at fraction u along a polyline
  let L = 0; const seg = []; for (let k = 1; k < path.length; k++) { const l = Math.hypot(path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1]); seg.push(l); L += l; }
  let d = u * L;
  for (let k = 0; k < seg.length; k++) { if (d <= seg[k] || k === seg.length - 1) { const t = seg[k] ? Math.min(1, d / seg[k]) : 0; return [lerp(path[k][0], path[k + 1][0], t), lerp(path[k][1], path[k + 1][1], t)]; } d -= seg[k]; }
  return path[path.length - 1];
}
function xrcDrawMolds() {
  const S = XRC.sluice; if (!S) return;
  const gl = xrcSh('xrc_dp_glyphs');
  S.molds.forEach((m, i) => {
    const X0 = m.x0 * TILE, X1 = (m.x1 + 1) * TILE, Y0 = m.y0 * TILE, Y1 = (m.y1 + 1) * TILE;
    if (m.st === 'set' || m.st === 'filling') {   // cast slag: molten, cooling to basalt with glowing seams
      const top = m.st === 'filling' ? Y1 - (Y1 - Y0) * m.fill : Y0, heat = m.st === 'filling' ? 1 : m.heat;
      for (let y = Math.round(top); y < Y1; y += 2) for (let x = X0 + 1; x < X1 - 1; x += 2) {
        const n = hash2(x >> 1, y >> 1), hot = heat * (0.6 + 0.4 * n);
        g.fillStyle = hot > 0.55 ? (n > 0.5 ? '#ffb040' : '#e05a18') : hot > 0.2 ? (n > 0.6 ? '#a8401a' : '#4a2418') : (n > 0.85 ? '#7a2a10' : n > 0.4 ? '#2e2426' : '#241c1e');
        g.fillRect(x, y, 2, 2);
      }
      if (heat > 0.05) addLight((X0 + X1) / 2, (top + Y1) / 2, 40, '255,120,40', 0.8 * heat);
    } else if (m.st === 'crack' || m.st === 'grave') {
      g.fillStyle = 'rgba(255,120,40,0.5)'; for (let y = Y0 + 4; y < Y1; y += 3) g.fillRect(X0 + 4 + (y % 5), y, 2, 2);
    }
    // the iron casting frame and its glyph plate
    g.fillStyle = '#26262c'; g.fillRect(X0 - 2, Y0 - 2, 2, Y1 - Y0 + 2); g.fillRect(X1, Y0 - 2, 2, Y1 - Y0 + 2);
    g.fillStyle = '#44444e'; for (let y = Y0; y < Y1; y += 12) { g.fillRect(X0 - 3, y, X1 - X0 + 6, 2); }
    if (gl.ok) drawSprite(gl, gl.first('g' + i), (X0 + X1) / 2, Y0 - 12, 1, { center: true });
  });
  const Pq = S.pour;
  if (Pq) drawGlow(() => {   // the measure running through its pipe, then pouring into the mould
    const path = xrcPipePath(Pq.i), u = Pq.run || 0;
    for (let k = 0; k <= 40; k++) { const t = k / 40 * u, [x, y] = xrcPolyPt(path, t); g.fillStyle = k % 3 ? '#ff8a2a' : '#ffd070'; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 3, 3); }
    if (u >= 1 && !Pq.done) { const [x, y] = path[path.length - 1]; g.fillStyle = '#ffb040'; g.fillRect(Math.round(x) - 1, Math.round(y), 3, 18); }
  });
  // the crucible's measures (three pips on its lip)
  const [cx, cy] = S.s.crucible;
  const cs = xrcSh('xrc_dp_crucible');
  if (cs.ok) { const pouring = S.pour && !S.pour.landed; drawSprite(cs, pouring ? cs.first('pour') + Math.floor(time * 12) % 4 : cs.first('idle'), cx * TILE + 8, TILE, 1, { pivot: [32, 0] }); }
  addLight(cx * TILE + 8, TILE + 30, 40, '255,130,50', 0.5 + 0.1 * S.measures);
  for (let k = 0; k < 3; k++) { g.fillStyle = k < S.measures ? '#ffb040' : '#3a2a28'; g.fillRect(cx * TILE - 1 + k * 6, TILE + 58, 4, 2); }
}
function xrcDrawValve(x, y, turn, n) {
  x = Math.round(x); y = Math.round(y);
  g.fillStyle = '#26262c'; g.fillRect(x - 2, y - 12, 4, 12);
  const a = turn * Math.PI * 2;
  const C = XRC_PIPE_COL[n - 1] || XRC_PIPE_COL[0];
  g.fillStyle = C[1]; for (let k = 0; k < 16; k++) { const q = a + k * Math.PI / 8; g.fillRect(Math.round(x + Math.cos(q) * 5), Math.round(y - 14 + Math.sin(q) * 5), 1, 1); }
  g.fillStyle = C[0]; for (let k = 0; k < 4; k++) { const q = a + k * Math.PI / 2; g.fillRect(Math.round(x + Math.cos(q) * 3), Math.round(y - 14 + Math.sin(q) * 3), 1, 1); }
  g.fillStyle = C[1]; g.fillRect(x - 1, y - 15, 3, 3);
  g.fillStyle = '#d8a850'; for (let k = 0; k < n; k++) g.fillRect(x - 4 + k * 2, y - 3, 1, 2);   // tally marks: valve 1…4
}

// ================================================================== back-layer art: the Stormwarden, rails, the sluice pipes
{
  const base = renderRoomLayers;
  renderRoomLayers = function (R) { base(R); if (R && R.xrcReady) xrcPaintBack(R); };
}
function xrcPaintBack(R) {
  const bx = R.back && R.back.getContext('2d'); if (!bx) return;
  const def = R.def;
  if (def.biome === 'crown' && def.indoor && def.x3) {   // inside the living wood: the Crown never had indoor walls, so paint bark
    const sh = tileSheet('crown'); bx.clearRect(0, 0, R.pw, R.ph);
    for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {
      if (isSolidT(R.grid[y * R.w + x])) continue;
      drawTile(bx, sh, (hash2(x * 3, y * 7) < 0.4 ? 16 : 0), x * TILE, y * TILE);
      const k = 0.62 + 0.12 * hash2(x >> 1, y >> 1);
      bx.fillStyle = `rgba(28,18,22,${k})`; bx.fillRect(x * TILE, y * TILE, TILE, TILE);
    }
    for (let i = 0; i < R.w * R.h / 40; i++) {   // knots and seams of sap-light in the bark
      const x = Math.floor(hash2(i, 91) * R.pw), y = Math.floor(hash2(i, 92) * R.ph);
      if (isSolidT(R.grid[Math.floor(y / TILE) * R.w + Math.floor(x / TILE)])) continue;
      bx.fillStyle = 'rgba(255,214,130,0.18)'; bx.fillRect(x, y, 1, 3 + Math.floor(hash2(i, 93) * 6));
    }
    for (let y = 0; y < R.h; y++) for (let x = 0; x < R.w; x++) {   // the deco chars still belong on top
      const d = { x: 42, r: 43, k: 44, b: 45 }[R.def.map[y][x]]; if (d !== undefined) drawTile(bx, sh, d, x * TILE, y * TILE);
    }
  }
  for (const s of def.spawns || []) {
    if (s.t !== 'xrc') continue;
    if (s.kind === 'colossus') {
      const sh = xrcSh('xrc_sp_colossus'); if (!sh.ok) continue;
      const f = sh.frames[sh.first('idle')], x = s.x * TILE + 8 - f.w / 2, y = (s.y + 1) * TILE + 6 - f.h;
      bx.save(); bx.globalAlpha = 0.92; bx.drawImage(sh.img, f.x, f.y, f.w, f.h, Math.round(x), Math.round(y), f.w, f.h); bx.restore();
    }
    if (s.kind === 'rails') {
      const y = (s.y + 1) * TILE, x0 = s.x * TILE, x1 = (s.x + (s.w || 10)) * TILE;
      bx.fillStyle = '#5a4a44'; bx.fillRect(x0, y - 3, x1 - x0, 1); bx.fillStyle = '#8a7060'; bx.fillRect(x0, y - 4, x1 - x0, 1);
      for (let x = x0; x < x1; x += 7) { bx.fillStyle = '#2a1c18'; bx.fillRect(x, y - 2, 4, 2); }
    }
    if (s.kind === 'crane_rail') {
      const y = s.y * TILE + 6, x0 = s.x * TILE, x1 = (s.x + (s.w || 10)) * TILE;
      bx.fillStyle = '#16141a'; bx.fillRect(x0, y, x1 - x0, 5); bx.fillStyle = '#44444e'; bx.fillRect(x0, y, x1 - x0, 1); bx.fillStyle = '#2a2830'; bx.fillRect(x0, y + 4, x1 - x0, 1);
      for (let x = x0; x < x1; x += 24) { bx.fillStyle = '#6c6c78'; bx.fillRect(x, y + 1, 2, 2); bx.fillStyle = '#16141a'; bx.fillRect(x + 11, y - 6, 2, 6); }
    }
    if (s.kind === 'sluice' && XRC.sluice) {   // the pipes, crossing each other on the back wall: each its own metal
      for (let i = 0; i < s.valves.length; i++) {
        const path = xrcPipePath(i), C = XRC_PIPE_COL[i];
        for (const pass of [0, 1]) for (let k = 1; k < path.length; k++) {
          const [ax, ay] = path[k - 1], [bx2, by] = path[k], n = Math.max(1, Math.ceil(Math.hypot(bx2 - ax, by - ay))), vert = Math.abs(ax - bx2) < 1;
          for (let j = 0; j <= n; j++) {
            const x = Math.round(lerp(ax, bx2, j / n)), y = Math.round(lerp(ay, by, j / n));
            if (pass === 0) { bx.fillStyle = '#0a080a'; bx.fillRect(x - 3, y - 3, 7, 7); continue; }
            bx.fillStyle = C[0]; bx.fillRect(x - 2, y - 2, 5, 5);
            bx.fillStyle = C[1]; if (vert) bx.fillRect(x - 2, y, 1, 1); else bx.fillRect(x, y - 2, 1, 1);
            if (j % 14 === 7) { bx.fillStyle = C[2]; if (vert) bx.fillRect(x - 3, y, 7, 2); else bx.fillRect(x, y - 3, 2, 7); }
          }
          if (pass === 1) { bx.fillStyle = C[2]; bx.fillRect(Math.round(bx2) - 3, Math.round(by) - 3, 7, 7); bx.fillStyle = C[1]; bx.fillRect(Math.round(bx2) - 2, Math.round(by) - 2, 4, 4); }
        }
      }
    }
  }
}
const XRC_PIPE_COL = [['#7a3e24', '#b8683a', '#4a2416'], ['#4e5260', '#8a90a0', '#2a2c36'], ['#7a6a2c', '#c0a850', '#4a3e18'], ['#3e5a4a', '#6a9a7a', '#223a2c']];   // copper, iron, brass, verdigris

// ================================================================== The Last Field: wheat that sways and parts around you
XRC_KIND.wheat = () => {
  const W0 = [], rows = room.h, cols = room.w;
  const skip = x => x < 2 || x > 105;                              // the old ash (west) and the storm-cliff (east)
  for (let tx = 0; tx < cols; tx++) {
    if (skip(tx)) continue;
    let ty = 0; while (ty < rows && !isSolidT(room.grid[ty * cols + tx])) ty++;
    if (ty >= rows || ty < 4) continue;
    const base = ty * TILE, thin = (tx >= 102 && tx <= 105) || (tx >= 35 && tx <= 39) || (tx >= 65 && tx <= 67) || tx === 13 || tx === 5 ? 0.35 : 1;
    for (let k = 0; k < 7; k++) {
      if (hash2(tx * 7 + k, 11) > thin) continue;
      const front = hash2(tx, k * 3 + 5) < 0.34 && !(tx >= 5 && tx <= 13);   // the nest's hollow: only the far wheat stands behind it
      W0.push({ x: tx * TILE + (k + hash2(tx, k)) * (TILE / 7), y: base + 1, h: (front ? 11 : 16) + Math.floor(hash2(tx * 3, k) * (front ? 8 : 13)),
                ph: hash2(k, tx) * 6.28, tone: Math.floor(hash2(tx + k, 9) * 3), front, bend: 0 });
    }
  }
  XRC.wheat = W0;
  props.push({ type: 'xrc_wheat', x: 0, y: 0, anim: { update() {} }, update: dt => xrcUpdateWheat(dt), draw: () => xrcDrawWheat(SYS.vista ? 'all' : 'back') });
};
function xrcUpdateWheat(dt) {
  const Wt = XRC.wheat; if (!Wt) return;
  const moving = Math.abs(P.vx) > 20 || P.state === 'roll';
  for (const s of Wt) {
    if (s.x < cam.x - 40 || s.x > cam.x + W + 40) { s.bend = 0; continue; }
    const dx = s.x - P.x, near = Math.abs(dx) < 24 && P.y > s.y - s.h - 14 && P.y < s.y + 6;
    const want = near ? sign(dx || 1) * (1 - Math.abs(dx) / 24) * (moving ? 13 : 9) : 0;
    s.bend = approach(s.bend, want, dt * (near ? 90 : 26));
    if (near && moving && Math.random() < 0.004) particles.push({ x: s.x, y: s.y - s.h, vx: sign(dx) * rand(10, 30), vy: -rand(8, 24), life: rand(1.2, 2.4), kind: Math.random() < 0.5 ? 'xrc_seed' : 'xrc_wheat', pet: true });
  }
}
const XRC_WHEAT_COL = { back: [['#5a3a22', '#6e4826', '#7c5228'], ['#b27a34', '#c08a3c', '#d09a44']], front: [['#8a5a2c', '#9e6a30', '#b07a34'], ['#e0aa4c', '#ecbc5a', '#f7d06c']] };
function xrcDrawWheat(which) {
  const Wt = XRC.wheat; if (!Wt) return;
  const vis = which === 'all' ? null : [cam.x - 30, cam.x + W + 30];
  const wind = 1.6 * Math.sin(time * 0.9) + 0.8;
  for (const layer of (which === 'all' ? ['back', 'front'] : [which])) {
    const C = XRC_WHEAT_COL[layer];
    for (let tone = 0; tone < 3; tone++) {
      g.fillStyle = C[0][tone]; g.beginPath();
      const heads = [];
      for (const s of Wt) {
        if (s.front !== (layer === 'front') || s.tone !== tone) continue;
        if (vis && (s.x < vis[0] || s.x > vis[1])) continue;
        const sway = (2.2 * Math.sin(time * 1.3 - s.x * 0.018 + s.ph * 0.2) + 0.9 * Math.sin(time * 2.4 + s.ph)) * (0.6 + 0.4 * wind) + s.bend;
        for (let i = 0; i < s.h; i += 3) { const t = i / s.h; g.rect(Math.round(s.x + sway * t * t), Math.round(s.y - i - 3), 1, 3); }
        heads.push([Math.round(s.x + sway), Math.round(s.y - s.h), sway]);
      }
      g.fill();
      g.fillStyle = C[1][tone]; g.beginPath();
      for (const [x, y, sw] of heads) { const lx = sw > 1.5 ? 1 : sw < -1.5 ? -1 : 0; g.rect(x - 1, y - 1, 2, 5); g.rect(x + lx, y - 3, 1, 2); }
      g.fill();
      g.fillStyle = layer === 'front' ? '#ffe9a0' : '#e8b85a'; g.beginPath();
      for (const [x, y] of heads) g.rect(x, y - 1, 1, 1);
      g.fill();
    }
  }
}

// ---- the nest's egg: take it, and it teaches Ember Hatchling
XRC_KIND.egg = (s, c) => {
  const sh = xrcSh('xrc_lf_egg'), taken = () => !!SAVE.flags['xrc:egg'];
  const p = { type: 'xrc_egg', x: c.cx, y: c.fy + 2, face: 1, sh, anim: new Anim(sh, taken() ? 'gone' : 'glow', true) };
  p.prompt = () => taken() || XRC.hatch ? null : 'Take the egg';
  p.interact = () => { if (!taken() && !XRC.hatch) xrcHatch(p); };
  p.update = () => { if (!taken()) { addLight(p.x, p.y - 10, 44 + Math.sin(time * 2) * 4, '255,150,70', 0.9); if (Math.random() < 0.05) particles.push({ x: p.x + rand(-5, 5), y: p.y - rand(6, 16), vx: 0, vy: -rand(6, 14), life: 1, kind: 'ember' }); } };
  p.draw = () => { if (sh.ok) drawSprite(sh, p.anim.frame, p.x, p.y, 1, { bottom: true }); };
  props.push(p);
};
function xrcHatch(egg) {
  const H = XRC.hatch = { t: 0, egg, x: egg.x, y: egg.y - 14, step: 0 };
  xrcSfx.crack(); shake = Math.max(shake, 2); P.ctrlLock = 5; P.vx = 0;
  if (typeof setP === 'function' && !['idle', 'run'].includes(P.state)) setP('idle', 'idle', true);
}
function xrcUpdateHatch(dt) {
  const H = XRC.hatch; if (!H) return;
  H.t += dt; P.ctrlLock = Math.max(P.ctrlLock || 0, 0.1); P.inv = Math.max(P.inv, 0.2);
  const sh = xrcSh('xrc_cub');
  if (H.step === 0 && H.t > 0.5) { H.step = 1; xrcSfx.crack(); for (let i = 0; i < 24; i++) particles.push({ x: H.x + rand(-4, 4), y: H.y + rand(-4, 6), vx: rand(-70, 70), vy: -rand(20, 120), g: 200, life: rand(0.5, 1.1), kind: i % 3 ? 'ember' : 'gold' });
    SAVE.flags['xrc:egg'] = 1; if (H.egg.sh.ok) H.egg.anim.set('gone', true);
    H.c = { x: H.x, y: H.y, anim: new Anim(sh, 'appear', false), face: -1 }; xrcSfx.hatch(); }
  if (H.c) {
    H.c.anim.update(dt);
    if (H.step === 1 && (H.c.anim.done || H.t > 1.4)) { H.step = 2; H.c.anim = new Anim(sh, 'fly', true); xrcSfx.chirp(); H.a0 = Math.atan2(H.c.y - (P.y - 30), H.c.x - P.x); }
    if (H.step === 2) {   // a first flight: one slow circle around you
      const k = (H.t - 1.4) / 2.4, a = H.a0 + k * Math.PI * 2, r = 26 - k * 8;
      const nx = P.x + Math.cos(a) * r * 1.3, ny = P.y - 30 + Math.sin(a) * r * 0.7;
      H.c.face = nx >= H.c.x ? 1 : -1; H.c.x = nx; H.c.y = ny;
      if (Math.random() < 0.3) particles.push({ x: H.c.x, y: H.c.y, vx: rand(-10, 10), vy: rand(-10, 10), life: 0.6, kind: 'ember' });
      if (k >= 1) { H.step = 3; H.c.anim = new Anim(sh, 'vanish', false); H.t3 = H.t; }
    }
    if (H.step === 3) {
      H.c.x = lerp(H.c.x, P.x, dt * 6); H.c.y = lerp(H.c.y, P.y - 16, dt * 6);
      if (H.t - H.t3 > 0.7) {
        H.step = 4; H.c = null; flashScreen = Math.max(flashScreen, 0.3);
        for (let i = 0; i < 30; i++) particles.push({ x: P.x + rand(-8, 8), y: P.y - rand(0, 26), vx: rand(-60, 60), vy: -rand(20, 90), life: rand(0.5, 1.2), kind: i % 2 ? 'ember' : 'gold' });
        grantItem('sp:ember_hatchling', P.x, P.y - 30);
        sysLater(4.2, () => { if (room && room.id === 'LF1' && typeof sysOpenPage === 'function') sysOpenPage('rc_6', { fromWorld: true }); });
      }
    }
    if (H.c) addLight(H.c.x, H.c.y, 40, '255,160,80', 0.9);
  }
  if (H.step === 4 && H.t > 4.5) { XRC.hatch = null; P.ctrlLock = 0; }
}
function xrcDrawHatch() {
  const H = XRC.hatch; if (!H || !H.c) return;
  const sh = xrcSh('xrc_cub'); if (sh.ok) drawSprite(sh, H.c.anim.frame, H.c.x, H.c.y, H.c.face, { center: true });
}

// ---- The Last Field's music: the Spire's bells turned warm, and a slow lullaby over the drone
const XRC_LULLABY = [[0, 2], [4, 1], [7, 1], [9, 3], [7, 1], [4, 2], [2, 2], [0, 4], [4, 2], [7, 1], [12, 1], [11, 3], [9, 1], [7, 2], [4, 2], [7, 4],
                     [9, 2], [7, 1], [4, 1], [2, 3], [4, 1], [0, 2], [-3, 2], [0, 4], [2, 1], [4, 1], [7, 2], [4, 1], [2, 1], [0, 6], [null, 4]];
function xrcMusic() {
  if (!AC || muted || !room || room.id !== 'LF1' || !['play', 'sysread'].includes(state)) { XRC.musAt = null; return; }
  const now = AC.currentTime, beat = 0.62, root = (ROOTS.lastfield || 46.25) * 8;
  if (XRC.musAt == null || XRC.musAt < now - 1) { XRC.musAt = now + 1.2; XRC.musI = 0; }
  const dest = MUSIC.gain || null, v = SETTINGS.music ?? 1;
  while (XRC.musAt < now + 0.25) {
    const [n, d] = XRC_LULLABY[XRC.musI % XRC_LULLABY.length], at = XRC.musAt - now;
    if (n !== null) {
      const f = root * Math.pow(2, n / 12);
      tone(f, d * beat * 1.6, 0.05 * v, 'sine', 1, at, dest); tone(f * 2, d * beat * 0.8, 0.012 * v, 'sine', 1, at + 0.01, dest);
      if (XRC.musI % 4 === 0) tone(root / 2 * Math.pow(2, ([0, 7, 9, 5][(XRC.musI / 4 | 0) % 4]) / 12), beat * 7, 0.03 * v, 'triangle', 1, at, dest);
    }
    XRC.musAt += d * beat; XRC.musI++;
  }
}

// ================================================================== parallax: The Last Field's five layers; the vistas' extra layers
function xrcLayer(sh, fac, vfac, oy0 = 0, drift = 0, alpha = 1) {
  if (!sh || !sh.ok) return;
  const f = sh.frames[sh.first('loop')];
  const ox = -(((cam.x * fac + drift) % f.w) + f.w) % f.w, oy = Math.round(oy0 - cam.y * vfac);
  if (alpha < 1) g.globalAlpha = alpha;
  for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy, f.w, f.h);
  g.globalAlpha = 1;
}
function xrcLastFieldSky() {
  g.fillStyle = '#140f2a'; g.fillRect(0, 0, W, H);
  const my = room ? clamp(room.ph - H, 1, 999) : 1, k = clamp(cam.y / my, 0, 1);   // 0 at the top of the room, 1 at the bottom
  const lift = Math.round((1 - k) * 34);
  xrcLayer(xrcSh('xrc_lf_sky'), 0.015, 0, lift * 0.3);
  // god-rays from the low sun, breathing slowly
  const sunX = 356 - cam.x * 0.015 % 512, sunY = 100 + lift * 0.3;
  g.save(); g.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 7; i++) {
    const a = -Math.PI * 0.5 + (i - 3) * 0.32 + Math.sin(time * 0.15 + i) * 0.04, len = 260, w = 0.05 + 0.02 * Math.sin(time * 0.4 + i * 1.7);
    g.fillStyle = `rgba(255,214,150,${0.02 + 0.012 * Math.sin(time * 0.3 + i)})`;
    g.beginPath(); g.moveTo(sunX, sunY); g.lineTo(sunX + Math.cos(a - w) * len, sunY + Math.sin(a - w) * len); g.lineTo(sunX + Math.cos(a + w) * len, sunY + Math.sin(a + w) * len); g.closePath(); g.fill();
  }
  g.restore();
  xrcLayer(xrcSh('xrc_lf_clouds'), 0.03, 0.01, lift * 0.35, time * 2.2);
  xrcLayer(xrcSh('xrc_lf_far'), 0.08, 0.03, lift * 0.55 + 6);
  xrcLayer(xrcSh('xrc_lf_mid'), 0.18, 0.06, lift * 0.8 + 10);
  xrcLayer(xrcSh('xrc_lf_near'), 0.36, 0.12, lift + 18);
  addLight(cam.x + sunX, cam.y + sunY + 40, 200, '255,190,120', 0.25, { shadow: false });
}
function xrcSpireLayers(extra) {   // the Spire's own two layers with an extra one between them (vista rooms)
  const A = AREAS.spire; g.fillStyle = A.tint; g.fillRect(0, 0, W, H);
  const far = sheet('bg_spire_far'), mid = sheet('bg_spire_mid'), tA = Math.floor(time * 6);
  const layer = (sh, fac, vfac) => { if (!sh.ok) return; const t = sh.tag('loop'), f = sh.frames[t.from + (tA % (t.to - t.from + 1))];
    const ox = -((cam.x * fac) % f.w + f.w) % f.w, oy = Math.round(clamp(-cam.y * vfac, -(f.h - H) - 20, 20));
    for (let x = Math.round(ox); x < W; x += f.w) g.drawImage(sh.img, f.x, f.y, f.w, f.h, x, oy + (H - f.h), f.w, f.h); };
  layer(far, 0.08, 0.02);
  if (extra) extra();
  layer(mid, 0.3, 0.08);
}
function xrcBeam(px, py, dir = 1) {   // the lighthouse's turning beam across the storm (screen space, additive)
  const a = Math.sin(time * 0.55) * 0.5 + (dir > 0 ? 0 : Math.PI), sx = px - cam.x * 0.3, sy = py - cam.y * 0.3;
  g.save(); g.globalCompositeOperation = 'lighter';
  for (const [w, al] of [[0.09, 0.05], [0.05, 0.07], [0.02, 0.08]]) {
    g.fillStyle = `rgba(255,226,170,${al})`; g.beginPath(); g.moveTo(sx, sy);
    g.lineTo(sx + Math.cos(a - w) * 700, sy + Math.sin(a - w) * 700); g.lineTo(sx + Math.cos(a + w) * 700, sy + Math.sin(a + w) * 700); g.closePath(); g.fill();
  }
  g.restore();
}
{
  const base = drawParallax;
  drawParallax = function () {
    if (!room) return base();
    if (room.def.biome === 'lastfield') return xrcLastFieldSky();
    if (room.id === 'SP15') return xrcSpireLayers(() => { xrcLayer(xrcSh('xrc_sp_seaview'), 0.12, 0.05, -36); xrcBeam(250, 40, -1); });
    if (room.id === 'X11') {
      const A = AREAS.crown; g.fillStyle = A.tint; g.fillRect(0, 0, W, H);
      xrcLayer(sheet('bg_crown_far'), 0.08, 0.02, clamp(-cam.y * 0.02, -20, 20));
      xrcLayer(xrcSh('xrc_cr_panorama'), 0.14, 0.05, 52);
      return;
    }
    base();
    if (room.id === 'SP8') xrcBeam(-60, 30, 1);
  };
}

// ================================================================== Petal Drift (X9): the kit's movers are great drifting petals
{
  const base = kitDrawSlab;
  kitDrawSlab = function (o, x0, y0, alpha = 1, crack = 0, jx = 0, jy = 0) {
    if (!(o && o.spec && o.spec.petal)) return base.apply(this, arguments);
    const w = o.w, X = Math.round(x0 + jx), Y = Math.round(y0 + jy), tilt = Math.sin(time * 1.1 + X * 0.05) * 1.2;
    g.save(); g.globalAlpha = alpha;
    for (const pass of [0, 1]) for (let i = -4; i < w + 4; i++) {   // pass 0: a dark rim so the petal reads against the pale sky
      const t = (i + 4) / (w + 8), th = Math.max(1, Math.round(11 * Math.sin(Math.PI * t))), dy = Math.round(tilt * (t - 0.5) * 2 + (1 - Math.sin(Math.PI * t)) * 3);
      if (pass === 0) { g.fillStyle = '#3a2030'; g.fillRect(X + i, Y + dy - 1, 1, th + 2); continue; }
      g.fillStyle = '#f4e2d6'; g.fillRect(X + i, Y + dy, 1, th);
      g.fillStyle = '#d8a8ae'; g.fillRect(X + i, Y + dy + Math.max(1, th - 3), 1, Math.min(3, th));
      g.fillStyle = '#fff8f0'; g.fillRect(X + i, Y + dy, 1, 1);
      if (Math.abs(i - w / 2) < 1.5 && th > 3) { g.fillStyle = '#d9a84a'; g.fillRect(X + i, Y + dy + 1, 1, th - 2); }
      else if ((i + 40) % 7 === 0 && th > 4) { g.fillStyle = '#e8c8c4'; g.fillRect(X + i, Y + dy + 2, 1, th - 4); }
    }
    g.restore();
    addLight(X + w / 2, Y + 2, 24, '255,245,230', 0.3);
  };
}

// ================================================================== soft draughts (wide updraft fields)
const XRC_SOFT_UPDRAFT = new Set(['SP16', 'SP17', 'X12']);
function xrcDrawDraughts() {
  for (const u of room.updrafts || []) {
    if (u.x1 < cam.x || u.x0 > cam.x + W || u.y1 < cam.y || u.y0 > cam.y + H) continue;
    const hgt = u.y1 - u.y0;
    for (let k = 0; k < 3; k++) {
      const y = u.y1 - ((time * (70 + k * 25) + hash2(u.x0, k) * 997) % hgt), a = 0.16 + 0.1 * Math.sin(time * 2 + k + u.x0);
      g.fillStyle = `rgba(215,230,245,${a})`; g.fillRect(u.x0 + 3 + k * 4, Math.round(y), 1, 7);
    }
  }
}

// ================================================================== drop markers over the wing's floor grates (↓ + jump to go through)
XRC_KIND.dropmark = (s, c) => {
  if (s.flag && !SAVE.flags[s.flag]) return;   // the grate is still sealed
  const p = { type: 'xrc_dropmark', x: c.cx, y: c.fy, face: 1, anim: { update() {} }, k: 0, hinted: false };
  p.update = dt => {
    const near = Math.abs(P.x - p.x) < 28 && Math.abs(P.y - p.y) < 20;
    p.k = approach(p.k, near ? 1 : 0.35, dt * 3);
    if (near && P.ground && !p.hinted && !XRC.hint['drop' + room.id]) { p.hinted = XRC.hint['drop' + room.id] = true;
      toast(matchMedia('(pointer: coarse)').matches ? 'Hold ▼ and press Jump to drop through the grate' : 'Hold ↓ and press Space to drop through the grate', 3.5); }
  };
  p.draw = () => {
    if (!isSolidT(tileAt(Math.floor(p.x / TILE), Math.floor(p.y / TILE))) && tileAt(Math.floor(p.x / TILE), Math.floor(p.y / TILE)) !== T_PLAT) return;
    const x = p.x, y = p.y - 16 + Math.sin(time * 4) * 2, a = (0.35 + 0.35 * Math.sin(time * 4)) * p.k + 0.1;
    drawGlow(() => { g.fillStyle = `rgba(255,190,110,${a})`;
      for (let i = 0; i < 4; i++) g.fillRect(Math.round(x - 4 + i), Math.round(y + i), 8 - i * 2, 1);
      g.fillRect(Math.round(x - 1), Math.round(y - 5), 2, 5); });
  };
  props.push(p);
};

// ================================================================== the Crow's Nest: sea-spray makes every wall too slick to hold
HOOKS.update.push(() => {
  if (!room || room.id !== 'SP17' || P.state !== 'wall') return;
  setP('air', 'jump_fall', false); P.wallDir = 0;
  if (!XRC.hint.slick) { XRC.hint.slick = 1; toast('The rock is slick with sea-spray. Nothing here will hold you.', 3); }
});

// ================================================================== respawn safety: never put the player back into a vent, a bolt or a rail
SAFE_CHECKS.push((x, y) => {
  if (!room || XRC.roomObj !== room) return false;
  for (const p of props) if (p.type === 'xrc_geyser' && Math.abs(x - p.x) < 20 && y > p.y - p.h - 8 && y <= p.y + 4) return true;
  if (XRC.bolts) for (const c of XRC.bolts.cols) if (Math.abs(x - c.x) < 14) return true;
  for (const k of XRC.carts) if (Math.abs(y - k.y) < 6) return true;   // the rails: carts come through on a beat
  return false;
});

// ================================================================== room entry, per-frame, rendering
HOOKS.enter.push(def => {
  xrcEnsure();
  XRC.lighthouse = XRC.panorama = XRC.petals = false; XRC.hatch = null;
  for (const s of def.spawns || []) if (s.t === 'xrc' && ['beam', 'panorama', 'petals'].includes(s.kind)) XRC_KIND[s.kind](s);
  room.xrcReady = true; xrcPaintBack(room);
  // wide draught fields: the stock updraft sprite per column turns into a wall of noise, so draw them as soft rising streaks
  if (XRC_SOFT_UPDRAFT.has(def.id)) { props = props.filter(p => p.type !== 'updraft'); props.push({ type: 'xrc_draught', x: 0, y: 0, anim: { update() {} }, glow: true, draw: xrcDrawDraughts }); }
  if (def.id === 'LF1' && !SAVE.hints.xrc_lf) { SAVE.hints.xrc_lf = 1; sysLater(1.2, () => xrcSfx.chime(0.75)); }
  if (def.id === 'D13' && !SAVE.hints.xrc_sluice) { SAVE.hints.xrc_sluice = 1; sysLater(1.4, () => toast('A crucible hangs over empty moulds. Pipes run from it through four valves.', 4)); }
  if (def.id === 'SP16' && !SAVE.items.gale && !SAVE.hints.xrc_gale) { SAVE.hints.xrc_gale = 1; sysLater(1.2, () => toast('Warm air roars up out of the storm. Something light could ride it.', 4)); }
});
HOOKS.update.push(dt => {
  xrcMusic();
  if (!room) return;
  xrcEnsure(); XRC.t += dt;
  xrcUpdateCub(dt); xrcUpdateShots(dt); xrcUpdateHatch(dt);
  xrcUpdateBolts(); xrcUpdateCarts(dt); xrcUpdateBelts();
  if (room.def.biome === 'lastfield') {   // warm wind: seeds and embers drifting across the field
    if (Math.random() < 0.35) particles.push({ x: cam.x - 10, y: cam.y + rand(20, H - 40), vx: rand(20, 45), vy: rand(-6, 6), life: rand(6, 10), kind: Math.random() < 0.7 ? 'xrc_seed' : 'ember', pet: true, amb: false, sway: rand(0, 6) });
  }
  if (XRC.petals && Math.random() < 0.25) particles.push({ x: cam.x + rand(-20, W), y: cam.y - 6, vx: rand(4, 18), vy: rand(8, 20), life: rand(6, 10), kind: 'petal', pet: true });
});
HOOKS.render.push(() => {
  if (!room) return;
  if (XRC.carts.length) xrcDrawCarts();
  if (XRC.bolts) xrcDrawBolts();
  if (XRC.belts) xrcDrawBeltWarn();
  if (XRC.wheat && !SYS.vista) xrcDrawWheat('front');
  xrcDrawHatch(); xrcDrawCub();
});

// ---- debug handle for headless tests (tools/shots/rc)
if (window.__game) window.__game.xrc = { XRC, pour: xrcPour, quench: xrcQuench, hatch: () => { const e = props.find(p => p.type === 'xrc_egg'); if (e) e.interact(); }, T_SLAG: XRC_T_SLAG,
  get room() { return room; }, get props() { return props; }, sys: () => SYS, kit: () => KIT };

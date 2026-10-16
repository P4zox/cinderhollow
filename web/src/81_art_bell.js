// ------------------------------------------------------------------ v17: the Warbell's own art, FUNERAL PEAL (docs/v17/bell_art.md)
// Swing the bell round and over the back, drive it mouth-first into the floor: a ring of sound rolls away along the floor
// both ways. Blunt (the bell's x1.3 stance damage), it swallows enemy missiles it passes through, and it rings the struck
// into the staff (78_mech_bell.js): every foe the forward ring strikes rings Ember, every foe the backward ring strikes
// rings Ash -- 2 notes at most (3 held). The peal plays no toll itself and does not empty the staff: it writes the notes the
// next Perform plays. A whiff rings nothing, as with every bell blow.
// Hold (the art key, >= 0.6 s, the bell hung over the back shoulder): the ring rolls further, hits harder, and stuns small
// foes. JS globals use fpl / FPL_ (bel / BEL_ belong to 78_mech_bell, `tolling_blow` is the Bell Hammer's unrelated art).
// Animation: art_funeral_peal (art/player_v17_bell.py): 3 = the charge hold, 5 = the impact (release). Icon: a_funeral_peal
// in ui_icons17_bell (art/gen_ui17_bell.py).
const FPL_TUNE = { fp: 14, cd: 6.5 };
const FPL = {
  tap: { mul: 2.8, poise: 70, range: 88, h: 32, speed: 300, notes: 2, stun: 0 },
  hold: { mul: 3.4, poise: 100, range: 140, h: 38, speed: 320, notes: 3, stun: 1.8, bossStance: 30 },
  origin: 14,      // px ahead of the feet: where the bell's lip bites the floor
  waves: [],
};
registerGear({ arts: {
  funeral_peal: { name: 'Funeral Peal', fp: FPL_TUNE.fp, cd: FPL_TUNE.cd, iconSheet: 'ui_icons17_bell',
    desc: 'Drive the bell into the floor: a ring of sound rolls out both ways, crushing stance and swallowing missiles. Each foe it strikes rings a note into the staff, Ember ahead and Ash behind. Hold for a ring that rolls further and stuns.' },
} }, 'ui_icons17_bell');
if (typeof ICON_SHEETS !== 'undefined' && !ICON_SHEETS.includes('ui_icons17_bell')) ICON_SHEETS.push('ui_icons17_bell');
// 77_types15.js names it the Warbell's art (WEAPONS.dirge_bell / WTYPE_INFO.bell); 60_wbal locks SAVE.art to it every frame, so
// saves still holding the borrowed War Cry are corrected on load. Like every other art, its old "Ash of" item is a cache.
if (ITEMS.ash_cache) ITEMS['art:funeral_peal'] = { ...ITEMS.ash_cache, legacyArt: 'funeral_peal' };

const FPL_REL = 5, FPL_CROWN = 3;   // art_funeral_peal frames: the impact, the charge hold
function fplFloorAt(x, y) {   // the floor under (x, y) within a tile: its top y, or null over a gap
  const tx = Math.floor(x / TILE);
  for (let ty = Math.floor((y - 6) / TILE); ty <= Math.floor((y + 6) / TILE); ty++) {
    const t = tileAt(tx, ty);
    if ((isSolidT(t) || t === T_PLAT) && !isSolidT(tileAt(tx, ty - 1))) return ty * TILE;
  }
  for (const d of (room && room.dyn) || []) if (d.on() && x >= d.x0 && x < d.x1 && Math.abs(d.y0 - y) <= 6) return d.y0;
  return null;
}
function fplBossStance(t, n) {
  if (!t.boss || t.state === 'stagger' || !(t.stanceImmune <= 0) || t.stanceMax === undefined) return;
  t.stance = (t.stance || 0) + n;
  if (t.stance >= t.stanceMax && (!t.canStagger || t.canStagger())) t.stagger();
}
// ---- the sound: a half-muffled funeral toll (a low bell under a dull thud), its peal answering a beat later
function fplToll(ch) {
  if (typeof belToll === 'function') belToll(ch ? 0.75 : 0.84, ch ? 1.15 : 1);
  const N = typeof wsNoise === 'function' ? wsNoise : noise;
  N(0.45, 160, 0.7, 0.5, 'lowpass', 0.4);                    // the thud of iron into stone
  if (typeof belBell === 'function') { belBell(130.8, 0.55, 1.6, 0.42); belBell(98, 0.35, 1.8, 0.85); }   // the peal answering
}

// ---- a ring rolling along the floor (dir +1 / -1); every foe it passes is struck once (one Set shared by both rings)
function fplWave(x, y, dir, P0, set, st) {
  FPL.waves.push({ x0: x, x, y, dir, P: P0, set, st, t: 0, done: false, fade: 0, last: x, trail: [] });
}
function fplWaveUpdate(w, dt) {
  w.t += dt;
  if (w.done) { w.fade += dt; return w.fade < 0.35; }
  const step = w.P.speed * dt * w.dir;
  let nx = w.x + step;
  const fy = fplFloorAt(nx, w.y);
  if (Math.abs(nx - w.x0) >= w.P.range || solidAtPx(nx, w.y - 8) || fy === null) { w.done = true; nx = w.x; }
  else w.y = fy;
  w.x = nx;
  if (Math.abs(w.x - w.last) >= 6) { w.trail.push({ x: w.x, y: w.y, t: w.t }); w.last = w.x; if (Math.random() < 0.7) particles.push({ x: w.x + rand(-2, 2), y: w.y - 1, vx: w.dir * rand(10, 40), vy: -rand(20, 60), g: 300, life: 0.4, kind: 'dust' }); }
  const H = w.P.h, band = rect(Math.min(w.x, w.x - w.dir * 10), w.y - H, Math.max(w.x, w.x - w.dir * 10), w.y + 2);
  // strike every foe the front passes through
  const A = ATK[P.state] || PLUNGE_A;
  for (const t of targets()) {
    if (w.set.has(t)) continue;
    const hb = hbOf(t); if (!hb || !overlap(band, hb)) continue;
    w.set.add(t);
    const fury = typeof belBuffs === 'function' && (belBuffs().fury || 0) > 0 ? 1.08 : 1;
    const info = { dmg: outgoing(D.light, w.P.mul * fury, 'melee'), poise: mvPoiseFor(t, w.P.poise, A, (hb.y0 + hb.y1) / 2), dir: w.dir, kind: 'heavy',
      x: clamp(w.x, hb.x0 + 3, hb.x1 - 3), y: clamp(w.y - 10, hb.y0, hb.y1), melee: true, big: true };
    t.hit(info); if (t.flash > 0.35) t.flash = 0.35;   // the ring's white flash stays short of blanking the foe
    runHooks('strike', t, { dmg: info.dmg, heavy: true, x: info.x, y: info.y }, A);
    if (t.prop) continue;
    if (w.P.stun && typeof GEAR2 !== 'undefined' && GEAR2.stun) GEAR2.stun(t, w.P.stun);
    if (w.P.bossStance) fplBossStance(t, w.P.bossStance);
    // the staff: Ember ahead, Ash behind -- one note per foe struck, up to the cap
    if (w.st.notes < w.P.notes && typeof belAddNote === 'function' && typeof mvOn === 'function' && mvOn('bell')) {
      w.st.notes++; belAddNote(w.dir === w.st.face ? 'E' : 'A', info.x, info.y);
    }
    hitstop = Math.max(hitstop, 0.035); shake = Math.max(shake, 3);
  }
  // swallow enemy missiles inside the ring
  for (const pr of projectiles) {
    if (pr.owner === 'player' || !(pr.life > 0) || pr.delay > 0 || pr.static || pr.fxName) continue;
    if (!overlap(band, rect(pr.x - 3, pr.y - 3, pr.x + 3, pr.y + 3))) continue;
    pr.life = 0; spawnFx('g_spark', pr.x, pr.y, 1, null, { tint: '#f2d6a0' });
    if (typeof belBell === 'function') belBell(BEL_NOTE.A.f * 2, 0.35, 0.4);
  }
  addLight(w.x, w.y - 12, 34, w.dir === w.st.face ? '236,150,110' : '236,226,206', 0.5);
  return true;
}

ART_IMPL.funeral_peal = {
  fallback: ['wb_toll', 1.0], armor: true,
  get release() { return P && P.artOwn ? FPL_REL : 4; },                         // wb_toll strikes the floor on frame 4
  get chargeAt() { return P && P.artOwn ? FPL_CROWN : 1; },                        // the bell over the back (wb_toll: frame 1)
  start() { P.g2 = { t: 0, rel: false, face: P.face, set: new Set(), notes: 0 }; P.vx *= 0.3; },
  update(dt, grav) {
    const s = P.g2 || (P.g2 = { t: 0, rel: false, face: P.face, set: new Set(), notes: 0 }), an = P.anim;
    s.t += dt;
    P.vx = approach(P.vx, 0, 900 * dt); grav();
    if (!s.rel) {
      if (P.artHold || an.i < P.artRel) { if (P.artCharged && Math.random() < 0.3) particles.push({ x: P.x - P.face * 10 + rand(-4, 4), y: P.y - 30 + rand(-4, 4), vx: 0, vy: -rand(10, 30), life: 0.4, kind: 'ember' }); return endIf(); }
      if (!P.ground) { an.i = Math.max(0, P.artRel - 1); an.t = 0; an.done = false; P.vy = Math.max(P.vy, 220); s.air = (s.air || 0) + dt; return endIf(s.air > 1.5); }
      fplRelease(s);
    }
    if (P.artOwn && an.i > FPL_REL && an.speed === 1) an.speed = 1.25;   // the recovery: the weight comes off a little quicker
    if (an.done || s.t > 3) return endIf(true);
    function endIf(go) { if (go || (P.state === 'art' && P.artT > 6)) { P.artI = false; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); } }
  },
};
function fplRelease(s) {
  s.rel = true; s.t = 0; s.ch = !!P.artCharged; s.face = P.face;
  const C = s.ch ? FPL.hold : FPL.tap, x = P.x + P.face * FPL.origin, fy = fplFloorAt(x, P.y);
  const y = fy === null ? P.y : fy, st = { notes: 0, face: P.face };
  fplToll(s.ch);
  shake = Math.max(shake, s.ch ? 6 : 5); hitstop = Math.max(hitstop, 0.05);
  addLight(x, y - 10, s.ch ? 60 : 48, '255,226,170', 0.8);
  if (typeof feelFlash === 'function') feelFlash(x, y - 4, s.ch ? 30 : 24, '255,226,170', 0.8, 0.1);
  for (let i = 0; i < (s.ch ? 16 : 10); i++) particles.push({ x: x + rand(-8, 8), y: y - 2, vx: rand(-70, 70), vy: -rand(30, 110), g: 320, life: 0.5, kind: 'dust' });
  if (typeof belRing === 'function') belRing(x, y - 3, s.ch ? 30 : 22, '255,236,190', 0.35, { sq: 0.3, w: 2 });
  // one ring each way from the lip; the backward one starts at the lip too and passes under the knight
  fplWave(x, y, P.face, C, s.set, st);
  fplWave(x, y, -P.face, C, s.set, st);
}

HOOKS.update.push(dt => {
  if (!FPL.waves.length) return;
  FPL.waves = FPL.waves.filter(w => fplWaveUpdate(w, dt));
});
HOOKS.enter.push(() => { FPL.waves = []; });
// ---- the ring drawn: a standing arc of sound on the floor (dots on a half ellipse, glow layer), two fainter echoes lagging
// behind it, and a seam of light left in the floor where it passed. Front ring cored Ember, back ring cored Ash.
HOOKS.render.push(() => {
  if (!FPL.waves.length) return;
  drawGlow(() => {
    for (const w of FPL.waves) {
      const life = w.done ? Math.max(0, 1 - w.fade / 0.35) : 1, far = Math.min(1, Math.abs(w.x - w.x0) / w.P.range);
      const a0 = life * (1 - 0.45 * far), H = w.P.h * (0.75 + 0.25 * (1 - far)), core = w.dir === w.st.face ? BEL_NOTE.E.rgb : BEL_NOTE.A.rgb;
      // the seam in the floor
      for (const p of w.trail) { const k = Math.max(0, 1 - (w.t - p.t) / 0.5) * life; if (k <= 0) continue; g.fillStyle = `rgba(255,214,150,${0.5 * k})`; g.fillRect(Math.round(p.x) - 3, Math.round(p.y) - 1, 6, 1); }
      // the front and its echoes
      for (let e = 0; e < 3; e++) {
        const x = w.x - w.dir * e * 7, a = a0 * [1, 0.45, 0.2][e], hh = H * [1, 0.8, 0.6][e], n = Math.round(hh * 1.4);
        if ((x - w.x0) * w.dir < -2) continue;
        for (let i = 0; i <= n; i++) {
          const th = i / n * Math.PI / 2, px = Math.round(x + w.dir * Math.cos(th) * 5 * (e ? 0.7 : 1)), py = Math.round(w.y - Math.sin(th) * hh);
          if (e && i % 2) continue;
          g.fillStyle = `rgba(255,236,196,${a})`; g.fillRect(px, py, 1, 1);
          if (!e && i % 3 === 0) { g.fillStyle = `rgba(${core},${a * 0.8})`; g.fillRect(px - w.dir, py, 1, 1); }
        }
      }
    }
  });
});

if (typeof window !== 'undefined' && window.__game) window.__game.fpl = { FPL, waves: () => FPL.waves };

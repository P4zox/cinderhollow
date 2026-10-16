// ------------------------------------------------------------------ v17 A2: the Martial Arts' own weapon art, Litany of Fists (`litany`)
// docs/v17/ARTS_BRIEF.md A2, write-up docs/v17/fist_art.md. The art follows the current style (P.ftStyle, 78_mech_fist.js);
// it never switches it:
//  * SWIFT: a stepping flurry of palm and knuckle blows (tap 6, hold 9, the hold steps further), closed by a rising
//    knee that launches small foes. Each blow rings one note of the litany (a rising pentatonic line).
//  * IRON: one planted, armoured bell-breaker palm (a blow under 20% of max HP doesn't flinch it, the Iron rule) whose
//    shock rolls forward along the floor: heavy stance damage, small foes shoved. Hold: a bigger, longer wave and the
//    palm and wave break guards (a shield warden's raised guard, the mirror's shield, the drowned shield's guard meter).
//  * Focus (the perfect-dodge buff) applies as to every martial-arts blow: x FT_PD_MUL damage, +FT_PD_REACH px reach.
//  * The art landing adds 1 Flow (once per use), like a Shift strike.
// Same contract as 16_gear3.js's arts: ART_IMPL[id] { fallback, release, chargeAt, armor, start, update }, P.g2 phases;
// animations art_litany (Swift) / art_litany_iron (Iron) from art/player_v17_fist.py, driven frame by frame here.
// Icon a_litany: ui_icons17_fist (art/gen_ui17_fist.py).
if (typeof ICON_SHEETS !== 'undefined' && !ICON_SHEETS.includes('ui_icons17_fist')) ICON_SHEETS.push('ui_icons17_fist');
// fp / cd (tools/shots/v17/fist/bench.js; docs/v17/fist_art.md "Balance")
const LT_TUNE = { fp: 14, cd: 5.5 };
registerGear({ arts: {
  litany: { name: 'Litany of Fists', fp: LT_TUNE.fp, cd: LT_TUNE.cd, iconSheet: 'ui_icons17_fist',
    desc: 'The penitents’ prayer, said with the hands. Swift: a stepping litany of palm and knuckle blows, closed by a rising knee that lifts small foes. Iron: one armoured palm that breaks like a bell, its shock rolling along the floor. Hold to pray longer.' },
} }, 'ui_icons17_fist');

const LT = {
  // Swift: blows every `gap` s, stepping in at `step` px/s; the knee hops the body up at `hop`
  swift: { n: [6, 9], gap: 0.075, step: [70, 100], dmg: 0.32, poise: 6, ys: [-24, -19, -13, -27], reach: 30,
           knee: [0.9, 1.15], kneePoise: [30, 40], launch: 200, hop: 150, clinch: 0.08 },
  // Iron: the palm, then the wave (speed px/s, range px, height px)
  iron: { palm: [1.4, 1.8], palmPoise: [60, 90], reach: 30, wave: [0.9, 1.4], wavePoise: [50, 80], speed: 300, range: [72, 116],
          h: [24, 34], shove: [200, 260], step: 140 },
  notes: [392, 440, 523, 587, 659, 784, 880, 1046, 1175, 1318],   // G pentatonic, rising: one note per blow
};
const LT_FX = [];   // { kind: 'print' | 'wave', ... } drawn by the render hook below
function ltSmall(t) { return t && !t.prop && !t.boss && t.alive !== false && !(t.cfg && (t.cfg.elite || t.cfg.flying)) && t.vy !== undefined; }
function ltFloor(x, y, max = 40) {   // px y of the floor under (x, y) within `max` px, or null
  for (let ty = Math.floor(y / TILE); ty <= Math.floor((y + max) / TILE); ty++) {
    const t = tileAt(Math.floor(x / TILE), ty);
    if ((isSolidT(t) || t === T_PLAT) && !isSolidT(tileAt(Math.floor(x / TILE), ty - 1))) return ty * TILE;
  }
  return null;
}
// a guard broken: a shield warden's raised guard (its stance breaks), the mirror's shield (dropped). The drowned shield's
// guard meter reads `charged` on the hit itself (+62 a heavy blow), so the palm and the wave together crack it.
function ltGuardBreak(t) {
  if (!t || t.prop || t.alive === false) return false;
  const dirIn = t.x >= P.x ? 1 : -1;
  if (t.guarding && dirIn === -t.face) { t.guarding = false; if (t.stanceImmune === undefined || t.stanceImmune <= 0) { if (t.stagger) t.stagger(); } return true; }
  const c = t.cfg || {};
  if (c.guard && !t.boss && t.breakStance && t.state !== 'stagger' && ['idle', 'walk', 'guard'].includes(t.state) && dirIn === -t.face) { t.breakStance(); return true; }
  return false;
}
const LT_FLASH_CAP = 0.3;
// one blow of `mul` x AR at the box (mvStrikeAt plus a hit set and extra info fields); returns the targets struck
function ltStrike(box, mul, poise, o = {}) {
  const out = [], A = PLUNGE_A;
  for (const t of targets()) {
    if (o.set && o.set.has(t)) continue;
    const hb = hbOf(t); if (!hb || !overlap(box, hb)) continue;
    if (o.set) o.set.add(t);
    if (o.guardBreak && ltGuardBreak(t)) { sfx.glint(); spawnFx(fxOr('parry_flash', 'parry_spark'), (hb.x0 + hb.x1) / 2, (hb.y0 + hb.y1) / 2, P.face, null, { tint: '#ffb070' }); MV.ltGuardBreaks = (MV.ltGuardBreaks || 0) + 1; }
    const info = Object.assign({ dmg: outgoing(D.light, mul * ftPdMul(), 'melee'), poise: typeof mvPoiseFor === 'function' ? mvPoiseFor(t, poise, A, (hb.y0 + hb.y1) / 2) : poise,
      dir: o.dir || (t.x > P.x ? 1 : -1), kind: o.kind || 'light', x: clamp((box.x0 + box.x1) / 2, hb.x0 + 3, hb.x1 - 3), y: (hb.y0 + hb.y1) / 2, melee: true, big: !!o.big }, o.extra || {});
    t.hit(info); out.push(t);
    if (t.flash > LT_FLASH_CAP) t.flash = LT_FLASH_CAP;   // six blows in a row: a full white flash each would blank the foe
    runHooks('strike', t, { dmg: info.dmg, heavy: info.kind === 'heavy', x: info.x, y: info.y }, A);
    if (o.onHit) o.onHit(t, info);
  }
  if (out.some(t => !t.prop) && P.g2 && !P.g2.flow) { P.g2.flow = true; if (typeof ftFlowAdd === 'function') ftFlowAdd(1); }
  return out;
}
// the gap to the nearest body in front (px from P.x to its near edge; Infinity if none): the flurry steps in to it, not through it
function ltGapAhead() {
  let best = Infinity;
  for (const t of targets()) {
    if (t.alive === false) continue;
    const hb = hbOf(t); if (!hb || hb.y1 < P.y - 34 || hb.y0 > P.y) continue;
    const edge = P.face > 0 ? hb.x0 - P.x : P.x - hb.x1, far = P.face > 0 ? hb.x1 - P.x : P.x - hb.x0;
    if (far > 0 && edge < best) best = edge;
  }
  return best;
}
const ltBox = (x0, y0, x1, y1) => rect(Math.min(P.x + P.face * x0, P.x + P.face * x1), P.y + y0, Math.max(P.x + P.face * x0, P.x + P.face * x1), P.y + y1);

const ART_LITANY = (() => {
  const frameTo = (i, keep = true) => { if (!P.artOwn) return; const an = P.anim; an.i = Math.min(i, an.n - 1); if (keep) { an.t = 0; an.done = false; } };
  function endArt() { P.artI = false; if (P.g2 && P.g2.face) P.face = P.g2.face; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); }
  function released() { const an = P.anim; if (!P.g2.rel && !P.artHold && (an.i >= P.artRel || an.done)) { P.g2.rel = true; P.g2.t = 0; P.g2.ch = !!P.artCharged; return 'now'; } return P.g2.rel; }
  const stop = (dt, k = 900) => { P.vx = approach(P.vx, 0, k * dt); };

  // ---------------------------------------------------------------- SWIFT
  function blow(s) {
    const L = LT.swift, k = s.n - 1, y = L.ys[k % L.ys.length], reach = L.reach + ftPdReach();
    const hit = ltStrike(ltBox(-2, y - 9, reach, y + 9), L.dmg, L.poise, { kind: 'light' });
    const hx = P.x + P.face * (hit.length ? 22 : reach - 6), hy = P.y + y;
    LT_FX.push({ kind: 'print', x: hx, y: hy, face: P.face, t: 0, life: 0.16, hit: hit.length > 0, focus: P.ftPdT > 0 });
    if (hit.length) mvSpark(hx, hy, 3, P.ftPdT > 0 ? '228,240,255' : '200,226,255', 110);
    noise(0.05, 2600, 1.2, hit.length ? 0.16 : 0.1, 'bandpass', 0.6);
    tone(LT.notes[Math.min(k, LT.notes.length - 1)], 0.22, hit.length ? 0.03 : 0.018, 'sine', 1.0);
    frameTo(2 + (k % 4));
  }
  function knee(s) {
    const L = LT.swift, reach = 24 + ftPdReach();
    if (P.ground) { P.vy = -L.hop; P.ground = false; }
    P.vx = P.face * 40;
    const hit = ltStrike(ltBox(-2, -38, reach, -2), L.knee[s.ch ? 1 : 0], L.kneePoise[s.ch ? 1 : 0], { kind: 'heavy', big: true,
      onHit: t => { if (ltSmall(t)) { t.vy = -L.launch; if (t.ground !== undefined) t.ground = false; if (t.breakStance && t.state !== 'stagger') t.breakStance(); MV.ltLaunch = (MV.ltLaunch || 0) + 1; } } });
    sfx.heavySwing(); if (hit.length) { tone(110, 0.25, 0.12, 'sine', 0.6); tone(LT.notes[LT.notes.length - 1], 0.5, 0.03, 'sine', 1.0, 0.04); }
    LT_FX.push({ kind: 'print', x: P.x + P.face * 16, y: P.y - 26, face: P.face, t: 0, life: 0.22, hit: hit.length > 0, big: true, focus: P.ftPdT > 0 });
    if (typeof feelFlash === 'function' && hit.length) feelFlash(P.x + P.face * 16, P.y - 26, 22, '214,232,252', 0.8, 0.08);
    frameTo(7);
  }
  function swiftUpdate(dt, grav, s) {
    const L = LT.swift, r = released();
    if (!r) { stop(dt); grav(); return; }
    if (r === 'now') { s.face = P.face; s.n = 0; s.tick = 0; s.max = L.n[s.ch ? 1 : 0]; s.phase = 1; s.t2 = 0; }
    s.t2 += dt;
    if (s.phase === 1) {   // the flurry: step in, a blow every `gap` s (the strike frames loop, one per blow)
      P.vx = approach(P.vx, ltGapAhead() > 12 ? P.face * L.step[s.ch ? 1 : 0] : 0, 1400 * dt); grav();
      if (P.artOwn) frameTo(2 + (Math.max(0, s.n - 1) % 4));
      if (s.n < s.max && (s.tick -= dt) <= 0) { s.tick += L.gap; s.n++; blow(s); }
      else if (s.n >= s.max && (s.tick -= dt) <= -0.01) { s.phase = 2; s.t2 = 0; }
    } else if (s.phase === 2) {   // the clinch
      stop(dt, 1400); grav(); frameTo(6);
      if (s.t2 >= L.clinch) { s.phase = 3; s.t2 = 0; knee(s); }
    } else if (s.phase === 3) {   // the knee, then the float down
      grav(); P.vx = approach(P.vx, P.face * 20, 300 * dt);
      frameTo(s.t2 < 0.09 ? 7 : 8);
      if ((P.ground && s.t2 > 0.08) || s.t2 > 1.2) { s.phase = 4; s.t2 = 0; if (P.ground) { spawnFx('dust', P.x, P.y, P.face); sfx.land(); } }
    } else {   // landed: guard up, then idle
      stop(dt, 1200); grav(); frameTo(9);
      if (s.t2 > 0.14) endArt();
    }
  }

  // ---------------------------------------------------------------- IRON
  function wave(s) {
    const L = LT.iron, ch = s.ch ? 1 : 0, x0 = P.x + P.face * 18;
    const fy = P.ground ? P.y : ltFloor(x0, P.y - 4, 40);
    if (fy === null || solidAtPx(x0, fy - 8)) return null;
    const w = { kind: 'wave', x: x0, x0, y: fy, face: P.face, t: 0, ch: !!s.ch, range: L.range[ch], h: L.h[ch], set: new Set(), done: false, fade: 0 };
    LT_FX.push(w); return w;
  }
  function waveUpdate(w, dt) {
    const L = LT.iron, ch = w.ch ? 1 : 0;
    if (!w.done) {
      const nx = w.x + w.face * L.speed * dt;
      if (Math.abs(nx - w.x0) >= w.range || solidAtPx(nx + w.face * 4, w.y - 6) || ltFloor(nx, w.y - 4, 10) === null) w.done = true;
      else w.x = nx;
      const box = rect(Math.min(w.x - w.face * 12, w.x + w.face * 6), w.y - w.h, Math.max(w.x - w.face * 12, w.x + w.face * 6), w.y + 2);
      ltStrike(box, L.wave[ch], L.wavePoise[ch], { set: w.set, kind: 'heavy', big: true, dir: w.face, guardBreak: w.ch, extra: { charged: w.ch, from: w.x - w.face * 20 },
        onHit: t => { if (ltSmall(t)) { t.vx = w.face * L.shove[ch]; t.vy = -100; if (t.ground !== undefined) t.ground = false; MV.ltShove = (MV.ltShove || 0) + 1; } } });
      if (Math.random() < 0.7) particles.push({ x: w.x + rand(-4, 4), y: w.y - 1, vx: w.face * rand(20, 90), vy: -rand(30, 110), g: 320, life: rand(0.3, 0.5), kind: Math.random() < 0.3 ? 'spark' : 'dust' });
      addLight(w.x, w.y - w.h * 0.4, w.ch ? 34 : 26, '255,150,70', 0.5);
    } else w.fade += dt;
    return w.fade < 0.18;
  }
  function palm(s) {
    const L = LT.iron, ch = s.ch ? 1 : 0, reach = L.reach + ftPdReach();
    P.vx = P.face * L.step;
    const hit = ltStrike(ltBox(-2, -32, reach, -6), L.palm[ch], L.palmPoise[ch], { kind: 'heavy', big: true, guardBreak: s.ch, extra: { charged: s.ch },
      onHit: t => { if (ltSmall(t)) { t.vx = P.face * L.shove[ch] * 0.6; MV.ltShove = (MV.ltShove || 0) + 1; } } });
    shake = Math.max(shake, s.ch ? 6 : 4); hitstop = Math.max(hitstop, hit.length ? 0.07 : 0.03);
    // the bell-breaker's voice: a struck bell that cracks (inharmonic partials, a low thud, a dry crack of noise)
    tone(98, 0.6, 0.16, 'sine', 0.7); tone(196 * (s.ch ? 0.9 : 1), 1.1, 0.07, 'triangle', 0.98); tone(523, 0.7, 0.035, 'sine', 0.97, 0.01); tone(731, 0.5, 0.025, 'sine', 0.95, 0.015);
    noise(0.22, 420, 0.9, 0.3, 'lowpass', 0.5); if (s.ch) noise(0.3, 1800, 1.4, 0.12, 'bandpass', 0.4);
    spawnFx('dust', P.x + P.face * 10, P.y, P.face);
    if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 26, P.y - 19, s.ch ? 30 : 24, '255,190,120', 0.8, 0.09);
    s.wave = wave(s);
  }
  function ironUpdate(dt, grav, s) {
    const r = released();
    if (!r) { stop(dt); grav(); return; }
    if (r === 'now') { s.face = P.face; s.phase = 1; s.t2 = 0; frameTo(2); palm(s); }
    s.t2 += dt; stop(dt, 1500); grav();
    if (P.artOwn) frameTo(s.t2 < 0.07 ? 2 : s.t2 < 0.29 ? 3 : s.t2 < 0.44 ? 4 : 5);
    if (s.t2 > (P.artOwn ? 0.57 : 0.5)) endArt();
  }

  // ---------------------------------------------------------------- registration
  ART_IMPL.litany = {
    fallback: ['ft_wind', 1], release: 1, chargeAt: 1,
    get armor() { return !!(P && P.g2 && P.g2.iron) && (P.ltHurtDmg || 0) < D.maxHp * 0.2; },   // the Iron rule (78_mech_fist hurt())
    start() {
      const iron = typeof ftIron === 'function' && ftIron();
      P.g2 = { t: 0, rel: false, face: 0, iron, set: new Set() };
      const tag = iron ? 'art_litany_iron' : 'art_litany';
      if (pHas(tag)) {
        P.artTag = tag; P.artOwn = true; setP('art', tag, false, 1);
        const m = ASSETS.player_meta && ASSETS.player_meta.moves && ASSETS.player_meta.moves[tag]; P.artRel = m ? m.active[0] : 2;
      } else { P.artOwn = false; setP('art', iron ? 'ft_palm' : 'ft_wind', false, 1); P.artRel = iron ? 2 : 1; }
      if (iron) { tone(73, 0.7, 0.08, 'sawtooth', 1.2); noise(0.4, 260, 0.7, 0.15, 'lowpass'); }
      else { tone(784, 0.5, 0.025, 'sine', 1.0); tone(1175, 0.6, 0.015, 'sine', 1.0, 0.06); }
      MV.ltUses = (MV.ltUses || 0) + 1;
    },
    update(dt, grav) {
      if (!P.g2) P.g2 = { t: 0, rel: false, face: 0, iron: false, set: new Set() };
      P.g2.t += dt;
      (P.g2.iron ? ironUpdate : swiftUpdate)(dt, grav, P.g2);
      if (P.state === 'art' && P.artT > 6) endArt();
    },
  };
  // the Iron armour reads the blow's size (playerHurt hooks run before 04_player decides `armored`)
  HOOKS.playerHurt.push(dmg => {
    P.ltHurtDmg = dmg;
    if (P.state === 'art' && P.artId === 'litany' && P.g2 && P.g2.iron && dmg < D.maxHp * 0.2) P.ftArmT = 0.18;
    return dmg;
  });

  // ---------------------------------------------------------------- effects
  HOOKS.update.push(dt => {
    if (!LT_FX.length) return;
    for (const f of LT_FX) f.t += dt;
    const keep = [];
    for (const f of LT_FX) { if (f.kind === 'wave' ? waveUpdate(f, dt) : f.t < f.life) keep.push(f); }
    LT_FX.length = 0; LT_FX.push(...keep);
  });
  HOOKS.enter.push(() => { LT_FX.length = 0; });
  const px = (x, y, w = 1, h = 1) => g.fillRect(Math.round(x), Math.round(y), w, h);
  function drawPrint(f) {   // a blow's mark: a small four-point burst and a short streak back along the arm
    const k = f.t / f.life, a = (1 - k) * (f.hit ? 1 : 0.55), r = (f.big ? 4 : 3) * (0.6 + 0.6 * k);
    const core = f.focus ? '240,248,255' : '226,240,255', mid = f.focus ? '190,220,255' : '150,196,240';
    g.fillStyle = `rgba(${core},${a})`; px(f.x, f.y);
    g.fillStyle = `rgba(${mid},${a * 0.9})`;
    for (let i = 1; i <= r; i++) { px(f.x + i, f.y); px(f.x - i, f.y); if (i < r - 0.5) { px(f.x, f.y + i); px(f.x, f.y - i); } }
    g.fillStyle = `rgba(${mid},${a * 0.5})`;
    for (let i = 3; i < 9 - 6 * k; i++) if (i % 3 !== 2) px(f.x - f.face * (i + 2), f.y + (f.big ? i * 0.6 : 0));
  }
  function drawWave(w) {   // the bell-breaker's shock: a dome of ember rolling along the floor, a cracked seam behind it
    const a = Math.max(0, 1 - w.fade / 0.18) * Math.min(1, w.t * 20), trav = Math.abs(w.x - w.x0), ease = 1 - 0.35 * Math.min(1, trav / w.range);
    // the seam: a hairline crack of embers from the palm to the front, dimming behind
    for (let d = 0; d < trav; d += 1) {
      const q = d / Math.max(1, trav), x = w.x0 + w.face * d;
      if ((Math.floor(x) * 7) % 5 === 0) continue;
      g.fillStyle = `rgba(${q > 0.75 ? '255,150,70' : '120,40,24'},${a * (0.25 + 0.6 * q)})`; px(x, w.y - 1);
    }
    // the front: a floor-anchored dome leaning into its travel (quarter ellipse), a hot 2 px rim, an ember haze behind it
    // (dithered, thinning upward) and a fainter echo rim 7 px back
    const H = Math.round(w.h * ease), Wd = w.ch ? 9 : 7;
    let prev = null;
    for (let h = 0; h <= H; h++) {
      const fr = h / Math.max(1, H), front = Wd * Math.sqrt(1 - fr * fr), y = w.y - 1 - h, xf = Math.round(w.x + w.face * front);
      g.fillStyle = `rgba(255,236,190,${a * 0.95})`;
      const p0 = prev === null ? xf : prev; for (let x = Math.min(p0, xf); x <= Math.max(p0, xf); x++) px(x, y);
      prev = xf;
      g.fillStyle = `rgba(255,170,90,${a * 0.85})`; px(xf - w.face, y);
      const trail = Math.round((w.ch ? 14 : 11) * (1 - fr * 0.7));
      for (let d = 2; d < trail; d++) {
        if ((Math.round(xf) + d + y) % 2) continue;
        g.fillStyle = `rgba(${d < 5 ? '255,140,60' : '168,66,30'},${a * 0.55 * (1 - d / trail)})`; px(xf - w.face * d, y);
      }
      if (h % 2 === 0) { const xe = w.x - w.face * 7 + w.face * front * 0.8; g.fillStyle = `rgba(255,150,70,${a * 0.4})`; px(xe, y); }
    }
  }
  HOOKS.render.push(() => {
    if (!P) return;
    for (const f of LT_FX) (f.kind === 'wave' ? drawWave : drawPrint)(f);
    // the charge: Swift a pale breath at the pressed palms, Iron the knuckles at the hip heating (particles; the light is
    // 04_player's charge light)
    if (P.state === 'art' && P.artId === 'litany' && P.g2 && !P.g2.rel) {
      const iron = P.g2.iron, hx = P.x + P.face * (iron ? -3 : 8), hy = P.y - (iron ? 11 : 20);
      if (Math.random() < (P.artHold ? 0.5 : 0.25)) particles.push({ x: hx + rand(-2, 2), y: hy + rand(-2, 2), vx: rand(-6, 6), vy: -rand(15, 40), life: 0.35, kind: iron ? 'spark' : 'mote' });
    }
  });
  const api = { LT, LT_TUNE, fx: LT_FX, guardBreak: ltGuardBreak };
  if (typeof window !== 'undefined' && window.__game) window.__game.litany = api;
  return api;
})();

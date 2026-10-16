// ------------------------------------------------------------------ v17 A1: the Bow's own art, Ashen Volley (`ashen_volley`)
// docs/v17/ARTS_BRIEF.md A1; write-up docs/v17/bow_art.md. Replaces the borrowed Backstep Slash on the Ashstring Recurve.
//  * Kick off the foe into a back-flip (i-frames 0.25 s from the kick). At the top of the flip -- belly-down, head to the foe
//    -- loose a fan of three burning arrows down and forward into the spot you just left (aimed at the nearest foe there,
//    else at the floor where you stood). They are real bow arrows (78_mech_bow.js's bwArrow): they burn out at BW_RANGE.
//  * Hold O (the usual art charge): five arrows that stick -- in the foe or the floor -- and burst a beat later.
//  * The first arrow of a volley that lands on a foe raises the bow's charge level by one (P.bwLv, the chain's level).
// The animation is art_ashen_volley (art/player_v17_bow.py); ART_SYNC keys its held frames off P.g2 (phase below).
// Same contract as 16_gear3.js's impl(): phase 0 waits for the release frame (and the charge hold), then a time-driven
// phase in P.g2. Without the dedicated tag (an old sheet) the bow's own tags stand in.
const AV = {
  fp: 12, cd: 5,
  kick: 0.5, kickPoise: 12,   // the kick (x light AR); light poise: a common foe is not flinched out of the spot the volley comes down on
  tap: { n: 3, mul: 0.6, poise: 12, spread: 0.12 },        // three arrows
  hold: { n: 5, mul: 0.35, poise: 8, spread: 0.1, burst: 0.25, burstPoise: 12, delay: 0.42, r: 13 },   // five; each bursts
  kickT: 0.06, vy: -210, vx: 150, drag: 400, inv: 0.25, shotAt: 0.2, hang: 0.12, spd: 470,
};
const AV_A = { kind: 'heavy', cls: 'bow', mv: { id: 'ashen_volley', type: 'bow' }, tags: ['art_ashen_volley'] };
const AVS = { arrows: [], bursts: [], fx: [], log: [] };   // (tests read AVS.log)
registerGear({ arts: { ashen_volley: { name: 'Ashen Volley', fp: AV.fp, cd: AV.cd, iconSheet: 'ui_icons17_bow',
  desc: 'Kick off the foe into a back-flip and, at the top of it, loose three burning arrows down into the spot you left. Any that lands raises the bow’s charge level. Hold for five arrows that stick and burst.' } } }, 'ui_icons17_bow');
if (typeof ICON_SHEETS !== 'undefined' && !ICON_SHEETS.includes('ui_icons17_bow')) ICON_SHEETS.push('ui_icons17_bow');
if (typeof ITEMS !== 'undefined' && ITEMS.ash_cache) ITEMS['art:ashen_volley'] = { ...ITEMS.ash_cache, legacyArt: 'ashen_volley' };   // as 60_wbal does for every art

// ---- sounds
function avKickSnd() { noise(0.07, 420, 1, 0.22, 'lowpass', 0.6); tone(95, 0.12, 0.1, 'sine', 0.55); }
function avFlipSnd() { noise(0.24, 1500, 1.1, 0.1, 'bandpass', 2.2); }
function avVolleySnd(n) { bwTwang(2); noise(0.3, 820, 0.8, 0.09, 'bandpass', 0.45); if (n > 3) tone(240, 0.22, 0.03, 'triangle', 0.7, 0.04); }
function avBurstSnd() { noise(0.28, 320, 0.8, 0.2, 'lowpass', 0.35); noise(0.18, 2400, 1.5, 0.05, 'bandpass', 0.5); tone(72, 0.2, 0.08, 'sine', 0.6); }

// ---- the volley
// aim: the nearest foe below-ahead of the bow within reach (its middle), else the floor where you stood
function avAim(o, s) {
  let best = null, bd = BW_RANGE + 6;
  for (const t of targets()) {
    if (t.prop || t.alive === false) continue;
    const hb = hbOf(t); if (!hb) continue;
    const cx = clamp(o.x + s.face * 30, hb.x0, hb.x1), cy = clamp(o.y + 26, hb.y0 + 4, Math.max(hb.y0 + 4, hb.y1 - 8));
    if ((cx - o.x) * s.face < 4 || cy < o.y + 2) continue;
    const d = Math.hypot(cx - o.x, cy - o.y);
    if (d < bd) { bd = d; best = { x: cx, y: cy, t }; }
  }
  const p = best || { x: s.x0 + s.face * 6, y: s.gy - 3 };
  return { a: clamp(Math.atan2(p.y - o.y, (p.x - o.x) * s.face), 0.3, 1.25), t: best && best.t };
}
function avVolley(s) {
  const ch = !!s.ch, V = ch ? AV.hold : AV.tap, face = s.face;
  let o = typeof bwTip === 'function' ? bwTip() : null;
  if (!o || Math.hypot(o.x - P.x, o.y - (P.y - 16)) > 30) o = { x: P.x + face * 10, y: P.y - 8 };
  const aim = avAim(o, s);
  s.aim = aim.a; s.from = { x: o.x, y: o.y };
  for (let i = 0; i < V.n; i++) {
    const k = i - (V.n - 1) / 2;
    const pr = bwArrow({ face, x: o.x, y: o.y, sx: P.x, ang: aim.a + k * V.spread, mul: V.mul, poise: V.poise, lv: 2, spd: AV.spd, life: 0.42,
      pb: true, heavy: true, A: AV_A, delay: Math.abs(k) * 0.025, av: true, avStick: ch,
      onHit(t, info) { avLanded(s, t, info, pr); } });
    pr.bw.avS = s; AVS.arrows.push(pr);
  }
  avVolleySnd(V.n); shake = Math.max(shake, 2);
  if (typeof feelFlash === 'function') feelFlash(o.x, o.y, 22, '255,170,90', 0.7, 0.08);
  for (let i = 0; i < 8; i++) particles.push({ x: o.x, y: o.y, vx: face * rand(20, 90) * Math.cos(aim.a), vy: rand(10, 70) * Math.sin(aim.a) - 20, life: rand(0.2, 0.4), kind: i % 2 ? 'ember' : 'ash' });
}
// an arrow of the volley struck a foe: the charge level (once per volley), and a stuck arrow (held art) waits to burst
function avLanded(s, t, info, pr) {
  if (t.prop) return;
  AVS.log.push({ kind: 'arrow', dmg: info.dmg / D.light, ch: !!s.ch });
  if (!s.banked) {
    s.banked = true;
    const was = P.bwLv || 1, lv = Math.min(3, was + 1);
    if (lv > was) { bwBank(lv, 'quiet'); bwLevelUpFx(lv); } else P.bwIdle = 0;
    s.lvUp = [was, P.bwLv];
  }
  if (pr && pr.bw.avStick) { pr.bw.avDone = true; avQueueBurst(t, info.x, info.y, pr); }
}
function avQueueBurst(t, x, y, pr) {
  AVS.bursts.push({ t, ox: t ? x - t.x : 0, oy: t ? y - t.y : 0, x, y, at: AV.hold.delay, ang: Math.atan2(pr.vy, pr.vx), face: pr.bw.face });
}
function avBurst(b) {
  const x = b.t ? b.t.x + b.ox : b.x, y = b.t ? b.t.y + b.oy : b.y, r = AV.hold.r;
  const n = mvStrikeAt(rect(x - r, y - r, x + r, y + r), AV.hold.burst, AV.hold.burstPoise, { A: AV_A, kind: 'heavy', big: true,
    onHit(t, info) { if (!t.prop) AVS.log.push({ kind: 'burst', dmg: info.dmg / D.light }); } });
  avBurstSnd(); shake = Math.max(shake, n ? 2.5 : 1.5); if (n) hitstop = Math.max(hitstop, 0.03);
  AVS.fx.push({ x, y, t: 0, max: 0.42, ang: b.ang, face: b.face, seed: Math.random() * 100 });
  for (let i = 0; i < 16; i++) { const a = rand(0, 6.283), v = rand(30, 120); particles.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 40, g: 160, life: rand(0.25, 0.6), kind: i % 3 ? 'ember' : 'ash' }); }
  // the arrow that stuck in the floor is spent
  for (const st of BW.stuck) if (!st.t && Math.abs(st.x - x) < 3 && Math.abs(st.y - y) < 3) st.life = 0;
}
function avTick(dt) {
  for (const pr of AVS.arrows) {
    const b = pr.bw; if (!b.done || b.avDone) continue;
    b.avDone = true;
    // stopped by the floor or a wall (not a foe, not the burn-out): a held volley's arrow sticks there and bursts
    if (b.avStick && !b.n && b.flown < BW_RANGE - 0.5) avQueueBurst(null, pr.x, pr.y, pr);
  }
  AVS.arrows = AVS.arrows.filter(pr => !pr.bw.avDone);
  for (const b of AVS.bursts) { b.at -= dt; if (b.at <= 0 && !b.fired) { b.fired = true; if (!b.t || b.t.alive !== false) avBurst(b); } }
  if (AVS.bursts.length) AVS.bursts = AVS.bursts.filter(b => !b.fired);
  for (const f of AVS.fx) f.t += dt;
  if (AVS.fx.length) AVS.fx = AVS.fx.filter(f => f.t < f.max);
  if (AVS.log.length > 60) AVS.log.splice(0, AVS.log.length - 60);
}

// ---- the art
(function () {
  const endArt = () => { P.artI = false; if (P.g2 && P.g2.face) P.face = P.g2.face; setP(P.ground ? 'idle' : 'air', P.ground ? 'idle' : 'jump_fall', P.ground); };
  const released = () => { const an = P.anim; if (!P.g2.rel && !P.artHold && (an.i >= P.artRel || an.done)) { P.g2.rel = true; P.g2.t = 0; P.g2.ch = !!P.artCharged; return 'now'; } return P.g2.rel; };
  const own = () => P.artOwn && P.anim.tag === P.artTag;
  const fb = (tag, sp = 1) => { if (!P.artOwn && pHas(tag) && P.anim.tag !== tag) P.anim.set(tag, false, sp); };
  ART_IMPL.ashen_volley = {
    fallback: ['bw_stab', 1], release: 1, chargeAt: 0,
    start() { P.g2 = { t: 0, rel: false, face: 0, set: new Set(), phase: 0 }; },
    update(dt, grav) {
      if (!P.g2) P.g2 = { t: 0, rel: false, face: 0, set: new Set(), phase: 0 };
      const s = P.g2; s.t += dt; P.bwIdle = 0;   // the art is a bow move: the banked level does not gutter while it plays
      const r = released();
      if (!r) {   // the coil (and the charge hold): an ember gathers on the nocked arrow
        P.vx = approach(P.vx, 0, 900 * dt); grav();
        if (Math.random() < 0.4) { const tp = bwTip() || { x: P.x + P.face * 10, y: P.y - 16 }; particles.push({ x: tp.x + rand(-2, 2), y: tp.y + rand(-2, 2), vx: rand(-8, 8), vy: -rand(10, 30), life: 0.3, kind: 'ember' }); }
        return;
      }
      if (r === 'now') {   // the kick: strike the foe in front, then push off it
        s.face = P.face; s.x0 = P.x; s.gy = P.y; s.phase = 1; P.artI = true; P.vx = 0;
        const n = mvStrikeAt(rect(P.x + P.face * 2 - (P.face < 0 ? 26 : 0), P.y - 30, P.x + P.face * 2 + (P.face > 0 ? 26 : 0), P.y - 6), AV.kick, AV.kickPoise,
          { A: AV_A, kind: 'light', onHit(t, info) { if (!t.prop) AVS.log.push({ kind: 'kick', dmg: info.dmg / D.light }); } });
        avKickSnd();
        if (n) { hitstop = Math.max(hitstop, 0.05); shake = Math.max(shake, 2); mvSpark(P.x + P.face * 20, P.y - 22, 6, '230,220,200', 120); }
        spawnFx('dust', P.x, P.y, P.face);
      }
      if (s.phase === 1) {   // the kick lands, then the push-off
        P.vx = 0; P.vy = Math.min(P.vy, 0); grav();
        if (s.t >= AV.kickT) {
          s.phase = 2; s.tl = s.t; P.vx = -s.face * AV.vx; P.vy = P.ground ? AV.vy : Math.min(P.vy, AV.vy * 0.85); P.ground = false;
          avFlipSnd(); spawnFx('dust', P.x, P.y, -s.face); fb('bw_recoil', 1.2);
        }
      } else if (s.phase === 2) {   // rising through the flip
        P.vx = approach(P.vx, 0, AV.drag * dt); grav();
        if (s.t > AV.inv) P.artI = false;   // 0.25 s from the kick
        if (Math.random() < 0.5 && typeof MV !== 'undefined') MV.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.14, max: 0.14, col: '#c8b8a0', alpha: 0.25, wf: P.anim.frame });
        const aimed = !own() || P.anim.i >= 4;
        if ((s.t - s.tl >= AV.shotAt && aimed) || s.t - s.tl > AV.shotAt + 0.12 || (P.ground && s.t - s.tl > 0.08)) {
          avVolley(s); s.phase = 3; s.ts = s.t; P.vy = Math.min(Math.max(P.vy, -40), 10); fb('bw_air', 1);
        }
      } else if (s.phase === 3) {   // the hang at the top while the volley looses
        P.vx = approach(P.vx, 0, AV.drag * dt);
        P.vy = Math.min(P.vy + GRAV_DN * 0.3 * dt, 60); if (s.t > AV.inv) P.artI = false;
        if (s.t - s.ts >= AV.hang) s.phase = 4;
      } else if (s.phase === 4) {   // coming round and down
        P.vx = approach(P.vx, 0, AV.drag * dt); grav(); P.artI = false;
        if (P.ground) { s.phase = 5; s.tland = s.t; P.vx = 0; sfx.land(); spawnFx('dust', P.x, P.y, s.face); fb('bw_diveshot', 1.4); }
      } else if (s.phase === 5) {   // the landing crouch and the rise
        P.vx = approach(P.vx, 0, 900 * dt); grav();
        if ((own() ? P.anim.done : s.t - s.tland > 0.32) || s.t - s.tland > 0.6) endArt();
      }
      if (P.state === 'art' && P.artT > 4) endArt();   // safety net
    },
  };
  // frames: 0 coil · 1 kick · 2-3 the turn · 4 aim (held) · 5 loose (held over the hang) · 6-7 come round (7 held falling) · 8-10 land
  const at = (an, i) => { an.i = i; an.t = 0; an.done = false; };
  ART_SYNC.ashen_volley = (an, s) => {
    if (!s.rel) return;
    if (s.phase === 1) { if (an.i !== 1) at(an, 1); }
    else if (s.phase === 2) { if (an.i < 2) at(an, 2); else if (an.i > 4) at(an, 4); else if (an.i === 4) { an.t = 0; an.done = false; } }
    else if (s.phase === 3) { if (an.i < 5) at(an, 5); else if (an.i > 5) at(an, 5); else { an.t = 0; an.done = false; } }
    else if (s.phase === 4) { if (an.i < 6) at(an, 6); else if (an.i > 7) at(an, 7); else if (an.i === 7) { an.t = 0; an.done = false; } }
    else if (s.phase === 5) { if (an.i < 8) at(an, 8); }
  };
})();

// ---- drawing: the arrows burn (a flickering flame on each head), the stuck ones smoulder until they burst
function avRender() {
  const fl = (x, y, ang, k, seed) => {   // a small flame licking back from a point along -ang (pixels)
    const c = Math.cos(ang), s = Math.sin(ang);
    for (let i = 0; i < 5; i++) {
      const w = Math.sin(time * 40 + seed + i * 1.7), len = i + 1;
      const px = Math.round(x - c * len + (-s) * w * 0.8), py = Math.round(y - s * len - 0.6 * i + c * w * 0.8);
      g.fillStyle = i < 1 ? `rgba(255,236,170,${0.95 * k})` : i < 3 ? `rgba(255,150,60,${0.85 * k})` : `rgba(190,60,30,${0.6 * k})`;
      g.fillRect(px, py, 1, 1);
    }
  };
  for (const pr of AVS.arrows) {
    if (pr.delay > 0 || pr.life <= 0) continue;
    const b = pr.bw, ang = Math.atan2(pr.vy, pr.vx), fa = typeof bwFadeA === 'function' ? bwFadeA(b) : 1;
    fl(pr.x - Math.cos(ang) * 2, pr.y - Math.sin(ang) * 2, ang, fa, b.ox);
    if (Math.random() < 0.45) particles.push({ x: pr.x - Math.cos(ang) * 4, y: pr.y - Math.sin(ang) * 4, vx: -pr.vx * 0.04, vy: -rand(10, 30), life: 0.28, kind: Math.random() < 0.3 ? 'ash' : 'ember' });
  }
  // stuck arrows waiting to burst: the ember on the shaft swells
  for (const b of AVS.bursts) {
    if (b.fired) continue;
    const x = b.t ? b.t.x + b.ox : b.x, y = b.t ? b.t.y + b.oy : b.y, k = 1 - Math.max(0, b.at) / AV.hold.delay;
    fl(x - Math.cos(b.ang) * 3, y - Math.sin(b.ang) * 3, -Math.PI / 2, 0.5 + 0.5 * k, b.ox * 7);
    drawGlow(() => { addLight(x, y, 8 + 10 * k, '255,140,60', 0.35 + 0.35 * k); g.fillStyle = `rgba(255,190,110,${0.4 + 0.5 * k * (0.7 + 0.3 * Math.sin(time * 30))})`; g.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2); });
  }
  // the bursts: a tight star of fire that tears outward into ash -- crisp bands, one light
  for (const f of AVS.fx) {
    const k = f.t / f.max, R = 3 + 12 * Math.pow(k, 0.6), N = 9;
    for (let i = 0; i < N; i++) {
      const a = (i / N) * 6.283 + f.seed, rr = R * (0.75 + 0.25 * Math.sin(f.seed * 3 + i * 2.1));
      for (let j = 0; j < 3; j++) {
        const d = rr - j * 2.2; if (d < 1) continue;
        const px = Math.round(f.x + Math.cos(a) * d), py = Math.round(f.y + Math.sin(a) * d * 0.85);
        g.fillStyle = k < 0.35 ? (j === 0 ? `rgba(255,150,60,${1 - k})` : `rgba(255,232,170,${1 - k})`) : j === 0 ? `rgba(90,70,64,${1 - k})` : `rgba(230,110,50,${(1 - k) * 0.9})`;
        g.fillRect(px, py, 1, 1);
      }
    }
    if (k < 0.3) { g.fillStyle = `rgba(255,240,200,${1 - k / 0.3})`; g.fillRect(Math.round(f.x) - 1, Math.round(f.y) - 1, 3, 3); }
    drawGlow(() => addLight(f.x, f.y, 16 + 14 * (1 - k), '255,150,70', 0.75 * (1 - k)));
  }
}
HOOKS.update.push(dt => { if (P) avTick(dt); });
HOOKS.render.push(() => { if (P) avRender(); });
HOOKS.enter.push(() => { AVS.arrows = []; AVS.bursts = []; AVS.fx = []; });
if (typeof window !== 'undefined' && window.__game) window.__game.av = { AV, AVS };

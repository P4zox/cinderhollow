// ------------------------------------------------------------------ v15: Close-range Bow (`bow`, prefix bw_, weapon ashstring)
// docs/WEAPON_REVAMP.md Part C, C2 (★★★); write-up docs/v15/bow.md. A Monster-Hunter bow fought up close.
//  * Charge levels 1-3. P.bwLv is the level banked for the NEXT shot: each shot in a chain raises it (J J J = lv 1, 2, 3),
//    the charge step (L) raises it, holding K draws it up one level every 0.4 s. A power shot (K release), the pinning shot
//    and the dive shot spend it (back to 1); 1.5 s without a shot or a step and it falls back to 1.
//  * Short range (v15b, the owner: "the arrow disappear at mid range so the player have to play melee"): every arrow burns
//    out BW_RANGE (72) px from where it was loosed -- it fades from 52 px, then chars into ash and embers and can't hit past
//    that (about 86 px from the archer). The arc shot's rain lands no further than 82 px ahead.
//  * The sweet spot: damage x1.0 when the foe's near edge is 12-56 px away, x0.9 point-blank (< 12 px), easing to x0.6 at
//    the burn-out. Point-blank moves (recoil shot, leaping point-blank, counter shot, dive shot) take no point-blank cut.
//    A glint on the arrowhead (the real one, found in the overlay frame) shows when the nearest foe ahead is in it.
//  * Arrows are real projectiles in `projectiles` (walls stop them, wards block them); this file sweeps them against the
//    targets itself (the engine's own hit test is kept shut with `win`), applies the sweet spot and draws them.
//  * K is "tap = the branch, hold = draw" everywhere: neutral tap = power shot at the banked level, J -> K tap = arrow stab,
//    stab -> K tap = recoil shot, L -> K tap = leaping point-blank, lv3 power shot -> K tap = hollow piercer (III).
//  * I = limb deflect: a 150 ms window; a blow in it is turned on the bow's limb and answered with a point-blank shot.
const BW_LV_MS = 400, BW_DECAY = 1.5, BW_TAP = 110, BW_MIN = 180;   // a power shot needs at least BW_MIN ms of draw
const BW_COL = [null, '196,214,255', '255,160,70', '255,220,130'];   // level glow: cold steel, amber, gold (the sweet-spot glint is pure white)
const BW_PWR = { dmg: [0, 0.9, 1.4, 2.0], poise: [0, 20, 35, 55], spd: [0, 380, 450, 540] };
// range: an arrow fades from BW_FADE px of flight and burns out at BW_RANGE. 72 px of flight from the arrowhead (it is
// loosed ~14 px ahead of the archer) = nothing hit past ~86 px from the archer: the whip's tipped crack (~70 px + its
// step), so the bow is never the longest reach in the game. A shot at the far edge of the sweet spot (56 px from the
// archer, ~42 px of flight) still has 30 px of clean flight before it starts to fade.
const BW_RANGE = 72, BW_FADE = 52, BW_SWEET = [12, 56], BW_REACH = 86;
const BW = { arrows: [], stuck: [], burn: [], tips: new Map(), tipSheet: null, cv: null, log: [] };

// ---- the sweet spot: d = px from the shooter to the foe's near edge
function bwSweet(d, pb) {
  if (d < BW_SWEET[0]) return pb ? 1 : 0.9;
  if (d <= BW_SWEET[1]) return 1;
  return Math.max(0.6, 1 - 0.4 * (d - BW_SWEET[1]) / (BW_REACH - BW_SWEET[1]));   // 56 -> 86 px (the burn-out): x1.0 -> x0.6
}
const bwInSweet = d => d >= BW_SWEET[0] && d <= BW_SWEET[1];
// the nearest foe ahead (or overlapping you): { t, d } with d to its near edge, or null
function bwNearest(range = 160) {
  let best = null;
  for (const t of targets()) {
    if (t.prop || t.alive === false) continue;
    const hb = hbOf(t); if (!hb) continue;
    if (hb.y1 < P.y - 48 || hb.y0 > P.y + 4) continue;
    const d = P.face > 0 ? hb.x0 - P.x : P.x - hb.x1;
    if (d < -10 || d > range) continue;
    const dd = Math.max(0, d);
    if (!best || dd < best.d) best = { t, d: dd };
  }
  return best;
}

// ---- the arrowhead in the current overlay frame (the broadhead's own pixels; cached per frame)
function bwTipRel(f) {
  const s = sheet('wpn_' + (SAVE.weapon || 'ashstring'));
  if (!s.ok) return null;
  if (BW.tipSheet !== s.name) { BW.tipSheet = s.name; BW.tips.clear(); }
  const hit = BW.tips.get(f); if (hit && (hit.r || BW.tipN - hit.n < 120)) return hit.r;   // a miss is looked at again later (sheet still decoding)
  const img = s.img, fr = s.frames[f];
  if (!fr || !img.complete || !img.naturalWidth) return null;
  let r = null;
  try {
    const c = BW.cv || (BW.cv = document.createElement('canvas')); c.width = fr.w; c.height = fr.h;
    const cx = c.getContext('2d', { willReadFrequently: true }); cx.clearRect(0, 0, fr.w, fr.h); cx.drawImage(img, fr.x, fr.y, fr.w, fr.h, 0, 0, fr.w, fr.h);
    const d = cx.getImageData(0, 0, fr.w, fr.h).data; let sx = 0, sy = 0, n = 0;
    for (let i = 0; i < d.length; i += 4) {
      if (!d[i + 3]) continue;
      const R = d[i], Gc = d[i + 1], B = d[i + 2];
      if ((R === 232 && Gc === 238 && B === 252) || (R === 128 && Gc === 134 && B === 158)) { const p = i >> 2; sx += p % fr.w; sy += (p / fr.w) | 0; n++; }
    }
    if (n) r = [sx / n + 0.5 - s.ax, sy / n + 0.5 - s.ay];
  } catch (e) { r = null; }
  BW.tipN = (BW.tipN || 0) + 1; BW.tips.set(f, { r, n: BW.tipN }); return r;
}
function bwTip() {
  const r = P && P.anim && bwTipRel(P.anim.frame);
  if (!r) return null;
  const s = sheet('wpn_' + (SAVE.weapon || 'ashstring')), fl = P.face === (s.native || 1) ? 1 : -1;
  return { x: P.x + fl * r[0], y: P.y + r[1] };
}

// ---- sounds
function bwTwang(lv = 1) { noise(0.05, 2600, 3, 0.05, 'bandpass', 0.6); tone(150 + lv * 28, 0.14, 0.05 + lv * 0.01, 'triangle', 0.55); if (lv >= 3) tone(820, 0.1, 0.025, 'sine', 1.4); }
function bwCreak(lv) { tone(420 + lv * 180, 0.16, 0.04, 'triangle', 1.25); noise(0.08, 900 + lv * 300, 4, 0.03, 'bandpass', 1.2); }

// ---- the bank
function bwBank(lv, why) {
  const was = P.bwLv || 1; P.bwLv = clamp(lv, 1, 3); P.bwIdle = 0;
  if (P.bwLv > was && why !== 'quiet') { const tp = bwTip() || { x: P.x + P.face * 14, y: P.y - 20 }; if (typeof feelFlash === 'function') feelFlash(tp.x, tp.y, 14 + P.bwLv * 6, BW_COL[P.bwLv], 0.9, 0.1); }
}

// ---- arrows (real projectiles)
// o: { mul, poise, lv, ang (rad, + = down), spd, life, g, pierce (true / n), drill, pb, flat, dx, dy, A, big, reel, burst, fromTip }
function bwArrow(o) {
  const face = o.face || P.face, a = o.ang || 0, spd = o.spd || 430;
  let x = P.x + face * (o.dx ?? 13), y = P.y + (o.dy ?? -20);
  if (o.fromTip !== false && o.dx === undefined) { const tp = bwTip(); if (tp && Math.abs(tp.x - P.x) < 30 && tp.y < P.y - 4) { x = tp.x; y = tp.y + (o.oy || 0); } }
  if (o.x !== undefined) { x = o.x; y = o.y; }
  const pr = { owner: 'player', kind: 'bw_arrow', fxName: 'bw_none', face, t: 0, hits: new Set(), win: [9e9, 9e9],
    x, y, vx: face * Math.cos(a) * spd, vy: Math.sin(a) * spd, g: o.g || 0, life: o.life || 0.5, r: 2, dmg: 0, pierce: true, delay: o.delay || 0,
    bw: { ...o, A: o.A || ATK[P.state] || ATK.bw_1, sx: o.sx ?? P.x, face, px: o.x !== undefined ? x : P.x, py: y, ox: x, oy: y, flown: 0, lv: o.lv || 1, n: 0, per: new Map(), trail: [], done: false } };
  projectiles.push(pr); BW.arrows.push(pr);
  return pr;
}
function bwArrowHit(pr, t, hb) {
  const b = pr.bw, A = b.A, heavy = A.kind === 'heavy' || !!b.heavy;
  const d = Math.max(0, b.face > 0 ? hb.x0 - b.sx : b.sx - hb.x1);
  const k = b.flat ? 1 : bwSweet(d, b.pb), sweet = !b.flat && bwInSweet(d);
  const W = D.W, fire = P.fireT > 0 || (W.fire && heavy);
  const dmg = outgoing(D.light, b.mul * k, 'melee') * (A.counter ? P.counterMul || 1 : 1) * (P.twinBuff ? 1.25 : 1);
  const y = clamp(pr.y, hb.y0 + 2, hb.y1 - 2), x = clamp(pr.x, hb.x0 + 2, hb.x1 - 2);
  let poise = (b.poise || 0) * (typeof skPoiseMul === 'function' ? skPoiseMul(A) : 1);
  poise = mvPoiseFor(t, poise, A, y);
  const info = { dmg: dmg * (fire && W.fire ? 1 + W.fire : 1), poise, dir: b.face, kind: heavy ? 'heavy' : 'light', charged: heavy && b.lv >= 2, bleed: (typeof skBleedUnits === 'function' ? skBleedUnits(heavy, b.mul * k) : bleedAmt(heavy)) * (b.bleedK ?? 1), fire, rotDot: !!W.rot,
    x, y, melee: true, big: heavy || b.lv >= 3 || !!b.big, arrow: true };
  t.hit(info);
  BW.log.push({ id: A.mv && A.mv.id, mul: b.mul, k, d: Math.round(d), lv: b.lv, dmg: info.dmg / D.light, flown: Math.round(Math.hypot(pr.x - b.ox, pr.y - b.oy)) }); if (BW.log.length > (BW.cap || 60)) BW.log.shift();   // (tests read it)
  runHooks('strike', t, { dmg, heavy, x, y }, A);
  if (A.counter && !P.mvGained && !t.prop) { P.mvGained = true; mvGain('counter'); }
  if (b.reel && !t.boss && !t.prop && t.alive !== false && t.breakStance && !(t.cfg && t.cfg.elite) && t.state !== 'stagger') t.breakStance();
  if (P.twinBuff) P.twinBuff = false;
  if (has('soul_siphon')) P.fp = Math.min(D.maxFp, P.fp + 2 * clamp(b.mul * k, 0.25, 3));
  // feedback: a clean white-gold bite in the sweet spot, a dull thud point-blank, a glancing tick far away
  if (!t.prop) {
    const col = sweet ? (b.lv >= 3 ? '255,244,210' : '255,226,160') : k < 0.8 ? '170,160,150' : '220,214,200';
    mvSpark(x, y, sweet ? 4 + b.lv * 2 : 3, col, sweet ? 150 : 90);
    if (sweet && b.lv >= 2) { if (typeof feelFlash === 'function') feelFlash(x, y, 10 + b.lv * 5, BW_COL[b.lv], 0.8, 0.07); }
    if (sweet && !b.sweetTone) { b.sweetTone = true; tone(1250 + b.lv * 120, 0.05, 0.03, 'sine', 1.1); }
    // V: point-blank burst -- a level 3 shot inside 20 px bursts through the foe (+0.6, hits behind it too)
    if (b.lv >= 3 && d < 20 && mvHas(5) && !b.bursted && !b.drill) {
      b.bursted = true;
      const bx0 = b.face > 0 ? hb.x0 - 4 : hb.x0 - 30, bx1 = b.face > 0 ? hb.x1 + 30 : hb.x1 + 4;
      mvStrikeAt(rect(bx0, hb.y0, bx1, hb.y1), 0.6, 20, { A, kind: 'heavy', big: true });
      spawnFx(fxOr('parry_flash', 'hit'), x, y, b.face, null, { alpha: 0.8 }); shake = Math.max(shake, 4);
      for (let i = 0; i < 14; i++) particles.push({ x, y, vx: b.face * rand(40, 200), vy: rand(-80, 40), g: 220, life: rand(0.2, 0.5), kind: i % 2 ? 'gold' : 'spark' });
      tone(180, 0.2, 0.08, 'sawtooth', 0.5);
    }
  }
  if (b.onHit) b.onHit(t, info);
}
// the burn-out: the arrow's last stretch of flight -- it chars from the head back, then falls apart as ash and embers
function bwBurnOut(pr, ang) {
  const b = pr.bw, len = b.drill ? 14 : 11, c = Math.cos(ang), s = Math.sin(ang);
  BW.burn.push({ x: pr.x, y: pr.y, ang, len, vx: pr.vx * 0.06, vy: pr.vy * 0.06, t: 0, max: 0.3, lv: b.lv });
  if (BW.burn.length > 24) BW.burn.shift();
  for (let i = 0; i <= len; i += 2) {
    const px = pr.x - c * i, py = pr.y - s * i;
    particles.push({ x: px, y: py, vx: pr.vx * 0.05 + rand(-10, 10), vy: rand(-28, -6), life: rand(0.35, 0.7), kind: i % 4 ? 'ash' : 'ember' });
  }
  for (let i = 0; i < 2 + b.lv; i++) particles.push({ x: pr.x + rand(-1, 1), y: pr.y + rand(-1, 1), vx: pr.vx * 0.08 + rand(-20, 20), vy: -rand(20, 50), life: rand(0.25, 0.5), kind: b.lv >= 3 ? 'gold' : 'ember' });
  addLight(pr.x, pr.y, 14, '255,140,60', 0.5);
}
// stick an arrow where it stopped (a wall, the floor, a foe for a moment)
function bwStick(x, y, ang, t, life = 1.4) {
  BW.stuck.push({ x, y, ang, t, ox: t ? x - t.x : 0, oy: t ? y - t.y : 0, life, max: life });
  if (BW.stuck.length > 28) BW.stuck.shift();
}
function bwArrowsTick(dt) {
  for (const pr of BW.arrows) {
    const b = pr.bw;
    if (pr.delay > 0) { b.px = pr.x; b.py = pr.y; continue; }
    if (b.done) continue;
    const ang = Math.atan2(pr.vy, pr.vx);
    if (pr.life <= 0 || !projectiles.includes(pr)) {   // the engine stopped it: a wall / the floor / a ward / the room changed
      b.done = true; if (pr.t > 0.02 && projectiles.length >= 0) { bwStick(pr.x, pr.y, ang, null); for (let i = 0; i < 3; i++) particles.push({ x: pr.x, y: pr.y, vx: rand(-40, 40), vy: -rand(10, 60), g: 300, life: 0.3, kind: 'spark' }); }
      continue;
    }
    // range: past BW_RANGE px of flight the arrow is pulled back to that point, sweeps up to it and burns out there
    let burn = false;
    if (!b.rain) {
      const d1 = Math.hypot(pr.x - b.ox, pr.y - b.oy);
      if (d1 >= BW_RANGE) {
        const d0 = Math.hypot(b.px - b.ox, b.py - b.oy), f = d1 > d0 ? clamp((BW_RANGE - d0) / (d1 - d0), 0, 1) : 0;
        pr.x = b.px + (pr.x - b.px) * f; pr.y = b.py + (pr.y - b.py) * f; burn = true;
      }
      b.flown = Math.min(BW_RANGE, d1);
    }
    // sweep the path since the last frame against the targets (a thin box around the segment)
    const x0 = Math.min(b.px, pr.x) - 2, x1 = Math.max(b.px, pr.x) + 2, y0 = Math.min(b.py, pr.y) - 2, y1 = Math.max(b.py, pr.y) + 2;
    const seg = rect(x0, y0, x1, y1);
    let stop = false, inside = false;
    for (const t of targets()) {
      const hb = hbOf(t); if (!hb || !overlap(seg, hb)) continue;
      if (b.drill) {   // the hollow piercer: bores slowly through each foe, a bite every 80 ms, up to b.drill per foe
        const h = b.per.get(t) || { n: 0, at: -1 };
        if (h.n < b.drill && !t.prop) inside = true;
        if (h.n >= b.drill || (h.at >= 0 && pr.t - h.at < 0.08)) continue;
        h.n++; h.at = pr.t; b.per.set(t, h); bwArrowHit(pr, t, hb);
        if (!t.prop) for (let i = 0; i < 3; i++) particles.push({ x: pr.x, y: pr.y + rand(-3, 3), vx: -b.face * rand(30, 90), vy: rand(-50, 50), life: 0.25, kind: 'gold' });
        continue;
      }
      if (pr.hits.has(t)) continue;
      pr.hits.add(t); b.n++;
      bwArrowHit(pr, t, hb);
      if (!b.pierce || (typeof b.pierce === 'number' && b.n >= b.pierce) || t.prop) {
        stop = true; if (!t.prop && t.alive !== false) bwStick(clamp(pr.x, hb.x0 + 3, hb.x1 - 3), clamp(pr.y, hb.y0 + 3, hb.y1 - 3), ang, t, 0.45);
        break;
      }
    }
    if (stop) { pr.life = 0; b.done = true; continue; }
    if (burn) { pr.life = 0; b.done = true; bwBurnOut(pr, ang); continue; }
    if (b.drill) { const sp = inside ? 34 : b.spd0 || 230; pr.vx = b.face * sp; if (inside && Math.random() < 0.5) shake = Math.max(shake, 1.5); }
    b.trail.push({ x: pr.x, y: pr.y }); if (b.trail.length > 6) b.trail.shift();
    b.px = pr.x; b.py = pr.y;
    if (b.lv >= 2 && Math.random() < 0.25 * b.lv) particles.push({ x: pr.x - Math.cos(ang) * 6, y: pr.y - Math.sin(ang) * 6, vx: -pr.vx * 0.05, vy: rand(-10, 10), life: 0.22, kind: b.lv >= 3 ? 'gold' : 'ember' });
    if (b.drill && Math.random() < 0.8) particles.push({ x: pr.x + rand(-2, 2), y: pr.y + Math.sin(pr.t * 40) * 4, vx: -pr.vx * 0.1, vy: 0, life: 0.3, kind: 'gold' });
  }
  BW.arrows = BW.arrows.filter(pr => !pr.bw.done || pr.life > 0);
  for (const q of BW.burn) { q.t += dt; q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 40 * dt; }
  if (BW.burn.length) BW.burn = BW.burn.filter(q => q.t < q.max);
  for (const s of BW.stuck) s.life -= dt;
  if (BW.stuck.length) BW.stuck = BW.stuck.filter(s => s.life > 0 && (!s.t || s.t.alive !== false));
}
// one arrow drawn as pixels along its heading: fletching, shaft, a steel broadhead (glowing by level)
function bwDrawArrow(x, y, ang, len, a, lv, glow) {
  const c = Math.cos(ang), s = Math.sin(ang), pts = [];
  for (let i = 0; i <= len; i++) pts.push([Math.round(x - c * i), Math.round(y - s * i), i]);
  if (!glow) {   // a dark outline first (like every sprite's), so the arrow reads on any background
    g.fillStyle = `rgba(16,12,18,${0.85 * a})`;
    for (const [px, py] of pts) { g.fillRect(px - 1, py, 3, 1); g.fillRect(px, py - 1, 1, 3); }
    g.fillRect(Math.round(x - c - s * 2) - 1, Math.round(y - s + c * 2) - 1, 3, 3); g.fillRect(Math.round(x - c + s * 2) - 1, Math.round(y - s - c * 2) - 1, 3, 3);
  }
  for (const [px, py, i] of pts) {
    if (glow && i > 2) continue;
    g.fillStyle = i <= 2 ? (glow ? `rgba(${BW_COL[lv] || '232,238,252'},${a})` : `rgba(232,238,252,${a})`) : i >= len - 2 ? `rgba(190,60,50,${a})` : `rgba(176,150,110,${a})`;
    g.fillRect(px, py, 1, 1);
  }
  if (!glow) {   // the broadhead's barbs and the fletching's vanes
    g.fillStyle = `rgba(128,134,158,${a})`; g.fillRect(Math.round(x - c - s), Math.round(y - s + c), 1, 1); g.fillRect(Math.round(x - c + s), Math.round(y - s - c), 1, 1);
    g.fillStyle = `rgba(150,44,40,${a})`; const tx = x - c * len, ty = y - s * len; g.fillRect(Math.round(tx + c - s), Math.round(ty + s + c), 1, 1); g.fillRect(Math.round(tx + c + s), Math.round(ty + s - c), 1, 1);
  }
}
const bwFadeA = b => (b.rain ? 1 : 1 - 0.65 * clamp((b.flown - BW_FADE) / (BW_RANGE - BW_FADE), 0, 1));   // 1 -> 0.35 over the last 20 px
function bwArrowsRender() {
  for (const s of BW.stuck) {
    const k = Math.min(1, s.life / Math.min(0.4, s.max));
    const x = s.t ? s.t.x + s.ox : s.x, y = s.t ? s.t.y + s.oy : s.y;
    // only the back half shows: the head is buried
    const c = Math.cos(s.ang), sn = Math.sin(s.ang);
    g.fillStyle = `rgba(16,12,18,${0.8 * k})`; for (let i = 3; i <= 9; i++) g.fillRect(Math.round(x - c * i), Math.round(y - sn * i) - 1, 1, 3);
    for (let i = 3; i <= 9; i++) { g.fillStyle = i >= 8 ? `rgba(190,60,50,${k})` : `rgba(150,124,90,${k})`; g.fillRect(Math.round(x - c * i), Math.round(y - sn * i), 1, 1); }
  }
  for (const pr of BW.arrows) {
    if (pr.delay > 0 || pr.life <= 0) continue;
    const b = pr.bw, ang = Math.atan2(pr.vy, pr.vx);
    bwDrawArrow(pr.x, pr.y, ang, b.drill ? 14 : 11, bwFadeA(b), b.lv, false);
  }
  // burnt-out arrows: a charred shaft that greys and crumbles away (the head first) as it drifts down
  for (const q of BW.burn) {
    const k = q.t / q.max, c = Math.cos(q.ang), s = Math.sin(q.ang), from = Math.floor(k * q.len);
    for (let i = from; i <= q.len; i++) {
      if ((i + Math.floor(q.t * 40)) % 3 === 0 && k > 0.3) continue;   // crumbling gaps
      const px = Math.round(q.x - c * i), py = Math.round(q.y - s * i + k * k * 3);
      g.fillStyle = i - from < 2 ? `rgba(255,${150 - 80 * k | 0},60,${1 - k})` : `rgba(${70 - 30 * k | 0},${60 - 25 * k | 0},${58 - 20 * k | 0},${0.9 * (1 - k)})`;
      g.fillRect(px, py, 1, 1);
    }
  }
  drawGlow(() => {
    for (const q of BW.burn) { const k = q.t / q.max; addLight(q.x, q.y, 12 * (1 - k), '255,130,50', 0.5 * (1 - k)); g.fillStyle = `rgba(255,170,80,${0.8 * (1 - k)})`; g.fillRect(Math.round(q.x - Math.cos(q.ang) * k * q.len), Math.round(q.y - Math.sin(q.ang) * k * q.len), 1, 1); }
    for (const pr of BW.arrows) {
      if (pr.delay > 0 || pr.life <= 0) continue;
      const b = pr.bw, ang = Math.atan2(pr.vy, pr.vx), col = b.drill ? '255,226,150' : BW_COL[b.lv], fa = bwFadeA(b);
      // the last stretch before the burn-out: the head smoulders orange
      if (fa < 1) { const h = 1 - (fa - 0.35) / 0.65; g.fillStyle = `rgba(255,140,60,${0.9 * h})`; g.fillRect(Math.round(pr.x), Math.round(pr.y), 1, 1); g.fillRect(Math.round(pr.x - Math.cos(ang)), Math.round(pr.y - Math.sin(ang)), 1, 1); addLight(pr.x, pr.y, 8, '255,130,50', 0.4 * h); if (Math.random() < 0.4 * h) particles.push({ x: pr.x, y: pr.y, vx: -pr.vx * 0.04, vy: -rand(8, 24), life: 0.3, kind: 'ember' }); }
      // the streak behind it: faint for level 1, an amber tail at 2, a long white-gold one at 3
      const tr = b.trail, n = tr.length;
      if (n > 1) {
        g.save(); g.globalCompositeOperation = 'lighter'; g.lineCap = 'round';
        for (let i = 1; i < n; i++) {
          const k = i / n * fa; g.strokeStyle = `rgba(${col},${(b.lv === 1 ? 0.18 : 0.32 + 0.12 * b.lv) * k})`; g.lineWidth = b.lv >= 3 || b.drill ? 2 : 1;
          g.beginPath(); g.moveTo(tr[i - 1].x, tr[i - 1].y); g.lineTo(tr[i].x, tr[i].y); g.stroke();
        }
        g.restore();
      }
      if (b.lv >= 2 || b.drill) bwDrawArrow(pr.x, pr.y, ang, 2, 0.95 * fa, b.lv, true);
      addLight(pr.x, pr.y, b.drill ? 30 : 10 + b.lv * 7, col, b.lv === 1 ? 0.35 : 0.7);
      if (b.drill) mvStar(pr.x + Math.cos(ang) * 2, pr.y + Math.sin(ang) * 2, 3 + Math.sin(pr.t * 50) * 1.5, '255,236,180', 0.9);
    }
  });
}

// ---- shots
function bwShootQuick(lv, mulEach = 0.4, o = {}) {
  const spread = lv === 1 ? [0] : lv === 2 ? [-0.035, 0.035] : [-0.06, 0, 0.06];
  for (const [i, a] of spread.entries()) bwArrow({ mul: mulEach, poise: o.poise ?? 8, lv, ang: a + (o.ang || 0), spd: 440 + lv * 20, life: 0.5, oy: (i - (spread.length - 1) / 2) * 1, pb: o.pb, ...o.arrow });
  bwTwang(lv);
}
function bwLevelUpFx(lv) {
  const tp = bwTip() || { x: P.x + P.face * 12, y: P.y - 20 };
  bwCreak(lv); if (lv >= 3) sfx.glint();
  if (typeof feelFlash === 'function') feelFlash(tp.x, tp.y, 18 + lv * 8, BW_COL[lv], 1.1, 0.12);
  mvSpark(tp.x, tp.y, 3 + lv * 2, BW_COL[lv], 90);
}

// a commit move's own roll-cancel, later than the engine's (from `ms` into the move)
function bwLateCancel(ax, ms) {
  if (P.mvT >= ms && peek('roll') && P.st > 0 && (P.ground || P.airDash)) { take('roll'); P.mvQ = null; mvDodgeStart(ax); return 'stop'; }
}

// ---- the draw (hold K): a loop move; tap K (released inside BW_TAP ms) plays the route's tap move instead
function bwDrawDef() {
  return { tags: ['bw_draw', 'sp_heavy'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, draw: true,
    on: {
      start(A, o) {
        P.bwDrawMs = 0; P.bwDraw0 = clamp(o.lv0 || P.bwLv || 1, 1, 3); P.bwDrawLv = P.bwDraw0; P.bwTapTo = o.tap || null;
      },
      update(dt, A, ax, grav) {
        P.bwDrawMs += dt * 1000; P.charge = P.bwDrawMs / 1000;
        const pull = Math.max(0, P.bwDrawMs - 120);   // the first 120 ms raise the bow and nock
        const lv = Math.min(3, P.bwDraw0 + Math.floor(pull / BW_LV_MS));
        if (lv !== P.bwDrawLv) { P.bwDrawLv = lv; bwLevelUpFx(lv); }
        // walk at 40% while drawn, turning with the stick (the aim follows)
        if (ax && ax !== P.face && P.bwDrawMs > 60) P.face = ax;
        if (P.ground) { P.vx = approach(P.vx, ax * MAXV * 0.4, 700 * dt); } else P.vx = approach(P.vx, ax * MAXV * 0.4, 400 * dt);
        grav();
        const walking = P.ground && Math.abs(P.vx) > 8 && P.bwDrawMs > 120;
        const an = P.anim;
        if (walking && pHas('bw_drawwalk')) { if (an.tag !== 'bw_drawwalk') an.set('bw_drawwalk', true, 1); an.speed = Math.abs(P.vx) / (MAXV * 0.4); }
        else if (pHas('bw_draw')) {
          if (an.tag !== 'bw_draw') an.set('bw_draw', true, 0);
          an.speed = 0; an.done = false;
          // frames: 0 raise, 1 nock, 2 lv1 draw, 3 lv2, 4 lv3, 5 lv3 strain (alternates with 4)
          const want = P.bwDrawMs < 60 ? 0 : P.bwDrawMs < 120 ? 1 : lv === 1 ? 2 : lv === 2 ? 3 : (Math.floor(P.bwDrawMs / 140) % 2 ? 5 : 4);
          const i = Math.min(want, an.n - 1); if (i !== an.i) { an.i = i; an.changed = true; } an.t = 0;
        }
        if (peek('parry') && P.ground && P.st > 0) { take('parry'); mvStart('bw_deflect'); return 'stop'; }
        if (peek('roll') && P.st > 0) {   // L while drawn: a charge step that banks what you drew (+1 for the step)
          take('roll'); P.bwLv = P.bwDrawLv; mvDodgeStart(ax); return 'stop';
        }
        if (!held.has('heavy')) {
          if (P.bwDrawMs < BW_TAP && P.bwTapTo && ATK[P.bwTapTo] && mvHas(ATK[P.bwTapTo].mv.rank)) {
            const id = P.bwTapTo; if (mvStart(id, { t0: Math.min(P.bwDrawMs, ATK[id].mv.wind - 30), lv: P.bwLv })) return 'stop';
          }
          if (P.bwDrawMs >= BW_MIN) { mvStart('bw_power', { lv, charged: lv >= 2 }); return 'stop'; }
        }
      },
    } };
}

// ---- the table
const BW_Q = { bw_1: 'bw_2', bw_2: 'bw_3', bw_3: 'bw_pin', bw_dash: 'bw_3' };
function bwQuick(id, step, tags) {
  return { tags, dmg: 0.4, poise: 8, stam: 9, wind: 120, total: 340, step, noHit: true, fx: null, lunge: step === 2 ? 6 : 0,
    next: { J: BW_Q[id], K: () => ({ id: 'bw_draw', tap: 'bw_stab' }) },
    on: { swing() { const lv = P.bwLv || 1; P.bwShotLv = lv; bwShootQuick(lv, 0.4); bwBank(lv + 1, 'quiet'); } } };
}
mvRegister('bow', {
  light: ['bw_1', 'bw_2', 'bw_3', 'bw_pin'], K: 'bw_draw', heavyTag: 'bw_power', up: 'bw_arc', air: 'bw_air', down: 'bw_down',
  plunge: { dmg: 1.5, poise: 36, stam: 16 },
  // L: the charge step -- neutral steps back (out to the sweet spot), a held direction steps that way
  dodge: () => ({ stam: 12, total: 300, inv: 0.16, dist: 40, tags: ['bw_step', 'kt_sidestep', 'roll'], chain: mvHas(2) ? 2 : 0, kind: 'bwstep', hopDir: true, jAt: 150, kAt: 120 }),
  rollJ: () => ({ id: 'bw_dash', step: 1 }),
  rollK() { return mvStart('bw_draw', { tap: 'bw_leap' }); },
  onK(ax) { return mvStart('bw_draw', { tap: null }); },
  onAirK(ax) {
    if (P.bwDived || P.st <= 0 || P.state === 'wall') return false;
    take('heavy'); if (ax) P.face = ax;
    return mvStart('bw_dive') || true;
  },
  onI(ax) {
    if (!P.ground) return false;
    take('parry'); if (ax) P.face = ax;
    if (P.st <= 0) { sfx.deny(); return true; }
    return mvStart('bw_deflect') || true;
  },
  // each step banks +1 level; back-to-back steps without a shot between stack only at Mastery II (L L)
  dodged0(g) {
    if (g.kind !== 'bwstep') return;
    P.bwSteps = (P.bwSteps || 0) + 1;
    if (P.bwSteps > (mvHas(2) ? 2 : 1)) return;
    const lv = Math.min(3, (P.bwLv || 1) + 1); if (lv > (P.bwLv || 1)) bwLevelUpFx(lv); bwBank(lv, 'quiet');
  },
  started(A, o) {
    const id = A.mv.id;
    if (BW_Q[id] || id === 'bw_stab') P.bwPrevQ = BW_Q[id] ? id : P.bwPrevQ;
    if (!A.mv.draw) { P.bwIdle = 0; P.bwSteps = 0; }
  },
  hurt(c) {
    // the limb deflect: a parryable blow inside the first 150 ms is turned on the bow's limb, then the point-blank counter shot.
    // v15 balance (like the katana's Iai): a blow that can't be parried is only turned aside -- block-cost stamina
    // (6 + 0.8 x dmg, guard-scaled), no counter shot; without the stamina it lands.
    if (P.state === 'bw_deflect' && P.mvT <= 150 && !c.negate && !(c.opt && c.opt.parryable)) {
      const cost = (6 + c.dmg * 0.8) * (typeof mvGuardScale === 'function' ? mvGuardScale() : 1);
      if (P.st < cost) return;
      c.negate = true; spend(cost); P.stDelay = 0.8;
      if (c.dir) { P.face = -c.dir; P.vx = c.dir * 90; }
      sfx.block(); hitstop = Math.max(hitstop, 0.06); shake = Math.max(shake, 2);
      spawnFx(fxOr('parry_spark', 'hit'), P.x + P.face * 12, P.y - 22, P.face);
      return;
    }
    if (P.state === 'bw_deflect' && P.mvT <= 150 && !c.negate) {
      c.negate = true; mvGain('counter');
      if (c.dir) P.face = -c.dir;
      sfx.parry(); hitstop = Math.max(hitstop, 0.12); shake = Math.max(shake, 3);
      spawnFx(fxOr('parry_flash', 'parry_spark'), P.x + P.face * 12, P.y - 22, P.face);
      mvSpark(P.x + P.face * 11, P.y - 24, 10, '255,236,200', 170);
      if (c.opt && c.opt.src && c.opt.src.onParried) c.opt.src.onParried();
      runHooks('parry', c.opt && c.opt.src);
      mvStart('bw_counter', { counterMul: 1 });
    }
  },
  regenMul() { const A = ATK[P.state]; return A && A.mv && A.mv.draw ? 0.5 : 1; },
  landed() { P.bwDived = false; },
  tickAll(dt, cur) {
    bwArrowsTick(dt);
    if (!cur) return;
    P.bwLv = P.bwLv || 1;
    const A = ATK[P.state], busy = A && A.mv && A.mv.type === 'bow';
    if (!busy && P.state !== 'roll') {
      P.bwIdle = (P.bwIdle || 0) + dt;
      if (P.bwIdle > BW_DECAY) P.bwSteps = 0;
      if (P.bwIdle > BW_DECAY && P.bwLv > 1) {   // the chain went cold: the level gutters back to 1
        P.bwLv = 1; P.bwSteps = 0; tone(300, 0.12, 0.03, 'triangle', 0.6);
        const tp = bwTip(); if (tp) for (let i = 0; i < 4; i++) particles.push({ x: tp.x, y: tp.y, vx: rand(-15, 15), vy: -rand(10, 30), life: 0.35, kind: 'ash' });
      }
    }
    // the sweet-spot glint: the nearest foe ahead sits 12-56 px away
    const n = bwNearest(90);
    const inSweet = !!(n && bwInSweet(n.d));
    if (inSweet && !P.bwSweet) P.bwGlintT = 0;
    P.bwSweet = inSweet; P.bwGlintT = (P.bwGlintT || 0) + dt;
  },
  interrupted() {},
  renderAll(cur) {
    bwArrowsRender();
    if (!cur || !P || P.state === 'dead') return;
    const A = ATK[P.state], tp = bwTip(); if (!tp) return;
    const drawing = A && A.mv && A.mv.draw, lv = drawing ? P.bwDrawLv || 1 : P.bwLv || 1;
    // the charge on the arrowhead: nothing much at level 1 (unless drawn), an amber coal at 2, a white-gold star at 3
    if (lv >= 2 || drawing) {
      const pul = 0.75 + 0.25 * Math.sin(P.clk * (lv >= 3 ? 16 : 9));
      addLight(tp.x, tp.y, 8 + lv * 8, BW_COL[lv], (drawing ? 0.5 : 0.3) + 0.15 * lv * pul);
      drawGlow(() => {
        g.save(); g.globalCompositeOperation = 'lighter';
        g.fillStyle = `rgba(${BW_COL[lv]},${(0.35 + 0.2 * lv) * pul})`; g.fillRect(Math.round(tp.x) - 1, Math.round(tp.y) - 1, 2, 2);
        if (lv >= 2) { g.fillStyle = `rgba(${BW_COL[lv]},${0.18 * pul})`; g.fillRect(Math.round(tp.x) - 2, Math.round(tp.y) - 2, 4, 4); }
        g.restore();
      });
      if (lv >= 2) mvStar(tp.x, tp.y, (lv >= 3 ? 2.5 : 1.5) + 1.5 * pul, BW_COL[lv], (lv >= 3 ? 0.6 : 0.4) + 0.3 * pul);
      if (Math.random() < 0.1 * lv) particles.push({ x: tp.x + rand(-1, 1), y: tp.y + rand(-1, 1), vx: rand(-6, 6), vy: -rand(10, 25), life: 0.3, kind: lv >= 3 ? 'gold' : 'ember' });
    }
    // the sweet-spot glint: a sharp white star sweeps over the broadhead every 0.55 s while the foe is in the spot
    if (P.bwSweet) {
      const ph = (P.bwGlintT % 0.55) / 0.55, k = ph < 0.35 ? Math.sin(ph / 0.35 * Math.PI) : 0;
      if (k > 0.02) { mvStar(tp.x + P.face * 1, tp.y, 2 + 3 * k, '255,255,255', 0.85 * k); addLight(tp.x, tp.y, 12, '255,250,235', 0.5 * k); }
      else drawGlow(() => { g.fillStyle = 'rgba(255,255,255,0.55)'; g.fillRect(Math.round(tp.x), Math.round(tp.y), 1, 1); });
    }
  },
  hud(x) {
    // three arrowheads for the charge level (the banked one, or the drawn one while you draw), a draw bar under them
    const A = ATK[P.state], drawing = A && A.mv && A.mv.draw, lv = drawing ? P.bwDrawLv || 1 : P.bwLv || 1;
    for (let i = 1; i <= 3; i++) {
      const on = i <= lv, cx = x + 3 + (i - 1) * 6, cy = 22;
      vctx.fillStyle = on ? `rgb(${BW_COL[lv]})` : 'rgba(40,34,44,0.85)';
      vctx.beginPath(); vctx.moveTo(ox + (cx + 2.2) * scale, oy + cy * scale); vctx.lineTo(ox + (cx - 1.6) * scale, oy + (cy - 2) * scale); vctx.lineTo(ox + (cx - 0.6) * scale, oy + cy * scale); vctx.lineTo(ox + (cx - 1.6) * scale, oy + (cy + 2) * scale); vctx.closePath(); vctx.fill();
    }
    if (drawing && lv < 3) { const f = clamp((Math.max(0, P.bwDrawMs - 120) % BW_LV_MS) / BW_LV_MS, 0, 1); mvHudBar(x + 1, 25.4, 16, 1, f, `rgb(${BW_COL[Math.min(3, lv + 1)]})`); }
    else if (!drawing && lv > 1) { mvHudBar(x + 1, 25.4, 16, 1, clamp(1 - (P.bwIdle || 0) / BW_DECAY, 0, 1), 'rgba(200,190,170,0.7)'); }
    if (P.bwSweet) { const k = 0.6 + 0.4 * Math.sin(P.clk * 8); vctx.fillStyle = `rgba(255,255,255,${k})`; vctx.fillRect(ox + (x + 21) * scale, oy + 21.2 * scale, 1.6 * scale, 1.6 * scale); }
  },
  unlocks: [
    { rank: 2, id: 'bw_step2', name: 'Double charge step', input: 'L L', desc: 'A second charge step straight out of the first: +1 level each.' },
    { rank: 3, id: 'bw_hollow', name: 'Hollow piercer', input: 'lv3 power shot → K', desc: 'One arrow drilling through everything in a line: 6 bites of 0.4.' },
    { rank: 4, id: 'bw_arc7', name: 'Arc shot ×7', input: '↑J', desc: 'The arc shot looses seven arrows instead of five.' },
    { rank: 5, id: 'bw_burst', name: 'Point-blank burst', input: '–', desc: 'Level 3 shots inside 20 px burst through the foe: +0.6, hits behind it.' },
  ],
  combos: [
    { rank: 1, name: 'Volley chain', input: 'J J J', desc: 'Quick shots: 1, 2, 3 arrows (0.4 each). Best at 12-56 px from the foe.' },
    { rank: 1, name: 'Pinning shot', input: 'J J J J', desc: 'One heavy arrow (1.7) that staggers small foes. Spends the level.' },
    { rank: 1, name: 'Draw', input: 'hold K', desc: '+1 level every 0.4 s, from the level you banked. Walk at 40%.' },
    { rank: 1, name: 'Power shot', input: 'release K', desc: '0.9 / 1.4 / 2.0 by level; lv3 pierces. Arrows burn out at ~85 px.' },
    { rank: 1, name: 'Charge step', input: 'L', desc: 'A quick sidestep that raises the next shot one level.' },
    { rank: 1, name: 'Step and draw', input: 'L → hold K', desc: 'Draw straight out of the step, from the level it banked.' },
    { rank: 1, name: 'Arrow stab', input: 'J → K', desc: 'Jab the nocked arrow into the foe (0.8). J: back to the volley.' },
    { rank: 1, name: 'Recoil shot', input: 'J → K → K', desc: 'A point-blank shot that kicks you 30 px back (1.2).' },
    { rank: 1, name: 'Dash shot', input: 'L → J', desc: 'Skid in and loose at the banked level (1.0 at lv2). J: volley.' },
    { rank: 1, name: 'Leaping point-blank', input: 'L → K', desc: 'Hop in and loose a fan of three down into the foe (1.5).' },
    { rank: 1, name: 'Limb deflect', input: 'I (timed)', desc: 'A 150 ms window: turn the blow on the limb, counter shot (1.6).' },
    { rank: 1, name: 'Arc shot', input: '↑J', desc: 'Loose high: five arrows rain 30-82 px ahead (0.3 each).' },
    { rank: 1, name: 'Aerial shot', input: 'air J', desc: 'Loose down at a slant in mid-air (0.9). Twice per jump.' },
    { rank: 1, name: 'Talon stomp', input: 'air ↓J', desc: 'Stamp down with the bow limb: pogo off foes and spikes.' },
    { rank: 1, name: "Hunter's dive", input: 'air K', desc: 'Dive at the foe and loose point-blank as you land (1.5).' },
    { rank: 2, name: 'Double charge step', input: 'L L', desc: 'Two steps in a row: straight to level 3.' },
    { rank: 3, name: 'Hollow piercer', input: 'lv3 power shot → K', desc: 'A drilling arrow through the whole line: 6 × 0.4.' },
    { rank: 4, name: 'Arc shot ×7', input: '↑J', desc: 'Seven arrows in the arc.' },
    { rank: 5, name: 'Point-blank burst', input: 'lv3 shot < 20 px', desc: 'The shot bursts through the foe: +0.6, and hits behind it.' },
  ],
}, {
  bw_1: bwQuick('bw_1', 0, ['bw_1', 'sp_1']),
  bw_2: bwQuick('bw_2', 1, ['bw_2', 'sp_2']),
  bw_3: bwQuick('bw_3', 2, ['bw_3', 'sp_1']),
  // J J J J: the pinning shot -- step in, a deep draw, one heavy arrow that staggers small foes; spends the level
  bw_pin: { tags: ['bw_pin', 'sp_3'], dmg: 1.7, poise: 30, stam: 12, wind: 200, total: 520, step: 3, fin: true, noHit: true, lunge: 8,
    on: { swing() { const lv = P.bwLv || 1; P.bwShotLv = lv; bwArrow({ mul: 1.7, poise: 30, lv, spd: 520, life: 0.5, reel: true, big: true }); bwTwang(Math.max(2, lv)); shake = Math.max(shake, 2); bwBank(1, 'quiet'); } } },
  bw_draw: bwDrawDef(),
  // release K: the power shot at the drawn level (lv3 pierces); K tap after a lv3 one = hollow piercer (III)
  // (commit, with its own roll-cancel from 260 ms: the shot -> charge step loop can't skip the bow's recoil)
  bw_power: { tags: ['bw_power', 'sp_heavy'], kind: 'heavy', dmg: 1.4, poise: 35, stam: 14, wind: 70, total: 520, noHit: true, fin: true, chainK: 450, commit: true,
    next: { K: () => ((P.mvLv || 1) >= 3 && mvHas(3) ? { id: 'bw_draw', tap: 'bw_hollow', lv0: 1 } : { id: 'bw_draw', tap: null, lv0: 1 }) },
    on: { update(dt, A, ax) { return bwLateCancel(ax, 260); },
      swing() {
      const lv = P.mvLv || 1; P.bwShotLv = lv;
      bwArrow({ mul: BW_PWR.dmg[lv], poise: BW_PWR.poise[lv], lv, spd: BW_PWR.spd[lv], life: 0.55, pierce: lv >= 3 ? 3 : false, heavy: true });
      bwTwang(lv); P.vx = -P.face * (20 + lv * 15); shake = Math.max(shake, lv);
      if (lv >= 3) { if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 18, P.y - 20, 40, BW_COL[3], 1.2, 0.1); }
      bwBank(1, 'quiet');
    } } },
  // III -- lv3 power shot -> K: the hollow piercer, one slow arrow drilling through everything in a line
  bw_hollow: { tags: ['bw_hollow', 'sp_heavy'], kind: 'heavy', rank: 3, dmg: 0.4, poise: 70, stam: 22, wind: 360, total: 1100, noHit: true, fin: true, commit: true,
    on: {
      update() { if (P.mvT < 360) { const tp = bwTip(); if (tp && Math.random() < 0.6) particles.push({ x: tp.x + rand(-8, 4) * P.face, y: tp.y + rand(-3, 3), vx: P.face * rand(20, 50), vy: rand(-8, 8), life: 0.25, kind: 'gold' }); P.vx *= 0.8; } },
      swing() {
        P.bwShotLv = 3;
        bwArrow({ mul: 0.4, poise: 70 / 6, lv: 3, spd: 230, spd0: 230, life: 1.6, drill: 6, pierce: true, heavy: true, pb: true });
        bwTwang(3); tone(90, 0.5, 0.08, 'sawtooth', 0.6); shake = Math.max(shake, 4); P.vx = -P.face * 70;
        if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 18, P.y - 20, 50, '255,226,150', 1.3, 0.14);
      } } },
  // J -> K tap: the arrow stab, a melee jab with the nocked arrow; K tap again = recoil shot, J = back to the volley
  bw_stab: { tags: ['bw_stab', 'sp_1'], dmg: 0.8, poise: 16, stam: 10, wind: 120, total: 380, lunge: 10, reach: 34, ys: [-30, -12], fx: null,
    next: { K: () => ({ id: 'bw_draw', tap: 'bw_recoil' }), J: () => BW_Q[P.bwPrevQ] || 'bw_1' },
    on: { swing() { tone(520, 0.05, 0.03, 'triangle', 0.7); } } },
  // stab -> K tap: the recoil shot, point-blank, the kick hops you 30 px back
  bw_recoil: { tags: ['bw_recoil', 'sp_heavy'], kind: 'heavy', dmg: 1.2, poise: 30, stam: 14, wind: 140, total: 520, noHit: true, fin: true, airOk: true,
    move(dt, A, ax, grav) { const t = P.mvT; P.vx = t >= 140 && t < 340 ? -P.face * 150 : approach(P.vx, 0, 1200 * dt); grav(); },   // 30 px back, then planted
    on: { swing() {
      const lv = P.bwLv || 1; P.bwShotLv = lv;
      bwArrow({ mul: 1.2, poise: 30, lv, ang: 0.2, spd: 480, life: 0.4, pb: true, heavy: true });
      bwTwang(Math.max(2, lv)); P.vy = -110; P.ground = false; shake = Math.max(shake, 3);
      spawnFx('dust', P.x, P.y, -P.face); bwBank(lv + 1, 'quiet');
    } } },
  // ↑J: the arc shot -- loose high; five (IV: seven) arrows come down 30-82 px ahead
  bw_arc: { tags: ['bw_arc', 'sp_up'], up: true, dmg: 0.3, poise: 40, stam: 16, wind: 300, total: 760, noHit: true,
    on: { swing() {
      const n = mvHas(4) ? 7 : 5, face = P.face, x0 = P.x, y0 = P.y, lv = P.bwLv || 1;
      for (let i = 0; i < 3; i++) bwArrow({ mul: 0.3, poise: 8, lv, ang: -1.25 + (i - 1) * 0.08, spd: 520, life: 0.28, flat: true, dy: -30, dx: 6 });
      bwTwang(Math.max(2, lv));
      for (let i = 0; i < n; i++) {
        const fx = x0 + face * (32 + 48 * i / (n - 1) + (i % 2 ? 2 : -2));   // 30-82 px ahead (never past the burn-out)
        let top = y0 - 24; while (top > y0 - 130 && !solidAtPx(fx - face * 12, top - 6)) top -= 6;   // under the ceiling
        bwArrow({ face, mul: 0.3, poise: 40 / n, lv, ang: 1.38, spd: 420, life: 0.9, flat: true, rain: true, x: fx - face * (y0 - top) * 0.19, y: top, delay: 0.3 + i * 0.045, sx: x0 });
      }
    } } },
  // L -> J: the dash shot -- skid in and loose at the banked level (0.5 + 0.25 per level, split over its arrows)
  bw_dash: { tags: ['bw_dash', 'sp_1'], dmg: 1.0, poise: 16, stam: 12, wind: 140, total: 400, step: 1, noHit: true, lunge: 22, dash: true, lungeLead: 140, lungeTail: 20,
    next: { J: 'bw_3', K: () => ({ id: 'bw_draw', tap: 'bw_stab' }) },
    on: { swing() { const lv = P.bwLv || 1; P.bwShotLv = lv; bwShootQuick(lv, (0.5 + 0.25 * lv) / lv, { poise: 16 / lv }); bwBank(lv + 1, 'quiet'); } } },
  // L -> K tap: the leaping point-blank -- a hop in, a fan of three loosed down into the foe
  bw_leap: { tags: ['bw_leap', 'sp_hoplunge', 'sp_heavy'], kind: 'heavy', dmg: 1.5, poise: 36, stam: 16, wind: 220, total: 600, noHit: true, fin: true, airOk: true, commit: true,
    lunge: 30, lungeLead: 200, lungeTail: 20, dash: true,
    on: {
      start() { P.vy = -150; P.ground = false; },
      swing() {
        const lv = P.bwLv || 1; P.bwShotLv = lv;
        for (const a of [0.18, 0.3, 0.42]) bwArrow({ mul: 0.5, poise: 12, lv, ang: a, spd: 470, life: 0.35, pb: true, heavy: true, dx: 10, dy: -20 });
        bwTwang(Math.max(2, lv)); shake = Math.max(shake, 3); P.vy = Math.min(P.vy, -60); bwBank(1, 'quiet');
      } } },
  // I: the limb deflect (150 ms), then the counter shot
  bw_deflect: { tags: ['bw_deflect', 'parry'], noHit: true, dmg: 0, poise: 0, stam: 8, wind: 150, total: 260,
    on: { update() { if (P.mvT <= 150) { const tp = { x: P.x + P.face * 10, y: P.y - 24 }; addLight(tp.x, tp.y, 20, '255,232,190', 0.6); } } } },
  bw_counter: { tags: ['bw_counter', 'sp_heavy'], kind: 'heavy', counter: true, dmg: 1.6, poise: 40, stam: 0, wind: 80, total: 460, noHit: true, fin: true, inv: [0, 240],
    on: { swing() {
      const lv = Math.max(2, P.bwLv || 1); P.bwShotLv = lv;
      bwArrow({ mul: 1.6, poise: 40, lv, spd: 520, life: 0.45, pb: true, heavy: true, dx: 6, dy: -20 });
      bwTwang(lv); bwBank(lv + 1, 'quiet'); if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 14, P.y - 20, 36, '255,236,200', 1.1, 0.1);
    } } },
  // air J: the aerial shot, loosed down at a slant (the first one hangs you a moment, like every type's air J)
  bw_air: { tags: ['bw_air', 'sp_air'], air: true, dmg: 0.9, poise: 12, stam: 10, wind: 150, total: 380, noHit: true,
    on: { swing() { const lv = P.bwLv || 1; P.bwShotLv = lv; bwArrow({ mul: 0.9, poise: 12, lv, ang: 0.42, spd: 460, life: 0.45 }); bwTwang(lv); P.vx = -P.face * 30; } } },
  // air ↓J: the talon stomp -- the bow's lower limb stamped down, pogo
  bw_down: { tags: ['bw_down', 'sp_down'], down: true, dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300 },
  // air K: hunter's dive -- dive at 50 degrees, loose point-blank on landing (or on reaching a foe)
  bw_dive: { tags: ['bw_dive', 'sp_dive', 'plunge'], kind: 'heavy', noHit: true, noAirCount: true, airOk: true, dmg: 1.5, poise: 36, stam: 16, wind: 1e9, total: 1e9, loop: true,
    on: {
      start() { P.bwDived = true; P.bwDiveT = 0; sfx.heavySwing(); },
      update(dt) {
        P.bwDiveT += dt;
        if (P.bwDiveT < 0.1) { P.vx = P.face * 30; P.vy = Math.min(P.vy, 0) * 0.5; }   // a beat at the top
        else { P.vx = P.face * 200; P.vy = 250; }
        if (Math.random() < 0.6) MV.ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.15, max: 0.15, col: '#e8d8b0', alpha: 0.3, wf: P.anim.frame });
        const n = bwNearest(26);
        if (P.ground || (P.bwDiveT > 0.1 && n && n.d < 14) || P.bwDiveT > 1.2) { mvStart('bw_diveshot', { lv: P.bwLv || 1, landed: P.ground }); return 'stop'; }
      } } },
  bw_diveshot: { tags: ['bw_diveshot', 'plunge_land'], kind: 'heavy', dmg: 1.5, poise: 36, stam: 0, wind: 60, total: 460, noHit: true, fin: true, airOk: true,
    on: {
      start(A, o) { if (!o.landed) P.vy = -170; P.vx = P.face * 20; spawnFx('dust', P.x, P.y, P.face); },
      swing() {
        const lv = P.mvLv || 1; P.bwShotLv = lv;
        for (const a of [0.1, 0.2, 0.3]) bwArrow({ mul: 0.5, poise: 12, lv, ang: P.ground ? a - 0.18 : a, spd: 480, life: 0.35, pb: true, heavy: true, dx: 10, dy: -16 });
        bwTwang(Math.max(2, lv)); shake = Math.max(shake, 4); bwBank(1, 'quiet');
      } } },
});
// keep the room's arrows in step with the room
HOOKS.enter.push(() => { BW.arrows = []; BW.stuck = []; BW.burn = []; });

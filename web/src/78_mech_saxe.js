// ------------------------------------------------------------------ v15: Switch Axe (`saxe`, prefix sx_, weapon Gravegrinder) -- C1
// docs/WEAPON_REVAMP.md C1, write-up docs/v15/saxe.md. ★★★★★: the gauge is earned the hard way.
// THE SWITCH GAUGE (P.sxG, 0-100). Only Blade mode fills it, only by landing blows on real foes (props / dummies of the
// world don't count):
//   +4 a landed blade hit (+7 "on the beat": the press came in the last 150 ms of the move before), Edge rush +10 (+13),
//   Ratchet cut +3 a tooth, Ratchet twist +12 only if both bites land; Hone (hold K) +10/s, rooted and open.
//   A blade swing that finds nothing while a foe is near: -10. Taking damage: -25. After 2 s without attacking: -4/s.
//   At 100 it LOCKS (no losses) and the edge burns: I = Morph slash (armoured; the blade unfolds into the axe on the hit).
//   I below 100 is a dry rev: a sputter, nothing else.
// AXE MODE: slow, heavy, the damage. The gauge drains 6/s (+15/s while grinding) and 4 for each axe move that lands
//   (Overdrive IV: -30%). At 0 the axe VENTS: it folds back to the blade with a 0.6 s stagger. I = Full Release
//   (III, >= 40: 3.0-6.0 by the gauge, empties it, folds back without venting) or Morph back (a rising cut) below 40.
// The two forms are two weapon overlays: wpn_gravegrinder (shared tags drawn as the SWORD) and wpn_gravegrinder_axe (as
// the AXE); the sx_ tags carry their own form either way (art/player_v15_saxe.py). While P.sxAxe is set, sheet() hands
// out the _axe overlay for wpn_gravegrinder, so every place that draws the weapon (09_main, ghosts, cores, feel) follows.
const SX = { hit: 4, beat: 7, rush: 10, rushBeat: 13, tooth: 3, twist: 12, hone: 10, whiff: 10, hurt: 25, bleed: 4, bleedAfter: 2,
  drain: 6, drainHit: 4, grind: 15, relMin: 40, ventMs: 600, grindTick: 80, grindDmg: 0.28 };
const SX_AXE_SHEET = 'wpn_gravegrinder_axe';
// ---- the overlay redirect (the cleanest single point: every weapon draw asks sheet('wpn_' + SAVE.weapon))
const SX_SHEET0 = sheet;
sheet = function (name, opt) {
  if (name === 'wpn_gravegrinder') { try { if (P && P.sxAxe && ASSETS[SX_AXE_SHEET]) name = SX_AXE_SHEET; } catch (e) {} }
  return SX_SHEET0(name, opt);
};
function sxP() { try { return typeof P !== 'undefined' ? P : null; } catch (e) { return null; } }
function sxIsAxe() { const p = sxP(); return !!(p && p.sxAxe); }
function sxGainG(n, why) {
  if (P.sxAxe || P.sxLock || n <= 0) return;
  P.sxG = Math.min(100, (P.sxG || 0) + n); P.sxFlash = 0.25;
  if (P.sxG >= 100) {   // locked full: the edge catches, a bright ring
    P.sxLock = true; P.sxG = 100; MV.sxFull = (MV.sxFull || 0) + 1;
    tone(880, 0.25, 0.06, 'triangle', 1.5); tone(1320, 0.35, 0.04, 'sine', 1.2, 0.06); sfx.glint && sfx.glint();
    mvSpark(P.x + P.face * 14, P.y - 20, 10, '255,190,110', 150);
    if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 10, P.y - 20, 34, '255,170,80', 1.0, 0.14);
  }
}
function sxLoseG(n, why) { if (P.sxAxe || P.sxLock || !(P.sxG > 0)) return; P.sxG = Math.max(0, P.sxG - n); P.sxLoss = 0.3; MV.sxLost = (MV.sxLost || 0) + n; }
function sxSetAxe(on) {
  if (!!P.sxAxe === on) return;
  P.sxAxe = on; P.sxLock = false;
  if (on) { P.sxG = 100; MV.sxMorphs = (MV.sxMorphs || 0) + 1; }
  if (typeof sheet === 'function') sheet(on ? SX_AXE_SHEET : 'wpn_gravegrinder').img;   // start decoding the other overlay
}
function sxReset() { P.sxAxe = false; P.sxLock = false; P.sxG = 0; P.sxRel = false; P.sxVentDue = false; P.sxIdleT = 0; P.sxTrack = null; }
function sxFoeNear(r = 90) { for (const t of targets()) { if (t.prop || t.alive === false) continue; if (Math.abs(t.x - P.x) < r && Math.abs(t.y - P.y) < 60) return true; } return false; }
// the move that just left the screen: a blade swing that came out and found nothing (foe nearby) costs 10
function sxSettle() {
  const k = P.sxTrack; P.sxTrack = null;
  if (!k || !k.swung || k.landed || !k.foe) return;
  sxLoseG(SX.whiff, 'whiff'); MV.sxWhiffs = (MV.sxWhiffs || 0) + 1;
}
const sxAxeOk = () => P.sxAxe && P.sxG > 0;
const sxBladeOk = () => !P.sxAxe;
// the dry rev: I below 100
function sxDryRev() {
  noise(0.18, 260, 1.5, 0.05, 'bandpass', 0.6); tone(70, 0.16, 0.05, 'sawtooth', 0.7);
  for (let i = 0; i < 5; i++) particles.push({ x: P.x + P.face * rand(4, 10), y: P.y - rand(14, 22), vx: P.face * rand(5, 25), vy: -rand(10, 30), life: rand(0.3, 0.5), kind: 'dust' });
  P.sxFlash = -0.4; MV.sxDry = (MV.sxDry || 0) + 1;
}
// the grind's chainsaw bite (hold K in axe mode): one strike every 80 ms in a box in front
function sxGrindBite() {
  const box = rect(P.x + P.face * 6, P.y - 30, P.x + P.face * 42, P.y - 8);
  const n = mvStrikeAt(box, SX.grindDmg * (P.mvMul || 1), 8, { A: ATK.sx_grind, kind: 'heavy' });
  noise(0.07, 700 + rand(-80, 80), 2, n ? 0.05 : 0.025, 'bandpass'); if (Math.random() < 0.5) tone(64 + rand(0, 8), 0.08, 0.03, 'sawtooth', 0.9);
  if (n) { mvSpark(P.x + P.face * 34, P.y - 20, 4, '255,200,120', 140); MV.sxGrindHits = (MV.sxGrindHits || 0) + n; }
  return n;
}
const SX_BLADE = { sxB: true, can: sxBladeOk };
const SX_AXEM = { sxA: true, can: sxAxeOk, armor: 0.25 };
mvRegister('saxe', {
  light: ['sx_1', 'sx_2', 'sx_3', 'sx_4'], K: 'sx_heavy', heavyTag: 'sx_heavy', down: 'sx_down',
  get up() { return sxIsAxe() ? 'sx_aup' : 'sx_up'; },
  get air() { return sxIsAxe() ? 'sx_aair' : 'sx_air'; },
  light0() { return P.sxAxe ? 'sx_a1' : 'sx_1'; },
  plunge() { return P.sxAxe ? { dmg: 1.8, poise: 90, stam: 20 } : { dmg: 1.3, poise: 45, stam: 16 }; },
  dodge() { return P.sxAxe ? { stam: 18, total: 520, inv: 0.22, dist: 34, move: 360, tags: ['sx_astep', 'roll'], kind: 'astep' } : MV_ROLL; },
  rollJ() { return P.sxAxe ? 'sx_a1' : 'sx_rollj'; },
  rollK() { return mvStart(P.sxAxe ? 'sx_arev' : 'sx_heavy'); },
  onK(ax) { return mvStart(P.sxAxe ? 'sx_arev' : 'sx_heavy'); },
  onJ(ax) {   // J J (pause) J: a press 110-450 ms after the Falling edge ended = the Ratchet cut (II)
    const c = P.mvChain;
    if (P.sxAxe || !P.ground || !c || c.id !== 'sx_2' || held.has('up') || !mvHas(2)) return false;
    const ms = (P.clk - c.t) * 1000;
    if (ms < 110 || ms > 450) return false;
    take('attack'); P.mvChain = null; if (ax) P.face = ax;
    return mvStart('sx_ratchet') || true;
  },
  onI(ax) {
    if (!P.ground) return false;
    take('parry'); if (ax) P.face = ax;
    if (!P.sxAxe) { if (P.sxLock && P.sxG >= 100) return mvStart('sx_morph') || true; sxDryRev(); return true; }
    if (mvHas(3) && P.sxG >= SX.relMin) return mvStart('sx_release', { mul: 1 + (P.sxG - SX.relMin) / 60, g: P.sxG }) || true;
    return mvStart('sx_unmorph') || true;
  },
  walkMul() { return P.sxAxe ? 0.75 : 1; },
  idleTag(want) { return P.sxAxe ? (want === 'run' ? 'sx_awalk' : 'sx_aidle') : null; },
  started(A) {
    sxSettle();
    const d = A.mv; P.sxIdleT = 0; P.sxGot = new Set(); P.sxLanded = 0; P.sxDrained = false;
    if (d.sxB && !d.noHit) P.sxTrack = { id: d.id, swung: false, landed: 0, foe: false };
  },
  tickAll(dt, cur) {
    const p = sxP(); if (!p) return;
    if (!cur) { if (p.sxAxe || p.sxG) sxReset(); return; }
    p.sxG = p.sxG || 0; p.sxFlash = (p.sxFlash || 0) > 0 ? Math.max(0, p.sxFlash - dt) : Math.min(0, (p.sxFlash || 0) + dt); p.sxLoss = Math.max(0, (p.sxLoss || 0) - dt);
    const A = ATK[p.state], d = A && A.mv;
    // the whiff tracker: did the blade swing on screen come out, land, with a foe about?
    if (p.sxTrack) {
      if (d && d.id === p.sxTrack.id) { if (p.mvHitK >= 0) { p.sxTrack.swung = true; if (!p.sxTrack.foe) p.sxTrack.foe = sxFoeNear(); } p.sxTrack.landed = p.sxLanded; }
      else sxSettle();
    }
    if (!p.sxAxe) {
      if (d && d.type === 'saxe' && !d.noHit) p.sxIdleT = 0; else p.sxIdleT = (p.sxIdleT || 0) + dt;
      if (!p.sxLock && p.sxIdleT > SX.bleedAfter && p.state !== 'sx_hone') p.sxG = Math.max(0, p.sxG - SX.bleed * dt);
    } else if (!p.sxRel) {
      p.sxG = Math.max(0, p.sxG - SX.drain * (mvHas(4) ? 0.7 : 1) * dt);
      if (p.sxG <= 0) p.sxVentDue = true;
    }
    if (p.sxRel && p.state !== 'sx_release') { p.sxRel = false; sxSetAxe(false); }   // a release cut short still folds the spent axe
    if (p.sxVentDue) {
      if (!p.sxAxe) p.sxVentDue = false;
      else if (p.ground && !A && !['roll', 'hurt', 'dead', 'gbreak'].includes(p.state)) { p.sxVentDue = false; mvStart('sx_vent'); }
    }
  },
  onHit(t, info, A, c) {
    if (!t || t.prop) return;
    const d = A.mv || {};
    P.sxLanded = (P.sxLanded || 0) + 1;
    if (d.sxGain !== undefined && !P.sxAxe) {
      const k = P.mvHitK; if (P.sxGot.has(k)) return; P.sxGot.add(k);
      const g = typeof d.sxGain === 'function' ? d.sxGain() : d.sxGain;
      sxGainG(g, d.id);
    }
    if (d.sxA && !P.sxDrained) { P.sxDrained = true; P.sxG = Math.max(0, P.sxG - SX.drainHit * (mvHas(4) ? 0.7 : 1)); if (P.sxG <= 0) P.sxVentDue = true; }
    if (d.sxA) mvSpark(info.x, info.y, 5, '255,190,110', 160);
  },
  render() {
    const p = P; if (!p) return;
    const ws = sheet('wpn_' + (SAVE.weapon || 'gravegrinder'));
    // the burning edge: locked full in blade mode the whole weapon glows ember, breathing; the axe runs hot
    if ((p.sxLock && !p.sxAxe) || p.sxAxe) {
      const a = p.sxAxe ? 0.18 + 0.06 * Math.sin(p.clk * 22) : 0.28 + 0.12 * Math.sin(p.clk * 6);
      if (ws.ok) drawGlow(() => { const o = g.globalCompositeOperation; g.globalCompositeOperation = 'lighter'; drawSprite(ws, p.anim.frame, p.x, p.y, p.face, { alpha: a, flash: 1, flashColor: p.sxAxe ? '#ff5a20' : '#ffa040' }); g.globalCompositeOperation = o; });
      addLight(p.x + p.face * 10, p.y - 20, p.sxAxe ? 26 : 22, p.sxAxe ? '255,110,50' : '255,160,70', p.sxAxe ? 0.35 : 0.45 + 0.1 * Math.sin(p.clk * 6));
      if (Math.random() < (p.sxAxe ? 0.25 : 0.35)) particles.push({ x: p.x + p.face * rand(6, 20), y: p.y - rand(14, 30), vx: rand(-6, 6), vy: -rand(15, 40), life: rand(0.3, 0.6), kind: p.sxAxe ? 'fire' : 'ember' });
    }
    if (p.state === 'sx_hone') {   // sparks off the grinding point
      addLight(p.x + p.face * 26, p.y - 2, 16, '255,180,90', 0.5 + 0.2 * Math.random());
      for (let i = 0; i < 2; i++) particles.push({ x: p.x + p.face * 26, y: p.y - 1, vx: -p.face * rand(20, 120), vy: -rand(30, 110), g: 420, life: rand(0.2, 0.4), kind: 'spark' });
    }
    if (p.state === 'sx_grind') {
      addLight(p.x + p.face * 34, p.y - 20, 20, '255,150,70', 0.5 + 0.2 * Math.random());
      if (Math.random() < 0.6) particles.push({ x: p.x + p.face * rand(30, 38), y: p.y - rand(16, 24), vx: p.face * rand(-40, 60), vy: -rand(20, 90), g: 380, life: rand(0.15, 0.35), kind: 'spark' });
    }
    if (p.state === 'sx_vent' && Math.random() < 0.8) particles.push({ x: p.x + p.face * rand(0, 12), y: p.y - rand(14, 26), vx: rand(-15, 15), vy: -rand(25, 55), life: rand(0.5, 0.9), kind: 'dust' });
  },
  hud(x) {
    // the Switch Gauge: a phial-shaped bar. Blade: amber filling; locked: white-gold, breathing; axe: red, draining
    // (a tick at the Full Release line from Mastery III). A tiny glyph left of it shows the form.
    const p = P, f = clamp((p.sxG || 0) / 100, 0, 1), y = 21, w = 38;
    const col = p.sxAxe ? (p.sxG < SX.relMin && mvHas(3) ? '#b03a22' : '#e0582a') : p.sxLock ? `rgb(255,${Math.round(214 + 30 * Math.sin(p.clk * 6))},150)` : '#d08a3a';
    mvHudBar(x + 6, y, w, 2.6, f, col);
    if ((p.sxFlash || 0) > 0) { vctx.fillStyle = `rgba(255,240,200,${p.sxFlash * 2})`; vctx.fillRect(ox + (x + 6) * scale, oy + y * scale, f * w * scale, 2.6 * scale); }
    if ((p.sxLoss || 0) > 0) { vctx.strokeStyle = `rgba(230,60,50,${p.sxLoss * 2.5})`; vctx.lineWidth = scale; vctx.strokeRect(ox + (x + 5) * scale, oy + (y - 1) * scale, (w + 2) * scale, 4.6 * scale); }
    if (p.sxAxe && mvHas(3)) { vctx.fillStyle = 'rgba(255,230,190,0.8)'; vctx.fillRect(ox + (x + 6 + w * SX.relMin / 100) * scale, oy + (y - 0.8) * scale, 0.6 * scale, 4.2 * scale); }
    // the form glyph
    vctx.fillStyle = p.sxAxe ? '#e0582a' : '#c8ccd8';
    if (p.sxAxe) { vctx.fillRect(ox + (x + 1.6) * scale, oy + (y - 1.2) * scale, 0.7 * scale, 5 * scale); vctx.beginPath(); vctx.arc(ox + (x + 2.3) * scale, oy + (y - 0.4) * scale, 2 * scale, -Math.PI / 2, Math.PI / 2); vctx.fill(); }
    else { vctx.fillRect(ox + (x + 2) * scale, oy + (y - 2) * scale, 0.9 * scale, 5.6 * scale); vctx.fillRect(ox + (x + 1) * scale, oy + (y + 1.6) * scale, 2.9 * scale, 0.7 * scale); }
    if (p.sxLock && !p.sxAxe && Math.sin(p.clk * 6) > 0) { vctx.fillStyle = 'rgba(255,230,170,0.9)'; vctx.font = `${Math.round(4 * scale)}px ${FONT}`; vctx.textAlign = 'left'; vctx.fillText('I', ox + (x + 8 + w) * scale, oy + (y + 2.6) * scale); }
  },
  unlocks: [
    { rank: 2, id: 'sx_ratchet', name: 'Ratchet cut', input: 'J J (pause) J', desc: 'The blade is sawn through the foe: three bites (0.6 each), +3 gauge a tooth.' },
    { rank: 2, id: 'sx_rip', name: 'Ripping heave', input: 'Axe: K → K', desc: 'Out of the rev thrust, the head torn up through the foe (2.6). Launches.' },
    { rank: 3, id: 'sx_release', name: 'Full Release', input: 'Axe: I (gauge ≥ 40)', desc: 'Lunge, bite, eight grinding bites and a burst: 3.0-6.0 by the gauge. Empties it.' },
    { rank: 4, id: 'sx_overdrive', name: 'Overdrive', input: '–', desc: 'The axe drains 30% slower (4.2/s, 2.8 a landed move).' },
    { rank: 5, id: 'sx_halo', name: 'Grinding halo', input: '–', desc: 'Full Release ends in a ring burst (0.8) and refunds 30 gauge.' },
  ],
  combos: [
    { rank: 1, name: 'Rising · Falling edge · Double slash · Edge rush', input: 'J J J J', desc: 'The gauge builder: +4 a hit, +7 on the beat, the rush +10 (13).' },
    { rank: 1, name: 'On the beat', input: 'press late', desc: 'Press in the last 150 ms of a swing: +7 gauge instead of +4.' },
    { rank: 1, name: 'Hook heave', input: 'J K', desc: 'Hook under the guard and heave up over the shoulder. Lifts light foes.' },
    { rank: 1, name: 'Phial thrust', input: 'K', desc: 'Drawn back level, then rammed out; the phial coughs fire.' },
    { rank: 1, name: 'Ratchet twist', input: 'K K', desc: 'Re-drive the buried blade and wrench it: +12 gauge if both land.' },
    { rank: 1, name: 'Hone', input: 'hold K', desc: 'Grind the edge on the floor: +10 gauge/s, rooted. A hit costs 25.' },
    { rank: 1, name: 'Skyward edge', input: '↑J', desc: 'One straight arc up over the helm.' },
    { rank: 1, name: 'Lunging edge', input: 'L → J', desc: 'A long low cut out of the roll. J: Falling edge.' },
    { rank: 1, name: 'Air edge  /  Pogo', input: 'air J  /  air ↓J', desc: 'A cut in the hang; the weapon driven under the feet.' },
    { rank: 1, name: 'Morph slash', input: 'I (gauge full)', desc: 'Armoured: the blade unfolds into the axe on the hit (2.0). Axe mode.' },
    { rank: 1, name: 'Axe: overhead · wild swing · grinder sweep', input: 'J J J', desc: 'The damage: 2.9, 3.2, then five chain bites (0.9 each).' },
    { rank: 1, name: 'Axe: rev thrust', input: 'K', desc: 'The head held out with the chain screaming: four bites.' },
    { rank: 1, name: 'Axe: chainsaw grind', input: 'hold K', desc: 'A bite every 80 ms (0.28); walk at 30%. Drains 15 more a second.' },
    { rank: 1, name: 'Axe: rising grinder', input: '↑J', desc: 'The head dragged up off the floor and over.' },
    { rank: 1, name: 'Axe: falling cleave  /  plunge', input: 'air J  /  air K', desc: 'A chop as you drop (1.4); the axe plunge (1.8).' },
    { rank: 1, name: 'Axe: heavy sidestep', input: 'L', desc: 'A short, slow shuffle under the weight. L → J: the overhead.' },
    { rank: 1, name: 'Morph back', input: 'Axe: I (gauge < 40)', desc: 'The blade jack-knifes out of the haft as a rising cut (1.4).' },
    { rank: 1, name: 'Vented', input: 'gauge runs dry', desc: 'The axe folds shut in a cloud of steam: 0.6 s you cannot act.' },
    { rank: 2, name: 'Ratchet cut', input: 'J J (pause) J', desc: 'Wait a beat after the 2nd cut: three sawing bites, +3 each.' },
    { rank: 2, name: 'Ripping heave', input: 'Axe: K K', desc: 'The head torn up through the foe and over (2.6). Launches.' },
    { rank: 3, name: 'Full Release', input: 'Axe: I (≥ 40)', desc: 'Eight bites and a burst, 3.0-6.0 by the gauge. Folds back.' },
    { rank: 5, name: 'Grinding halo', input: 'Full Release', desc: 'Ends in a ring burst and refunds 30 gauge.' },
  ],
}, {
  // ---------------------------------------------------------------- blade mode (the gauge builder)
  sx_1: { ...SX_BLADE, tags: ['sx_1', 'gs_1'], dmg: 0.9, poise: 10, stam: 10, wind: 140, total: 360, step: 0, sxGain: () => (P.mvO.perfect ? SX.beat : SX.hit), fx: 'slash_up', next: { J: 'sx_2', K: 'sx_hook', I: '@I' } },
  sx_2: { ...SX_BLADE, tags: ['sx_2', 'gs_2'], dmg: 0.95, poise: 10, stam: 10, wind: 140, total: 360, step: 1, sxGain: () => (P.mvO.perfect ? SX.beat : SX.hit), fx: 'slash', next: { J: 'sx_3', I: '@I' } },
  sx_3: { ...SX_BLADE, tags: ['sx_3', 'gs_3'], hits: [0.55, 0.55], gap: 120, poise: 16, stam: 12, wind: 160, total: 420, step: 2, sxGain: () => (P.mvO.perfect ? SX.beat : SX.hit), next: { J: 'sx_4', I: '@I' } },
  sx_4: { ...SX_BLADE, tags: ['sx_4', 'gs_3'], dmg: 1.3, poise: 30, stam: 14, wind: 220, total: 560, step: 3, fin: true, lunge: 24, sxGain: () => (P.mvO.perfect ? SX.rushBeat : SX.rush), next: { I: '@I' },
    on: { hit(t) { if (!t.prop) mvSpark(P.x + P.face * 30, P.y - 18, 5, '255,210,150', 140); } } },
  sx_ratchet: { ...SX_BLADE, tags: ['sx_ratchet', 'sx_heavy'], rank: 2, hits: [0.6, 0.6, 0.6], gap: 120, poise: 24, stam: 14, wind: 160, total: 600, step: 2, reach: 40, lunge: 10, sxGain: SX.tooth, next: { J: 'sx_4', I: '@I' },
    on: { hitStart(k) { noise(0.06, 1400, 3, 0.04, 'bandpass'); } } },
  sx_heavy: { ...SX_BLADE, tags: ['sx_heavy', 'gs_heavy'], kind: 'heavy', dmg: 1.3, poise: 28, stam: 16, wind: 240, total: 600, lunge: 16, reach: 42, sxGain: () => (P.mvO.perfect ? SX.beat : SX.hit), next: { K: 'sx_twist', I: '@I' },
    on: {
      update() {   // hold K: the thrust's draw-back turns into the Hone instead
        if (P.mvT >= 190 && P.mvT < 240 && P.ground && !P.sxLock && held.has('heavy') && P.sxHoldK) { mvStart('sx_hone'); return 'stop'; }
      },
      swing() { tone(160, 0.12, 0.05, 'sawtooth', 0.6); },
    } },
  sx_twist: { ...SX_BLADE, tags: ['sx_twist', 'sx_heavy'], kind: 'heavy', hits: [0.7, 0.7], gap: 150, poise: 30, stam: 16, wind: 200, total: 640, fin: true, reach: 40, sxGain: 0, next: { I: '@I' },
    on: { end() { if (P.sxGot && P.sxGot.size >= 2) sxGainG(SX.twist, 'twist'); }, hitStart() { noise(0.08, 900, 2, 0.05, 'bandpass'); } } },
  sx_hook: { ...SX_BLADE, tags: ['sx_hook', 'gs_up'], kind: 'heavy', dmg: 1.2, poise: 34, stam: 14, wind: 220, total: 620, launch: 220, lunge: 12, sxGain: () => (P.mvO.perfect ? SX.beat : SX.hit), next: { J: 'sx_2', I: '@I' } },
  sx_hone: { tags: ['sx_hone', 'gs_charge_hold'], kind: 'heavy', loop: true, noHit: true, noSkillCharge: true,   // v15 balance: Charged Arts never speeds the Hone (the gauge stays hard to earn)
    dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, can: sxBladeOk,
    on: {
      start() { P.sxHoneT = 0; noise(0.25, 1800, 2, 0.04, 'bandpass'); },
      update(dt, A, ax) {
        P.vx = 0; P.sxHoneT += dt;
        sxGainG(SX.hone * dt, 'hone'); MV.sxHoned = (MV.sxHoned || 0) + SX.hone * dt;
        if ((P.sxHoneS = (P.sxHoneS || 0) - dt) <= 0) { P.sxHoneS = 0.09; noise(0.08, 2200 + rand(-300, 300), 4, 0.03, 'bandpass'); }
        if (peek('roll') && P.st > 0) { take('roll'); mvDodgeStart(ax); return 'stop'; }
        if (peek('attack') && P.st > 0) { take('attack'); mvStart('sx_1', { step: 0 }); return 'stop'; }
        if (peek('parry') && P.sxLock) { take('parry'); mvStart('sx_morph'); return 'stop'; }
        if (!held.has('heavy') || P.sxLock) { setP('idle', 'idle', true); return 'stop'; }
      },
    } },
  sx_up: { ...SX_BLADE, tags: ['sx_up', 'gs_up'], up: true, dmg: 1.0, poise: 14, stam: 12, wind: 160, total: 400, reach: 30, sxGain: () => (P.mvO.perfect ? SX.beat : SX.hit), fx: 'slash_up', next: { I: '@I' } },
  sx_rollj: { ...SX_BLADE, tags: ['sx_rollj', 'attack1'], dmg: 1.1, poise: 14, stam: 12, wind: 140, total: 400, lunge: 28, lungeLead: 140, sxGain: () => (P.mvO.perfect ? SX.beat : SX.hit), next: { J: 'sx_2', I: '@I' } },
  sx_air: { ...SX_BLADE, tags: ['sx_air', 'gs_air'], air: true, dmg: 1.0, poise: 12, stam: 12, wind: 150, total: 330, sxGain: SX.hit },
  sx_down: { tags: ['sx_down', 'gs_down'], down: true, dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300 },
  sx_morph: { tags: ['sx_morph', 'gs_charged'], kind: 'heavy', dmg: 2.0, poise: 60, stam: 0, wind: 300, total: 700, fin: true, slam: true, armor: 0.35, lunge: 12, commit: true,
    can: () => !P.sxAxe && P.sxLock,
    on: {
      start() { P.sxClank = false; tone(240, 0.1, 0.05, 'square', 0.8); },
      update() { if (!P.sxClank && P.mvT >= 250) { P.sxClank = true; tone(150, 0.14, 0.09, 'square', 0.5); noise(0.1, 500, 1.5, 0.08, 'bandpass'); mvSpark(P.x - P.face * 6, P.y - 34, 6, '255,220,160', 120); } },
      hitStart(k) { if (k === 0) { sxSetAxe(true); mvGain('morph'); flashScreen = Math.max(flashScreen, 0.05); tone(55, 0.5, 0.08, 'sawtooth', 1.4); } },
    },
    next: { J: 'sx_a2', K: 'sx_arev' } },
  sx_vent: { tags: ['sx_vent', 'hurt'], noHit: true, dmg: 0, poise: 0, stam: 0, wind: SX.ventMs, total: SX.ventMs, commit: true,
    on: { start() { sxSetAxe(false); P.sxG = 0; MV.sxVents = (MV.sxVents || 0) + 1; noise(0.6, 3000, 0.7, 0.07, 'highpass', 0.4); tone(90, 0.3, 0.05, 'sawtooth', 0.5); toast && toast('Vented', 0.8); }, update() { P.vx *= 0.85; } } },
  // ---------------------------------------------------------------- axe mode (the damage, while the gauge lasts)
  sx_a1: { ...SX_AXEM, tags: ['sx_a1', 'gs_1'], kind: 'heavy', dmg: 2.9, poise: 45, stam: 16, wind: 420, total: 920, step: 0, slam: true, lunge: 14, next: { J: 'sx_a2', K: 'sx_arev', I: '@I' } },
  sx_a2: { ...SX_AXEM, tags: ['sx_a2', 'gs_2'], kind: 'heavy', dmg: 3.2, poise: 50, stam: 18, wind: 400, total: 900, step: 1, lunge: 16, next: { J: 'sx_a3', I: '@I' } },
  sx_a3: { ...SX_AXEM, tags: ['sx_a3', 'gs_3'], kind: 'heavy', hits: [0.9, 0.9, 0.9, 0.9, 0.9], gap: 65, poise: 70, stam: 20, wind: 360, total: 1100, step: 2, fin: true, lunge: 10, reach: 44, next: { I: '@I' },
    on: { hitStart() { noise(0.07, 650, 2, 0.05, 'bandpass'); } } },
  sx_arev: { ...SX_AXEM, tags: ['sx_arev', 'gs_heavy'], kind: 'heavy', hits: [0.6, 0.6, 0.6, 0.6], gap: 60, poise: 50, stam: 16, wind: 300, total: 900, reach: 44, next: { K: 'sx_rip', I: '@I' },
    on: {
      update() { if (P.mvT >= 200 && P.mvT < 300 && held.has('heavy') && P.sxHoldK) { mvStart('sx_grind'); return 'stop'; } },
      hitStart() { noise(0.06, 700, 2, 0.05, 'bandpass'); },
    } },
  sx_grind: { tags: ['sx_grind', 'gs_charge_hold'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, armor: 0.25, can: sxAxeOk,
    on: {
      start() { P.sxGrindT = 0; MV.sxGrinds = (MV.sxGrinds || 0) + 1; },
      update(dt, A, ax, grav) {
        P.vx = approach(P.vx, ax * MAXV * 0.3, 600 * dt); grav();
        const tag = Math.abs(P.vx) > 8 ? 'sx_grindw' : 'sx_grind'; if (pHas(tag) && P.anim.tag !== tag) P.anim.set(tag, true);
        P.sxG = Math.max(0, P.sxG - SX.grind * (mvHas(4) ? 0.7 : 1) * dt);
        P.sxGrindT += dt * 1000;
        while (P.sxGrindT >= SX.grindTick) { P.sxGrindT -= SX.grindTick; sxGrindBite(); }
        if (peek('roll') && P.st > 0) { take('roll'); mvDodgeStart(ax); return 'stop'; }
        if (P.sxG <= 0) { P.sxVentDue = false; mvStart('sx_vent'); return 'stop'; }
        if (!held.has('heavy')) { setP('idle', 'sx_aidle', true); return 'stop'; }
      },
    } },
  sx_rip: { ...SX_AXEM, tags: ['sx_rip', 'gs_up'], rank: 2, kind: 'heavy', dmg: 2.6, poise: 80, stam: 20, wind: 420, total: 1000, fin: true, launch: 280, lunge: 12, next: { I: '@I' } },
  sx_release: { tags: ['sx_release', 'gs_heavy'], rank: 3, kind: 'heavy', hits: [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 1.0], gap: 60, poise: 120, stam: 0, wind: 500, total: 1500, fin: true, commit: true, armor: 0.35,
    lunge: 18, lungeLead: 200, back: 8, reach: 46, can: () => P.sxAxe && P.sxG >= SX.relMin,
    on: {
      start(A, o) { P.sxRel = true; P.sxG = 0; P.sxRelG = o.g || 0; MV.sxReleases = (MV.sxReleases || 0) + 1; tone(110, 0.5, 0.06, 'sawtooth', 1.8); },
      hitStart(k) {
        if (k < 8) { noise(0.06, 600 + k * 40, 2, 0.05, 'bandpass'); return; }
        // the burst: the phial empties through the foe, and the spent grinder folds back into the blade
        shake = Math.max(shake, 7); flashScreen = Math.max(flashScreen, 0.12); sfx.boom && sfx.boom(); mvGain('release');
        mvSpark(P.x + P.face * 36, P.y - 20, 14, '255,200,120', 200);
        if (typeof feelFlash === 'function') feelFlash(P.x + P.face * 34, P.y - 20, 48, '255,150,60', 1.2, 0.18);
        P.sxRel = false; sxSetAxe(false); P.sxG = 0;
        if (mvHas(5)) {   // Grinding halo: a ring burst and 30 gauge back
          mvShockwave({ r: 46, h: 34, dmg: 0.8 * (P.mvMul || 1), poise: 40, fire: true, pk: 'fire', shake: 6 });
          P.sxG = 30; P.sxFlash = 0.4;
        }
      },
    } },
  sx_unmorph: { tags: ['sx_unmorph', 'gs_up'], kind: 'heavy', dmg: 1.4, poise: 40, stam: 0, wind: 260, total: 620, lunge: 10, can: () => P.sxAxe,
    on: { start() { tone(200, 0.1, 0.05, 'square', 1.3); }, hitStart(k) { if (k === 0) { sxSetAxe(false); P.sxG = 0; tone(300, 0.12, 0.06, 'square', 0.7); } } },
    next: { J: 'sx_2', I: '@I' } },
  sx_aair: { ...SX_AXEM, tags: ['sx_aair', 'gs_air'], air: true, kind: 'heavy', dmg: 1.4, poise: 40, stam: 16, wind: 200, total: 520 },
  sx_aup: { ...SX_AXEM, tags: ['sx_aup', 'gs_up'], up: true, kind: 'heavy', dmg: 1.5, poise: 40, stam: 16, wind: 300, total: 760, reach: 34, next: { I: '@I' } },
});
// K held from the press: the thrust / rev thrust only turn into the Hone / grind if K went down for THIS move (not a
// K still held from before)
HOOKS.update.push(() => {
  const p = sxP(); if (!p || !mvOn('saxe')) return;
  const A = ATK[p.state];
  if (A && A.mv && (A.mv.id === 'sx_heavy' || A.mv.id === 'sx_arev')) { if (p.mvT < 40 && p.sxHoldId !== p.mvO) { p.sxHoldId = p.mvO; p.sxHoldK = held.has('heavy'); } else if (!held.has('heavy')) p.sxHoldK = false; }
  else { p.sxHoldK = false; p.sxHoldId = null; }
});
HOOKS.playerHurt.push(dmg => { const p = sxP(); if (p && mvOn('saxe') && dmg > 0) sxLoseG(SX.hurt, 'hurt'); });
HOOKS.death.push(() => { const p = sxP(); if (p && p.sxAxe !== undefined) sxReset(); });
HOOKS.rest.push(() => { const p = sxP(); if (p && p.sxAxe !== undefined) sxReset(); });

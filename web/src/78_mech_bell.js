// ------------------------------------------------------------------ v15: Warbell (`bell`, weapon Dirgebell) -- WEAPON_REVAMP.md C5
// The bell moveset agent's table (docs/v15/bell.md). JS globals use bel / BEL_ (wb / WB_ belong to 60_wbal); the move ids and
// animation tags are wb_* (art/player_v15_bell.py; nothing else in the game uses that prefix).
// ================================================================== Warbell: the tolling bell
// NOTES: a blow that lands rings a note into a 3-note staff (HUD, oldest note falls off): J blows ring Ash (white), K blows ring
// Ember (crimson), the up J rings Gold. Each note is its own bell pitch (Ember G3, Ash D4, Gold Bb4). A whiff rings nothing.
// TOLLS: a run of notes in the staff, in order: Ash Ash = Swiftness (stamina regen +25%), Ash Ember = Iron hymn (finishers and
// heavies don't flinch from hits under 20% max HP), Ember Ember = Fury (+8% damage), Gold Gold = Echo (the next 3 hits ring
// again for 30%), Ash Gold Ember = Mending (Mastery II: heal 10% max HP over 10 s, once per 60 s). A 3-note staff can hold two
// tolls at once (Ash Ash Ember = Swiftness + Iron hymn).
// I = PERFORM (needs a note): a ringing blow on both sides (1.2) that plays every toll the staff holds, empties it and grants
// their buffs for 30 s. III: I again = Encore (1.4, refreshes the buffs). IV: the ring sends an echo wave (+0.6 out to 64 px).
// V: Grand toll -- a Perform with a full staff stuns small foes and adds 60 stance damage to bosses.
// Bell hits are blunt (x1.3 stance damage). Hold K = the wind-up toll (armoured while winding against hits < 25% max HP).
const BEL_NOTE = {
  A: { name: 'Ash', f: 293.66, col: '#ece6da', rgb: '236,230,218', y: 22 },
  E: { name: 'Ember', f: 196.0, col: '#e0383e', rgb: '224,56,62', y: 24.6 },
  G: { name: 'Gold', f: 466.16, col: '#f2c463', rgb: '242,196,99', y: 19.4 },
};
const BEL_TOLLS = [
  { id: 'swift', name: 'Swiftness', seq: 'AA', rgb: '236,230,218', desc: 'stamina regen +25%' },
  { id: 'iron', name: 'Iron hymn', seq: 'AE', rgb: '150,172,206', desc: 'finishers don\'t flinch' },
  { id: 'fury', name: 'Fury', seq: 'EE', rgb: '224,56,62', desc: '+8% damage' },
  { id: 'mend', name: 'Mending', seq: 'AGE', rank: 2, rgb: '156,214,150', desc: 'heal 10% over 10 s' },
  { id: 'echo', name: 'Echo', seq: 'GG', rgb: '242,196,99', desc: 'next 3 hits ring again' },
];
const BEL_SECS = 30, BEL_MEND_CD = 60, BEL_MEND_SECS = 10, BEL_ECHO_N = 3;
const BEL_TAP = 170, BEL_WOUND = 650, BEL_OVER = 2200;   // hold K: under 170 ms a tap (forward slam); from 650 ms the toll is wound
const BEL_PAUSE = [110, 450];                              // J J (pause) J: ms after the right swing ended
const BEL = { fx: [], rings: [] };

// ---- sound: a struck bell is a stack of inharmonic partials (hum, prime, minor-third tierce, quint, nominal)
function belBell(f, vol = 1, dur = 1.1, delay = 0) {
  const T = (fr, d, v, ty = 'sine') => (typeof wsTone === 'function' ? wsTone : tone)(fr, d, v, ty, 0.998, delay);
  T(f * 0.5, dur * 1.25, 0.026 * vol);
  T(f, dur, 0.05 * vol);
  T(f * 1.19, dur * 0.7, 0.022 * vol);
  T(f * 1.5, dur * 0.5, 0.014 * vol);
  T(f * 2.0, dur * 0.6, 0.02 * vol);
  T(f * 2.76, 0.09, 0.03 * vol, 'triangle');   // the strike
}
function belToll(p = 1, v = 1) {   // the great toll of a Perform: a low bell under the arpeggio
  belBell(98 * p, 1.5 * v, 2.2);
  belBell(147 * p, 0.8 * v, 1.6, 0.02);
  if (typeof wsNoise === 'function') wsNoise(0.3, 900, 0.8, 0.18 * v, 'bandpass', 0.4);
}

// ---- notes and tolls
function belNotes() { return P.belNotes || (P.belNotes = []); }
function belTollsOf(notes) { const s = notes.join(''); return BEL_TOLLS.filter(t => (!t.rank || mvHas(t.rank)) && s.includes(t.seq)); }
function belBuffs() { return P.belBuff || (P.belBuff = {}); }
function belFx(o) { BEL.fx.push(o); if (BEL.fx.length > 40) BEL.fx.shift(); }
function belRing(x, y, r1, rgb, life = 0.4, o = {}) { BEL.rings.push({ x, y, r0: o.r0 || 2, r1, rgb, life, max: life, sq: o.sq || 0.5, w: o.w || 1 }); if (BEL.rings.length > 24) BEL.rings.shift(); }
// a blow landed: ring its note (once per move, or once per hit for noteEach moves)
function belAddNote(n, x, y) {
  const N = BEL_NOTE[n]; if (!N) return;
  const s = belNotes(); s.push(n); if (s.length > 3) s.shift();
  P.belPop = P.clk; P.belPopN = s.length - 1;
  belBell(N.f, 1, 1.0);
  belRing(x, y, 12, N.rgb, 0.3, { sq: 0.8 });
  belFx({ kind: 'note', x: x + rand(-3, 3), y: y - 6, vy: -22, life: 0.8, max: 0.8, rgb: N.rgb });
  if (typeof feelFlash === 'function') feelFlash(x, y, 20, N.rgb, 0.9, 0.1);
  mvSpark(x, y, 4, N.rgb, 110);
}
// I: Perform -- every toll in the staff (the staff empties); V: a full staff is a Grand toll
function belPerformStart() {
  const notes = belNotes().slice(); P.belNotes = [];
  P.belPlay = notes; P.belGrand = notes.length === 3 && mvHas(5);
  notes.forEach((n, i) => belBell(BEL_NOTE[n].f, 0.7, 0.5, i * 0.07));   // the staff played back as the bell swings up
}
function belPerformRing(encore) {
  const cx = P.x + P.face * 6, cy = P.y - 16;
  belToll(encore ? 1.19 : 1, P.belGrand ? 1.25 : 1);
  shake = Math.max(shake, P.belGrand ? 6 : 4); hitstop = Math.max(hitstop, 0.04);
  const tolls = encore ? [] : belTollsOf(P.belPlay || []);
  const col = tolls.length ? tolls[tolls.length - 1].rgb : '242,214,150';
  belRing(cx, cy, 44, '255,236,190', 0.42, { sq: 0.55, w: 2 });
  belRing(cx, cy, 30, col, 0.32, { sq: 0.55 });
  if (P.belGrand) belRing(cx, cy, 58, '255,214,120', 0.55, { sq: 0.5, w: 2 });
  addLight(cx, cy, 70, '255,220,160', 1.4);
  if (typeof feelFlash === 'function') feelFlash(cx, cy, 52, '255,226,170', 1.2, 0.14);
  for (let i = 0; i < 14; i++) particles.push({ x: P.x + rand(-30, 30), y: P.y - 2, vx: rand(-70, 70), vy: -rand(20, 80), g: 320, life: 0.5, kind: 'dust' });
  const B = belBuffs();
  if (encore) {   // III: re-ring every buff still sounding back to 30 s
    for (const k of Object.keys(B)) if (B[k] > 0 && k !== 'mend') B[k] = BEL_SECS;
    if (B.echo > 0) P.belEchoN = BEL_ECHO_N;
  } else {
    for (const t of tolls) {
      if (t.id === 'mend') {
        if ((P.belMendCd || 0) > 0) { popups.push({ x: P.x, y: P.y - 46, v: 'Mending: not yet', color: '#8a9a86', life: 0.9 }); continue; }
        B.mend = BEL_MEND_SECS; P.belMendCd = BEL_MEND_CD;
      } else B[t.id] = BEL_SECS;
      if (t.id === 'echo') P.belEchoN = BEL_ECHO_N;
    }
    tolls.forEach((t, i) => { tone(880 + i * 220, 0.18, 0.025, 'sine', 1.0, 0.12 + i * 0.08); popups.push({ x: P.x, y: P.y - 44 - i * 8, v: t.name, color: `rgb(${t.rgb})`, life: 1.1 }); });
  }
  if (mvHas(4)) mvLater(0.1, () => {   // IV: the echo wave rolls out both ways to 64 px
    if (!P) return;
    belRing(P.x, P.y - 14, 64, '255,226,170', 0.36, { r0: 24, sq: 0.45 });
    mvStrikeAt(rect(P.x - 64, P.y - 40, P.x + 64, P.y + 2), 0.6, 20, { A: ATK.wb_perform, kind: 'heavy' });
  });
}

mvRegister('bell', {
  light: ['wb_1', 'wb_2', 'wb_3'], K: 'wb_slam', heavyTag: 'wb_slam', up: 'wb_up', air: 'wb_air', down: 'wb_down',
  plunge: { dmg: 1.8, poise: 90, stam: 20, shock: { r: 44, dmg: 0.4, poise: 30 } },
  dodge: { stam: 18, total: 480, inv: 0.26, dist: 66, tags: ['roll'], kAt: 260 },
  rollJ: 'wb_rollj',
  rollK() { return mvStart('wb_rollk'); },
  onJ(ax) {   // J J (pause) J: a press 110-450 ms after the right swing ended = the chime spin (II)
    const c = P.mvChain;
    if (!P.ground || !c || c.id !== 'wb_2' || held.has('up') || !mvHas(2)) return false;
    const ms = (P.clk - c.t) * 1000;
    if (ms < BEL_PAUSE[0] || ms > BEL_PAUSE[1]) return false;
    take('attack'); P.mvChain = null; if (ax) P.face = ax;
    return mvStart('wb_chime') || true;
  },
  onK(ax) { return P.ground ? mvStart('wb_kwind') : false; },
  onAirK(ax) {
    if (P.state === 'wall') return false;
    take('heavy'); if (ax) P.face = ax;
    mvStart('wb_plunge'); return true;
  },
  onI(ax) {
    if (!P.ground) return false;
    take('parry');
    if (!belNotes().length || P.st <= 0) { sfx.deny(); P.belDeny = P.clk; return true; }   // nothing in the staff: a dull clank
    if (ax) P.face = ax;
    return mvStart('wb_perform') || true;
  },
  poiseMod(t, poise) { return t && !t.prop ? poise * 1.3 : poise; },   // blunt: x1.3 stance damage
  hitMod(c) { if ((belBuffs().fury || 0) > 0) c.mul *= 1.08; },
  regenMul() { return (belBuffs().swift || 0) > 0 ? 1.25 : 1; },
  started(A) { hvStarted(); P.belRungK = -1; },
  tick() { hvTick(); },
  onHit(t, info, A, c) {
    if (!t || t.prop) return;
    const d = A && A.mv; if (!d) return;
    const k = c ? c.k : 0;
    if (d.note && (P.belRungK < 0 || (d.noteEach && k > P.belRungK))) { P.belRungK = k; belAddNote(d.noteEach && d.notes ? d.notes[k] || d.note : d.note, info.x, info.y); }
    // Echo: the next hits ring again for 30% a beat later (not the Perform's own ring)
    if (P.belEchoN > 0 && (belBuffs().echo || 0) > 0 && !d.perform && c) {
      P.belEchoN--; if (P.belEchoN <= 0) belBuffs().echo = 0;
      const mul = 0.3 * c.mul, at = { x: info.x, y: info.y };
      mvLater(0.16, () => {
        if (!P || t.alive === false) return;
        const hb = hbOf(t); if (!hb) return;
        mvStrikeAt(rect(hb.x0, hb.y0, hb.x1, hb.y1), mul, 6, { only: t, A });
        belBell(BEL_NOTE.G.f * 2, 0.5, 0.5); belRing(at.x, at.y, 16, BEL_NOTE.G.rgb, 0.3, { sq: 0.8 });
      });
    }
    // V: Grand toll -- small foes are stunned by a full-staff Perform
    if (d.perform && P.belGrand && !t.boss && t.breakStance && t.alive !== false && t.state !== 'stagger') t.breakStance();
  },
  hurt(c) {
    if (c.negate) return;
    const A = ATK[P.state], d = A && A.mv;
    // Iron hymn: finishers and heavies hold through hits under 20% max HP
    if (d && (belBuffs().iron || 0) > 0 && (d.fin || A.kind === 'heavy') && c.dmg < D.maxHp * 0.2) c.armor = true;
    // winding the toll: armoured against hits under 25% max HP
    if (P.state === 'wb_kwind' && c.dmg < D.maxHp * 0.25) c.armor = true;
  },
  tickAll(dt, cur) {
    if (!P) return;
    if (!cur) { if (P.belNotes && P.belNotes.length) P.belNotes = []; if (P.belBuff) P.belBuff = {}; BEL.fx.length = 0; BEL.rings.length = 0; return; }
    const B = belBuffs();
    for (const k of Object.keys(B)) if (B[k] > 0) B[k] = Math.max(0, B[k] - dt);
    if (B.mend > 0 && P.hp > 0) P.hp = Math.min(D.maxHp, P.hp + D.maxHp * 0.1 / BEL_MEND_SECS * dt);
    if (P.belMendCd > 0) P.belMendCd = Math.max(0, P.belMendCd - dt);
    if (!(B.echo > 0)) P.belEchoN = 0;
    for (const f of BEL.fx) { f.life -= dt; f.y += (f.vy || 0) * dt; }
    if (BEL.fx.length) BEL.fx = BEL.fx.filter(f => f.life > 0);
    for (const r of BEL.rings) r.life -= dt;
    if (BEL.rings.length) BEL.rings = BEL.rings.filter(r => r.life > 0);
  },
  interrupted() { P.belWound = false; },
  landed(pre) { if (pre === 'wb_plunge' && P.state === 'wb_plunge') mvStart('wb_pland'); },
  render() {
    const B = belBuffs();
    // the wind-up: the bell hums ember-red, brighter once the toll is wound
    if (P.state === 'wb_kwind') {
      const k = clamp((P.belKMs || 0) / BEL_WOUND, 0, 1), bx = P.x - P.face * 10, by = P.y - 30;
      addLight(bx, by, 14 + k * 16, P.belWound ? '255,120,90' : '224,56,62', 0.3 + k * 0.5);
      if (Math.random() < 0.15 + k * 0.4) particles.push({ x: bx + rand(-5, 5), y: by + rand(-4, 4), vx: 0, vy: -rand(15, 40), life: 0.4, kind: 'ember' });
      if (P.belWound && Math.sin(P.clk * 30) > 0) mvStar(bx, by - 4, 3, '255,170,140', 0.8);
    }
    // the tolls still sounding: one mote per buff circling the knight, a soft light in its colour
    const live = BEL_TOLLS.filter(t => (B[t.id] || 0) > 0);
    live.forEach((t, i) => {
      const a = P.clk * 2.2 + i * 6.283 / live.length, x = P.x + Math.cos(a) * 12, y = P.y - 16 + Math.sin(a) * 4, front = Math.sin(a) > 0;
      const fade = Math.min(1, B[t.id] / 3);
      drawGlow(() => { g.fillStyle = `rgba(${t.rgb},${(front ? 0.85 : 0.4) * fade})`; g.fillRect(Math.round(x), Math.round(y), 1, 1); g.fillStyle = `rgba(${t.rgb},${0.25 * fade})`; g.fillRect(Math.round(x) - 1, Math.round(y), 3, 1); g.fillRect(Math.round(x), Math.round(y) - 1, 1, 3); });
      if (i === 0) addLight(P.x, P.y - 16, 22, t.rgb, 0.18 * fade);
    });
    if (B.mend > 0 && Math.random() < 0.3) particles.push({ x: P.x + rand(-6, 6), y: P.y - rand(2, 24), vx: 0, vy: -rand(15, 30), life: 0.5, kind: 'mote' });
    // shock rings (pixel dots on an ellipse, glow layer) and the little note glyphs that float off each struck note
    if (BEL.rings.length || BEL.fx.length) drawGlow(() => {
      for (const r of BEL.rings) {
        const q = 1 - r.life / r.max, R = r.r0 + (r.r1 - r.r0) * (1 - Math.pow(1 - q, 2.2)), a = (1 - q) * 0.95, n = Math.max(12, Math.round(R * 1.6));
        for (let w = 0; w < r.w; w++) {
          const RR = R - w * 2.5, aa = a * (w ? 0.5 : 1);
          g.fillStyle = `rgba(${r.rgb},${aa})`;
          for (let i = 0; i < n; i++) { if (w && i % 2) continue; const th = i / n * 6.2832; g.fillRect(Math.round(r.x + Math.cos(th) * RR), Math.round(r.y + Math.sin(th) * RR * r.sq), 1, 1); }
        }
      }
      for (const f of BEL.fx) {
        if (f.kind !== 'note') continue;
        const a = Math.min(1, f.life / f.max * 1.6), x = Math.round(f.x), y = Math.round(f.y);
        g.fillStyle = `rgba(${f.rgb},${a})`;
        g.fillRect(x, y, 2, 2); g.fillRect(x + 2, y - 4, 1, 5); g.fillRect(x + 3, y - 4, 1, 1); g.fillRect(x + 4, y - 3, 1, 1);
      }
    });
  },
  hud(x) {
    // the staff: three lines, a note head per slot (Gold high, Ash middle, Ember low), the newest pops in
    const notes = belNotes(), w = 26, deny = P.belDeny && P.clk - P.belDeny < 0.35;
    vctx.fillStyle = 'rgba(10,8,14,0.7)'; vctx.fillRect(ox + (x - 1.5) * scale, oy + 17.4 * scale, (w + 3) * scale, 9.4 * scale);
    for (const ly of [BEL_NOTE.G.y, BEL_NOTE.A.y, BEL_NOTE.E.y]) { vctx.fillStyle = deny ? 'rgba(200,70,70,0.75)' : 'rgba(150,136,120,0.55)'; vctx.fillRect(ox + x * scale, oy + ly * scale, w * scale, Math.max(1, 0.4 * scale)); }
    vctx.fillStyle = 'rgba(150,136,120,0.55)'; vctx.fillRect(ox + (x + w) * scale, oy + BEL_NOTE.G.y * scale, Math.max(1, 0.5 * scale), (BEL_NOTE.E.y - BEL_NOTE.G.y) * scale);
    for (let i = 0; i < 3; i++) {
      const nx = x + 5 + i * 8, n = notes[i];
      if (!n) { mvHudPip(nx, BEL_NOTE.A.y + 0.2, false, '', 0.7); continue; }
      const N = BEL_NOTE[n], pop = i === P.belPopN && P.clk - P.belPop < 0.18 ? 1 + 0.6 * (1 - (P.clk - P.belPop) / 0.18) : 1;
      vctx.fillStyle = N.col; vctx.beginPath(); vctx.ellipse(ox + nx * scale, oy + (N.y + 0.2) * scale, 1.7 * pop * scale, 1.25 * pop * scale, -0.35, 0, 6.2832); vctx.fill();
      vctx.fillRect(ox + (nx + 1.2) * scale, oy + (N.y - 4.2) * scale, Math.max(1, 0.45 * scale), 4.2 * scale);   // the stem
    }
    // what a Perform would play now
    const tolls = notes.length ? belTollsOf(notes) : [];
    let tx = x + w + 4;
    if (tolls.length) { const s = tolls.map(t => t.name).join(' · '); text(s, tx, 24.4, 5, `rgb(${tolls[tolls.length - 1].rgb})`, 'left', { weight: 600 }); }
    // the tolls sounding: a ring per buff draining over its 30 s, a glyph in its colour; Echo shows its charges
    const B = belBuffs(); let bx = x + 2.5;
    for (const t of BEL_TOLLS) {
      const left = B[t.id] || 0; if (left <= 0) continue;
      const max = t.id === 'mend' ? BEL_MEND_SECS : BEL_SECS, by = 31, c = `rgb(${t.rgb})`;
      const blink = left < 3 && Math.sin(P.clk * 16) < 0;
      mvHudRing(bx, by, 2.9, left / max, blink ? 'rgba(80,70,70,0.9)' : c);
      vctx.fillStyle = c; vctx.strokeStyle = c; vctx.lineWidth = Math.max(1, 0.6 * scale);
      const X = v => ox + (bx + v) * scale, Y = v => oy + (by + v) * scale;
      vctx.beginPath();
      if (t.id === 'swift') { vctx.moveTo(X(-1.4), Y(-1.2)); vctx.lineTo(X(0), Y(0)); vctx.lineTo(X(-1.4), Y(1.2)); vctx.moveTo(X(0.2), Y(-1.2)); vctx.lineTo(X(1.4), Y(0)); vctx.lineTo(X(0.2), Y(1.2)); vctx.stroke(); }
      else if (t.id === 'iron') { vctx.moveTo(X(-1.2), Y(-1.3)); vctx.lineTo(X(1.2), Y(-1.3)); vctx.lineTo(X(1.2), Y(0)); vctx.lineTo(X(0), Y(1.4)); vctx.lineTo(X(-1.2), Y(0)); vctx.closePath(); vctx.fill(); }
      else if (t.id === 'fury') { vctx.moveTo(X(0), Y(-1.6)); vctx.quadraticCurveTo(X(1.5), Y(0.2), X(0), Y(1.3)); vctx.quadraticCurveTo(X(-1.5), Y(0.2), X(0), Y(-1.6)); vctx.fill(); }
      else if (t.id === 'mend') { vctx.fillRect(X(-0.35), Y(-1.4), 0.7 * scale, 2.8 * scale); vctx.fillRect(X(-1.4), Y(-0.35), 2.8 * scale, 0.7 * scale); }
      else if (t.id === 'echo') { vctx.arc(X(-0.8), Y(0), 1.0 * scale, -1.1, 1.1); vctx.stroke(); vctx.beginPath(); vctx.arc(X(-0.8), Y(0), 2.0 * scale, -0.9, 0.9); vctx.stroke(); }
      if (t.id === 'echo') for (let i = 0; i < BEL_ECHO_N; i++) mvHudPip(bx - 1.6 + i * 1.6, by + 4.4, i < (P.belEchoN || 0), c, 0.55);
      bx += 8;
    }
  },
  unlocks: [
    { rank: 2, id: 'wb_chime', name: 'Chime spin', input: 'J J (pause) J', desc: 'Wait a beat after the right swing: the bell whirled round you, both sides (0.7 ×2, Ash).' },
    { rank: 2, id: 'wb_mending', name: 'Three-note tolls', input: 'Ash Gold Ember → I', desc: 'Mending: heal 10% of max HP over 10 s (once per 60 s).' },
    { rank: 3, id: 'wb_encore', name: 'Encore', input: 'Perform → I', desc: 'Ring it again: 1.4 both sides, and every toll still sounding is back to 30 s.' },
    { rank: 4, id: 'wb_echowave', name: 'Echo wave', input: 'Perform / Encore', desc: 'The ring rolls on out to 64 px both ways (+0.6).' },
    { rank: 5, id: 'wb_grand', name: 'Grand toll', input: 'Perform, 3 notes', desc: 'A full staff stuns small foes and adds 60 stance damage to bosses.' },
  ],
  combos: [
    { rank: 1, name: 'Left · Right · Overhead clang', input: 'J J J', desc: 'Three Ash blows, the last a downward clang (finisher).' },
    { rank: 1, name: 'Knell', input: 'J J J → K', desc: 'Off the clang, the bell dragged low round your front (Ember).' },
    { rank: 1, name: 'Backswing', input: 'J → K  /  J J → K', desc: 'A backhand of the bell\'s shoulder (Ember). J: the overhead clang.' },
    { rank: 1, name: 'Forward slam', input: 'K', desc: 'The bell mouth-first into the floor (Ember).' },
    { rank: 1, name: 'Double slam', input: 'K K', desc: 'Up and down twice into the same spot: two Ember notes.' },
    { rank: 1, name: 'Wind-up toll', input: 'hold K', desc: 'Swing the bell round behind you; from 0.65 s it\'s wound: 2.4 (Ember).' },
    { rank: 1, name: 'Peal uppercut', input: '↑J', desc: 'The bell heaved up past the head, for fliers (Gold). ↑J again: Gold.' },
    { rank: 1, name: 'Falling peal', input: '↑J → J', desc: 'The raised bell brought straight down (Ash).' },
    { rank: 1, name: 'Perform', input: 'I (1+ notes)', desc: 'A ring both sides (1.2); plays every toll in the staff: 30 s buffs.' },
    { rank: 1, name: 'Swiftness', input: 'Ash Ash → I', desc: 'Stamina regenerates 25% faster.' },
    { rank: 1, name: 'Iron hymn', input: 'Ash Ember → I', desc: 'Finishers and heavies don\'t flinch from hits under 20% max HP.' },
    { rank: 1, name: 'Fury', input: 'Ember Ember → I', desc: '+8% damage.' },
    { rank: 1, name: 'Echo', input: 'Gold Gold → I', desc: 'The next 3 hits ring again a beat later for 30%.' },
    { rank: 1, name: 'Ringing lunge', input: 'L → J', desc: 'Out of the roll, a lunging swing (Ash). J: the right swing.' },
    { rank: 1, name: 'Bell drop', input: 'L → K', desc: 'Out of the roll, the bell hauled over and dropped (Ember).' },
    { rank: 1, name: 'Air swing', input: 'air J', desc: 'A swing in the air (Ash).' },
    { rank: 1, name: 'Bell pogo', input: 'air ↓J', desc: 'Mouth-down onto a foe: pogo off it (Ash).' },
    { rank: 1, name: 'Bell plunge', input: 'air K', desc: 'Dive mouth-first: 1.8, and a shock ring where it lands (Ember).' },
    { rank: 2, name: 'Chime spin', input: 'J J (pause) J', desc: 'Wait a beat after the 2nd swing: a whirl both sides (0.7 ×2, Ash).' },
    { rank: 2, name: 'Mending', input: 'Ash Gold Ember → I', desc: 'Heal 10% max HP over 10 s (once per 60 s).' },
    { rank: 3, name: 'Encore', input: 'Perform → I', desc: 'Ring again (1.4) and refresh every toll still sounding.' },
    { rank: 4, name: 'Echo wave', input: 'Perform / Encore', desc: 'The ring rolls on to 64 px both ways (+0.6).' },
    { rank: 5, name: 'Grand toll', input: 'Perform with 3 notes', desc: 'Stuns small foes; +60 stance damage to bosses.' },
  ],
}, {
  // ---- Ash: the J chain
  wb_1: { tags: ['wb_1', 'ml_bb1'], note: 'A', dmg: 1.1, poise: 18, stam: 12, wind: 190, total: 460, step: 0, reach: 36, lunge: 8, fx: null,
    next: { J: 'wb_2', K: q => (mvHeldK(q) ? '@K' : 'wb_back'), I: '@I' } },
  wb_2: { tags: ['wb_2', 'ml_bb2'], note: 'A', dmg: 1.15, poise: 18, stam: 12, wind: 190, total: 460, step: 1, reach: 36, lunge: 8, fx: null,
    next: { J: 'wb_3', K: q => (mvHeldK(q) ? '@K' : 'wb_back'), I: '@I' } },
  wb_3: { tags: ['wb_3', 'ml_1'], note: 'A', dmg: 1.8, poise: 45, stam: 16, wind: 290, total: 720, step: 2, fin: true, reach: 38, lunge: 10, fx: null,
    next: { K: q => (mvHeldK(q) ? '@K' : 'wb_knell'), I: '@I' } },
  // II: J J (pause) J -- the bell whirled round at the waist, both sides
  wb_chime: { tags: ['wb_chime', 'ml_spin_end'], rank: 2, note: 'A', hits: [0.7, 0.7], gap: 210, poise: 30, stam: 14, wind: 220, total: 640, spin: true, reach: 36, backReach: 34, fin: true, fx: null,
    next: { J: 'wb_3', I: '@I' } },
  // J J J -> K: the knell, the bell dragged low round the front
  wb_knell: { tags: ['wb_knell', 'ml_side'], kind: 'heavy', note: 'E', dmg: 1.6, poise: 55, stam: 18, wind: 320, total: 820, reach: 38, back: 8, lunge: 10, fin: true, fx: null,
    on: { hit(t) { if (t && !t.boss && !t.prop && !(t.cfg && t.cfg.elite) && t.vx !== undefined) t.vx = P.face * 150; } },
    next: { I: '@I' } },
  // ---- Ember: the K side
  wb_back: { tags: ['wb_back', 'ml_bb2'], kind: 'heavy', note: 'E', dmg: 1.2, poise: 30, stam: 14, wind: 240, total: 620, reach: 36, back: 6, fx: null,
    next: { J: 'wb_3', I: '@I' } },
  wb_kwind: { tags: ['wb_kwind', 'ml_charge_idle'], kind: 'heavy', loop: true, noHit: true, dmg: 0, poise: 0, stam: 0, wind: 1e9, total: 1e9, charge: true,
    move() {},
    on: {
      start(A, o) { P.belKMs = o.bank || 0; P.belWound = false; },
      update(dt, A, ax, grav) {
        P.vx = approach(P.vx, 0, 900 * dt); grav();
        P.belKMs += dt * 1000; P.charge = P.belKMs / 1000;
        if (!P.belWound && P.belKMs >= BEL_WOUND) {   // wound: the bell hums its Ember note before it lands
          P.belWound = true; sfx.glint(); belBell(BEL_NOTE.E.f, 0.45, 0.6);
          if (typeof feelFlash === 'function') feelFlash(P.x - P.face * 10, P.y - 30, 24, '255,120,90', 1, 0.12);
        }
        if (peek('roll') && P.st > 0) { take('roll'); mvDodgeStart(ax); return 'stop'; }
        if (!P.ground) { setP('air', 'jump_fall'); return 'stop'; }
        if (!held.has('heavy') || P.belKMs >= BEL_OVER) {
          if (ax) P.face = ax;
          if (P.belWound) mvStart('wb_toll', { charged: true });
          else mvStart('wb_slam', { t0: Math.min(P.belKMs, 200) });   // a tap (or an early let-go): the forward slam, its wind-up already begun
          return 'stop';
        }
      },
    } },
  wb_slam: { tags: ['wb_slam', 'ml_1'], kind: 'heavy', note: 'E', dmg: 1.5, poise: 40, stam: 16, wind: 280, total: 680, reach: 36, lunge: 10, fx: null,
    on: { swing() { belImpact(32); } },
    next: { K: q => (mvHeldK(q, 180) ? '@K' : 'wb_dslam'), I: '@I' } },
  wb_dslam: { tags: ['wb_dslam', 'ml_double'], kind: 'heavy', note: 'E', noteEach: true, hits: [1.05, 1.05], gap: 330, poise: 60, stam: 20, wind: 300, total: 880, reach: 36, fin: true, fx: null,
    on: { hitStart() { belImpact(32); } },
    next: { I: '@I' } },
  wb_toll: { tags: ['wb_toll', 'ml_bigsmash'], kind: 'heavy', note: 'E', dmg: 2.4, poise: 80, stam: 22, wind: 200, total: 760, reach: 38, lunge: 12, fin: true, armor: 0.25, slam: true, fx: null,
    on: { swing() { belImpact(26, true); belRing(P.x + P.face * 24, P.y - 4, 34, BEL_NOTE.E.rgb, 0.4, { sq: 0.4, w: 2 }); } },
    next: { I: '@I' } },
  // ---- Gold: the up J
  wb_up: { tags: ['wb_up', 'ml_up'], up: true, note: 'G', dmg: 1.1, poise: 25, stam: 12, wind: 220, total: 560, reach: 30, fx: null,
    next: { J: 'wb_peal', I: '@I' } },
  wb_peal: { tags: ['wb_peal', 'ml_drop'], note: 'A', dmg: 1.2, poise: 30, stam: 12, wind: 200, total: 560, reach: 36, fx: null,
    on: { swing() { belImpact(30); } },
    next: { I: '@I' } },
  // ---- I: Perform / Encore
  wb_perform: { tags: ['wb_perform', 'ml_quake'], perform: true, kind: 'heavy', dmg: 1.2, poise: 40, stam: 14, wind: 300, total: 900, spin: true, reach: 40, backReach: 40, ys: [-40, 2], fx: null,
    mod(c) { if (P.belGrand && c.t && c.t.boss) c.poise += 60 / 1.3; },
    on: { start() { belPerformStart(); }, swing() { belPerformRing(false); } },
    next: { I: 'wb_encore' } },
  wb_encore: { tags: ['wb_encore', 'ml_quake'], perform: true, rank: 3, kind: 'heavy', dmg: 1.4, poise: 50, stam: 10, wind: 260, total: 800, spin: true, reach: 40, backReach: 40, ys: [-40, 2], fin: true, fx: null,
    on: { start() { P.belGrand = false; tone(587, 0.3, 0.03, 'sine', 1, 0.05); }, swing() { belPerformRing(true); } } },
  // ---- out of the roll
  wb_rollj: { tags: ['wb_rollj', 'ml_rollswing'], note: 'A', dmg: 1.0, poise: 20, stam: 12, wind: 160, total: 440, reach: 36, lunge: 22, dash: true, fx: null, next: { J: 'wb_2', I: '@I' } },
  wb_rollk: { tags: ['wb_rollk', 'ml_drop'], kind: 'heavy', note: 'E', dmg: 1.4, poise: 45, stam: 16, wind: 260, total: 640, reach: 36, lunge: 12, fin: true, slam: true, fx: null, next: { I: '@I' } },
  // ---- air
  wb_air: { tags: ['wb_air', 'ml_air'], air: true, note: 'A', dmg: 1.0, poise: 18, stam: 12, wind: 180, total: 420, reach: 34, fx: null },
  wb_down: { tags: ['wb_down', 'ml_down'], down: true, note: 'A', dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300, box: [-12, 14, -16, 26], fx: null },
  // air K: dive mouth-first (heave, fall); a foe struck on the way down = 1.8 and a bounce, the floor = the landing blow + a shock ring
  wb_plunge: { tags: ['wb_plunge', 'plunge_fall'], airCount: true, airOk: true, loop: true, noHit: true, kind: 'heavy', note: 'E', dmg: 1.8, poise: 90, stam: 20, wind: 1e9, total: 1e9, fx: null,
    move() {},
    on: {
      start() { P.belDive = false; P.vy = Math.min(P.vy, -70); },
      update(dt, A, ax, grav) {
        const t = P.mvT, an = P.anim, R = A._r;
        const nf = R ? R.n : 4, fi = t < 200 ? (t < 100 ? 0 : 1) : Math.min(nf - 1, 2 + Math.floor((t - 200) / 70) % Math.max(1, nf - 2));
        if (an.i !== fi) { an.i = fi; an.changed = true; } an.t = 0; an.speed = 0;
        if (t < 200) { P.vx *= Math.pow(0.05, dt); P.vy = Math.min(P.vy + 420 * dt, 30); return; }
        if (!P.belDive) { P.belDive = true; P.vy = 330; sfx.heavySwing(); }
        P.vy = Math.min(P.vy + 1100 * dt, 540); P.vx = approach(P.vx, ax * 45, 500 * dt);
        if (Math.random() < 0.6) particles.push({ x: P.x + P.face * rand(2, 12), y: P.y - rand(0, 20), vx: 0, vy: -rand(40, 90), life: 0.25, kind: 'ember' });
        // a foe under the falling bell
        const r = rect(P.x - 6 + P.face * 2, P.y - 8, P.x + P.face * 22, P.y + 14);
        let hit = null;
        for (const q of targets()) { if (q.prop) continue; const hb = hbOf(q); if (hb && overlap(r, hb)) { hit = q; break; } }
        if (hit) {
          P.hitSet = new Set(); P.belRungK = -1;
          mvStrikeAt(r, 1.8, 90, { A, kind: 'heavy', big: true, onHit: (q, info) => MV.types.bell.onHit(q, info, A, { k: 0, mul: 1.8 }) });
          shake = Math.max(shake, 6); hitstop = Math.max(hitstop, 0.07); sfx.boom();
          P.vy = -250; P.vx = -P.face * 40; P.ground = false; P.airDash = true; setP('air', 'jump_up'); return 'stop';
        }
        grav();
        if (P.ground) { mvStart('wb_pland'); return 'stop'; }
        if (t > 3000) { setP('air', 'jump_fall'); return 'stop'; }
      },
    } },
  wb_pland: { tags: ['wb_pland', 'plunge_land'], kind: 'heavy', note: 'E', dmg: 1.8, poise: 90, stam: 0, wind: 40, total: 560, reach: 30, back: 10, fin: true, fx: null,
    on: { swing() {
      belImpact(16, true); mvShockwave({ r: 44, dmg: 0.4, poise: 30, shake: 7 });
      belRing(P.x, P.y - 2, 44, BEL_NOTE.E.rgb, 0.4, { sq: 0.3, w: 2 });
      if (typeof wsTone === 'function') wsTone(70, 0.35, 0.08, 'sine', 0.6);
    } } },
});
hvHoldEnd('bell', 'wb_kwind');
// a bell landing on the floor: dust, a crack of light at the lip
function belImpact(dx, big) {
  const x = P.x + P.face * dx;
  for (let i = 0; i < (big ? 12 : 6); i++) particles.push({ x: x + rand(-8, 8), y: P.y - 2, vx: rand(-60, 60), vy: -rand(20, 90), g: 320, life: 0.45, kind: 'dust' });
  addLight(x, P.y - 6, big ? 34 : 20, '255,206,140', big ? 0.9 : 0.5);
  if (big) shake = Math.max(shake, 5);
}

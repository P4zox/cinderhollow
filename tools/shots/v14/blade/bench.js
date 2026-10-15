// v14 blade bench: dmg/s (x light AR) of every Longsword / Katana loop, from real inputs, against a dummy that follows
// (infinite stamina, 12 s per route) + stamina per second; then a real-boss duel (Gravetusk in the Training Grounds, its
// own AI) per weapon style: damage dealt / taken over 40 s with a scripted player who attacks in openings and rolls.
// Run: SHOT_HTML=web/dist/v14_blade.html sh tools/shots/wm/run.sh tools/shots/v14/blade/bench.js <out>
const SECS = window.__bbSecs || 12;
const st = () => G.P.state;
// a route: steps pressed in order whenever the player can queue (free, or in a move with nothing queued, 40 ms in);
// 'J' 'K' 'I' 'L' taps; {b, beat: n} = press n frames after the current move ENDED; {hold: ms} = hold K; {pre: js} once per loop
const ROUTES = [
  ['longsword', 1, 'J J J J', ['J', 'J', 'J', 'J']],
  ['longsword', 1, 'J J K', ['J', 'J', 'K']],
  ['longsword', 1, 'J J J K', ['J', 'J', 'J', 'K']],
  ['longsword', 1, 'K', ['K']],
  ['longsword', 1, 'hold K (charged) loop', [{ hold: 520 }]],
  ['longsword', 1, 'J K (lifting cleave) loop', ['J', 'K']],
  ['longsword', 1, 'J K J J', ['J', 'K', 'J', 'J']],
  ['longsword', 2, 'J J (beat) J J (wheel -> crit)', ['J', 'J', { b: 'J', beat: 9 }, 'J']],
  ['longsword', 4, 'J J J hold K (pommel)', ['J', 'J', 'J', { hold: 220 }]],
  ['longsword', 5, 'J J J J ember (perfect 4th)', ['J', 'J', 'J', { b: 'J', late: 120 }]],
  ['longsword', 1, 'K J J J (v14c return slash)', ['K', 'J', 'J', 'J']],
  ['longsword', 1, 'K K (v14c crosswise) loop', ['K', 'K']],
  ['longsword', 1, 'J K K (v14c splitting cleave)', ['J', 'K', 'K']],
  ['katana', 1, 'J J J', ['J', 'J', 'J']],
  ['katana', 1, 'K -> K loop', ['K']],
  ['katana', 1, 'J K J J (v14c kesa)', ['J', 'K', 'J', 'J']],
  ['katana', 1, 'J J J K (v14c helm splitter)', ['J', 'J', 'J', 'K']],
  ['katana', 1, 'Iai J K loop (v14c thrust home)', [{ pre: 'P.sheathed = true' }, 'K', 'J', 'K']],
  ['katana', 1, 'I K (sheathe, Iai) loop', ['I', 'K']],
  ['katana', 1, 'J J K K (crescent sheathe, Iai)', ['J', 'J', 'K', 'K']],
  ['katana', 1, 'Iai J I (draw, swallow return, sheathe) loop', [{ pre: 'P.sheathed = true' }, 'K', 'J', 'I']],
  ['katana', 1, 'J J J I K (flurry sheathe, Iai)', ['J', 'J', 'J', 'I', 'K']],
  ['katana', 4, 'J J J I K (thousand cuts, Iai)', ['J', 'J', 'J', 'I', 'K']],
  ['katana', 1, 'sheathed J J J I (draw cut chain)', ['J', 'J', 'J', 'I']],
  ['katana', 1, 'hold K focus loop (I, hold K)', ['I', { hold: 450 }]],
];
const only = window.__bbOnly;
const out = { table: [], boss: [] };
for (const [type, rank, name, pat] of ROUTES) {
  if (only && !only.includes(type)) continue;
  W().reset(type, rank); arena(); W().reset(type, rank); E('D.maxSt = 1e6; P.st = 1e6');
  W().dummy(26); E('window.__wm.follow = 26');
  let i = 0, holdLeft = 0, t0 = null, stam = 0, endSeen = null, prevSt = st();
  for (let f = 0; f < SECS * 60 + 900; f++) {
    if (holdLeft > 0 && --holdLeft === 0) W().up('heavy');
    E('P.st = 1e6; if (P.x > 330) P.x -= 200');
    const s = st();
    if (s !== prevSt && E('!!ATK[' + JSON.stringify(prevSt) + ']')) endSeen = f;   // the frame a move ended (state changed)
    prevSt = s;
    let p = pat[i % pat.length];
    if (p && p.pre) { E(p.pre); i++; p = pat[i % pat.length]; }
    const busy = E('!!ATK[P.state] && !!P.mvQ'), free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
    let go = holdLeft === 0 && free && !busy;
    if (go && p.beat !== undefined) go = !E('!!ATK[P.state]') && endSeen !== null && f - endSeen >= p.beat;
    if (go && p.late !== undefined) go = E('!!ATK[P.state]') ? E('ATK[P.state].mv.total - P.mvT') <= p.late : true;
    if (go) {
      const b = typeof p === 'string' ? p : p.b;
      const st0 = E('P.st');
      if (p.hold) { W().down('heavy'); holdLeft = Math.round(p.hold / (1000 / 60)); W().frame(1); }
      else { const k = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll' }[b]; W().down(k); W().frame(1); W().up(k); }
      i++; endSeen = null;
      if (t0 === null) { t0 = W().ms; W().log = []; E('window.__bbSt = 0'); }
      continue;
    }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const secs = (W().ms - t0) / 1000, L = G.D.light;
  const dmg = W().log.filter(h => h.melee).reduce((a, h) => a + h.dmg, 0) / L + W().log.filter(h => !h.melee).reduce((a, h) => a + h.dmg, 0) / L;
  const tally = {}; for (const h of W().log) tally[h.st] = (tally[h.st] || 0) + 1;
  out.table.push({ type, rank, route: name, dps: +(dmg / secs).toFixed(2), hits: Object.entries(tally).map(([k, v]) => k + 'x' + v).join(' ') });
}
// stamina per loop with real stamina: how long until empty from full, mashing the route (no waiting)
// ---- real boss duel: Gravetusk (hound) with its own AI; the player stands ~30 px off, attacks with the route while the
// boss is not winding up an attack nearby, rolls through when it is (a simple reactive bot), takes real hits (no god).
if (!window.__bbNoBoss) {
  const STYLES = [
    ['longsword', 1, 'J J J J', ['J', 'J', 'J', 'J']],
    ['longsword', 1, 'J J K', ['J', 'J', 'K']],
    ['longsword', 1, 'J K J J', ['J', 'K', 'J', 'J']],
    ['katana', 1, 'J J J', ['J', 'J', 'J']],
    ['katana', 1, 'K -> K', ['K']],
    ['katana', 1, 'J J K K', ['J', 'J', 'K', 'K']],
    ['katana', 1, 'Iai J I', ['K', 'J', 'I']],
    ['katana', 1, 'J J J K', ['J', 'J', 'J', 'K']],
    ['longsword', 1, 'K J J J', ['K', 'J', 'J', 'J']],
    ['greatsword', 1, 'J J J', ['J', 'J', 'J']],
    ['sns', 1, 'J J J J', ['J', 'J', 'J', 'J']],
    ['dual', 1, 'J J J J', ['J', 'J', 'J', 'J']],
    ['spear', 1, 'J J J', ['J', 'J', 'J']],
  ];
  const BS = window.__bbBossSecs || 40;
  for (const bk of (window.__bbBosses || ['hound', 'omen'])) for (const [type, rank, name, pat] of STYLES) {
    if (only && !only.includes(type)) continue;
    W().reset(type, rank); E('enemies = enemies.filter(e => !e.wmDummy)');
    G.trn.start(); G.step(10);
    G.trn.summon(bk); const b = G.boss;
    W().reset(type, rank); E('P.lastHit = null');
    b.maxHp = 1e7; b.hp = 1e7;
    let dealt = 0, taken = 0, hitsTaken = 0, rolls = 0; const oh = b.hit;
    b.hit = function (info) { if (info.melee) dealt += info.dmg / (info.fire && G.D.W.fire && info.kind === 'heavy' ? 1 + G.D.W.fire : 1); return oh.call(this, info); };
    let i = 0, act = false, stag = 0, bst = b.state;
    for (let f = 0; f < 60 * (BS + 6); f++) {
      if (!b.active) { W().down(b.x > G.P.x ? 'right' : 'left'); W().frame(1); W().up('right'); W().up('left'); continue; }
      if (!act) { act = true; f = 0; }
      if (f >= 60 * BS) break;
      const hp0 = G.P.hp, d = b.x - G.P.x, ad = Math.abs(d);
      const threat = E("boss && boss.state !== 'idle' && boss.state !== 'stagger' && boss.state !== 'walk' && boss.state !== 'chase' && boss.state !== 'dormant' && boss.state !== 'intro'");
      const free = E("['idle','run','land'].includes(P.state) || (!!ATK[P.state] && !P.mvQ && P.mvT > 40 && !ATK[P.state].mv.loop)");
      if (threat && ad < 70 && f % 40 === 0 && G.P.st > 5 && G.P.state !== 'roll') { E("if (ATK[P.state] && !ATK[P.state].mv.commit && P.mvT < ATK[P.state].mv.wind) setP('idle','idle',true)"); W().down(d > 0 ? 'right' : 'left'); W().tap('roll'); W().up('right'); W().up('left'); rolls++; }
      else if (ad > 44 && ['idle', 'run'].includes(G.P.state)) { W().down(d > 0 ? 'right' : 'left'); W().frame(1); W().up('right'); W().up('left'); }
      else if (free && G.P.st > 12) { G.P.face = d > 0 ? 1 : -1; const p = pat[i++ % pat.length]; W().tap({ J: 'attack', K: 'heavy', I: 'parry' }[p]); }
      else W().frame(1);
      if (b.state !== bst) { if (b.state === 'stagger') stag++; bst = b.state; }
      if (G.P.hp < hp0) { taken += hp0 - G.P.hp; hitsTaken++; }
      if (G.P.hp < G.D.maxHp * 0.3) G.P.hp = G.D.maxHp;   // keep the duel going (taken is still counted)
      if (G.state !== 'play') { G.step(1, [], ['pause']); }
    }
    b.hit = oh;
    out.boss.push({ boss: bk, type, style: name, staggers: stag, dps: +(dealt / G.D.light / BS).toFixed(2), takenPerMin: Math.round(taken / BS * 60), hitsTaken, rolls });
    G.trn.clear(); G.step(5);
  }
}
return out;

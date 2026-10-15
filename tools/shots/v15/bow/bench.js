// v15 bow dmg/s bench (tools/shots/wm/bench.js style): each route played with real key presses for SECS on the training
// dummy kept at a fixed distance (the sweet spot unless noted), infinite stamina; dmg in light-AR units per second.
const SECS = 12, ONLY = window.__bwOnly;
// pattern items: 'J' / 'K' / 'L' / 'U' (up J) pressed as soon as the driver may queue a press, 'J!' etc. only from neutral,
// { draw: ms } holds K until the draw has run `ms` (then lets go: the power shot), { draw, idle: true } starts from neutral
const ROUTES = [
  // [name, rank, pattern, dx, note]
  ['J J J J (main loop)', 1, ['J', 'J', 'J', 'J!'], 44],
  ['J J J J point-blank', 1, ['J', 'J', 'J', 'J!'], 14, 'x0.7 inside 16 px'],
  ['J J J J far (110 px)', 1, ['J', 'J', 'J', 'J!'], 110],
  ['J J J -> hold K (lv3 from the bank)', 1, ['J!', 'J', 'J', { draw: 120 }], 44],
  ['K tap loop (lv1)', 1, ['K!'], 44],
  ['hold K lv3 loop', 1, [{ draw: 920, idle: true }], 44],
  ['L -> hold K (lv2 power), step-cancel', 1, ['L', { draw: 120 }], 44],
  ['L L -> hold K (II, lv3 power), step-cancel', 2, ['L', 'L', { draw: 120 }], 44],
  ['J K K (stab, recoil)', 1, ['J!', 'K', 'K'], 26],
  ['L -> J (dash shot) loop', 1, ['L', 'J'], 44],
  ['L -> K tap (leaping point-blank)', 1, ['L', 'K'], 26],
  ['up J arc shot', 1, ['U!'], 64],
  ['up J arc shot x7 (IV)', 4, ['U!'], 64],
  ['lv3 -> hollow piercer (III)', 3, [{ draw: 920, idle: true }, 'K'], 44],
];
const out = [];
for (const [name, rank, pat, dx, note] of ROUTES.filter(r => !ONLY || ONLY.some(o => r[0].includes(o)))) {
  E('BW.log = []; BW.cap = 1e5');
  W().reset('bow', rank); arena(); W().reset('bow', rank);
  E('D.maxSt = 1e6; P.st = 1e6; P.bwLv = 1; P.bwSteps = 0; P.x = 160'); W().dummy(dx); E('window.__wm.follow = ' + dx);
  let i = 0, holding = null, t0 = null, upHeld = false;
  for (let f = 0; f < SECS * 60 + 900; f++) {
    if (holding) { holding.n++; if (E(`P.state === 'bw_draw' && P.bwDrawMs >= ${holding.draw}`) || holding.n > 200) { W().up('heavy'); holding = null; } }
    if (upHeld) { W().up('up'); upHeld = false; }
    E('P.st = 1e6; P.face = 1; if (P.x > 330) P.x -= 200; if (P.x < 90) P.x += 150');
    const p = pat[i % pat.length], neutral = typeof p === 'string' ? p.endsWith('!') : !!p.idle;
    const idle = E("['idle','run','land'].includes(P.state)");
    const free = idle || (!neutral && E(`(!!ATK[P.state] && !P.mvQ && P.mvT > (ATK[P.state].mv.commit && '${p}' === 'L' ? 240 : 40) && !ATK[P.state].mv.loop) || (P.state === 'roll' && P.dg && P.dg.t > 160 && !peek('roll'))`));
    if (!holding && free) {
      const b = typeof p === 'string' ? p.replace('!', '') : 'H';
      if (b === 'J' || b === 'L' || b === 'K') { const a = { J: 'attack', L: 'roll', K: 'heavy' }[b]; W().down(a); W().frame(1); W().up(a); }
      else if (b === 'U') { W().down('up'); W().down('attack'); W().frame(1); W().up('attack'); upHeld = true; }
      else { W().down('heavy'); holding = { draw: p.draw, n: 0 }; W().frame(1); }
      i++;
      if (t0 === null) { t0 = W().ms; W().log = []; E('BW.log = []'); }
      continue;
    }
    W().frame(1);
    if (t0 !== null && W().ms - t0 >= SECS * 1000) break;
  }
  W().up('heavy');
  const secs = (W().ms - t0) / 1000, dmg = W().log.reduce((a, h) => a + h.dmg / h.light, 0);
  const tally = {}; for (const h of E('BW.log')) tally[h.id + ' lv' + h.lv] = (tally[h.id + ' lv' + h.lv] || 0) + 1;
  out.push({ route: name, rank, dx, dps: +(dmg / secs).toFixed(2), hits: W().log.length, note: (note || '') + ' ' + JSON.stringify(tally) });
}
return out.map(r => `${r.dps.toFixed(2)}  ${r.route} [rank ${r.rank}, foe at ${r.dx} px] ${r.hits} hits ${r.note}`);

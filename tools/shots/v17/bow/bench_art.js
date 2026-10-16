// v17 Ashen Volley vs the bow's best routes on a boss-sized dummy (copied from tools/shots/v15/bow/bench.js)
// v15 bow dmg/s bench (tools/shots/wm/bench.js style): each route played with real key presses for SECS on the training
// dummy kept at a fixed distance (the sweet spot unless noted), infinite stamina; dmg in light-AR units per second.
const SECS = 20, ONLY = window.__bwOnly;
// pattern items: 'J' / 'K' / 'L' / 'U' (up J) pressed as soon as the driver may queue a press, 'J!' etc. only from neutral,
// { draw: ms } holds K until the draw has run `ms` (then lets go: the power shot), { draw, idle: true } starts from neutral
const ROUTES = [
  // [name, rank, pattern, dx, note]  ('O' = the art, when it is off cooldown and affordable; skipped otherwise)
  ['J J J J (main loop)', 1, ['J', 'J', 'J', 'J!'], 30],
  ['J J J -> hold K (lv3 from the bank)', 1, ['J!', 'J', 'J', { draw: 120 }], 30],
  ['L L -> hold K (II, lv3 power), step-cancel', 2, ['L', 'L', { draw: 120 }], 30],
  ['art only (Ashen Volley, tap, on cooldown)', 1, ['O!'], 24],
  ['art only (Ashen Volley, held)', 1, [{ art: 50 }], 24],
  ['art -> hold K (the banked level), J J J J between', 1, ['O!', { draw: 120 }, 'J!', 'J', 'J', 'J!'], 24],
  ['J J J J + art when ready', 1, ['J', 'J', 'J', 'J!', 'O!'], 24],
];
const out = [];
for (const [name, rank, pat, dx, note] of ROUTES.filter(r => !ONLY || ONLY.some(o => r[0].includes(o)))) {
  E('BW.log = []; BW.cap = 1e5');
  W().reset('bow', rank); arena(); W().reset('bow', rank);
  E('D.maxSt = 1e6; P.st = 1e6; P.bwLv = 1; P.bwSteps = 0; P.x = 160'); W().dummy(dx, { boss: true }); E('P.fp = D.maxFp; P.cds = {}'); E('window.__wm.follow = ' + dx);
  let i = 0, holding = null, t0 = null, upHeld = false;
  for (let f = 0; f < SECS * 60 + 900; f++) {
    if (holding) { holding.n++; if (E(`P.state === 'bw_draw' && P.bwDrawMs >= ${holding.draw}`) || holding.n > 200) { W().up('heavy'); holding = null; } }
    if (upHeld) { W().up('up'); upHeld = false; }
    E('P.st = 1e6; P.face = 1; if (P.x > 330) P.x -= 200; if (P.x < 90) P.x += 150');
    const p = pat[i % pat.length], neutral = typeof p === 'string' ? p.endsWith('!') : !!p.idle;
    const idle = E("['idle','run','land'].includes(P.state)");
    const free = idle || (!neutral && E(`(!!ATK[P.state] && !P.mvQ && P.mvT > (ATK[P.state].mv.commit && '${p}' === 'L' ? 240 : 40) && !ATK[P.state].mv.loop) || (P.state === 'roll' && P.dg && P.dg.t > 160 && !peek('roll'))`));
    if (!holding && free && (p === 'O!' || (p && p.art)) && (E("cdLeft('art', SAVE.art) > 0 || P.fp < ARTS[SAVE.art].fp"))) { if (pat.every(q => q === 'O!' || (q && q.art))) { W().frame(1); if (t0 !== null && W().ms - t0 >= SECS * 1000) break; continue; } i++; continue; }
    if (!holding && free && p && p.art) { W().down('art'); W().frame(p.art); W().up('art'); i++; if (t0 === null) { t0 = W().ms; W().log = []; E('BW.log = []'); } continue; }
    if (!holding && free) {
      const b = typeof p === 'string' ? p.replace('!', '') : 'H';
      if (b === 'O') { W().down('art'); W().frame(1); W().up('art'); i++; if (t0 === null) { t0 = W().ms; W().log = []; E('BW.log = []'); } continue; }
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

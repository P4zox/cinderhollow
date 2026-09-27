G.tp('DU16', 5, 3); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
const P = () => G.P; const out = [];
const zones = [[176, 205], [304, 42], [432, 250], [560, 84], [688, 214], [816, 92], [9999, 248]];
G.step(1, [], ['interact']); G.step(1);
const a0 = S.SYS.trial.attempts;
for (let i = 0; i < 1400; i++) {
  const p = P();
  let inp;
  if (i < 3 || (p.ground && p.y < 100)) inp = [['right'], []];
  else { const z = zones.find(z => p.y < z[0] - 2); const d = z[1] - p.x; inp = [(Math.abs(d) < 3 ? [] : d > 0 ? ['right'] : ['left']).concat(['jump']), []]; }
  G.step(1, inp[0], inp[1]);
  if (i % 20 === 0) out.push(i + ':' + p.state + ' ' + (p.x|0) + ',' + (p.y|0) + ' vy' + (p.vy|0));
  if (S.SYS.trial.attempts !== a0) { out.push('RESET at ' + i + ' ' + S.SYS.trial.why + ' last ' + (p.x|0) + ',' + (p.y|0)); break; }
}
return out;

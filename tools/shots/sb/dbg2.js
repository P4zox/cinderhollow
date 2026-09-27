G.tp('DU16', 5, 3); for (let i = 0; i < 6; i++) { G.step(20); settle(); }
const P = () => G.P; const out = [];
const B = [[12, 212], [20, 50], [28, 245], [36, 80], [44, 205], [52, 90]];
const tgt = y => { for (const [r, x] of B) if (y < (r + 1) * 16 + 28) return x; return 248; };
G.step(1, [], ['interact']); G.step(1);
const a0 = S.SYS.trial.attempts;
for (let i = 0; i < 1600; i++) {
  const p = P(); let inp;
  if (p.ground && p.y < 100) inp = [['right'], []];
  else { const d = tgt(p.y) - p.x; inp = [(Math.abs(d) < 3 ? [] : d > 0 ? ['right'] : ['left']).concat(['jump']), []]; }
  G.step(1, inp[0], inp[1]);
  if (i % 25 === 0) out.push(i + ':' + p.state + ' ' + (p.x|0) + ',' + (p.y|0));
  if (!S.SYS.trial) { out.push('DONE ' + JSON.stringify(S.SYS.result)); break; }
  if (S.SYS.trial.attempts !== a0) { out.push('RESET at ' + i + ' ' + S.SYS.trial.why + ' prev ' + (p.x|0) + ',' + (p.y|0)); break; }
}
return out;

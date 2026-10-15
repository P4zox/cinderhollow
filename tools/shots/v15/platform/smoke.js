// v15 platform smoke: every type equips, its light chain lands on a dummy
const out = [];
arena();
for (const t of E('WTYPES')) {
  W().reset(t, 1); E('P.face = 1'); W().dummy(26);
  for (let i = 0; i < 3; i++) { W().tap('attack', 2); W().frame(28); }
  W().frame(40);
  out.push(`${t}: weapon ${E('SAVE.weapon')} type ${E('wtype()')} hits ${W().log.length} states ${[...new Set(W().log.map(l => l.st))].join(',')}`);
}
return out;

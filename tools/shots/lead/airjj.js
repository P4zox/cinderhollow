const out = {};
for (const type of ['longsword', 'dual', 'staff', 'whip', 'maul']) for (const gap of [8, 20, 26]) {
  W().reset(type, 5); arena(); W().reset(type, 5); E('D.maxSt = 1e6; P.st = 1e6');
  W().tap('jump', 14); W().frame(2); W().tap('attack');
  for (let k = 0; k < 60; k++) { W().frame(1); if (E("!ATK[P.state]") ) break; }
  W().frame(gap > 20 ? 4 : 0);
  const s = []; W().tap('attack'); for (let k = 0; k < 50; k++) { W().frame(1); const x = E('P.state'); if (s[s.length - 1] !== x) s.push(x); }
  out[type + ' 2nd J ' + (gap > 20 ? '4f after' : 'right after')] = s.join(' ');
}
return out;

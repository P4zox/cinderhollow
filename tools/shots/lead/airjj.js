const out = {};
for (const type of ['longsword', 'dual', 'whip', 'staff', 'maul', 'katana', 'greatsword']) for (const [jf, d1, gap] of [[1, 4, 10], [1, 8, 18], [12, 14, 22]]) {
  W().reset(type, 5); arena(); W().reset(type, 5); E('D.maxSt = 1e6; P.st = 1e6');
  W().down('jump'); W().frame(jf); W().up('jump'); W().frame(Math.max(0, d1 - jf)); W().tap('attack'); W().frame(gap); W().tap('attack');
  const s = []; for (let k = 0; k < 90; k++) { W().frame(1); const x = E('P.state + (P.ground ? "_g" : "")'); if (s[s.length - 1] !== x) s.push(x); }
  out[`${type} jump${jf}f J@${d1} +${gap}`] = s.join(' ');
}
return out;

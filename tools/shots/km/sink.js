await boot();
const out = [];
G.tp('T1', 4, 16); G.step(5);
const o = G.KIT.objs.filter(q => q.kind === 'sinker')[0];
const P = G.P; P.x = (o.d.x0 + o.d.x1) / 2; P.y = o.d.y0; P.vx = P.vy = 0; P.ground = true;
for (let i = 0; i < 300; i++) { G.step(1); if (i % 10 == 0 && i > 60) out.push(`${i} P ${P.x.toFixed(1)},${P.y.toFixed(2)} g=${P.ground} s=${P.state} vy=${P.vy.toFixed(1)} d ${o.d.x0},${o.d.y0} sink=${o.sink.toFixed(2)}`); }
return out;

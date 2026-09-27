await boot(); const K = G.KIT, out = [];
G.tp('T1', 27, 56); G.step(3);
const sp = K.objs.find(q => q.kind === 'spring'); const P = G.P; P.x = sp.x; P.y = sp.d.y0; P.vx = P.vy = 0;
for (let i = 0; i < 40; i++) { G.step(1); out.push(i + ' y' + Math.round(P.y) + ' vy' + Math.round(P.vy) + ' ' + P.state + ' b' + (K.boost ? Math.round(K.boost.vy) : '-')); }
return out.join(' | ');

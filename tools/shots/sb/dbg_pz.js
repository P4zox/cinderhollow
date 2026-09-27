const K = G.KIT, out = []; G.SETTINGS.god = 1;
G.tp('NV12', 9, 10); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
out.push('start ' + (G.P.x|0) + ',' + (G.P.y|0) + ' ground ' + G.P.ground + ' b1 box ' + JSON.stringify(K.byId.b1.hurtbox()));
for (const fr of [2, 4, 6, 8, 10]) {
  G.P.x = 9 * 16 + 8; G.P.y = 176; G.step(20);
  G.step(1, ['jump'], ['jump']); let hitAt = -1, ys = [];
  for (let i = 0; i < 40; i++) { G.step(1, i < fr ? ['jump'] : [], i === fr ? ['attack'] : []); ys.push(G.P.y|0); if (K.byId.b1.flash > 0.9 && hitAt < 0) hitAt = i; }
  out.push('fr ' + fr + ' hit ' + hitAt + ' ys ' + ys.slice(0, 16).join(',') + ' state ' + G.P.state);
  G.step(40);
}
return out;

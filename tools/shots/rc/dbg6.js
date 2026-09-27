await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { crown: 1 }; const out = [];
G.tp('X9', 20, 16); G.step(120); const K = G.xrc.kit();
out.push('kit objs ' + K.objs.map(o => o.kind + (o.spec && o.spec.petal ? '(petal)' : '') + '@' + Math.round(o.x || 0) + ',' + Math.round(o.y || 0)).join(' '));
await snap('dbg_x9');
G.tp('X6', 30, 11); for (let i = 0; i < 10; i++) { G.step(25); out.push(G.state + ' hp' + Math.round(G.P.hp) + ' ' + G.P.state); }
await snap('dbg_x6');
return out;

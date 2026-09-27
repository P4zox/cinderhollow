await boot(); G.SAVE.seenAreas = { hoarfrost: 1 }; G.give({ items: { talon: 1, hook: 1, emberdash: 1 } }); G.SETTINGS.god = true;
const RB = window.__rb, sim = RB.sim, out = [];
G.tp('HF15', 14, 6); G.step(30);
sim(1, ['right', 'jump'], ['jump']);
for (let f = 1; f < 60; f++) { sim(1, f < 12 ? ['right', 'jump'] : ['right'], f === 16 ? ['roll'] : []); out.push(`${f} ${G.P.state} ${G.P.anim.tag}:${G.P.anim.i} x${(G.P.x/16).toFixed(2)} y${(G.P.y/16).toFixed(2)} ad ${G.P.airDash} st ${Math.round(G.P.st)}`); }
return out.filter((l, i) => i % 2 === 0);

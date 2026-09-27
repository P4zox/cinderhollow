await boot(); G.SAVE.seenAreas = { archives: 1 }; G.give({ items: { talon: 1, hook: 1 } }); G.SETTINGS.god = true;
const RB = window.__rb, sim = RB.sim, out = [], P = () => G.P;
G.tp('A15', 3, 28); G.step(30);
sim(1, ['right', 'jump'], ['jump']);
for (let f = 1; f < 60; f++) { sim(1, f < 6 ? ['right', 'jump'] : ['right'], f === 4 ? ['hook'] : []); if (P().hook && !P().hook.zip) { out.push('hooked at f' + f); break; } }
for (let f = 0; f < 70; f++) { sim(1, ['right']); if (f % 5 === 0) out.push(`pump ${f} x${(P().x/16).toFixed(1)} y${(P().y/16).toFixed(1)} av ${P().hook && P().hook.av.toFixed(2)} ang ${P().hook && P().hook.ang.toFixed(2)}`); }
sim(1, ['right', 'jump'], ['jump']);
for (let f = 1; f < 50; f++) { sim(1, ['right'], f === 10 ? ['hook'] : []); if (f % 3 === 0 || f === 10 || f === 11) out.push(`${f} ${P().state} x${(P().x/16).toFixed(1)} y${(P().y/16).toFixed(1)} vx ${Math.round(P().vx)} vy ${Math.round(P().vy)} hook ${P().hook ? (P().hook.h.x - 8) / 16 : '-'}`); }
return out;

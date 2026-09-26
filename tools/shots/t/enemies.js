await boot(); G.give({ items: { talon: 1 } });
const out = {};
G.tp('TV3', 45, 10); G.step(30); await snap('en_0');
let last = G.P.hp, hits = 0;
for (let i = 0; i < 8; i++) { for (let k = 0; k < 40; k++) { G.step(1, ['left'], k % 10 === 0 ? ['attack'] : []); if (G.P.hp < last) hits++; G.P.hp = 999; last = 999; } await snap('en_' + (i + 1)); }
out.hits = hits; out.enemies = G.step(1).enemies;
G.tp('TV5', 8, 23); G.step(60); await snap('en_tv5');
G.tp('TV2', 20, 10); for (let k = 0; k < 120; k++) { G.step(1, ['left']); G.P.hp = 999; } await snap('en_tv2');
return out;

await boot(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; const S = window.__sys, out = [];
G.tp('K12', 20, 38); G.step(10); G.step(1, [], ['interact']); G.step(5); const hp = G.P.hp;
out.push('trial on: ' + !!S.SYS.trial);
G.P.x = 21 * 16 + 8; G.P.y = 20 * 16; G.step(1); for (let i = 0; i < 60; i++) G.step(1, ['right']);
out.push(`after touching the wall spikes: attempts ${S.SYS.trial && S.SYS.trial.attempts}, hp ${G.P.hp}/${hp}, at ${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)}`);
return out;

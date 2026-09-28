await boot(); G.grantTechniques(); G.giveArmory(); G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1; G.SETTINGS.god = 1; const o = [];
const tryUp = (room, x, y, target) => { G.tp(room, x, y); for (let k = 0; k < 40 && G.room === room; k++) { G.step(2, ['up'], ['jump']); G.step(6, ['up']); } return G.room; };
const tryDir = (room, x, y, dir, target) => { G.tp(room, x, y); for (let k = 0; k < 60 && G.room === room; k++) { G.step(3, [dir], k % 8 === 0 ? ['jump'] : []); } return G.room; };
delete G.SAVE.flags['boss:executioners']; delete G.SAVE.flags['boss:pharaoh'];
o.push('NV10 summit -> Hollow Court, Executioners alive: ended in ' + tryUp('NV10', 43, 5));
o.push('DU10 Sea -> Sanctum chamber, Pharaoh alive: ended in ' + tryDir('DU10', 8, 12, 'left'));
G.SAVE.flags['boss:executioners'] = 1; G.SAVE.flags['boss:pharaoh'] = 1;
o.push('NV10 summit -> Hollow Court, Executioners dead: ended in ' + tryUp('NV10', 43, 5));
G.tp('DU10', 8, 12); G.step(10); let r = 'DU10';
for (let k = 0; k < 60 && G.room === 'DU10'; k++) { G.step(3, ['left'], k % 6 === 0 ? ['jump'] : []); if (G.P.x < 5 * 16) { G.step(3, ['up'], ['jump']); } }
o.push('DU10 -> chamber/lobby, Pharaoh dead: x now ' + Math.round(G.P.x) + ' in ' + G.room + ' (chamber is x<80)');
return o;

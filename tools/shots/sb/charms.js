const out = []; G.SAVE.charms.push('c_x3_hood', 'c_x3_scarab');
G.SAVE.charmsEq = ['c_x3_hood', 'c_x3_scarab'];
// Scarab Wing: fall from high, no 'land' pose
G.tp('NV10', 14, 7); for (let i = 0; i < 4; i++) { G.step(10); settle(); } G.enemies.length = 0;
G.P.x = 14 * 16; G.P.y = 20 * 16; G.P.vy = 0; const states = new Set();
for (let i = 0; i < 120; i++) { G.step(1); states.add(G.P.state); }
out.push('scarab: states while falling/landing ' + [...states].join(','));
G.SAVE.charmsEq = ['c_x3_hood'];
G.P.x = 14 * 16; G.P.y = 20 * 16; G.P.vy = 0; states.clear();
for (let i = 0; i < 120; i++) { G.step(1); states.add(G.P.state); }
out.push('without it: ' + [...states].join(','));
// Headsman's Hood: a blow soaked in the first instants of a roll stalls time; a late one does not
G.tp('NV8', 30, 10); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
const hp0 = G.P.hp; G.step(1, ['left'], ['roll']); G.step(3); const i1 = G.P.anim.i; G.sbHurt(20); const early = G.sb.hoodT > 0;
for (let i = 0; i < 260; i++) G.step(1);
G.step(1, ['left'], ['roll']); G.step(11); const i2 = G.P.anim.i; G.sbHurt(20); const late = G.sb.hoodT > 0 && G.sb.hoodCd > 2.9;
out.push('hood: early roll (frame ' + i1 + ') fired ' + early + ' · late roll (frame ' + i2 + ') fired ' + late + ' · hp ' + G.P.hp + '/' + hp0);
return out;

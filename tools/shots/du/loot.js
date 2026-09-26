await boot(); G.grantTechniques(); const o = [];
const pos = () => [G.room, Math.round(G.P.x/16*10)/10, Math.round(G.P.y/16*10)/10, G.P.state].join(' ');
const kill = () => { for (const e of G.enemies) if (e.alive) { e.hp = 0; e.state = 'dead'; } };
const items = () => G.props.filter(p => p.type === 'item').length;
// DU3: the palm (c_scarab) via the basin thermal
G.tp('DU3', 37, 18); kill(); G.step(10); const n0 = items();
G.step(1, ['right'], ['jump']);
for (let i = 0; i < 300; i++) { kill(); const inT = G.P.x > 38*16 && G.P.x < 40*16; const over = G.P.x > 40.6*16 && G.P.x < 43*16; const k = over ? [] : G.P.y > 9*16 ? (inT ? ['jump'] : ['jump', G.P.x < 38.5*16 ? 'right' : 'left']) : ['jump', 'right']; G.step(1, k); if (G.P.ground && i > 20) break; }
o.push('palm ' + pos()); G.step(1, [], ['interact']); G.step(30); o.push('DU3 items ' + n0 + ' -> ' + items() + ' c_scarab=' + G.SAVE.charms.includes('c_scarab'));
// DU5 gallery (sp:sunbeam)
G.tp('DU5', 34, 8); kill(); G.step(5); G.step(1, ['right'], ['jump']); for (let i=0;i<30;i++) G.step(1, ['jump', 'right']); G.step(20);
o.push('gallery ' + pos()); G.step(40, ['right']); o.push('sunbeam=' + G.SAVE.spellsOwned.includes('sunbeam'));
// DU6 platform
G.SAVE.flags['boss:scarab'] = 1; G.tp('DU6', 17, 11); G.step(5); G.step(1, ['right'], ['jump']); for (let i=0;i<30;i++) G.step(1, ['jump', 'right']); G.step(20); o.push('du6 plat ' + pos() + ' stones=' + JSON.stringify(G.SAVE.inv));
// DU1 lintel via thermal 2 from the east ledge
G.tp('DU1', 39, 10); G.step(5); G.P.face = -1; G.step(1, ['left'], ['jump']);
for (let i = 0; i < 400; i++) { const inT = G.P.x > 31*16 && G.P.x < 33*16; const k = G.P.y > 4*16 ? (inT ? ['jump'] : ['jump', 'left']) : ['jump', 'right']; G.step(1, k); if (G.P.ground && i > 20) break; }
o.push('lintel ' + pos() + ' stones=' + JSON.stringify(G.SAVE.inv));
return o;

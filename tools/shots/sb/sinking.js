const out = []; G.SAVE.items.gale = 0; const hp0 = 9999;
const st = (h = [], t = []) => { G.step(1, h, t); };
const hop = (tx, hold = 26) => { st(['right', 'jump'], ['jump']); for (let i = 0; i < 100; i++) { const d = tx - G.P.x; st((Math.abs(d) < 3 ? [] : d > 0 ? ['right'] : ['left']).concat(i < hold ? ['jump'] : [])); if (G.P.ground && i > 3) break; } };
const log = n => out.push(n + ' at ' + (G.P.x / 16).toFixed(1) + ',' + (G.P.y / 16).toFixed(2) + ' g ' + G.P.ground + ' hp ' + Math.round(G.P.hp));
G.tp('DU12', 11, 11); for (let i = 0; i < 3; i++) { G.step(10); settle(); } G.enemies.length = 0; G.P.hp = hp0;
for (let i = 0; i < 40 && G.P.x < 13 * 16 + 4; i++) st(['right']);
for (const [tx, name] of [[16 * 16, 'sinker1'], [20 * 16, 'sinker2'], [25 * 16, 'pillar1'], [29 * 16, 'crumble'], [33 * 16, 'sinker3'], [37 * 16, 'pillar2'], [41 * 16, 'sinker4'], [44 * 16, 'crumble2'], [48 * 16, 'east landing']]) { hop(tx); log(name); }
out.push('hp ' + Math.round(G.P.hp) + '/' + hp0 + ' (swallowed = lost hp)');
for (let i = 0; i < 40 && G.P.x < 51 * 16; i++) st(['right']);
for (let i = 0; i < 90 && G.room === 'DU12'; i++) st(['down', 'jump'], i % 8 === 0 ? ['jump'] : []);
out.push('-> ' + G.room);
return out;

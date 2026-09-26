await boot();
const D = window.__db; window.__dbLog = [];
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.seenAreas = { barrows: 1 };
const out = [];
const st = () => { const b = G.boss; const B = D.DBW.boat; return { b: b ? [b.state, b.atk, Math.round(b.x), Math.round(b.y), b.hp, b.phase] : null, boat: B && [Math.round(B.x), Math.round(B.v)], p: [Math.round(G.P.x), Math.round(G.P.y), G.P.state, G.P.ground], cut: G.state }; };
G.tp('DB5', 3, 4); G.step(10); out.push(['shore', st()]); await snap('f00');
G.step(40, ['right']); out.push(['to jetty', st()]);
G.step(30, ['right']); out.push(['board?', st()]);
for (let i = 0; i < 12 && G.state === 'cut'; i++) { G.step(40); if (i == 2) await snap('f01_cut'); }
out.push(['post cut', st()]);
await snap('f02');
for (let i = 0; i < 30; i++) { G.step(20); G.P.hp = G.D.maxHp; if (i % 6 == 0) { out.push(['t' + i, st()]); await snap('f1_' + i); } }
const tally = {}; for (const h of window.__dbLog) tally[h[1]] = (tally[h[1]] || 0) + 1;
out.push(['hits', window.__dbLog.length, tally]);
const b = G.boss; b.hp = Math.round(b.maxHp * 0.49); b.hit({ dmg: 10, poise: 0, dir: 1, kind: 'light', x: b.x, y: b.y - 40 });
for (let i = 0; i < 30; i++) { G.step(20); G.P.hp = G.D.maxHp; if (i % 6 == 0) { out.push(['p2 t' + i, st()]); await snap('f2_' + i); } }
b.hp = 5; b.hit({ dmg: 50, poise: 0, dir: 1, kind: 'light', x: b.x, y: b.y - 40 });
await new Promise(r => setTimeout(r, 6000)); G.step(200);
out.push(['dead', st(), G.SAVE.flags['boss:ferryman'], JSON.stringify(G.SAVE.weapons), G.SAVE.inv, G.props.filter(p => p.type === 'fog').map(p => p.on())]);
// ferry ride after the fight
G.tp('DB5', 8, 7); G.step(20);
const B = D.DBW.boat; G.P.x = B.x; G.P.y = B.deck - 20; G.step(30); out.push(['on boat', st()]);
G.step(600); out.push(['ferried', st()]);
await snap('f3_ferried');
return out;

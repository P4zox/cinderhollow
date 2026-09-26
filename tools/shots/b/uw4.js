await boot();
const D = window.__db;
G.give({ items: { hook: 1, talon: 1, tidebreath: 1 } });
G.SAVE.seenAreas = { barrows: 1 };
const out = [];
// cutscene plays once
G.tp('DB6', 1, 6); G.step(30, ['right']); let cut1 = G.state; for (let i = 0; i < 40 && G.state === 'cut'; i++) G.step(20); out.push(['first entry', cut1, G.state]);
G.tp('DB9', 12, 6); G.step(5); G.tp('DB6', 1, 6); G.step(30, ['right']); out.push(['second entry', G.state]);
const b = D.choir(); window.__dbLog = [];
// seal slam hits near the surface
G.P.x = 300; G.P.y = 112 + 30; b.begin('seal');
for (let i = 0; i < 150 && !D.DBW.seal; i++) { G.step(2); G.P.x = b.sealX > 320 ? 200 : 440; G.P.y = 112 + 30; G.P.vx = G.P.vy = 0; }
out.push(['seal slam near surface hits', window.__dbLog.map(h => h[1])]);
D.DBW.seal && (D.DBW.seal.t = 99); G.step(5);
// clamp: sample the spine for 2000 frames of free AI + forced breaches
let bad = 0, out_ = 0, n = 0;
D.SETTINGS.god = true;
for (let i = 0; i < 1000; i++) { G.step(2); if (i % 200 === 0) b.begin('seal'); for (const p of b.spine) { n++; if (D.solidAt(p.x, p.y)) bad++; if (p.x < 32 || p.x > 608 || p.y < 32 || p.y > 320) out_++; } }
out.push(['spine samples', n, 'in solid', bad, 'outside pool', out_]);
// phase 2
b.hp = Math.round(b.maxHp * 0.49); b.parts[0].hit({ dmg: 10, poise: 0, dir: 1, kind: 'light', x: b.H.x, y: b.H.y, melee: true });
for (let i = 0; i < 30; i++) { G.step(20); if (G.state !== 'cut' && i > 3) break; }
out.push(['p2', b.phase, b.speed, (D.DBW.wraiths || []).length, G.state]);
for (let i = 0; i < 8; i++) { G.step(40); await snap('p2_' + i); }
// death
b.hp = 5; b.parts[1].hit({ dmg: 50, poise: 0, dir: 1, kind: 'light', x: b.spine[5].x, y: b.spine[5].y, melee: true });
await new Promise(r => setTimeout(r, 11000)); G.step(400);
out.push(['dead', G.SAVE.flags['boss:choir'], JSON.stringify(G.SAVE.weapons), G.SAVE.charms, G.SAVE.spellsOwned, !!D.DBW.seal, G.props.filter(p => p.type === 'fog').map(p => p.on())]);
// exit east: swim up and out
D.SETTINGS.god = false;
G.P.x = 590; G.P.y = 150; for (let i = 0; i < 30; i++) G.step(4, ['right', 'up']); for (let i = 0; i < 6; i++) G.step(6, ['right'], ['jump']); G.step(60, ['right']);
out.push(['exit', G.room, Math.round(G.P.x), Math.round(G.P.y)]);
return out;

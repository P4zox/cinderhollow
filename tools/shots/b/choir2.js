await boot();
const D = window.__db; window.__dbLog = [];
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.flags['cut:choir'] = 1; G.SAVE.seenAreas = { barrows: 1 };
const out = [];
const st = () => { const b = D.choir(); return b ? { bs: b.bs, hp: b.hp, ph: b.phase, tide: Math.round(D.DBW.tide.y), hx: Math.round(b.spine[0].x), hy: Math.round(b.spine[0].y), p: [Math.round(G.P.x), Math.round(G.P.y), G.P.state, Math.round(G.P.hp)], wr: (D.DBW.wraiths||[]).length } : { none: true }; };
G.tp('DB6', 22, 10); G.step(5);   // on the mid platform (row 11)
G.step(30, ['right']);
out.push(['start', st()]);
// passive player, no god: 40 s of AI, record hits
D.SETTINGS.god = true;
for (let i = 0; i < 20; i++) { G.step(120); out.push(['t' + i, st()]); if (i % 4 == 0) await snap('d_p1_' + i); }
out.push(['hits p1', window.__dbLog.length, window.__dbLog.slice(0, 30)]);
window.__dbLog = [];
// knock it to phase 2
const b = D.choir();
b.hp = Math.round(b.maxHp * 0.52); b.parts[0].hit({ dmg: 100, poise: 0, dir: 1, kind: 'light', x: b.spine[0].x, y: b.spine[0].y, melee: true });
for (let i = 0; i < 20; i++) { G.step(120); out.push(['p2 t' + i, st()]); if (i % 4 == 0) await snap('d_p2_' + i); }
out.push(['hits p2', window.__dbLog.length, window.__dbLog.slice(0, 30)]);
// kill
b.hp = 10; b.parts[1].hit({ dmg: 200, poise: 0, dir: 1, kind: 'light', x: b.spine[5].x, y: b.spine[5].y, melee: true });
for (let i = 0; i < 6; i++) { G.step(60); await snap('d_death_' + i); }
await new Promise(r => setTimeout(r, 13000)); G.step(600);
out.push(['after', st(), G.SAVE.flags['boss:choir'], G.SAVE.items.tidebreath, JSON.stringify(G.SAVE.weapons), G.SAVE.charms, G.SAVE.spellsOwned, Math.round(D.DBW.tide.y)]);
out.push(['fog', G.props.filter(p => p.type === 'fog').map(p => p.on())]);
await snap('d_after');
return out;

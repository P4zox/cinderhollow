await boot();
const D = window.__db; window.__dbLog = [];
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.seenAreas = { barrows: 1 };
const out = [];
const st = () => { const b = D.choir(); return b ? { bs: b.bs, hp: b.hp, ph: b.phase, h: [Math.round(b.spine[0].x), Math.round(b.spine[0].y)], seal: D.DBW.seal ? (D.DBW.seal.on ? 'ON' : 'forming') : '-', p: [Math.round(G.P.x), Math.round(G.P.y), G.P.state, Math.round(G.P.hp), +D.DBS.breath.toFixed(1)], st: G.state } : { none: true, room: G.room, st: G.state, items: G.SAVE.items.tidebreath }; };
// the reliquary: take the relic
G.tp('DB9', 4, 15); G.step(10); out.push(['reliquary', st()]); await snap('u00_reliq');
G.tp('DB9', 12, 6); G.step(30); out.push(['relic taken', G.SAVE.items.tidebreath]); await snap('u01_relic');
G.step(20, ['right']); G.step(60, ['right']); out.push(['into arena', st()]);
for (let i = 0; i < 30 && G.state === 'cut'; i++) { G.step(30); if (i % 3 == 0) await snap('u02_cut' + i); }
out.push(['after cut', st()]);
D.SETTINGS.god = true;
for (const m of ['bite', 'sweep', 'tail', 'coil', 'wail', 'bile', 'whirl', 'sonar', 'seal']) {
  const b = D.choir(); b.begin(m);
  for (let k = 0; k < 6; k++) { G.step(20); await snap(`u_${m}_${k}`); }
  out.push([m, st()]); G.step(90);
}
return out;

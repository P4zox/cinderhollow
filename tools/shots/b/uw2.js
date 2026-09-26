await boot();
const D = window.__db; window.__dbLog = [];
G.give({ items: { hook: 1, talon: 1 } });
G.SAVE.seenAreas = { barrows: 1 }; G.SAVE.flags['cut:choir'] = 1;
const out = [];
const st = () => { const b = D.choir(); return b ? { bs: b.bs, hp: b.hp, ph: b.phase, h: [Math.round(b.spine[0].x), Math.round(b.spine[0].y)], seal: D.DBW.seal ? (D.DBW.seal.on ? 'ON' : 'forming') : '-', p: [Math.round(G.P.x), Math.round(G.P.y), G.P.state, Math.round(G.P.hp), +D.DBS.breath.toFixed(1)] } : { none: true }; };
G.tp('DB9', 12, 6); G.step(30); out.push(['relic', G.SAVE.items.tidebreath, G.SAVE.flags.dbBreathScene]);
G.tp('DB6', 10, 11); G.step(20); out.push(['in pool', st()]);
D.SETTINGS.god = true;
const b = D.choir(); b.begin('seal');
for (let k = 0; k < 12; k++) { G.step(15, ['up']); await snap(`s_seal_${String(k).padStart(2,'0')}`); out.push(['seal', st()]); }
// try to surface: blocked
G.step(60, ['up']); out.push(['pressed up under seal', st(), D.DBS.headIn]);
// swim to the bell and strike it
for (let i = 0; i < 200; i++) {
  const bell = G.props.find(p => p.type === 'db_bell');
  const dx = bell.x - G.P.x, dy = (bell.y + 36) - G.P.y;
  const hold = []; if (Math.abs(dx) > 22) hold.push(dx > 0 ? 'right' : 'left'); if (Math.abs(dy) > 6) hold.push(dy > 0 ? 'down' : 'up');
  G.step(3, hold, Math.abs(dx) < 30 && Math.abs(dy) < 16 ? ['attack'] : []);
  if (!D.DBW.seal) { out.push(['bell struck after frames', i * 3, st()]); break; }
}
await snap('s_broken');
G.step(40, ['up']); out.push(['surfaced', st(), D.DBS.headIn]);
await snap('s_surfaced');
return out;

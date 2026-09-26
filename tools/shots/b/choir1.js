await boot();
window.__db.SETTINGS.god = true;
G.give({ items: { hook: 1, talon: 1 } });
const out = [];
const B = () => window.__db.choir();
const st = () => { const b = B(); return b ? { bs: b.bs, st: b.state, hp: b.hp, ph: b.phase, hx: Math.round(b.spine[0].x), hy: Math.round(b.spine[0].y), tide: Math.round(window.__db.DBW.tide.y), cut: G.state, p: [Math.round(G.P.x), Math.round(G.P.y), G.P.state] } : { none: true, room: G.room, st: G.state }; };
G.tp('DB6', 3, 15); G.step(10);
out.push(['enter', st()]);
await snap('c00_enter');
G.step(80, ['right']); out.push(['walk in', st()]);
for (let i = 0; i < 12; i++) { G.step(40); if (i % 3 == 0) await snap('c01_cut' + i); out.push(['cut', st()]); if (G.state === 'play') break; }
out.push(['after cut', st()]);
for (const m of ['bite', 'breach', 'sweep', 'wail', 'bile', 'song']) {
  const b = B(); b.begin(m); 
  for (let k = 0; k < 6; k++) { G.step(22); await snap(`c_${m}_${k}`); }
  out.push([m, st()]);
  G.step(60);
}
return out;

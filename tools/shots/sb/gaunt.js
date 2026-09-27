const S = window.__sys, out = []; G.SETTINGS.god = 1;
const run = async (room, x, y, gid, gate, tag) => {
  G.tp(room, x, y); for (let i = 0; i < 4; i++) { G.step(15); settle(); }
  const gstate = () => { const d = S.roomObj.dyn.find(q => q.kit && q.kit.id === gate); return d ? (d.y1 - d.y0 > 8 ? 'closed' : 'open') : 'none'; };
  out.push(tag + ' before: gate ' + gstate());
  G.step(1, [], ['interact']); G.step(90); out.push(tag + ' started ' + !!S.SYS.gaunt + ' gate ' + gstate());
  let waves = 0;
  for (let w = 0; w < 6 && S.SYS.gaunt; w++) {
    for (let i = 0; i < 300 && S.SYS.gaunt && S.SYS.gaunt.state !== 'wave'; i++) G.step(1);
    for (let i = 0; i < 90; i++) G.step(1);
    const alive = G.enemies.filter(e => e.alive && e.x3g);
    if (w === 1 || w === 3) await snap(tag + '_wave' + (w + 1));
    out.push(tag + ' wave ' + (S.SYS.gaunt && S.SYS.gaunt.wave + 1) + ': ' + alive.map(e => e.type).join(','));
    for (const e of alive) e.die({ dir: 1 }); waves++;
    for (let i = 0; i < 90; i++) G.step(1);
  }
  for (let i = 0; i < 300; i++) G.step(1);
  out.push(tag + ' after: running ' + !!S.SYS.gaunt + ' gate ' + gstate() + ' flag ' + G.SAVE.flags['x3:' + room + ':' + gid] + ' emberstones ' + (G.SAVE.inv.emberstone || 0));
};
await run('NV13', 26, 12, 'legion', 'gY', 'legion');
await run('NV14', 30, 10, 'charnel', 'gB', 'charnel');
return out;

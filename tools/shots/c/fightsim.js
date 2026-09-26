// let each boss fight a passive, immortal player for a while at various positions: no errors, stays inside the arena
await boot();
const log = {};
for (const [room, kind, tx] of [['CM6', 'butler', 4], ['CM7', 'sanguine', 4]]) {
  G.SAVE.flags['cut:' + kind] = 1; G.SAVE.flags['cutp2:' + kind] = 1;
  G.tp(room, tx, room === 'CM7' ? 14 : 9); G.step(20, ['right']);
  const B = G.boss; let mn = 1e9, mx = -1e9, mnY = 1e9, states = {}, dmg = 0;
  for (let k = 0; k < 3600; k++) {
    const hp = G.P.hp; G.step(1); dmg += Math.max(0, hp - G.P.hp); G.P.hp = G.D.maxHp;
    if (k === 1800) B.hp = Math.floor(B.maxHp * 0.45);
    if (k % 600 === 0) G.P.x = [60, 300, 600, 200, 500, 100][k / 600 % 6] * (room === 'CM6' ? 0.6 : 1);
    mn = Math.min(mn, B.x); mx = Math.max(mx, B.x); mnY = Math.min(mnY, B.y); states[B.state] = (states[B.state] || 0) + 1;
    if (G.state !== 'play') G.step(1, [], ['pause']);
  }
  log[kind] = { minX: Math.round(mn), maxX: Math.round(mx), L: B.L, R: B.R, minY: Math.round(mnY), floor: B.floor, phase: B.phase, dmg: Math.round(dmg), states };
}
return log;

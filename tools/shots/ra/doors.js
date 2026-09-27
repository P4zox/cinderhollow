// doors both ways, the one-way shortcuts (lift lock, gates), and the breakable walls
await boot(); G.grantTechniques(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; G.SETTINGS.god = true;
const out = [], K = G.KIT;
const use = (r, x, y) => { G.tp(r, x, y); G.step(10); G.step(1, [], ['interact']); for (let i = 0; i < 90 && G.room === r; i++) G.step(1); G.step(30); return G.room + '@' + (G.P.x / 16).toFixed(1) + ',' + (G.P.y / 16 - 1).toFixed(1) + (G.P.ground ? ' ground' : ' AIR'); };
for (const [r, x, y] of [['R2', 27, 10], ['R5', 121, 11], ['R1', 6, 10], ['R8', 40, 11], ['C1', 15, 24], ['C7', 43, 10], ['C4', 10, 10], ['C10', 41, 10], ['K1', 41, 10], ['K5', 3, 10], ['K3', 13, 24], ['K8', 3, 10]])
  out.push(`door ${r}(${x},${y}) -> ${use(r, x, y)}`);
// the Undercroft lift: locked from below, free once the winch lever is struck
G.tp('R8', 21, 11); G.step(30); const y0 = G.P.y; G.step(120); out.push(`lift locked: moved ${Math.round(G.P.y - y0)} px (want 0)`);
G.tp('R8', 25, 6); G.step(10); G.step(1, [], ['interact']); G.step(20); out.push('winch lever on: ' + K.byId.winch.active);
G.tp('R8', 21, 11); G.step(10); const y1 = G.P.y; G.step(150); out.push(`lift free: moved ${Math.round(G.P.y - y1)} px (want about -80)`);
// the one-way gates: closed from the far side until the lever inside is struck
for (const [r, lv, gt, lx, ly] of [['C10', 'glv', 'gt', 33, 10], ['K8', 'klv', 'gk', 10, 10]]) {
  G.tp(r, lx, ly); G.step(10); const before = G.KIT.byId[gt].on; G.step(1, [], ['interact']); G.step(60);
  out.push(`${r} gate ${gt}: before ${before}, after lever ${G.KIT.byId[gt].on}; persisted ${!!G.SAVE.flags['x3:' + r + ':' + gt]}`);
}
// breakable walls: R5's cracked wall, C10's false tomb, K7's altar wall
for (const [r, x, y, dir, want] of [['R5', 97, 18, 'right', 'R14'], ['C10', 45, 10, 'right', 'C14'], ['K7', 2, 27, 'left', 'K13']]) {
  G.tp(r, x, y); G.step(10); for (let i = 0; i < 12; i++) { G.step(1, [dir], ['attack']); G.step(14, [dir]); }
  let got = null; for (let i = 0; i < 240 && !got; i++) { G.step(1, [dir]); if (G.room !== r) got = G.room; if (r === 'R5' && G.P.x / 16 > 101.5 && G.P.x / 16 < 105) G.step(40); }
  out.push(`${r} broken wall -> ${got} (want ${want})`);
}
return out;

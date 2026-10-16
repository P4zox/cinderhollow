// AREA look pass: every forge room from a few spots (no enemies), snapshots for review. Prepend nothing: run with shot.js
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1, wings: 1, hook: 1 });
G.SAVE.flags['boss:hearthkeeper'] = 1;
const SPOTS = window.__cfSpots || [['E6', 25, 14], ['CF1', 6, 16], ['CF1', 30, 9], ['CF2', 10, 6], ['CF2', 45, 5], ['CF3', 3, 6], ['CF3', 14, 26], ['CF3', 8, 42], ['CF3', 20, 60],
  ['CF4', 80, 11], ['CF4', 60, 11], ['CF4', 30, 7], ['CF4', 6, 9], ['CF9', 20, 9], ['CF5', 22, 5], ['CF5', 45, 14], ['CF5', 72, 14], ['CF10', 30, 7],
  ['CF6', 4, 9], ['CF6', 20, 15], ['CF6', 45, 15], ['CF6', 70, 15], ['CF13', 20, 11], ['CF7', 10, 15], ['CF7', 30, 15], ['CF12', 10, 20], ['CF12', 38, 25], ['CF11', 14, 15],
  ['CF8', 10, 17], ['CF8', 35, 17], ['CT1', 10, 13], ['CT1', 30, 13], ['CT2', 20, 31], ['CT2', 60, 31], ['CT2', 80, 31]];
const out = [];
for (const [r, x, y] of SPOTS) {
  try {
    G.tp(r, x, y); for (let i = 0; i < 90; i++) { G.step(1); if (!window.__keepFoes) G.enemies.length = 0; if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']); }
    if (G.boss && G.boss.alive) { /* leave the boss dormant */ }
    if (G.xs) G.xs.clean();
    G.step(2); await snap(`look_${r}_${x}_${y}`); out.push(`${r} ${x},${y} ok room=${G.room}`);
  } catch (e) { out.push(`${r} ERR ${e.message}`); }
}
return out;

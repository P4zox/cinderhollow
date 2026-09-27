// the three trial charms: Moonlit Stride (apex hang + run speed), Glitch Driver (longer air dash + cutting afterimages), First Flame (cooldowns)
await boot(); G.grantTechniques(); const out = [];
G.tp('NH11', 66, 14); G.step(30); for (const e of G.enemies) { e.hp = 0; e.die({ dir: 1 }); }
const runSpeed = () => { G.tp('NH11', 66, 14); G.step(5); G.step(40, ['right']); const x0 = G.P.x; G.step(30, ['right']); return ((G.P.x - x0) / 0.5).toFixed(1); };
const airTime = () => { G.tp('NH11', 70, 14); G.step(20); G.step(1, ['jump'], ['jump']); let n = 0; while (!G.P.ground && n < 200) { G.step(1, ['jump']); n++; } return n; };
const dashLen = () => { G.tp('NH11', 66, 14); G.step(20); G.step(1, ['right', 'jump'], ['jump']); G.step(8, ['right', 'jump']); const x0 = G.P.x; G.step(1, ['right'], ['roll']); G.step(30, ['right']); return ((G.P.x - x0) / 16).toFixed(2); };
out.push(`base: run ${runSpeed()} px/s, air ${airTime()} frames, dash+30f ${dashLen()} tiles`);
G.SAVE.charms.push('c_x3_moon', 'c_x3_glitch', 'c_x3_flame'); G.SAVE.charmSlots = 6; G.SAVE.charmsEq = ['c_x3_moon'];
out.push(`moon: run ${runSpeed()} px/s, air ${airTime()} frames`);
G.SAVE.charmsEq = ['c_x3_glitch'];
out.push(`glitch: dash+30f ${dashLen()} tiles, glitch projectiles seen ${window.__game.xs ? 'yes' : '?'}`);
G.SAVE.charmsEq = [];

return out;

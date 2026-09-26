await boot(); G.give({ items: { talon: 1 } });
const out = { snaps: [] };
G.tp('TV4', 31, 10); G.step(5);
let sawCut = false;
for (let i = 0; i < 120; i++) { G.step(2, ['left']); if (G.state === 'cut') { sawCut = true; break; } }
out.cut = sawCut; await snap('cv_00_cut');
for (let i = 0; i < 40 && G.state === 'cut'; i++) { G.step(12); if (i === 6) await snap('cv_01_cut'); }
out.afterCut = G.state; out.bossActive = G.boss && G.boss.active;
// fight: let them attack for a while, logging hits taken
let hits = 0, lastHp = G.P.hp, frames = 0, xs = [];
for (let i = 0; i < 900; i++) {
  const hold = []; const tap = [];
  if (i % 50 < 25) hold.push('right'); else hold.push('left');
  G.step(1, hold, tap); frames++;
  if (G.P.hp < lastHp) hits++;
  G.P.hp = 999; lastHp = 999;
  for (const q of G.boss.parts) xs.push(q.x);
  if (i % 150 === 75) await snap('cv_fight_' + i);
}
out.hitsTaken = hits;
out.witchX = [Math.min(...xs) / 16, Math.max(...xs) / 16].map(v => +v.toFixed(2));
// edge test: pin the player at each fog wall and force blinks and strikes
for (const px of [2.6, 33.4]) for (let k = 0; k < 6; k++) {
  for (const q of G.boss.parts) if (q.alive) { q.state = 'idle'; q.cool = 0; q.start(k % 2 ? 'blink' : 'strike'); }
  for (let i = 0; i < 80; i++) { G.P.x = px * 16; G.P.hp = 999; G.step(1); for (const q of G.boss.parts) xs.push(q.x); }
}
out.witchXedge = [Math.min(...xs) / 16, Math.max(...xs) / 16].map(v => +v.toFixed(2));
// can the player leave while it lives?  (west = exit fog, east = entry fog)
G.P.x = 2.2 * 16; G.step(60, ['left']); out.roomWhileAlive = G.room;
// kill them one by one
for (const q of G.boss.parts) { q.hit({ dmg: 9999, poise: 0, dir: 1, kind: 'light', x: q.x, y: q.y - 20 }); G.step(30); await snap('cv_kill_' + q.idx); }
G.step(400);
out.flag = !!G.SAVE.flags['boss:coven']; out.bossState = G.boss && G.boss.state;
out.spells = G.SAVE.spellsOwned; out.inv = G.SAVE.inv;
G.P.x = 2 * 16; G.step(90, ['left']); out.roomAfter = G.room;
return out;

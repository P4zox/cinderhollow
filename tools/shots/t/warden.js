await boot(); G.give({ items: { talon: 1 } });
const out = {}; const sleep = ms => new Promise(r => setTimeout(r, ms));
G.tp('TV8', 5, 10); G.step(5);
let sawCut = false;
for (let i = 0; i < 200; i++) { G.step(2, ['right']); if (G.state === 'cut') { sawCut = true; break; } }
out.cut = sawCut;
for (let i = 0, k = 0; i < 60 && G.state === 'cut'; i++) { G.step(10); if (i % 8 === 2) await snap('wd_cut_' + (k++)); }
out.after = G.state;
const b = G.boss; out.active = b.active;
const hitsBy = {};
let last = G.P.hp;
function tick(n, tag) { for (let i = 0; i < n; i++) { G.step(1); if (G.P.hp < last) hitsBy[tag] = (hitsBy[tag] || 0) + 1; G.P.hp = 999; last = 999; G.P.inv = 0; } }
// force each move with the player in range and snapshot the active frames
const moves = [['sweep', 60], ['thrust', 90], ['erupt', 110], ['volley', 150], ['summon', 120], ['charge', 180], ['sink', 90]];
for (const [m, dist] of moves) {
  b.x = 20 * 16; b.state = 'idle'; b.cool = 99; G.P.x = b.x + dist; G.P.y = 176; G.step(2);
  b.face = 1; b.begin(m);
  for (let i = 0; i < 150; i++) { tick(1, m); if (i === 20 || i === 45 || i === 70) await snap(`wd_${m}_${i}`); if (b.state === 'idle') break; }
  b.cool = 99;
}
out.hitsBy = hitsBy;
// dodge check: roll through a sweep (i-frames) -> should not be hit
// phase 2
b.hit({ dmg: b.hp - b.maxHp * 0.49, poise: 0, dir: -1, kind: 'light', x: b.x, y: b.y - 50 });
b.cool = 0; for (let i = 0; i < 300 && G.state !== 'cut'; i++) { tick(1, 'p2wait'); }
out.p2cut = G.state === 'cut';
for (let i = 0; i < 40 && G.state === 'cut'; i++) { G.step(10); if (i === 3) await snap('wd_p2_cut'); }
tick(60, 'p2'); out.phase = b.phase;
for (let i = 0; i < 6; i++) { tick(90, 'p2'); await snap('wd_p2_' + i); }
// edge tests: pin player at each end, force charge / sink / thrust
const xs = [];
for (const px of [3.4, 46.4]) for (const m of ['charge', 'sink', 'thrust', 'charge', 'sink']) {
  b.state = 'idle'; b.cool = 99; b.x = px < 10 ? 10 * 16 : 38 * 16; b.facePlayer(); b.begin(m);
  for (let i = 0; i < 200; i++) { G.P.x = px * 16; G.P.y = 176; tick(1, 'edge'); xs.push(b.x); if (b.state === 'idle') break; }
}
out.edgeX = [Math.min(...xs) / 16, Math.max(...xs) / 16].map(v => +v.toFixed(2)); out.LR = [b.L / 16, b.R / 16];
out.hitsBy = hitsBy;
// can't leave while it lives
G.P.x = 3.5 * 16; b.state = 'idle'; b.cool = 99; b.x = 30 * 16; G.step(90, ['left']); out.roomWhileAlive = G.room;
// death
b.hit({ dmg: 99999, poise: 0, dir: -1, kind: 'light', x: b.x, y: b.y - 50 });
for (let i = 0; i < 8; i++) { G.step(30); if (i % 3 === 1) await snap('wd_death_' + i); }
await sleep(9000); G.step(30);
out.flag = !!G.SAVE.flags['boss:warden']; out.shards = G.SAVE.shards; out.charms = G.SAVE.charms;
G.P.x = 4 * 16; G.step(90, ['left']); out.roomAfter = G.room;
return out;

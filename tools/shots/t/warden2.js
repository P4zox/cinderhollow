await boot(); G.give({ items: { talon: 1 } });
const out = { hits: {} }; const sleep = ms => new Promise(r => setTimeout(r, ms));
G.tp('TV8', 5, 10); G.step(5);
let sawCut = false;
for (let i = 0; i < 200; i++) { G.step(2, ['right']); if (G.state === 'cut') { sawCut = true; break; } }
out.cut = sawCut; for (let i = 0; i < 60 && G.state === 'cut'; i++) G.step(10);
const b = G.boss; let last = G.P.hp;
function tick(n, tag) { for (let i = 0; i < n; i++) { G.step(1); if (G.P.hp < last) out.hits[tag] = (out.hits[tag] || 0) + 1; G.P.hp = 999; last = 999; G.P.inv = 0; if (G.state === 'cut') G.step(1, [], ['pause']); } }
async function force(m, dist, snaps, stag) {
  b.x = 22 * 16; b.state = 'idle'; b.cool = 99; b.y = b.floor; G.P.x = b.x + dist; G.P.y = 176; G.step(2);
  b.face = 1; stag ? b.beginStag(m) : b.begin(m);
  for (let i = 0; i < 260; i++) { if (m === 'pillars' || m === 'rain') { G.P.x = b.x + dist; } tick(1, m); if (snaps.includes(i)) await snap(`w2_${stag ? 's' : 'm'}_${m}_${i}`); if (b.state === 'idle' && i > 20) break; }
  tick(80, m); b.cool = 99;
}
for (const [m, d, sn] of [['sweep', 60, [30]], ['thrust', 90, []], ['combo', 70, [22, 40, 58]], ['leap', 150, [40, 62]], ['gore', 60, [40]], ['nova', 80, [60]],
                          ['erupt', 110, []], ['wave', 140, [80]], ['volley', 150, []], ['summon', 120, []], ['charge', 180, []], ['sink', 100, []],
                          ['pillars', 140, [70, 95]], ['rain', 140, [100]]]) await force(m, d, sn, false);
out.p1hits = { ...out.hits }; out.hits = {};
// pillar telegraph accuracy: a pillar at a known spot; stand on its line vs 22px away
const tp = G.TVR;
function pillarTest(off) {
  tp.pillars = []; G.P.x = 30 * 16 + off; G.P.y = 176; G.P.hp = 999; last = 999;
  G.tvPillar(30 * 16, 1, 0, 8, 36, b);
  let hit = false; for (let i = 0; i < 90; i++) { G.step(1); if (G.P.hp < last) hit = true; G.P.hp = 999; last = 999; G.P.inv = 0; b.cool = 99; b.state = 'idle'; }
  return hit;
}
out.pillarOnLine = pillarTest(2); out.pillarOff = pillarTest(26);
// transformation
b.state = 'idle'; b.cool = 99; b.hit({ dmg: b.hp - b.maxHp * 0.49, poise: 0, dir: -1, kind: 'light', x: b.x, y: b.y - 50 });
for (let i = 0; i < 300 && G.state !== 'cut'; i++) tick(1, 'wait');
out.xcut = G.state === 'cut';
for (let i = 0, k = 0; i < 80 && G.state === 'cut'; i++) { G.step(8); if (i % 5 === 1 && k < 6) await snap('w2_x_' + (k++)); }
out.form = b.form; out.phase = b.phase;
for (const [m, d, sn] of [['gallop', 200, [50, 70]], ['rear', 90, [40, 60]], ['toss', 80, [45]], ['bound', 160, [40, 90]], ['bellow', 120, [60]]]) await force(m, d, sn, true);
out.p2hits = { ...out.hits };
// edges in stag form
const xs = [];
for (const px of [3.4, 46.4]) for (const m of ['gallop', 'bound', 'rear', 'gallop']) {
  b.state = 'idle'; b.cool = 99; b.x = px < 10 ? 20 * 16 : 30 * 16; b.facePlayer(); b.beginStag(m);
  for (let i = 0; i < 260; i++) { G.P.x = px * 16; G.P.y = 176; tick(1, 'edge'); xs.push(b.x); if (b.state === 'idle' && i > 10) break; }
}
out.edgeX = [Math.min(...xs) / 16, Math.max(...xs) / 16].map(v => +v.toFixed(2)); out.LR = [b.L / 16, b.R / 16];
G.P.x = 3.5 * 16; b.state = 'idle'; b.cool = 99; G.step(90, ['left']); out.roomWhileAlive = G.room;
b.hit({ dmg: 99999, poise: 0, dir: -1, kind: 'light', x: b.x, y: b.y - 50 });
for (let i = 0; i < 8; i++) { G.step(30); if (i % 3 === 1) await snap('w2_death_' + i); }
await sleep(9000); G.step(30);
out.flag = !!G.SAVE.flags['boss:warden']; out.charms = G.SAVE.charms;
G.P.x = 4 * 16; for (let i = 0; i < 120; i++) G.step(1, ['left'], i % 15 === 0 ? ['jump'] : []); out.roomAfter = G.room;
return out;

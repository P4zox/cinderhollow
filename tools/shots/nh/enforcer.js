await boot();
const out = [];
window.__nhLog = [];
G.tp('NH5', 6, 12); G.step(10);
for (let i = 0; i < 12; i++) { G.step(20); if (i % 3 === 0) await snap('a_intro_' + i); }
for (let i = 0; i < 300 && G.state === 'cut'; i++) G.step(10);
const B = G.boss; out.push(['active', B.active, B.state, G.state]);
// stand still (no god) for a while: do the attacks land?
const hp0 = G.P.hp; const moves = new Set();
for (let i = 0; i < 80; i++) { G.step(6); moves.add(B.state + ':' + (B.atk || '')); if (i % 8 === 0) await snap('b_p1_' + String(i).padStart(2, '0')); if (G.P.hp < 60) G.P.hp = 400; }
out.push(['p1 moves', [...moves].join(' '), 'hits', window.__nhLog.length, window.__nhLog.slice(0, 6)]);
G.nhGod(true);
// clamp: pin the player at each fog wall and force every move
const bad = [];
for (const px of [3 * 16 + 14, 40 * 16]) {
  G.P.x = px; G.P.y = 13 * 16; 
  for (const m of ['bash', 'sweep', 'stomp', 'missiles', 'walk']) { B.state = 'idle'; B.start(m); for (let k = 0; k < 90; k++) { G.step(1); if (B.x < B.L - 0.5 || B.x > B.R + 0.5 || B.y !== B.floor) bad.push([m, Math.round(B.x), B.y]); } }
}
out.push(['clamp violations', bad.length, bad.slice(0, 4), 'L', B.L, 'R', B.R]);
B.hp = B.maxHp * 0.45; B.state = 'idle'; G.step(30);
for (let i = 0; i < 300 && G.state === 'cut'; i++) G.step(10);
out.push(['p2', B.phase, B.sh.name]);
for (let i = 0; i < 40; i++) { G.step(8); if (i % 8 === 0) await snap('c_p2_' + String(i).padStart(2, '0')); }
B.hp = 1; B.hit({ dmg: 50, poise: 0, dir: 1, x: B.x, y: B.y - 40 });
for (let i = 0; i < 60; i++) G.step(10);
await snap('d_dead');
out.push(['dead', B.state, G.SAVE.flags['boss:enforcer'], 'fog on', G.NHR.fogs.map(f => f.on()).join(',')]);
// walk out east
G.P.x = 38 * 16; for (let i = 0; i < 200 && G.room === 'NH5'; i++) G.step(3, ['right']);
out.push(['exit', G.room]);
return out;

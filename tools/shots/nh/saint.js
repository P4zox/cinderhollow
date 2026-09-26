await boot();
const out = [];
G.tp('NH7', 8, 10); G.step(10);
for (let i = 0; i < 16; i++) { G.step(30); if (i % 2 === 0) await snap('a_intro_' + String(i).padStart(2, '0')); }
for (let i = 0; i < 400 && G.state === 'cut'; i++) G.step(10);
const B = G.boss; out.push(['after intro', G.state, B.state, B.active, Math.round(B.x), Math.round(B.y)]);
G.nhGod(true);
const moves = ['orbs', 'volley', 'limbo', 'grid', 'gaze', 'burn', 'spiral', 'dive', 'delete', 'lighthouse', 'rain'];
for (const m of moves) {
  B.state = 'idle'; B.cool = 99; B.cancelMove(); G.step(30);
  if (['lighthouse', 'rain'].includes(m)) B.phase = 3; else if (['burn', 'spiral', 'dive', 'delete'].includes(m)) B.phase = 2; else B.phase = 1;
  B.startMove(m); let k = 0;
  for (let f = 0; f < 600 && B.state === 'attack'; f++) { G.step(1); if (f % 45 === 20 && k < 3) { await snap('b_' + m + '_' + k); k++; } }
  out.push([m, 'ended', B.state, Math.round(B.x), Math.round(B.y)]);
}
B.phase = 1; B.state = 'idle'; B.startExposed(); G.step(60); await snap('c_exposed');
B.state = 'idle'; B.cool = 99; B.hp = B.maxHp * 0.3; B.phase = 2; B.pendingPhase = 3; B.state = 'idle';
for (let i = 0; i < 400; i++) { G.step(3); if (i === 60 || i === 120) await snap('d_cyber_' + i); }
out.push(['p3', B.phase, G.nhRoom().def.biome, B.state]);
B.state = 'idle'; B.cool = 99; B.startMove('orbs'); for (let f = 0; f < 60; f++) G.step(1); await snap('d_cyber_orbs');
B.hp = 1; B.hit({ dmg: 50, poise: 0, dir: 1, x: B.x, y: B.y, crit: true });
for (let i = 0; i < 40; i++) { G.step(6); if (i % 8 === 0) await snap('f_death_' + i); }
out.push(['dead', B.state, G.SAVE.flags['boss:saint0'], G.nhRoom().def.biome]);
return out;

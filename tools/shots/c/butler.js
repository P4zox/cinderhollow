await boot();
G.SAVE.flags['cutp2:butler'] = 1;
G.tp('CM6', 3, 9); G.step(20, ['right']);
for (let i = 0; i < 400 && G.state === 'cut'; i++) { G.step(5); if (i === 30) await snap('b_cut'); }
const B = G.boss, P = G.P, out = {};
for (const m of ['slash', 'thrust', 'serve', 'flourish', 'vanish']) {
  P.hp = G.D.maxHp; B.x = 250; P.x = m === 'serve' ? 120 : m === 'vanish' ? 150 : 210; P.face = 1; B.state = 'idle'; B.cool = 99; B.cmNext = null;
  window.__cm.force(m); const hp0 = P.hp; let mn = 1e9, mx = -1e9;
  for (let k = 0; k < 110; k++) { G.step(1); mn = Math.min(mn, B.x); mx = Math.max(mx, B.x); if (k % 22 === 8) await snap(`b_${m}_${String(k).padStart(3, '0')}`); }
  out[m] = { dmg: Math.round(hp0 - P.hp), range: [Math.round(mn), Math.round(mx)], st: B.state };
}
// edges: vanish with the player pinned at each fog wall
for (const [n, px] of [['L', 40], ['R', 390]]) { P.x = px; B.x = 200; B.state = 'idle'; B.cool = 99; window.__cm.force('vanish'); let mn = 1e9, mx = -1e9; for (let k = 0; k < 120; k++) { G.step(1); P.x = px; mn = Math.min(mn, B.x); mx = Math.max(mx, B.x); } out['edge' + n] = [Math.round(mn), Math.round(mx), B.L, B.R]; }
B.hp = 1; B.state = 'idle'; B.hit({ dmg: 30, poise: 0, dir: 1, x: B.x, y: B.y - 30 });
P.hp = G.D.maxHp; G.step(200); await snap('b_dead');
out.dead = { alive: B.alive, flag: G.SAVE.flags['boss:butler'], fog: G.props.filter(p => p.type === 'fog').map(p => p.on()) };
return out;

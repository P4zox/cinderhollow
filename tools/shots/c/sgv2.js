await boot();
G.SAVE.flags['cut:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P, out = {};
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
G.step(170);
const run = async (m, px, frames = 150, snapEvery = 30) => {
  P.hp = G.D.maxHp; P.inv = 0; B.x = 400; B.alt = 0; B.hidden = false; B.state = 'idle'; B.cool = 99; P.x = px; P.y = 240; B.face = -1;
  window.__cm.force(m); const hp0 = P.hp, bhp = B.hp; let mn = 1e9, mx = -1e9;
  for (let k = 0; k < frames; k++) { G.step(1); B.cool = Math.max(B.cool, 50); mn = Math.min(mn, B.x); mx = Math.max(mx, B.x); if (k % snapEvery === snapEvery / 2) await snap(`v_${m}_${String(k).padStart(3, '0')}`); }
  out[m] = { dmg: Math.round(hp0 - P.hp), range: [Math.round(mn), Math.round(mx)], st: B.state, heal: B.hp - bhp };
};
await run('combo', 330, 200, 20);
await run('charge', 200, 120, 15);
await run('sneak', 300, 120, 20);
await run('lances', 250, 150, 30);
await run('grab', 340, 260, 30);
await run('requiem', 300, 360, 30);
out.meta = { L: B.L, R: B.R };
return out;

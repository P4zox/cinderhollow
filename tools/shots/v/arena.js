// arena edges: pin the player against each wall and force every movement move; then a long AI brawl (god mode)
await boot();
G.give({ flags: { ...G.SAVE.flags, 'boss:omen': 1, 'boss:sovereign': 1, 'cut:sovereign': 1, venn_betrayed: 1, 'cut:venn': 1, 'cutp2:venn': 1, 'cutp3:venn': 1 } });
G.tp('X5', 20, 10); G.step(5);
const b = G.boss; G.P.x = 300; G.step(20);
const L = b.L, R = b.R, fl = b.floor;
const out = { L, R, fl, edge: [] };
const MOVES = { 1: ['sweep', 'reap', 'rising', 'glide'], 2: ['lance', 'dive', 'reap', 'glide'], 3: ['flurry', 'blinkcut', 'slam'] };
for (const px of [36, 60, 740, 700]) {
  for (const ph of [1, 2, 3]) {
    b.phase = ph; b.speed = [1, 1, 1.12, 1.3][ph]; b.pendingPhase = 0; b.hp = b.maxHp * [1, 0.9, 0.5, 0.15][ph];
    for (const m of MOVES[ph]) {
      b.x = px < 400 ? L + 10 : R - 10; b.face = px < b.x ? -1 : 1; b.airH = 0; b.hidden = false; b.state = 'idle';
      G.P.x = px; G.P.y = fl; G.P.hp = G.D.maxHp;
      b.cool = 99; b.start(m);
      let minX = 1e9, maxX = -1e9, maxY = -1e9, minY = 1e9;
      for (let f = 0; f < 240; f++) { G.step(1); G.vn.hold(); minX = Math.min(minX, b.x); maxX = Math.max(maxX, b.x); maxY = Math.max(maxY, b.y); minY = Math.min(minY, b.y); if (b.state !== 'attack' && b.state !== 'glide' && f > 30) break; }
      const bad = minX < L - 0.5 || maxX > R + 0.5 || maxY > fl + 0.01;
      if (bad) out.edge.push(`BAD p${ph} ${m} px=${px}: x ${minX.toFixed(1)}..${maxX.toFixed(1)} y ${minY.toFixed(1)}..${maxY.toFixed(1)}`);
    }
  }
}
out.edgeChecked = true;
// jitter: player standing inside her; she should not flip-flop every frame
b.phase = 1; b.speed = 1; b.hp = b.maxHp; b.x = 400; b.state = 'idle'; b.cool = 99; G.P.x = 400;
let flips = 0, lastF = b.face;
for (let f = 0; f < 120; f++) { G.P.x = 400 + (f % 2 ? 0.4 : -0.4); G.step(1); G.vn.hold(); if (b.face !== lastF) flips++; lastF = b.face; }
out.flipsWhenOverlapping = flips;
// brawl: god mode, the player swings and rolls; she runs her own AI through all three phases
G.SAVE.flags['cutp2:venn'] = 0; G.SAVE.flags['cutp3:venn'] = 0;
b.phase = 1; b.speed = 1; b.hp = b.maxHp; b.stanceImmune = 0; b.cool = 0.5; b.x = 500; b.state = 'idle'; G.P.x = 420;
window.__game.give({}); 
const seen = {}, phases = [];
let shots = 0;
for (let s = 0; s < 1400; s++) {
  if (G.state === 'cut') { G.step(20, [], []); continue; }
  if (G.state !== 'play') break;
  G.P.hp = G.D.maxHp;
  const dx = b.x - G.P.x, far = Math.abs(dx) > 40;
  const act = [];
  if (far) act.push(dx > 0 ? 'right' : 'left');
  const tap = [];
  if (!far && s % 6 === 0) tap.push('attack');
  if (G.vn.danger() && s % 2 === 0) tap.push('roll');
  G.step(6, act, tap);
  // she has to lose hp for the phases: help the player a little
  if (s % 10 === 0 && b.alive && b.active) b.hit({ dmg: 30, poise: 10, x: b.x, y: b.y - 30, dir: 1, melee: true, kind: 'light' });
  if (b.state === 'attack') seen[b.atk] = (seen[b.atk] || 0) + 1;
  if (!phases.length || phases[phases.length - 1] !== b.phase) phases.push(b.phase);
  if (s % 60 === 0 && shots < 24) { await snap('b' + String(shots).padStart(2, '0')); shots++; }
  if (!b.alive) break;
}
out.moves = seen; out.phases = phases; out.bossHp = b.hp; out.alive = b.alive; out.state = G.state;
return out;

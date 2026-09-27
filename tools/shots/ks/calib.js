await boot(); G.SETTINGS.god = 1; const out = {};
const meas = (fn) => { G.tp('T2', 10, 26); G.step(20); const x0 = G.P.x, y0 = G.P.y; let minY = y0, f = 0, left = false, land = null;
  for (f = 0; f < 200; f++) { fn(f); if (!G.P.ground) left = true; minY = Math.min(minY, G.P.y); if (left && G.P.ground) { land = G.P.x - x0; break; } }
  return { rise: +(y0 - minY).toFixed(1), dx: land === null ? null : +land.toFixed(1), frames: f }; };
out.standJump = meas(f => G.step(1, ['jump'], f === 0 ? ['jump'] : []));
out.hop = meas(f => G.step(1, f < 6 ? ['jump'] : [], f === 0 ? ['jump'] : []));
// running jump: 15 frames of run-up first
out.runJump = meas(f => { if (f === 0) for (let i = 0; i < 15; i++) G.step(1, ['right']); G.step(1, ['right', 'jump'], f === 0 ? ['jump'] : []); });
out.runJumpDash = meas(f => { if (f === 0) for (let i = 0; i < 15; i++) G.step(1, ['right']); G.step(1, ['right', 'jump'], f === 0 ? ['jump'] : f === 30 ? ['roll'] : []); });
return out;

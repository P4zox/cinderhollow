// the two edges the wing walks don't cross: X4 -(the Sky Stair, W6)-> SF1 and back; SF18 -(the cracked seam)-> SF19 and back
const climbUp = (target, max = 60) => {   // hop up platform to platform (any '=' or solid top 1.5..4 rows above) until the room changes
  for (let n = 0; n < max && G.room !== target; n++) {
    const d = window.__sys.roomObj.def, fy = Math.round(py()), cx = px();
    let best = null;
    for (let r = fy - 4; r <= fy - 2; r++) for (let x = 0; x < d.w; x++) {
      if (r < 0 || r >= d.h) continue; const ch = d.map[r][x], up = r > 0 ? d.map[r - 1][x] : '.';
      if ((ch === '=' || ch === '#' || ch === '?') && '.+'.includes(up) && Math.abs(x + 0.5 - cx) > 1.2) { const s = Math.abs(x + 0.5 - cx) + (fy - r) * 0.5; if (!best || s < best.s) best = { x, r, s }; }
    }
    if (!best) { G.step(1, ['jump'], ['jump']); until(() => G.P.ground, ['jump'], 90); continue; }
    leap(best.x, best.r - 1, { jumps: 1 });
  }
  return G.room === target;
};
G.tp('X4', 7, 10); G.step(30); log('X4');
leap(7, 7, { jumps: 0 }); leap(3, 4, { jumps: 0 }); leap(7, 1, { jumps: 0 }); G.step(1, ['jump'], ['jump']); until(() => G.room === 'W6', ['jump'], 60); until(() => G.P.ground, [], 90);
climbUp('SF1', 80); expect('SF1'); until(() => G.P.ground, [], 120);
for (let i = 0; i < 1200 && G.room !== 'X4'; i++) { if (G.P.ground && i % 30 === 29) dropThrough(); else G.step(1, [i % 200 < 100 ? 'left' : 'right']); }
until(() => G.P.ground, [], 300); expect('X4'); log('back on the Crown Shrine');
// SF19: up the Moonstep Spire the trial's way (the trial not started), break the seam, into the Comet's Heart and back
G.tp('SF18', 36, 44); G.step(20);
walkTo(25.5); leap(18, 41); leap(11, 38); leap(4, 35); leap(11, 28, { jumps: 2 }); walkTo(12.8);
for (const [id, x, y] of [['tm0', 17, 26], ['tm1', 22, 24], ['tm2', 27, 25], ['tm3', 32, 23]]) { waitSolid(id, 0.05, 600, 0.9); leap(x, y, { jumps: 1 }); }
leap(39, 21, { jumps: 2 }); walkTo(37.6); leap(21, 15, { jumps: 2, margin: 20, dash: true, dashAt: 40, dashT: 60 }); walkTo(15.2); chimney(13, 17, 4);
for (let i = 0; i < 90 && !(G.P.ground && py() < 4.2); i++) G.step(1, [px() < 17.4 ? 'right' : px() > 17.7 ? 'left' : 'down', ...(G.P.vy < 0 ? ['jump'] : [])], (G.P.vy > 0 && G.P.y > 3.5 * 16 && G.P.airJumps > 0 && i % 10 == 0) ? ['jump'] : []);
hopDash(1, 5); until(() => !G.P.ground, ['right'], 60); G.step(1, ['right'], ['roll']); until(() => G.P.ground, ['right'], 120); walkTo(44.8, 0.2);
for (let i = 0; i < 8 && G.room === 'SF18'; i++) { G.step(1, ['right'], ['attack']); G.step(14, ['right']); }
wander(1, 'SF19'); walkTo(7); wander(-1, 'SF18'); log('back in the Spire');
return { log: LOG.filter(l => !/landed|airTo ok/.test(l)), rooms: ROOMLOG };

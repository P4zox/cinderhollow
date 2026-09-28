// after the scripted clear, walk out of the goal area with plain inputs (the goal's exit edge)
{
  const W = window.__walker, RB = window.__rb, exitTo = window.__exitTo;
  for (let i = 0; i < 200; i++) RB.sim(1);
  const from = G.room, h = W.hop(RB.snap(), exitTo, { budget: 300 });
  if (!h.fail) { RB.restore(RB.snap()); }
  res.exit = h.fail ? `FAIL leaving ${from} for ${exitTo}` : `left ${from} for ${exitTo} in ${h.path.length} programs: ${h.path.map(p => p.k + (p.d ?? p.side ?? '')).join(' ')}`;
}
return res;

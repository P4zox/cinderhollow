await boot(); window.__godS = true;
G.giveArmory(); G.give({ stats: { vig: 40, mnd: 30, end: 40, str: 30, dex: 25, fth: 20 } });
G.SAVE.flags['cut:astrel'] = 1;
const out = {};
for (const wid of ['longsword', 'greatsword', 'starblade', 'spear', 'katana', 'maul', 'kalden']) {
  G.SAVE.weapon = wid; delete G.SAVE.flags['boss:astrel'];
  G.tp('SF7', 26, 16); S(3); const b = G.boss;
  for (let i = 0; i < 100 && !b.active; i++) S(2, ['right']);
  S(100);
  let maxT = 0, frozen = 0, n = 0, maxP = 0, hs = 0, states = {};
  for (let k = 0; k < 12; k++) {
    b.cool = 2; b.state = 'idle'; G.P.x = b.x - 4; G.P.y = b.y - 70; G.P.vy = 0; G.P.state = 'air';
    S(1, [], ['heavy']);
    for (let i = 0; i < 90; i++) {
      const t0 = performance.now(); S(1, ['heavy']); const dt = performance.now() - t0;
      maxT = Math.max(maxT, dt); n++; if (window.__sfDbg.hs() > 0) frozen++; hs = Math.max(hs, window.__sfDbg.hs()); maxP = Math.max(maxP, window.__sfDbg.particles());
      states[G.P.state] = (states[G.P.state] || 0) + 1;
      b.cool = 2;
    }
  }
  out[wid] = { maxT: +maxT.toFixed(1), frozenFrac: +(frozen / n).toFixed(2), hs: +hs.toFixed(2), maxP, hp: Math.round(b.hp), states: JSON.stringify(states) };
}
return out;

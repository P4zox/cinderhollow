// the plunge is dodged by rolling as he drops (falling frame), in either direction, both phases
await boot();
G.SAVE.flags['cut:kalden'] = 1; G.SAVE.flags['cutp2:kalden'] = 1; delete G.SAVE.flags['boss:kalden'];
G.tp('M5', 6, 10); const b = G.boss;
for (let i = 0; i < 200 && !b.active; i++) { G.step(2, ['right']); if (G.state === 'cut') G.step(1, [], ['pause']); }
for (let i = 0; i < 100 && b.introT > 0; i++) G.step(2);
const res = [];
for (const ph of [1, 2]) {
  if (ph === 2) { b.hp = b.maxHp * 0.45; for (let i = 0; i < 400 && b.phase !== 2; i++) { G.step(2); G.P.hp = 99999; } for (let i = 0; i < 200 && G.state !== 'play'; i++) G.step(1, [], ['pause']); }
  for (const dir of [null, 'away', 'toward']) {
    for (let i = 0; i < 60; i++) { G.step(2); G.P.hp = 99999; }
    window.__kd.hazards.length = 0;
    b.x = 300; b.y = b.floor; G.P.x = 450; G.P.y = b.floor; G.P.inv = 0; G.P.hp = 99999; b.cool = 99; b.state = 'idle'; b.chain = 99; b.cds = {};
    b.start('plunge'); b.chain = 99; let rolled = false, lost = 0;
    for (let i = 0; i < 150 && b.state === 'attack'; i++) {
      let tap = [], hold = [];
      if (!rolled && b.anim.i === 5) { rolled = true; tap = ['roll']; if (dir) hold = [(dir === 'away') === (G.P.x > b.x) ? 'right' : 'left']; }
      const h0 = G.P.hp; G.step(1, hold, tap); b.cool = 9; if (b.anim.i >= 6 && b.anim.i <= 8) lost += Math.max(0, h0 - G.P.hp);
    }
    res.push(`p${ph} roll ${dir || 'in place'}: damage from the landing ${lost}`);
  }
}
return res;

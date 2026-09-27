await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1;
const out = [];
for (const ph of [1, 2, 3]) {
  delete G.SAVE.flags['boss:saint0']; for (const f of ['cut:','cutp2:','cutp3:']) G.SAVE.flags[f+'saint0']=1;
  G.tp('NH7', 8, 10); const b = G.boss;
  for (let i=0;i<200 && !b.active;i++){ G.step(4,['right']); G.P.hp=99999; if(G.state!=='play')G.step(1,[],['pause']); }
  if (ph >= 2) { b.hp = b.maxHp * (ph === 2 ? 0.6 : 0.3); }
  const moves = {}; let hurt = 0, dmg = 0, pulses = 0, lastMove = null, t = 0;
  for (let i = 0; i < 60 * 45; i += 2) {
    const hp0 = G.P.hp;
    const hug = i < 60 * 15;   // first 15 s: stand under the eye
    const dir = hug ? (Math.abs(b.x - G.P.x) > 20 ? [b.x < G.P.x ? 'left' : 'right'] : []) : (Math.random() < 0.5 ? ['left'] : ['right']);
    G.step(2, dir, !hug && Math.random() < 0.05 ? ['jump'] : []);
    if (G.P.hp < hp0) { hurt++; dmg += hp0 - G.P.hp; }
    G.P.hp = 99999; G.P.inv = 0;
    if (b.pulse && !b._pc) { pulses++; b._pc = 1; } if (!b.pulse) b._pc = 0;
    if (b.move !== lastMove && b.state === 'attack') { moves[b.move] = (moves[b.move] || 0) + 1; }
    lastMove = b.state === 'attack' ? b.move : null;
    if (G.state !== 'play') G.step(1, [], ['pause']);
    if (b.hp < b.maxHp * 0.05) b.hp = b.maxHp * 0.3;
  }
  out.push(`phase ${b.phase}: hits taken ${hurt}, dmg ${Math.round(dmg)} in 45s, pulses ${pulses}, moves ${JSON.stringify(moves)}`);
}
return out;

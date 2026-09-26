// agent G (Expansion 2): cast every new spell at R2's enemies, snap frames, log damage
await boot();
const SP = ['bramble_snare','drowning_hymn','blood_lance','crimson_rite','soul_chains','sunbeam','sandstorm','comet','pulse_shot','null_field'];
G.give({ spellsOwned: SP, spellsEq: SP.slice(), spellSlots: 10, stats: { ...G.SAVE.stats, fth: 30, mnd: 30 } });
const log = [];
const setup = () => {
  G.tp('R2', 5, 10); G.step(2);
  const xs = [128, 150, 172, 200];
  G.enemies.forEach((e, i) => { e.x = xs[i] || 300; e.y = 176; e.vx = 0; e.vy = 0; e.hp = e.maxHp = 5000; e.aggro = false; e.cool = 5; e.state = 'idle'; });
  G.P.fp = 999; G.P.hp = G.D.maxHp; G.P.face = 1;
};
const plan = { bramble_snare: [20, 40, 80, 140, 200], comet: [20, 40, 55, 62, 70], sandstorm: [20, 50, 90, 140, 200], null_field: [20, 60, 120, 200, 300] };
for (const id of SP) {
  setup(); G.SAVE.spell = id;
  const hp0 = G.enemies.map(e => e.hp), php0 = G.P.hp;
  G.step(1, [], ['cast']);
  let f = 0;
  for (const k of plan[id] || [20, 26, 32, 40, 55]) { G.step(k - f); f = k; if (id !== 'crimson_rite') G.P.hp = Math.max(G.P.hp, 50); await snap(id + '_' + String(k).padStart(3, '0')); }
  G.step(60);
  log.push(id + ': ' + G.enemies.map((e, i) => (hp0[i] - e.hp) | 0).join(',') + ' st ' + G.enemies.map(e => e.state + (e._slowT > 0 ? '~' : '') + (e.gStun > 0 ? '*' : '')).join(',') + ' php ' + (php0 | 0) + '->' + (G.P.hp | 0) + ' light ' + G.D.light.toFixed(1));
}
return log;

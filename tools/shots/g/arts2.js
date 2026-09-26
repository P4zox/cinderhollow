// agent G (Expansion 2): every new art, plain and charged (held ~0.8 s), vs R2 enemies
await boot();
const AR = ['reap','harvest_moon','lash','chain_drag','blood_frenzy','tidal_surge','solar_flare','starfall','overclock','pale_pyre'];
G.give({ arts: AR });
const log = [];
const setup = () => {
  G.tp('R2', 5, 10); G.step(2);
  const xs = [128, 150, 172, 200];
  G.enemies.forEach((e, i) => { e.x = xs[i] || 300; e.y = 176; e.vx = 0; e.vy = 0; e.hp = e.maxHp = 5000; e.aggro = false; e.cool = 5; e.state = 'idle'; });
  G.P.fp = 999; G.P.hp = G.D.maxHp; G.P.face = 1;
};
const only = (window.__only || AR);
for (const id of only) for (const ch of [false, true]) {
  setup(); G.SAVE.art = id;
  const hp0 = G.enemies.map(e => e.hp), php0 = G.P.hp, x0 = G.P.x;
  if (ch) G.step(60, ['art'], ['art']); else G.step(1, [], ['art']);
  const charged = G.P.artCharged;
  const seq = [];
  for (let k = 0; k < 8; k++) { G.step(7); seq.push(G.P.state[0] + ':' + G.P.anim.tag + ':' + Math.round(G.P.x)); if (k % 2 === 1) await snap(id + (ch ? '_ch' : '') + '_' + k); }
  G.step(60);
  log.push(id + (ch ? '*' + charged : '') + ': dmg ' + G.enemies.map((e, i) => (hp0[i] - e.hp) | 0).join(',') + ' st ' + G.enemies.map(e => e.state + (e._slowT > 0 ? '~' : '') + (e.gStun > 0 ? '*' : '')).join(',') + ' | P ' + G.P.state + ' hp ' + (php0 | 0) + '->' + (G.P.hp | 0) + ' x ' + x0 + '->' + Math.round(G.P.x) + ' | ' + seq.join(' '));
}
return log;

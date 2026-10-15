// Within one page: old pipeline (hard shadows, single-pass ring bloom at output res, no rim / shafts / mood) vs the v15
// defaults (soft shadows, bloom chain, rim, soft shafts, region mood), interleaved in batches so machine load hits both.
// Optional first line: const ROOMS=[...], NB=batches, BF=frames per batch.
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev, GF = G.GFX, o = [];
const OLD = { shaders: 1, light: 2, rim: 0, rays: 0, mood: 0, bloom: 1, vig: 1, grade: 0, tex: 0, scan: 0, grain: 0, ca: 0, bright: 1 };
const NEW = { ...OLD, light: 3, rim: 1, rays: 1, mood: 1 };
const rooms = typeof ROOMS !== 'undefined' ? ROOMS : [['C2', 24, 10], ['K1', 24, 10], ['D2', 24, 8], ['R1', 24, 10], ['X1', 12, 10], ['A2', 24, 10]];
const nb = typeof NB === 'number' ? NB : 4, bf = typeof BF === 'number' ? BF : 30;
for (const [id, tx, ty] of rooms) {
  G.tp(id, tx, ty); for (let i = 0; i < 6; i++) G.step(30); E('regionCard = null; enemies.forEach(e => { e.x = -9999; })');
  const acc = { old: [0, 0], new: [0, 0], off: [0, 0] };
  for (let b = 0; b < nb; b++) for (const [k, cfg, chain] of [['off', { ...OLD, shaders: 0 }, true], ['old', OLD, false], ['new', NEW, true]]) {
    Object.assign(G.SETTINGS, cfg); GF.chain = chain; GF.sync = true; G.step(1);
    GF.pt = 0; GF.pn = 0;
    for (let i = 0; i < bf; i++) { G.step(1); G.P.hp = 99999; }
    acc[k][0] += GF.pt; acc[k][1] += GF.pn;
  }
  GF.sync = false; GF.chain = true;
  const m = k => acc[k][0] / acc[k][1];
  o.push(`${id}: shaders off ${m('off').toFixed(2)} | old ${m('old').toFixed(2)} (GL +${(m('old') - m('off')).toFixed(2)}) | v15 ${m('new').toFixed(2)} (GL +${(m('new') - m('off')).toFixed(2)}) ms/frame, lights ${G.lx.LX.n}`);
}
return o;

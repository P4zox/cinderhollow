// Busy room A/B in one page: Training Grounds TR2 with ~37 foes (tools/shots/tr/mass_spawn.js setup), the old pipeline vs the
// v15 defaults interleaved in batches, gl-synced so the GPU time counts. Whole step = sim + render + present.
await new Promise(r => setTimeout(r, 300));
const T = G.trn, E = G.sk.ev, GF = G.GFX, o = [];
T.start(); G.step(10); E("trnGoto('TR2')"); G.step(10);
E("TRN.count = 20"); E("menu = { screen: 'trn', tab: 4, sel: 0 }; state = 'menu'");
for (const t of ['hollow_soldier', 'rot_crawler', 'gloom_wisp', 'hollow_archer', 'grave_knight']) E(`trnSpawnEnemy('${t}')`);
E("menu = null; state = 'play'"); G.SETTINGS.god = 1;
const OLD = { shaders: 1, light: 2, rim: 0, rays: 0, mood: 0, bloom: 1, vig: 1, grade: 0, tex: 0, scan: 0, grain: 0, ca: 0, bright: 1 };
const NEW = { ...OLD, light: 3, rim: 1, rays: 1, mood: 1 };
const nb = typeof NB === 'number' ? NB : 5, bf = typeof BF === 'number' ? BF : 40, acc = {};
for (let b = 0; b < nb; b++) for (const [k, cfg, chain] of [['off', { ...OLD, shaders: 0 }, true], ['old', OLD, false], ['new', NEW, true], ['new_hard', { ...NEW, light: 2 }, true], ['new_norays', { ...NEW, rays: 0 }, true]]) {
  Object.assign(G.SETTINGS, cfg); GF.chain = chain; GF.sync = true; G.step(1);
  GF.pt = 0; GF.pn = 0; const t0 = performance.now();
  for (let i = 0; i < bf; i++) G.step(1, [], i % 10 === 0 ? ['attack'] : []);
  const a = acc[k] || (acc[k] = [0, 0, 0]); a[0] += GF.pt; a[1] += GF.pn; a[2] += performance.now() - t0;
}
GF.sync = false; GF.chain = true;
for (const [k, a] of Object.entries(acc)) o.push(`${k}: present ${(a[0] / a[1]).toFixed(2)} ms, whole step ${(a[2] / a[1]).toFixed(2)} ms`);
o.push(`foes alive ${E('trnFoesAlive()')}, lights ${G.lx.LX.n}`);
return o;

// riding test: stand the player on each moving part for 10 s (600 frames) and log per-frame P.y deltas vs the slab
await boot(); G.SAVE.items.wings = 1; G.SETTINGS.god = true;
const out = [], K = G.KIT;
const obj = (kind, i = 0) => K.objs.filter(q => q.kind === kind)[i];
function ride(name, o, n = 600, hold = []) {
  const P = G.P; P.x = (o.d.x0 + o.d.x1) / 2; P.y = o.d.y0; P.vx = P.vy = 0; P.ground = true;
  G.step(2);
  const rel = new Set(), relX = new Set(), dys = new Map(); let air = 0, lastY = P.y, travel = [1e9, -1e9, 1e9, -1e9];
  for (let i = 0; i < n; i++) {
    G.step(1, hold);
    rel.add(+(P.y - o.d.y0).toFixed(2)); relX.add(Math.round(P.x) - Math.round(o.d.x0));
    const d = +(P.y - lastY).toFixed(2); dys.set(d, (dys.get(d) || 0) + 1); lastY = P.y;
    if (!P.ground) air++;
    travel = [Math.min(travel[0], o.d.x0), Math.max(travel[1], o.d.x0), Math.min(travel[2], o.d.y0), Math.max(travel[3], o.d.y0)];
  }
  const ok = rel.size === 1 && rel.has(0) && relX.size === 1 && air === 0;
  out.push(`${ok ? 'OK ' : 'BAD'} ${name}: P.y-slab=${[...rel].join(',')} screenX-offsets=${[...relX].join(',')} airborne=${air} slab x ${travel[0]}..${travel[1]} y ${travel[2]}..${travel[3]} | P.y per-frame deltas {${[...dys].sort((a, b) => a[0] - b[0]).map(([d, c]) => d + ':' + c).join(' ')}}`);
}
G.tp('T1', 4, 16); G.step(5);
ride('mover oneway horizontal', K.byId.mA); ride('mover solid vertical', K.byId.mB); ride('mover loop', K.byId.mC);
ride('mover stand-trigger', K.byId.mD); ride('lift (stand)', K.byId.lift1); ride('lift auto', K.byId.lift2);
ride('sinker', obj('sinker', 0), 300);
G.tp('T1', 2, 36); G.step(3);
ride('phase (while solid)', obj('phase', 0), 60);
G.tp('T1', 60, 96); G.step(3);
ride('static slab', obj('mover', 4), 600);
// crate: stand on top
G.tp('T1', 38, 56); G.step(3);
{ const c = obj('crate', 0); ride('crate (standing on it)', c, 300); }
// landing on a rising lift from a jump (scoop): drop the player just above the auto lift's path
G.tp('T1', 58, 16); G.step(3);
{ const o = K.byId.lift2; let landed = 0; const P = G.P; for (let t = 0; t < 400; t++) { G.step(1); if (o.v > 20 && o.pts[o.i].y > o.d.y0 === false) {} }
  P.x = (o.d.x0 + o.d.x1) / 2; P.y = o.d.y0 - 40; P.vy = 200; P.ground = false;
  let hist = []; for (let i = 0; i < 60; i++) { G.step(1); hist.push(Math.round(P.y - o.d.y0)); } out.push('drop onto moving lift: rel y trace ' + hist.slice(0, 20).join(',') + ' … final ' + hist[59]); }
// walking across the horizontal mover while it moves
G.tp('T1', 4, 16); G.step(3);
{ const o = K.byId.mA, P = G.P; P.x = o.d.x0 + 6; P.y = o.d.y0; P.ground = true; let rel = new Set(); for (let i = 0; i < 30; i++) { G.step(1, ['right']); rel.add(+(P.y - o.d.y0).toFixed(2)); } out.push('walk on mover: rel y ' + [...rel].join(',')); }
return out;

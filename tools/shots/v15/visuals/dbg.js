// debug views of the light pass: light only (hard vs soft shadows), the SDF, the rim normals. MODE line: const ROOMS=[[id,tx,ty]]
await boot(); G.SETTINGS.god = 1;
Object.assign(G.SETTINGS, { shaders: 1, light: 3, lband: 0, bright: 1, bloom: 1, vig: 1, rays: 1, mood: 1, rim: 1 });
const LX = G.lx.LX, o = [];
for (const [id, tx, ty] of (typeof ROOMS !== 'undefined' ? ROOMS : [['C2', 30, 10], ['K1', 20, 10]])) {
  G.tp(id, tx, ty); for (let i = 0; i < 8; i++) G.step(30);
  for (const [n, light, dbg] of [['hard_L', 2, 3], ['soft_L', 3, 3], ['sdf', 3, 7], ['nrm', 3, 8], ['soft', 3, 0], ['hard', 2, 0]]) {
    G.SETTINGS.light = light; LX.dbg = dbg; G.step(1); await snap(`dbg_${id}_${n}`);
  }
  LX.dbg = 0; o.push(id + ' lights ' + LX.n + ' map ' + (LX.mapMs || 0).toFixed(1) + ' ms');
}
return o;

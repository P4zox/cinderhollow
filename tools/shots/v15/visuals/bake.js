// per-room light-map bake time (AO + occluders, + the v15 SDF): biggest rooms; repeated entries for a stable number
await boot(); Object.assign(G.SETTINGS, { shaders: 1, light: 3 });
const o = [], LX = G.lx.LX;
for (const id of ['E5', 'R5', 'SF4', 'NV3', 'C2', 'TR2']) {
  const t = [];
  for (let k = 0; k < 4; k++) { G.tp(id, 4, 2); G.step(2); t.push(LX.mapMs); G.tp('R1', 4, 2); G.step(2); }
  o.push(`${id}: bake ${t.map(x => x.toFixed(1)).join(' / ')} ms, map ${LX.map ? '' : '?'}`);
}
return o;

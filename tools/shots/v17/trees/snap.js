// Trees pass: in-game snapshots of the Thornveil trees (TV14 standing + seated, other rooms). Run with shot.js:
//   SHOT_HTML=$PWD/web/dist/trees.html node tools/shots/shot.js tools/shots/v17/trees/snap.js <outdir>
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1, wings: 1, hook: 1, dash: 1 });
const settle = n => { for (let i = 0; i < n; i++) { G.step(1); G.enemies.length = 0; if (G.state === 'cut' || G.state === 'cine' || G.state === 'dialog') G.step(1, [], ['pause']); } };
let SPOTS = [['TV14_stand', 'TV14', 14, 13], ['TV14_east', 'TV14', 24, 13], ['TV2', 'TV2', 15, 10], ['TV8', 'TV8', 17, 10], ['TV10', 'TV10', 22, 11],
  ['TV9_elder', 'TV9', 50, 27], ['TV9_cleft', 'TV9', 56, 10], ['TV9_west', 'TV9', 18, 27], ['TV13', 'TV13', 15, 11]];
const only = (globalThis.__only || '').split(',').filter(Boolean);
if (only.length) SPOTS = SPOTS.filter(s => only.includes(s[0]));
const out = [];
for (const [name, r, x, y] of SPOTS) {
  try { G.tp(r, x, y); settle(200); if (G.xs && G.xs.clean) G.xs.clean(); G.step(2); await snap(name); out.push(`${name} ok p=${Math.round(G.P.x)},${Math.round(G.P.y)}`); }
  catch (e) { out.push(`${name} ERR ${e.message}`); }
}
if (!only.length || only.includes('TV14_seat')) {
  G.tp('TV14', 14, 13); settle(200);
  G.props.find(p => p.type === 'sys_bench').interact(); settle(150);
  const S = G.xrc && G.xrc.sys && G.xrc.sys(); if (S && S.vista) S.vista.lore = null;
  settle(2); await snap('TV14_seat'); out.push('seat ok');
}
return out;

// v15 visuals: the same camera spot in rooms across the biomes, shaders + Dynamic+shadows at the default look,
// plus per-room frame cost of presentWorld (gl.finish inside the probe, so GPU time is included).
// Usage: SHOT_HTML=web/dist/v15_visuals.html node tools/shots/shot.js tools/shots/v15/visuals/rooms.js <outdir>
// The first line of the script may set TAG (file prefix), MODE ('shots' | 'perf' | 'both') and FRAMES (perf frames).
const tag = typeof TAG === 'string' ? TAG : 'x', mode = typeof MODE === 'string' ? MODE : 'both';
await boot(); G.SETTINGS.god = 1; G.giveArmory();
const E = G.sk.ev;
Object.assign(G.SETTINGS, { shaders: 1, light: 2, lband: 0, bright: 1, tex: 0, bloom: 1, vig: 1, scan: 0, grain: 0, ca: 0, grade: 0 });
const R = [['R1', 'ramparts dusk'], ['C2', 'catacombs dark'], ['K1', 'cathedral'], ['X1', 'crown bright'], ['D3', 'deep lava', [30, 10]], ['D2', 'deep 48 lights'], ['HF6', 'hoarfrost'],
  ['DU1', 'dunes bright'], ['NV2', 'necropolis dark'], ['TV2', 'thornveil'], ['SF2', 'starfall night'], ['NH2', 'neohallow'], ['A2', 'archives']];
const o = [];
for (const [id, label, spot] of R) {
  E(`(() => { const d = ROOMS.find(r => r.id === '${id}'); window.__rw = d.w; window.__rh = d.h; })()`);
  G.tp(id, Math.floor(window.__rw / 2), 1); G.step(5);
  // find an open column near the middle with a floor under it
  const cx = E(`(() => { const R = room, m = Math.floor(R.w / 2); for (let d = 0; d < R.w / 2; d++) for (const s of [1, -1]) { const x = m + s * d; for (let y = 1; y < R.h - 2; y++) if (!isSolidT(tileAt(x, y)) && !isSolidT(tileAt(x, y + 1)) && !isSolidT(tileAt(x, y - 1))) { let f = y; while (f < R.h - 1 && !isSolidT(tileAt(x, f + 1))) f++; if (f < R.h - 1) return [x, f]; } } return [m, 2]; })()`);
  if (spot) cx.splice(0, 2, ...spot);
  G.tp(id, cx[0], cx[1]); G.step(90);
  for (let i = 0; i < 5 && G.state !== 'play'; i++) G.step(1, [], ['pause']);
  G.P.hp = 99999; E('enemies.forEach(e => { e.x = -9999; })'); for (let i = 0; i < 8; i++) G.step(30);
  E('regionCard = null; areaCard = null');
  if (mode !== 'perf') await snap(`${tag}_${id}`);
  if (mode !== 'shots') {
    const NF = typeof FRAMES === 'number' ? FRAMES : 200, res = {};
    for (const sh of [0, 1]) {   // shaders off = the readback probe's own floor; on = the full GL path
      G.SETTINGS.shaders = sh; G.GFX.sync = true; G.step(5); G.GFX.pt = 0; G.GFX.pn = 0; const t0 = performance.now();
      for (let i = 0; i < NF; i++) { G.step(1); G.P.hp = 99999; }
      res[sh] = [G.GFX.pt / G.GFX.pn, (performance.now() - t0) / NF];
    }
    G.GFX.sync = false;
    o.push(`${id} (${label}): present ${res[1][0].toFixed(2)} ms (shaders off ${res[0][0].toFixed(2)}, GL cost ${(res[1][0] - res[0][0]).toFixed(2)}), step ${res[1][1].toFixed(2)} ms, lights ${G.lx.LX.n}`);
  } else o.push(`${id} at ${cx}`);
  if (!G.GFX.ok || !G.lx.LX.on) o.push(`!! ${id}: shaders ${G.GFX.ok} dynamic light ${G.lx.LX.on} chain ${G.GFX.chain}`);
}
return o;

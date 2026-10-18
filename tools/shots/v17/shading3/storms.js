// Shading phase 3: every open-sky Spire room under a sky flash, and the Pharaoh's storm (DU8), deterministic.
//   SHOT_HTML=<build> node ../../shot.js storms.js <out>
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev;
E('window.requestAnimationFrame = () => 0');
E(`(() => { let seed = 1; window.__shSeed = (n) => { seed = n; }; Math.random = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; })()`);
Object.assign(G.SETTINGS, window.__shSet || {});
const world = async (n) => { E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(n); };
const out = [];
const settle = () => { for (let i = 0; i < 160; i++) { G.step(1); if (G.state !== 'play') G.step(1, [], ['pause']); } E('for (const e of enemies) e.update = () => {}; if (typeof SPR !== "undefined") { SPR.skyT = 99; SPR.flash = 0; SPR.strikes = []; }'); for (let i = 0; i < 40; i++) E('renderWorld()'); };
for (const [r, x, y] of window.__rooms || [['SP2', 30, 12], ['SP3', 12, 22], ['SP4', 24, 9], ['SP5', 18, 9], ['SP6', 12, 30], ['SP8', 30, 17], ['SP9', 24, 9], ['SP11', 24, 9], ['SP14', 40, 12], ['SP15', 16, 14], ['SP16', 24, 30], ['SP17', 10, 9]]) {
  E('time = 100'); window.__shSeed(31);
  G.tp(r, x, y); settle();
  E('spSkyFlash(true); SPR.flash = 0.9; SPR.flashDx = -0.4; SPR.skyT = 99');
  G.step(1); E('SPR.skyT = 99'); await world(`${r}_flash`);
  for (let i = 0; i < 30; i++) { G.step(1); E('SPR.skyT = 99'); }
  E('spStrike(P.x + 40, { warn: 0.25, harmless: true, quiet: true }); SPR.skyT = 99');
  for (let f = 1; f <= 16; f++) { G.step(1); E('SPR.skyT = 99'); }
  await world(`${r}_strike`);
  out.push(`${r} -> ${G.room} open=${E('spOpenSky()')}`);
}
// the Pharaoh's storm (the boss arena DU8, its storm forced on, a bolt beside the knight)
E('time = 100'); window.__shSeed(31);
G.tp('DU8', 28, 14); settle();
E('DU.storm = { boss: true, on: true, t: 0, dir: 1, k: 1, wallT: 99, boltT: 0.01, walls: [], bolts: [], flash: 0, L: P.x - 160, R: P.x + 160, floor: P.y }');
for (let f = 1; f <= 50; f++) { G.step(1); E('DU.storm.wallT = 99'); if (f === 2 || f === 44) await world(`DU8_storm_f${f}`); }
out.push(`DU8 -> ${G.room} storm=${E('!!DU.storm')}`);
return out;

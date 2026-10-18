// Shading phase 3: the Spire's lightning, deterministic. A sky flash and a strike next to the knight, frames through the decay.
//   SHOT_HTML=<build> node ../../shot.js storm.js <out>     (window.__shSet: settings)
await boot(); G.SETTINGS.god = 1;
const E = G.sk.ev;
E('window.requestAnimationFrame = () => 0');
E(`(() => { let seed = 1; window.__shSeed = (n) => { seed = n; }; Math.random = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; })()`);
Object.assign(G.SETTINGS, window.__shSet || {});
const log = [];
const world = async (n) => { E(`vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height); renderWorld(); presentWorld();`); await snap(n); log.push(n + ' ' + E('[Math.round(P.x), Math.round(P.y), Math.round(cam.x), Math.round(cam.y), P.state].join(" ")')); };
const out = [];
for (const [tag, r, x, y] of window.__stRooms || [['sp8', 'SP8', 68, 17], ['sp3', 'SP3', 20, 20]]) {
  E('time = 100'); window.__shSeed(77);
  G.tp(r, x, y);
  for (let i = 0; i < 200; i++) { G.step(1); if (G.state !== 'play') G.step(1, [], ['pause']); }
  E(`(() => { let k = 0; for (const e of enemies) { e.update = () => {}; if (Math.abs(e.x - P.x) > 150) { e.x = P.x + (k % 2 ? -1 : 1) * (44 + 24 * k); e.y = P.y; } k++; } SPR.skyT = 99; SPR.flash = 0; SPR.strikes = []; })()`);
  for (let i = 0; i < 40; i++) E('renderWorld()');
  G.step(2); await world(`${tag}_0calm`);
  // a sky flash from the upper left, the strongest the game makes (0.9: the Cindervane's entrance)
  E('spSkyFlash(true); SPR.flash = 0.9; SPR.flashDx = -0.4; SPR.skyT = 99');
  const at = [1, 4, 8, 14, 22];
  for (let f = 1; f <= 22; f++) { G.step(1); E('SPR.skyT = 99'); if (at.includes(f)) await world(`${tag}_1sky_f${String(f).padStart(2, '0')}`); }
  for (let i = 0; i < 60; i++) { G.step(1); E('SPR.skyT = 99'); }
  // a strike to the knight's right (harmless): the flash leans toward it
  E('spStrike(P.x + 46, { warn: 0.25, harmless: true, quiet: true }); SPR.skyT = 99');
  for (let f = 1; f <= 26; f++) { G.step(1); E('SPR.skyT = 99'); if ([16, 19, 24].includes(f)) await world(`${tag}_2strike_f${f}`); }
  out.push(`${tag} ${G.room} open=${E('spOpenSky()')} lights=${G.lx ? G.lx.LX.n : '-'}`);
}
return out.concat(log);

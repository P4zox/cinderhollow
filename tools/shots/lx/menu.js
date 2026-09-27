// LX: Graphics menu rows, smooth bands, shaders off, flicker over time
await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = {}; for (const k of Object.keys(G.lx.LX_AMB)) G.SAVE.seenAreas[k] = 1;
const o = [];
G.tp('C2', 24, 10); G.enemies.length = 0; for (let i = 0; i < 6; i++) G.step(40);
G.SETTINGS.light = 2; G.SETTINGS.lband = 1; G.step(1); await snap('smooth');
G.SETTINGS.lband = 0; G.step(1); await snap('pixel');
G.SETTINGS.shaders = 0; G.step(1); await snap('shaders_off'); o.push('off: LX.on=' + G.lx.LX.on);
G.SETTINGS.shaders = 1; G.step(1);
// flicker: the lantern's light strength over 20 frames
const ks = []; for (let i = 0; i < 20; i++) { G.step(1); const L = G.lx.LX; for (let j = 0; j < L.n; j++) if (Math.abs(L.LP[j * 4 + 2] - 72) < 6) { ks.push(L.LP[j * 4 + 3].toFixed(2)); break; } }
o.push('lantern k over frames: ' + ks.join(' '));
// open the Graphics submenu
G.step(1, [], ['pause']); G.step(2);
if (G.menu) { G.menu.sub = { kind: 'gfx', sel: 1, off: 0 }; G.step(1); await snap('gfxmenu_light'); G.menu.sub.sel = 2; G.step(1); await snap('gfxmenu_bands'); }
G.step(1, [], ['pause']); G.step(1, [], ['pause']); G.step(2); o.push('state ' + G.state);
return o;

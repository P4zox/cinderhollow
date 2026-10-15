// Settings › Graphics: the list scrolls (17 rows), top and bottom of the list, plus a row change via input
await boot(); Object.assign(G.SETTINGS, { shaders: 1 });
G.tp('K1', 20, 10); for (let i = 0; i < 12; i++) G.step(30);
const E = G.sk.ev; E("regionCard = null");
E("menu = { screen: 'pause', tab: 3, sel: 0, sub: { kind: 'gfx', sel: 0, off: 0 } }; state = 'menu'");
G.step(1); await snap('menu_gfx_top');
for (let i = 0; i < 9; i++) G.step(1, [], ['down']);
G.step(1); await snap('menu_gfx_mid');
const before = G.SETTINGS.rays; G.step(1, [], ['right']); const after = G.SETTINGS.rays;
for (let i = 0; i < 9; i++) G.step(1, [], ['down']);
G.step(1); await snap('menu_gfx_bottom');
return { sel: E('menu.sub.sel'), row: E('GFX_ROWS[menu.sub.sel].k'), raysRowChange: [before, after] };

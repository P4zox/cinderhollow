// AREA: the set pieces — the E6 grate (whole / broken), the Last Hearth burning low, the furnace shut / open, CT2's gate,
// the forge foes in place, the map, the vents and an anvil ringing.
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); Object.assign(G.SAVE.items, { talon: 1, slam: 1 });
const out = [];
const settle = (n = 90, keep = false) => { for (let i = 0; i < n; i++) { G.step(1); if (!keep) G.enemies.length = 0; if (G.state === 'cut' || G.state === 'cine') G.step(1, [], ['pause']); if (G.state === 'dialog') G.step(1, [], ['interact']); } if (G.xs) G.xs.clean(); };
G.tp('E6', 22, 14); settle(); G.P.x = 22 * 16; settle(30); await snap('s_E6_grate_whole');
for (const x of [28, 29, 30, 31]) G.SAVE.flags['brk:E6:' + x + ',15'] = 1;
G.tp('E6', 24, 14); settle(); await snap('s_E6_grate_broken');
G.SAVE.flags['boss:hearthkeeper'] = 1; delete G.SAVE.flags['w2:open'];
G.tp('CF8', 44, 17); settle(); await snap('s_CF8_shut');
G.tp('CF8', 30, 17); settle(); await snap('s_CF8_shut_wide');
G.SAVE.flags['w2:open'] = 1; window.__game.cf.open(); for (let i = 0; i < 200; i++) G.step(1); await snap('s_CF8_opening'); for (let i = 0; i < 900 && G.state !== 'play'; i++) G.step(1);
settle(30); await snap('s_CF8_open');
G.tp('E6', 22, 14); settle(); await snap('s_E6_lowfire');
G.tp('CT2', 70, 31); settle(); await snap('s_CT2_gate');
G.tp('CT2', 83, 31); settle(10); G.step(1, [], ['interact']); G.step(30); await snap('s_CT2_touch'); settle(20);
for (const [r, x, y] of [['CF4', 44, 11], ['CF5', 30, 5], ['CF6', 40, 15], ['CF9', 30, 9], ['CF2', 40, 6], ['CF3', 16, 12]]) { G.tp(r, x, y); settle(60, true); await snap(`s_foes_${r}`); out.push(r + ': ' + G.enemies.filter(e => e.alive).map(e => e.type).join(',')); }
G.enemies.length = 0;
G.tp('CF4', 64, 11); settle(20); G.P.face = 1; G.step(1, [], ['heavy']); for (let i = 0; i < 26; i++) G.step(1); await snap('s_CF4_ring'); settle(30); await snap('s_CF4_open');
G.tp('CF6', 14, 15); for (let i = 0; i < 400; i++) { G.step(1); G.enemies.length = 0; const C = window.__game.cf.CFA; if (C.vents[0] && C.vents[0].any && i > 60) break; } await snap('s_CF6_vents');
return out;

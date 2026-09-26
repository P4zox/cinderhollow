await boot(); window.__godS = true;
G.give({ items: { wings: 1, talon: 1, hook: 1, emberdash: 1, gale: 1, slam: 1 } });
Object.assign(G.SAVE.flags, { 'sf:stair': 1, 'boss:orrery': 1, 'boss:astrel': 1 });
const R = {};
const T = (k, v) => { R[k] = JSON.stringify(v); };
// SF1 down to X4 (fall through the open bottom)
G.tp('SF1', 17, 4); S(5); T('sf1_down', run('left', 400, 'X4'));
// SF2 west->east, east->west
G.tp('SF2', 2, 12); S(5); clearFoes(); T('sf2_we', run('right', 1500, 'SF3'));
G.tp('SF2', 61, 12); S(5); clearFoes(); T('sf2_ew', run('left', 1500, 'SF1'));
// SF3 both ways
G.tp('SF3', 2, 12); S(5); T('sf3_we', run('right', 600, 'SF4'));
G.tp('SF3', 21, 12); S(5); T('sf3_ew', run('left', 600, 'SF2'));
// SF4 climb bottom -> top -> SF5
G.tp('SF4', 3, 48); S(5); clearFoes();
walkTo(20); T('sf4_1', jumpTo(22, 43)); T('sf4_2', jumpTo(16, 39)); walkTo(8); T('sf4_3', jumpTo(4, 35)); T('sf4_4', jumpTo(10, 30)); walkTo(19); T('sf4_5', jumpTo(22, 26));
T('sf4_6', jumpTo(17, 21)); walkTo(8); T('sf4_7', jumpTo(4, 17)); T('sf4_8', jumpTo(10, 12)); T('sf4_top', run('right', 600, 'SF5'));
// SF4 top -> down (drop through the gaps) -> exit west into SF3
G.tp('SF4', 12, 12); S(5); clearFoes(); T('sf4_down1', run('left', 500)); T('sf4_down_pos', pos());
// SF5 both ways (orrery dead)
G.tp('SF5', 2, 12); S(5); T('sf5_we', run('right', 900, 'SF6'));
G.tp('SF5', 37, 12); S(5); T('sf5_ew', run('left', 900, 'SF4'));
// SF6: rim -> descend -> bottom
G.tp('SF6', 4, 12); S(5); clearFoes(); T('sf6_desc', run('right', 300)); for (let i = 0; i < 200 && !G.P.ground; i++) S(1); T('sf6_land', pos());
G.tp('SF6', 6, 48); S(5); clearFoes();
T('sf6_c1', jumpTo(2, 41)); T('sf6_c2', jumpTo(8, 35)); T('sf6_c3', jumpTo(2, 29)); T('sf6_c4', jumpTo(8, 23)); T('sf6_c5', jumpTo(10, 17)); T('sf6_c6', jumpTo(5, 12));
// SF6 bottom -> SF8 (gate closed from the east until the lever) -> SF4
G.tp('SF6', 4, 48); S(5); T('sf6_w', run('left', 400, 'SF8')); clearFoes();
T('sf8_lever', walkTo(36)); S(1, [], ['interact']); S(60);
T('sf8_gate', { flag: G.SAVE.flags['lever:SF8'] }); T('sf8_w', run('left', 900, 'SF4'));
G.tp('SF8', 2, 12); S(5); clearFoes(); T('sf8_e', run('right', 900, 'SF6'));
// SF6 <-> SF7
G.tp('SF6', 22, 48); S(5); T('sf6_e', run('right', 400, 'SF7'));
G.tp('SF7', 10, 16); S(5); T('sf7_w', run('left', 600, 'SF6'));
// Moonstep secrets: SF6 ledge -> Last Light, without and with the Moonstep
G.tp('SF6', 4, 12); S(5); clearFoes(); T('sf6_hop', jumpTo(14, 11)); T('sf6_ledge', jumpTo(23, 12));
G.tp('SF6', 26, 12); S(20); await flush(); T('ms_without', tower('right', 2, 'right', 90));
G.SAVE.items.moonstep = 1;
G.tp('SF6', 26, 12); S(20); await flush(); T('ms_with', tower('right', 3, 'right', 90)); S(20, ['right']); T('ms_with_room', pos()); await snap('sf9');
T('sf9_back', run('left', 300, 'SF6'));
G.SAVE.items.moonstep = 0;
G.tp('SF2', 49, 9); S(20); clearFoes(); await flush(); T('isle_without', tower(null, 2, 'left', 34));
G.SAVE.items.moonstep = 1;
G.tp('SF2', 49, 9); S(20); await flush(); T('isle_with', tower(null, 3, 'left', 34)); await snap('isle');
T('items', Object.keys(G.SAVE.flags).filter(k => k.startsWith('item:SF')));
return R;

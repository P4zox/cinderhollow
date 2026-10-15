await boot();
const E = G.sk.ev, out = [];
const settle = async () => { await new Promise(r => setTimeout(r, 300)); G.step(1); };
G.step(20); E('openPauseMenu()'); G.step(3); E('wmScreenOpen(menu)'); G.step(2); await settle(); await snap('m0_mastery');
G.step(1, [], ['confirm']); G.step(3); out.push('list ' + E('menu.mastery.list')); await settle(); await snap('m1_list');
for (let i = 0; i < 12; i++) G.step(1, [], ['down']); G.step(3); await snap('m2_list_scrolled');
G.step(1, [], ['right']); G.step(3); await snap('m3_katana');
G.step(1, [], ['back']); G.step(2); out.push('after back list ' + E('menu.mastery && menu.mastery.list'));
return out;

// Funeral Peal in the menus: Esc > Equipment (the art row: icon, name, FP, desc of the selected row) and the Weapon Mastery card.
// Run: SHOT_HTML=$PWD/web/dist/v17_bell.html node tools/shots/shot.js tools/shots/v17/bell/menu.js tools/shots/v17/bell/snap_menu
await boot();
const E = G.sk.ev, out = [];
const settle = async () => { await new Promise(r => setTimeout(r, 300)); G.step(1); };
E("wmEquip('bell', { quiet: true })"); G.step(20);
out.push('art ' + E('SAVE.art'));
E('openPauseMenu()'); G.step(3);
await settle(); await snap('equip0');
G.step(1, [], ['down']); G.step(3); await settle(); await snap('equip1');
E('wmScreenOpen(menu)'); G.step(2); await settle(); await snap('mastery');
return out;

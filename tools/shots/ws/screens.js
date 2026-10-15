// every new WS screen, for a look: title weapon select, shrine Change Weapon, Esc mastery screen, skill-tree Weapon Mastery page,
// equipment slot (read-only), training weapon tab
const E = G.sk.ev, out = [];
const settle = async () => { await new Promise(r => setTimeout(r, 300)); G.step(1); };   // let the weapon overlays decode
E("state = 'title'; titleSel = 0"); G.step(3);
const choose = name => { const i = E('titleOptions()').indexOf(name); E(`titleSel = ${i}`); G.step(1, [], ['confirm']); G.step(2); };
choose('New Game'); out.push('diff open ' + E('TITLE_DIFF.open') + ' stage ' + E('TITLE_DIFF.stage'));
await snap('t1_diff');
G.step(1, [], ['confirm']); G.step(20); out.push('after diff confirm stage ' + E('TITLE_DIFF.stage'));
await settle(); await snap('t2_weapon0');
// the preview mid-swing: jump the loop clock past the idle part
const idle = E("Math.max(1100, wmTagMs(sheet('player'), 'idle'))");
E(`TITLE_WSEL.t0 = time - ${idle / 1000 + 0.12}`); G.step(1); await settle(); await snap('t2b_longsword_swing');
E("TITLE_WSEL.sel = 1"); E(`TITLE_WSEL.t0 = time - ${idle / 1000 + 0.15}`); G.step(1); await settle(); await snap('t2c_katana_swing');
E("TITLE_WSEL.sel = 0; TITLE_WSEL.t0 = time"); G.step(1);
G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(45); await settle(); await snap('t3_weapon_maul');
G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(30); await settle(); await snap('t4_weapon_whip');
G.step(1, [], ['back']); out.push('Esc -> stage ' + E('TITLE_DIFF.stage') + ' open ' + E('TITLE_DIFF.open'));
G.step(1, [], ['confirm']); G.step(2); for (let i = 0; i < 3; i++) G.step(1, [], ['right']);
G.step(1, [], ['confirm']); G.step(5);
for (let i = 0; i < 300 && G.state !== 'play'; i++) { if (G.state === 'cine' || G.state === 'cut') G.step(1, [], ['pause']); else G.step(10); }
out.push(`started: state ${G.state} weapon ${G.SAVE.weapon} type ${G.ws.wtype()} diff ${G.SAVE.diff} pending ${JSON.stringify(G.ws.WSEL.pending)}`);
G.step(20);
E('openPauseMenu()'); G.step(3); await settle(); await snap('e1_equip_weapon');
G.step(1, [], ['confirm']); G.step(3); out.push('Enter on weapon -> mastery ' + !!E('menu.mastery') + ' pick ' + !!E('menu.pick')); await snap('e2_mastery');
G.step(1, [], ['down']); G.step(1, [], ['down']); G.step(3); await snap('e3_mastery_gs');
G.step(1, [], ['back']); G.step(2); out.push('Esc -> back to slots, menu ' + E('menu && menu.screen') + ' mastery ' + !!E('menu.mastery'));
G.step(1, [], ['right']); G.step(2); out.push('←→ on weapon slot keeps ' + G.SAVE.weapon);
G.step(1, [], ['map']); G.step(2); await snap('e4_inventory');
G.step(1, [], ['back']); G.step(2);
G.st.open(0); G.step(2); G.st.page(1); G.step(30); await settle(); await snap('s1_tree_mastery');
out.push('tree pages ' + G.st.layout().map(p => p.name).join(' / ') + ' arsenal nodes ' + G.st.SKILLS.filter(s => /^m_/.test(s.id)).length);
G.st.input('right'); G.st.input('right'); G.step(10); await snap('s2_tree_mastery_sel');
G.st.input('back'); G.step(2);
E('menu = null; state = "play"'); G.step(2);
E("openShrineMenu({ name: 'Test Shrine' })"); G.step(2); E(`menu.sel = SHRINE_OPTS.indexOf('Change Weapon')`); G.step(1, [], ['confirm']); G.step(2);
G.step(1, [], ['down']); G.step(1, [], ['down']); G.step(1, [], ['down']); G.step(1, [], ['down']); G.step(5); await settle(); await snap('w1_change_sns');
E("closeMenu()"); G.SAVE.weapons.maul = 3; G.SAVE.weapons.knight_shield = 5; G.SAVE.inv.emberstone = 6; G.SAVE.cinders = 5000;
E("menu = { screen: 'forge', sel: 4 }; state = 'menu'"); G.step(3); await settle(); await snap('f1_forge');
E("closeMenu()"); G.step(2);
return out;

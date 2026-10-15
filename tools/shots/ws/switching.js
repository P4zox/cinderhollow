// weapons change only at shrines: the Esc slot is read-only (Enter shows Weapon Mastery), the bag can't equip one,
// the shrine's Change Weapon does; the Training Grounds pick any type and set its rank
await boot();
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const w0 = G.SAVE.weapon;
E('openPauseMenu()'); G.step(2);
G.step(1, [], ['right']); G.step(1, [], ['left']); G.step(2);
ok(G.SAVE.weapon === w0, 'Esc › Equipment ←→ on the weapon slot does nothing');
ok(E('toasts.map(t => t.msg)').some(m => /shrine/.test(m)), 'and says to rest at a shrine');
G.step(1, [], ['confirm']); G.step(2);
ok(!!E('menu.mastery') && !E('menu.pick'), 'Enter opens Weapon Mastery, not a picker');
G.step(1, [], ['down']); G.step(1, [], ['confirm']); G.step(2);
ok(G.SAVE.weapon === w0, 'confirming in the mastery screen does not equip');
G.step(1, [], ['back']); G.step(1);
ok(E('menu && menu.screen') === 'pause' && !E('menu.mastery'), 'Esc leaves the mastery screen, not the menu');
G.step(1, [], ['map']); G.step(2); E('menu.cat = 0; menu.bar = false; menu.isel = 1'); G.step(1, [], ['confirm']); G.step(2);
ok(G.SAVE.weapon === w0, 'Inventory › Weapons: Enter does not equip');
await snap('inv_weapons');
G.step(1, [], ['pause']); G.step(2);
// the shrine
E("openShrineMenu({ name: 'Test Shrine' })"); G.step(2);
ok(E('SHRINE_OPTS').includes('Change Weapon'), 'shrine menu lists Change Weapon');
E(`menu.sel = SHRINE_OPTS.indexOf('Change Weapon')`); G.step(1, [], ['confirm']); G.step(2);
ok(E('menu.screen') === 'wchange', 'it opens the Change Weapon screen');
for (let i = 0; i < 5; i++) G.step(1, [], ['down']);   // longsword -> dual blades
G.step(20); await snap('shrine_change');
G.step(1, [], ['confirm']); G.step(2);
ok(G.SAVE.weapon === 'twinfangs' && G.ws.wtype() === 'dual' && G.SAVE.art === 'twin_tempest', `took up ${G.SAVE.weapon} (${G.ws.wtype()}), art ${G.SAVE.art}`);
ok(E('menu.screen') === 'shrine', 'back on the shrine menu');
ok(E('D.wid') === 'twinfangs', 'derived stats follow the new weapon');
ok(JSON.parse(localStorage.getItem('cinderhollow_save_v1')).weapon === 'twinfangs', 'saved');
// mouse: click the Whip row, then click it again (= confirm)
E(`menu = wchangeOpen(menu)`); G.step(2);
const click = (x, y) => E(`(() => { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1); const cx = r.left + (ox + ${x} * scale) / k, cy = r.top + (oy + ${y} * scale) / k;
  const init = { clientX: cx, clientY: cy, button: 0, buttons: 1, pointerType: 'mouse', pointerId: 1, bubbles: true, cancelable: true };
  window.dispatchEvent(new PointerEvent('pointermove', init)); })()`);
const down = (x, y) => E(`(() => { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1); const cx = r.left + (ox + ${x} * scale) / k, cy = r.top + (oy + ${y} * scale) / k;
  view.dispatchEvent(new PointerEvent('pointerdown', { clientX: cx, clientY: cy, button: 0, buttons: 1, pointerType: 'mouse', pointerId: 1, bubbles: true, cancelable: true })); })()`);
click(60, 31 + 8 * 18.6 + 8); G.step(2); ok(E('menu.sel') === 8, 'mouse hover selects the Whip row: ' + E('menu.sel'));
down(60, 31 + 8 * 18.6 + 8); G.step(2); ok(G.SAVE.weapon === 'headsman_chain', 'click takes it up: ' + G.SAVE.weapon);
E('closeMenu()'); G.step(2);
// the Training Grounds weapon tab
E('trainingStart()'); G.step(30);
E('trnOpen(1)'); G.step(2);
const rows = E('trnRows({ tab: 1 }).map(r => r.label)'); out.push('training weapon tab: ' + rows.join(' | '));
ok(['Longsword', 'Katana', 'Greatsword', 'Maul', 'Sword & Shield', 'Dual Blades', 'Spear', 'Staff', 'Whip'].every(n => rows.includes(n)) && rows.includes('Mastery rank'), 'nine types + a Mastery rank row');
E(`(() => { const R = trnRows(menu); const i = R.findIndex(r => r.label === 'Spear'); menu.sel = i; })()`); G.step(1, [], ['confirm']); G.step(2);
ok(G.SAVE.weapon === 'spear', 'Training: pick the Spear freely');
E(`(() => { const R = trnRows(menu); menu.sel = R.findIndex(r => r.label === 'Mastery rank'); })()`); G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(2);
ok(G.ws.rank('spear') === 4, 'Training: Mastery rank ▸▸▸ -> IV: ' + G.ws.rank('spear'));
await snap('training_weapon');
E('trainingExit()'); G.step(5);
ok(G.SAVE.weapon === 'headsman_chain' && G.ws.rank('spear') === 1, 'leaving the Training Grounds restores the real journey');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;

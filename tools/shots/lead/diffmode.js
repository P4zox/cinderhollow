// difficulty modes, quit confirmation, title chooser (mouse), the golden seal's one-hit fix
await boot();
const E = G.sk.ev, out = [];
const ev = (type, x, y, o = {}) => E(`(() => { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1);
  const init = { clientX: r.left + (ox + ${x} * scale) / k, clientY: r.top + (oy + ${y} * scale) / k, button: ${o.button || 0}, pointerType: 'mouse', pointerId: 1, bubbles: true, cancelable: true };
  ('${type}' === 'pointermove' ? window : view).dispatchEvent(new PointerEvent('${type}', init)); })()`);
const click = (x, y) => { ev('pointermove', x, y); G.step(1); ev('pointerdown', x, y); G.step(2); };
// --- title: New Game opens the chooser; pick Hard with the mouse
E("state = 'title'; titleSel = 0"); G.step(2);
const opts = E('titleOptions()'); const ng = opts.indexOf('New Game');
click(192, 96 + ng * 13 - 4); out.push('title click New Game -> chooser ' + E('TITLE_DIFF.open'));
await snap('chooser');
click(192, 104 + 2 * 14 - 4); out.push('click Hard -> state ' + G.state + ' diff ' + G.SAVE.diff);
await boot(); G.step(10);
// --- boss HP by mode (Gravetusk)
const bossHp = d => { E(`SAVE.diff = ${d}`); delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1; G.tp('C5', 6, 10); G.step(3); return G.boss.maxHp; };
out.push(`hound maxHp easy ${bossHp(0)} normal ${bossHp(1)} hard ${bossHp(2)}`);
// --- damage outside a boss fight
const dmgAt = d => { E(`SAVE.diff = ${d}`); G.tp('R1', 12, 10); G.step(3); G.P.hp = G.D.maxHp; G.P.inv = 0; const h = G.P.hp; E(`P.lastHit = null; hurtPlayer(100, 1, 'dt' + time + ${d})`); return Math.round(h - G.P.hp); };
out.push(`100 dmg taken easy ${dmgAt(0)} normal ${dmgAt(1)} hard ${dmgAt(2)}`);
// --- cinders
const gain = d => { E(`SAVE.diff = ${d}`); const c = G.SAVE.cinders; E('gainCinders(100, P.x, P.y)'); return G.SAVE.cinders - c; };
out.push(`gainCinders(100) easy +${gain(0)} normal +${gain(1)} hard +${gain(2)}`);
// --- Hard: the remnant holds half
E('SAVE.diff = 2; SAVE.remnant = null; SAVE.cinders = 1000; finishDeath()'); G.step(90);
out.push('hard death with 1000 -> remnant ' + JSON.stringify(G.SAVE.remnant && G.SAVE.remnant.amount));
E('SAVE.diff = 0; SAVE.remnant = null; SAVE.cinders = 1000; finishDeath()'); G.step(2);
out.push('easy death with 1000 -> kept ' + G.SAVE.cinders + ' remnant ' + JSON.stringify(G.SAVE.remnant && G.SAVE.remnant.amount)); G.step(88);
E('SAVE.diff = 1; SAVE.remnant = null; SAVE.cinders = 1000; finishDeath()'); G.step(2); out.push('normal death with 1000 -> kept ' + G.SAVE.cinders + ' remnant ' + JSON.stringify(G.SAVE.remnant && G.SAVE.remnant.amount)); G.step(88); out.push('state ' + G.state + ' cinders now ' + G.SAVE.cinders + ' room ' + G.room.id);
out.push('normal death with 1000 -> remnant ' + JSON.stringify(G.SAVE.remnant && G.SAVE.remnant.amount));
// --- Settings row cycles the mode
E('openPauseMenu(); menu.tab = 3; menu.sel = SETTING_ROWS.findIndex(r => r.k === "diff")'); G.step(2);
G.step(1, [], ['right']); out.push('settings right -> diff ' + G.SAVE.diff);
await snap('settings');
// --- quit asks first
E('menu.sel = SETTING_ROWS.findIndex(r => r.k === "quit")'); G.step(1);
G.step(1, [], ['confirm']); out.push('quit -> popup ' + !!E('menu && menu.confirmQuit') + ' state ' + G.state);
await snap('quit_popup');
G.step(1, [], ['confirm']); out.push('confirm on Stay -> popup ' + !!E('menu && menu.confirmQuit') + ' state ' + G.state);
G.step(1, [], ['confirm']); G.step(1, [], ['left']); G.step(1, [], ['confirm']); out.push('Quit -> state ' + G.state);
// --- golden seal: a weak heavy rings once and the swing ends on time
E("state = 'play'; menu = null"); delete G.SAVE.flags['sc:seal'];
G.tp('R1', 3, 10); G.step(20); G.P.face = -1; G.step(1, ['left'], ['heavy']);
let n = 0; while (G.P.state === 'heavy' && n < 600) { G.step(1); n++; }
out.push(`uncharged heavy on the seal lasted ${n} frames (open ground ~59)`);
return out;

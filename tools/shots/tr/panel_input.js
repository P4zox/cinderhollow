// the control panel with keyboard, controller and mouse
await new Promise(r=>setTimeout(r,300));
const E = G.sk.ev, T = G.trn, out = [];
const ev = (type, x, y, o = {}) => E(`(() => { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1);
  const cx = r.left + (ox + ${x} * scale) / k, cy = r.top + (oy + ${y} * scale) / k;
  const init = { clientX: cx, clientY: cy, button: ${o.button || 0}, buttons: 1, pointerType: 'mouse', pointerId: 1, bubbles: true, cancelable: true, deltaY: ${o.dy || 0} };
  const tgt = '${type}' === 'pointermove' ? window : view;
  if ('${type}' === 'wheel') view.dispatchEvent(new WheelEvent('wheel', init));
  else if ('${type}' === 'mousedown') view.dispatchEvent(new MouseEvent('mousedown', init));
  else tgt.dispatchEvent(new PointerEvent('${type}', init)); })()`);
const click = async (x, y, button = 0) => { ev('pointermove', x, y); G.step(1); ev('pointerdown', x, y, { button }); ev('mousedown', x, y, { button }); G.step(2); };
const M = () => E('menu ? { screen: menu.screen, sel: menu.sel, tab: menu.tab } : null');
const key = (code) => { window.dispatchEvent(new KeyboardEvent('keydown', { code, bubbles: true })); G.step(1); window.dispatchEvent(new KeyboardEvent('keyup', { code, bubbles: true })); G.step(1); };
T.start(); G.step(20);
// ---- keyboard
key('Escape'); out.push('Esc in play -> ' + JSON.stringify(M()));
const v0 = G.SAVE.stats.vig; key('ArrowRight'); out.push(`→ on Vigor: ${v0} -> ${G.SAVE.stats.vig}`);
key('Enter'); key('ArrowRight'); out.push(`Enter (step ×10) then →: -> ${G.SAVE.stats.vig}`); key('Enter');
key('ArrowDown'); key('ArrowDown'); out.push('↓↓ -> sel ' + M().sel);
key('Tab'); out.push('Tab -> tab ' + M().tab); key('KeyQ'); out.push('Q -> tab ' + M().tab);
key('Tab'); key('ArrowDown'); key('ArrowDown'); key('Enter'); out.push('Weapon tab ↓↓ Enter -> weapon ' + G.SAVE.weapon);
key('Escape'); out.push('Esc -> state ' + G.state);
key('Tab'); out.push('Tab in play -> ' + JSON.stringify(M()));
key('Escape');
// ---- controller (standard mapping): Start opens, RB/LB tabs, D-pad, A confirm, B back
const pad = { id: 'Xbox Wireless Controller (STANDARD GAMEPAD)', connected: true, buttons: Array.from({ length: 17 }, () => ({ pressed: false, value: 0 })), axes: [0, 0, 0, 0] };
navigator.getGamepads = () => [pad];
const frame = n => { for (let i = 0; i < n; i++) { E('padPoll(1/60)'); G.step(1); } };
const btn = (i) => { pad.buttons[i].pressed = true; frame(3); pad.buttons[i].pressed = false; frame(3); };
frame(3);
btn(9); out.push('pad Start -> ' + JSON.stringify(M()));
btn(5); btn(5); btn(5); btn(5); out.push('pad RB×4 -> tab ' + (M() && M().tab));
btn(13); btn(13); const c0 = E('TRN.hitbox'); btn(0); out.push(`pad ↓↓ A on World › Hitbox overlay (${E('trnRows(menu)[menu.sel].label')}): ${c0} -> ${E('TRN.hitbox')}`); btn(0);
btn(4); out.push('pad LB -> tab ' + M().tab);
btn(1); out.push('pad B -> state ' + G.state);
navigator.getGamepads = () => []; frame(3);
// ---- mouse
T.open(0); G.step(2);
await click(108, 17); out.push('click WEAPON tab -> tab ' + M().tab);
ev('pointermove', 100, 49 + 12.2 * 4); G.step(2); out.push('hover row 4 -> sel ' + M().sel);
await click(100, 49 + 12.2 * 4); out.push('click row 4 -> weapon ' + G.SAVE.weapon);
const lv0 = E('SAVE.weapons[SAVE.weapon]'); await click(224, 49 + 12.2 * 1); out.push(`click ▸ on Upgrade: +${lv0} -> +${E('SAVE.weapons[SAVE.weapon]')}`);
ev('wheel', 100, 120, { dy: 400 }); G.step(1); out.push('wheel down -> sel ' + M().sel + ' off ' + E('menu.off'));
await click(52, 17); await click(100, 49 + 12.2 * 1); out.push('Player tab, click Vigor -> sel ' + M().sel + ' vig ' + G.SAVE.stats.vig);
const v1 = G.SAVE.stats.vig; await click(224, 49 + 12.2 * 1); out.push(`click ▸ Vigor: ${v1} -> ${G.SAVE.stats.vig}`);
await snap('panel_mouse');
const vt = E('SAVE.stats.vig'); const sx = E('Math.round(236 - 22 - 44)'); await click(sx, 49 + 12.2 * 1); out.push(`click +10 Vigor: ${vt} -> ${G.SAVE.stats.vig}`);
const hb = E('P.state'); await click(300, 120); out.push('click empty panel area: state ' + G.state + ' player ' + G.P.state + ' (no swing)');
await click(100, 100, 2); out.push('right-click -> state ' + G.state);
// spawn tab via mouse: summon the Hound
T.open(4); G.step(2); const rows = T.rows(4); const hi = rows.findIndex(r => r.boss && r.boss.kind === 'hound');
E(`menu.sel = ${hi}; menu.off = ${Math.max(0, hi - 5)}`); G.step(2);
await click(100, 49 + 12.2 * 5); out.push('click Gravetusk -> state ' + G.state + ' boss ' + (G.boss && G.boss.kind) + ' room ' + G.room);
return out;

// v15 platform: every screen that lists the weapon types, with 14 of them (run with tools/shots/shot.js).
// New Game select strip, shrine Change Weapon, Esc Weapon Mastery + Move List, the skill tree's Mastery page, the forge,
// the Training Grounds weapon tab and the inventory: nothing overflows (checked from the layout numbers + snapshots)
// and the mouse still selects every row.
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const settle = async () => { await new Promise(r => setTimeout(r, 300)); G.step(1); };
const ptr = (type, x, y) => E(`(() => { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1); const cx = r.left + (ox + ${x} * scale) / k, cy = r.top + (oy + ${y} * scale) / k;
  const init = { clientX: cx, clientY: cy, button: 0, buttons: 1, pointerType: 'mouse', pointerId: 1, bubbles: true, cancelable: true };
  (${JSON.stringify(type)} === 'pointermove' ? window : view).dispatchEvent(new PointerEvent(${JSON.stringify(type)}, init)); })()`);
const n = E('WTYPES.length');
ok(n === 14, '14 types');
localStorage.removeItem('cinderhollow_old_saves_v1');
// ---- New Game: choose your weapon
E("state = 'title'; menu = null; titleSel = 0; TITLE_DIFF.open = false; TITLE_SLOTS.screen = null"); G.step(3);
{ const i = E('titleOptions()').indexOf('New Game'); E(`titleSel = ${i}`); G.step(1, [], ['confirm']); G.step(2); }
G.step(1, [], ['confirm']); G.step(20);
ok(E('TITLE_DIFF.stage') === 'weapon', 'the weapon select is open');
const pitch = E('Math.min(36, Math.floor(372 / WTYPES.length))'), x0 = 192 - pitch * (n - 1) / 2, cs = Math.min(26, pitch - 4);
ok(x0 - cs / 2 - 2 >= 0 && x0 + pitch * (n - 1) + cs / 2 + 2 <= 384, `strip fits the screen: cells ${cs} px, pitch ${pitch}, ${(x0 - cs / 2).toFixed(1)}..${(x0 + pitch * (n - 1) + cs / 2).toFixed(1)}`);
let hov = 0;
for (let i = 0; i < n; i++) { ptr('pointermove', x0 + pitch * i, 45); G.step(2); if (E('TITLE_WSEL.sel') === i) hov++; }
ok(hov === n, `mouse hover selects each of the ${n} cells (${hov})`);
for (const i of [9, 10, 11, 12, 13]) { E(`TITLE_WSEL.sel = ${i}; TITLE_WSEL.t0 = time - 1.2`); G.step(2); await settle(); await snap('select_' + E('WTYPES[TITLE_WSEL.sel]')); }
ptr('pointermove', x0 + pitch * 13, 45); G.step(2); ptr('pointerdown', x0 + pitch * 13, 45); G.step(3);
for (let i = 0; i < 300 && G.state !== 'play'; i++) { if (G.state === 'cine' || G.state === 'cut') G.step(1, [], ['pause']); else G.step(10); }
ok(G.SAVE.weapon === 'dirge_bell' && G.ws.wtype() === 'bell' && G.SAVE.art === 'warcry', `clicking the Warbell begins the journey with it (${G.SAVE.weapon}, ${G.SAVE.art})`);
ok(Object.keys(G.SAVE.weapons).length === 14, 'the new journey holds all 14 weapons');
G.step(20);
// ---- shrine: Change Weapon
E("openShrineMenu({ name: 'Test Shrine' })"); G.step(2); E(`menu.sel = SHRINE_OPTS.indexOf('Change Weapon')`); G.step(1, [], ['confirm']); G.step(2);
ok(E('menu.screen') === 'wchange', 'Change Weapon open');
const ph = E('wchangeRowH()');
ok(30 + n * ph <= 202, `Change Weapon rows fit the panel: ${n} x ${ph.toFixed(2)} px -> ends at ${(30 + n * ph).toFixed(1)} (panel bottom 202)`);
hov = 0; for (let i = 0; i < n; i++) { ptr('pointermove', 60, 30 + i * ph + ph / 2); G.step(1); if (E('menu.sel') === i) hov++; }
ok(hov === n, `mouse hover selects each row (${hov})`);
ptr('pointermove', 60, 30 + 11 * ph + ph / 2); G.step(2); await settle(); await snap('shrine_fist');
ptr('pointerdown', 60, 30 + 11 * ph + ph / 2); G.step(2);
ok(G.SAVE.weapon === 'penitent_knuckles' && G.ws.wtype() === 'fist' && G.SAVE.art === 'bloodstep', `clicking Martial Arts takes it up (${G.SAVE.weapon})`);
E('closeMenu()'); G.step(2);
// ---- Esc › Equipment › Weapon Mastery + Move List
E('openPauseMenu()'); G.step(3); G.step(1, [], ['confirm']); G.step(3);
ok(!!E('menu.mastery'), 'Weapon Mastery open');
const mph = E('Math.min(16.8, 151 / WTYPES.length)');
ok(48 + n * mph <= 200, `mastery rows fit: ${n} x ${mph.toFixed(2)} px -> ${(48 + n * mph).toFixed(1)} (panel bottom 202)`);
hov = 0; for (let i = 0; i < n; i++) { ptr('pointermove', 80, 48 + i * mph + mph / 2); G.step(1); if (E('menu.mastery.sel') === i) hov++; }
ok(hov === n, `mouse hover selects each mastery row (${hov})`);
E('menu.mastery.sel = WTYPES.indexOf("scythe")'); G.step(3); await snap('mastery_scythe');
G.step(1, [], ['confirm']); G.step(3);
ok(!!E('menu.mastery.list') && E('wmMoveList("scythe").length') >= 8, 'Enter -> the Scythe move list (' + E('wmMoveList("scythe").length') + ' moves)');
await snap('movelist_scythe');
G.step(1, [], ['right']); G.step(2); ok(E('WTYPES[menu.mastery.sel]') === 'bell', '→ in the move list: the Warbell');
G.step(1, [], ['right']); G.step(2); ok(E('WTYPES[menu.mastery.sel]') === 'longsword', '→ wraps round to the Longsword');
G.step(1, [], ['back']); G.step(1, [], ['back']); G.step(2);
G.step(1, [], ['map']); G.step(2); await snap('inventory');
G.step(1, [], ['back']); G.step(2);
// ---- skill tree: the Mastery page
G.st.open(0); G.step(2); const mi = G.st.layout().findIndex(p => p.id === 'mastery'); G.st.page(mi); G.step(20);
const fit = E(`(() => { const pg = stLayout().find(p => p.id === 'mastery'); return { z: stZooms(pg), w: pg.b.x1 - pg.b.x0, h: pg.b.y1 - pg.b.y0, aw: pg.aw, vp: ST_VP }; })()`);
ok(fit.z.length === 1 && fit.z[0] === 1 && fit.w <= fit.vp.w && fit.h <= fit.vp.h, `Mastery page fits the field at full size: ${fit.w} x ${fit.h} in ${fit.vp.w} x ${fit.vp.h}, alcoves ${fit.aw} px`);
await settle(); await snap('tree_mastery');
E("ST.sel = 'wm:saxe'"); G.step(6); await snap('tree_mastery_saxe');
G.st.input('right'); G.step(2); ok(E('ST.sel') === 'wm:bow', 'tree: → from Switch Axe -> Bow: ' + E('ST.sel'));
G.st.input('up'); G.step(2); out.push('tree: ↑ from Bow -> ' + E('ST.sel'));
G.st.input('back'); G.step(2); E('menu = null; state = "play"'); G.step(2);
// ---- the forge
G.SAVE.inv.emberstone = 6; G.SAVE.cinders = 5000; G.SAVE.weapons.gravegrinder = 2;
E("menu = { screen: 'forge', sel: 0 }; state = 'menu'"); G.step(3);
const fph = E('Math.min(14.4, 134 / Object.keys(SAVE.weapons).filter(id => WEAPONS[id]).length)'), fy0 = 56 - (1 - fph / 14.4) * 8;
ok(fy0 + (n - 1) * fph <= 186, `forge rows fit above its footer: last row at ${(fy0 + (n - 1) * fph).toFixed(1)}`);
hov = 0; for (let i = 0; i < n; i++) { ptr('pointermove', 100, fy0 + i * fph - 10.5 * fph / 14.4 + fph / 2); G.step(1); if (E('menu.sel') === i) hov++; }
ok(hov === n, `forge: mouse hover selects each row (${hov})`);
await settle(); await snap('forge');
E('closeMenu()'); G.step(2);
// ---- the Training Grounds weapon tab
E('trainingStart()'); G.step(30); E('trnOpen(1)'); G.step(3);
const rows = E('trnRows({ tab: 1 }).map(r => r.label)');
ok(['Switch Axe', 'Bow', 'Martial Arts', 'Scythe', 'Warbell'].every(x => rows.includes(x)), 'Training weapon tab lists the five: ' + rows.slice(-6).join(' | '));
E(`(() => { const R = trnRows(menu); menu.sel = R.findIndex(r => r.label === 'Scythe'); })()`); G.step(1, [], ['confirm']); G.step(3);
ok(G.SAVE.weapon === 'requiem_scythe', 'Training: pick the Scythe');
await settle(); await snap('training_weapons');
E('trainingExit()'); G.step(5);
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;

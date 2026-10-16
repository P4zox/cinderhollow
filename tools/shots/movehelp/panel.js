// MOVEHELP: the Move List panel (Esc › Equipment › Weapon mastery › Enter): keyboard, mouse hits, every entry of all 14
// types renders, a snapshot per type (montage: tools/shots/movehelp/montage.py), and the saved Combo hints setting.
// SHOT_HTML=web/dist/movehelp.html node tools/shots/shot.js tools/shots/movehelp/panel.js tools/shots/movehelp/out
await boot();
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const settle = async () => { await new Promise(r => setTimeout(r, 260)); G.step(1); };
const S = () => E('menu && menu.mastery');
G.step(20); E('openPauseMenu()'); G.step(3); E('wmScreenOpen(menu)'); G.step(2);
G.step(1, [], ['confirm']); G.step(3);
ok(!!E('menu.mastery.list') && !E('MH.err'), 'Enter on the mastery screen opens the Move List panel');
const T0 = E('menu.mastery.sel'), types = E('WTYPES');
// keyboard: ↓ / ↑ walk the entries (wrapping), ←/→ switch the weapon type
const n0 = E(`mhList(WTYPES[${T0}]).items.length`);
G.step(1, [], ['down']); G.step(1, [], ['down']); G.step(2); ok(E('menu.mastery.row') === 2, `↓ ↓ -> row ${E('menu.mastery.row')}`);
G.step(1, [], ['up']); G.step(1, [], ['up']); G.step(1, [], ['up']); G.step(2); ok(E('menu.mastery.row') === n0 - 1, `↑ from the top wraps to the last row (${E('menu.mastery.row')} of ${n0})`);
G.step(1, [], ['right']); G.step(2); ok(E('menu.mastery.sel') === (T0 + 1) % types.length && E('menu.mastery.row') === 0, `→ switches to ${E('WTYPES[menu.mastery.sel]')}, row 0`);
G.step(1, [], ['left']); G.step(2); ok(E('menu.mastery.sel') === T0, '← back');
// mouse: hover a row selects it; click the ▸ arrow switches type; the ◂ MASTERY button closes the list
G.step(2);
const hits = E('UIM.shown.map(h => [h.x, h.y, h.w, h.h, !!h.hover, !!h.click])');
const rowHits = hits.filter(h => h[0] > 10 && h[0] < 16 && h[2] > 190 && h[4]);
ok(rowHits.length >= 10, `${rowHits.length} row hit boxes on screen (one per visible entry)`);
E(`(() => { const h = UIM.shown.filter(h => h.x > 10 && h.x < 16 && h.w > 190 && h.hover)[5]; h.hover(); })()`); G.step(2);
const r5 = E('menu.mastery.row'); ok(r5 > 0, `hovering the 6th visible row selects entry ${r5}`);
E(`(() => { const h = UIM.shown.filter(h => h.x > 10 && h.x < 16 && h.w > 190 && h.click)[2]; h.click(); })()`); G.step(2);
ok(E('menu.mastery.row') !== r5, `clicking the 3rd visible row selects entry ${E('menu.mastery.row')}`);
E(`(() => { const h = UIM.shown.find(h => h.x > 40 && h.x < 140 && h.y < 40 && h.w < 12 && h.click && h.x > 60); h.click(); })()`); G.step(2);
ok(E('menu.mastery.sel') === (T0 + 1) % types.length, `clicking ▸ switches the type (${E('WTYPES[menu.mastery.sel]')})`);
E(`(() => { const h = UIM.shown.find(h => Math.abs(h.x - 34) < 0.5 && h.y < 40 && h.click); h.click(); })()`); G.step(2);
ok(E('menu.mastery.sel') === T0, 'clicking ◂ switches back');
// the wheel scrolls: 30 rows down moves the list (top > 0)
for (let i = 0; i < 18; i++) G.step(1, [], ['down']); G.step(3);
ok(E('menu.mastery.top') > 0, `scrolled: first visible line ${E('menu.mastery.top')}`);
// every entry of every type renders (no error), and the list holds every combos entry once
let rows = 0, prev = 0; const missing = [];
for (let ti = 0; ti < types.length; ti++) {
  const t = types[ti];
  E(`menu.mastery.sel = ${ti}; menu.mastery.row = 0; menu.mastery.top = 0`);
  const L = E(`mhList('${t}').items.length`), C = E(`MV.types['${t}'].combos.length`);
  if (L !== C) missing.push(`${t} ${L}/${C}`);
  for (let k = 0; k < L; k++) { E(`menu.mastery.row = ${k}`); G.step(1); rows++; if (E('MH.err')) { missing.push(t + ' row ' + k + ': ' + E('MH.err')); E('MH.err = null'); } }
  prev += E(`mhList('${t}').items.filter(it => it.row.paths.length && mhPreviewSeq('${t}', it.row).length).length`);
}
ok(!missing.length, `every Move List entry of the ${types.length} types renders (${rows} rows)${missing.length ? ': ' + missing.slice(0, 4).join('; ') : ''}`);
const withMove = E(`WTYPES.reduce((s, t) => s + mhList(t).items.filter(it => it.row.paths.length).length, 0)`);
ok(prev === withMove, `${prev}/${withMove} entries with a real move have an animation preview (the rest show the idle)`);
// numbers: the final move row of mapped entries
const nums = E(`WTYPES.reduce((s, t) => s + mhList(t).items.filter(it => mhFinal(it.row) && mhNumbers(mhFinal(it.row))).length, 0)`);
ok(nums >= withMove * 0.9, `${nums} entries show dmg / poise / stamina numbers`);
// snapshots: each type, an entry deep enough to have a multi-step preview
for (let ti = 0; ti < types.length; ti++) {
  const t = types[ti];
  const k = E(`(() => { const L = mhList('${t}').items; let b = 0, bn = 0; L.forEach((it, i) => { const n = it.row.paths[0] ? it.row.paths[0].steps.length : 0; if ((+it.e.rank || 1) === 1 && n > bn && n <= 4) { b = i; bn = n; } }); return b; })()`);
  E(`menu.mastery.sel = ${ti}; menu.mastery.row = ${k}; menu.mastery.top = 0; menu.mastery.t0 = time - 0.9`); G.step(2);
  await settle(); await snap('panel_' + String(ti).padStart(2, '0') + '_' + t);
}
// a locked entry (Mastery I) and the scrolled mastery group
E(`menu.mastery.sel = WTYPES.indexOf('longsword'); menu.mastery.row = mhList('longsword').items.findIndex(it => it.e.name === 'Wheel slash'); menu.mastery.t0 = time - 1.2`); G.step(2); await settle(); await snap('panel_locked');
G.step(1, [], ['back']); G.step(2); ok(!!E('menu.mastery') && !E('menu.mastery.list'), 'Esc closes the panel first (back to the mastery screen)');
E('menu = null; state = "play"'); G.step(2);
// the setting is saved (outside the Training Grounds sandbox) and survives a reload of the settings object
const row = E("SETTING_ROWS.findIndex(r => r.k === 'combohint')");
E(`openPauseMenu(); menu.tab = 3; menu.sel = ${row}`); G.step(2); await settle(); await snap('settings_row');
E("pauseInput('right')");
ok(E('SETTINGS.combohint') === 0 && JSON.parse(E('localStorage.getItem(SETTINGS_KEY)')).combohint === 0, 'Settings › Combo hints Off is saved');
E("pauseInput('left')");
ok(E('SETTINGS.combohint') === 1 && JSON.parse(E('localStorage.getItem(SETTINGS_KEY)')).combohint === 1, 'and On again (saved)');
E('menu = null; state = "play"');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL OK');
return out;

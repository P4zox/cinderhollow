// New Game: difficulty, then a starting weapon (all nine, with name, identity, strengths / weaknesses, art, looping preview)
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
const wait = ms => new Promise(r => setTimeout(r, ms));
localStorage.removeItem('cinderhollow_old_saves_v1');
E("state = 'title'; menu = null; titleSel = 0; TITLE_DIFF.open = false; TITLE_SLOTS.screen = null"); G.step(3);
const choose = name => { const i = E('titleOptions()').indexOf(name); E(`titleSel = ${i}`); G.step(1, [], ['confirm']); G.step(2); };
choose('New Game');
ok(E('TITLE_DIFF.open') && E('TITLE_DIFF.stage') === 'diff', 'New Game opens the difficulty first');
G.step(1, [], ['down']); G.step(1, [], ['confirm']); G.step(2);   // Hard
ok(E('TITLE_DIFF.stage') === 'weapon', 'then the weapon select');
const n = E('WTYPES.length'); ok(n === 14, 'all fourteen types offered (v15: nine + five)');
for (let i = 0; i < n; i++) {
  E(`TITLE_WSEL.sel = ${i}; TITLE_WSEL.t0 = time`); G.step(2); await wait(250); G.step(1);
  const t = E('WTYPES[TITLE_WSEL.sel]'), I = E(`WTYPE_INFO['${t}']`);
  ok(!!(I.name && I.desc && I.str && I.weak && I.art && E(`!!ARTS['${I.art}']`) && E(`sheet('player').has(wmFirstTag('${t}'))`)), `${t}: ${I.name}, art ${I.art}, preview tag ${E(`wmFirstTag('${t}')`)}`);
  if (i === 0 || i === 3 || i === 5 || i === 8 || i === 9 || i === 13) { G.step(28); await wait(150); G.step(1); await snap('select_' + t); }
}
G.step(1, [], ['back']); G.step(1);
ok(E('TITLE_DIFF.open') && E('TITLE_DIFF.stage') === 'diff', 'Esc from the weapons goes back to the difficulty');
G.step(1, [], ['back']); G.step(1);
ok(!E('TITLE_DIFF.open') && E('state') === 'title', 'Esc again leaves to the title');
choose('New Game'); G.step(1, [], ['down']); G.step(1, [], ['confirm']); G.step(2);
G.step(1, [], ['right']); G.step(1, [], ['right']); G.step(1, [], ['left']);   // -> katana
ok(E('WTYPES[TITLE_WSEL.sel]') === 'katana', '←→ moves the choice');
// mouse: hover the Spear cell, click it
const ev = (type, x, y) => E(`(() => { const r = view.getBoundingClientRect(), k = view.width / (r.width || 1); const cx = r.left + (ox + ${x} * scale) / k, cy = r.top + (oy + ${y} * scale) / k;
  const init = { clientX: cx, clientY: cy, button: 0, buttons: 1, pointerType: 'mouse', pointerId: 1, bubbles: true, cancelable: true };
  (${JSON.stringify(type)} === 'pointermove' ? window : view).dispatchEvent(new PointerEvent(${JSON.stringify(type)}, init)); })()`);
const pitch = E('Math.min(36, Math.floor(372 / WTYPES.length))'), cx = 192 - pitch * (n - 1) / 2 + pitch * 6;   // v15: the strip scales with the count
ev('pointermove', cx, 45); G.step(2); ok(E('WTYPES[TITLE_WSEL.sel]') === 'spear', 'mouse hover selects the Spear');
ev('pointerdown', cx, 45); G.step(3);
ok(E('state') === 'cine' || E('state') === 'play', 'clicking it begins the journey (intro): ' + E('state'));
for (let i = 0; i < 300 && G.state !== 'play'; i++) { if (G.state === 'cine' || G.state === 'cut') G.step(1, [], ['pause']); else G.step(10); }
ok(G.SAVE.weapon === 'spear' && G.ws.wtype() === 'spear' && G.SAVE.art === 'thunder_lunge', `the journey starts with the Spear (${G.SAVE.weapon}, ${G.SAVE.art})`);
ok(G.SAVE.diff === 2, 'and on Hard (the difficulty survives the intro): ' + G.SAVE.diff);
ok(E('D.wid') === 'spear', 'derived stats use it');
ok(JSON.parse(localStorage.getItem('cinderhollow_save_v1')).weapon === 'spear', 'saved');
ok(!G.ws.WSEL.pending, 'the pending choice is cleared');
ok(Object.keys(G.SAVE.weapons).length === n && Object.values(G.SAVE.weapons).every(v => v === 0), 'all fourteen at +0');
// a plain newGame (tests, NG) still gives the Longsword
G.newGame(); for (let i = 0; i < 300 && G.state !== 'play'; i++) { if (G.state === 'cine' || G.state === 'cut') G.step(1, [], ['pause']); else G.step(10); }
ok(G.SAVE.weapon === 'longsword', 'newGame() without a choice: Longsword');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;

// ------------------------------------------------------------------ Settings sub-screens: Key bindings and Cheats (test)
// Opened from the Settings tab (08b_menus.js routes M.sub here). Bindings live in 00_core.js (BINDINGS / bindKey).

const CHEAT_ROWS = [
  { k: 'god', label: 'God mode', toggle: true, desc: 'You take no damage and cannot die.' },
  { k: 'infst', label: 'Infinite stamina', toggle: true, desc: 'Stamina never runs out.' },
  { k: 'inffp', label: 'Infinite FP', toggle: true, desc: 'FP never runs out: cast and use arts freely.' },
  { k: 'armory', label: 'Armory: unlock all gear', desc: 'Every weapon, art, spell and charm, plus wall-jump and double jump.' },
  { k: 'tech', label: 'Grant all techniques', desc: 'Root Hook, Ember Dash, Gale Cloak, Cinder Slam, swimming and the triple jump.' },
  { k: 'shrines', label: 'Kindle every shrine', desc: 'Light every shrine so you can travel anywhere.' },
];

function settingsSubInput(M, a) {
  const S = M.sub, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  if (S.capture) return;   // the next key press goes to KEY_CAPTURE instead of here
  if (['pause', 'back', 'heavy'].includes(a) || (a === 'left' && S.kind === 'cheats')) { M.sub = null; sfx.menu(); return; }
  if (S.kind === 'cheats') {
    const n = CHEAT_ROWS.length;
    if (a === 'up') { S.sel = (S.sel + n - 1) % n; sfx.menu(); return; }
    if (a === 'down') { S.sel = (S.sel + 1) % n; sfx.menu(); return; }
    const R = CHEAT_ROWS[S.sel];
    if (R.toggle && (conf || a === 'right')) { SETTINGS[R.k] = SETTINGS[R.k] ? 0 : 1; saveSettings(); sfx.menu(); return; }
    if (!conf) return;
    menu = null; state = 'play'; clearBuffer();
    if (R.k === 'armory') giveArmory();
    else if (R.k === 'tech') { grantTechniques(); SAVE.items.tidebreath = 1; SAVE.items.moonstep = 1; saveGame(); }
    else if (R.k === 'shrines') { for (const r of ROOMS) if (r.shrine && !r.test && !SAVE.shrines.includes(r.id)) SAVE.shrines.push(r.id); saveGame(); sfx.kindle(); toast('Every shrine burns. Rest at one to travel.', 4); }
    return;
  }
  // key bindings: rows = actions + a reset row
  const n = BINDABLE.length + 1;
  if (a === 'up') { S.sel = (S.sel + n - 1) % n; sfx.menu(); }
  else if (a === 'down') { S.sel = (S.sel + 1) % n; sfx.menu(); }
  else if (a === 'left' || a === 'right') { S.col = a === 'left' ? 0 : 1; sfx.menu(); }
  else if (conf) {
    if (S.sel === BINDABLE.length) { BINDINGS = defaultBindings(); saveBindings(); sfx.kindle(); toast('Keys reset to defaults', 2.5); return; }
    const action = BINDABLE[S.sel][0], slot = Math.min(S.col, (BINDINGS[action] || []).length);   // no gaps: slot 2 fills only after slot 1
    S.capture = true; sfx.glint();
    KEY_CAPTURE = code => {
      S.capture = false; clearBuffer();
      if (code === 'Escape') { sfx.menu(); return; }
      if (code === 'Backspace') { bindKey(action, slot, null); sfx.menu(); return; }
      if (FIXED_KEYS[code]) { sfx.deny(); toast(`${keyLabel(code)} is reserved for menus`, 2.5); return; }
      const was = Object.entries(BINDINGS).find(([a2, codes]) => a2 !== action && codes.includes(code));
      bindKey(action, slot, code); sfx.kindle();
      if (was) toast(`${keyLabel(code)} moved from ${BINDABLE.find(b => b[0] === was[0])[1]}`, 3);
    };
  }
}

function renderSettingsSub(M) {
  const S = M.sub;
  uiBackdrop(0.9); uiStrips();
  if (S.kind === 'cheats') {
    uiTitle('CHEATS', 17, 9);
    text('For testing. They work on this save only while switched on.', W / 2, 30, 5.6, '#9a8f78', 'center', { weight: 400 });
    panel(72, 38, 240, 18 + CHEAT_ROWS.length * 17);
    CHEAT_ROWS.forEach((R, i) => {
      const y = 54 + i * 17, sel = i === S.sel;
      if (sel) uiSel(77, y - 11, 230, 15);
      text(R.label, 86, y, 6.8, sel ? '#f5e3b0' : '#d8cdb4', 'left', { weight: sel ? 600 : 400 });
      if (R.toggle) { const on = !!SETTINGS[R.k]; text((sel ? '◂ ' : '') + (on ? 'On' : 'Off') + (sel ? ' ▸' : ''), 300, y, 6.8, on ? '#ffd070' : '#8a7f6a', 'right', { weight: 600 }); }
      else text('▸', 300, y, 6.8, UIC.gold, 'right');
    });
    const R = CHEAT_ROWS[S.sel];
    text(R.desc, W / 2, 62 + CHEAT_ROWS.length * 17, 5.8, '#b8ab90', 'center', { weight: 400 });
    uiFooter(R.toggle ? [['↑↓', 'select'], ['Enter', 'toggle'], ['Esc', 'back']] : [['↑↓', 'select'], ['Enter', 'use'], ['Esc', 'back']]);
    return;
  }
  uiTitle('KEY BINDINGS', 17, 9);
  if (TOUCH_UI) text('Key bindings are for keyboards; touch buttons are fixed.', W / 2, 28, 5.4, '#9a8f78', 'center', { weight: 400 });
  const rows = [...BINDABLE, ['__reset', 'Reset to defaults']], vis = 11, n = rows.length;
  S.off = clamp(S.off, Math.max(0, S.sel - vis + 1), Math.min(S.sel, n - vis));
  const px = 40, pw = 304, top = 36, rh = 14;
  panel(px, top, pw, 12 + vis * rh);
  text('ACTION', px + 12, top + 10, 5, '#8a7f6a', 'left', { spacing: 1 });
  text('KEY 1', px + 196, top + 10, 5, '#8a7f6a', 'center', { spacing: 1 });
  text('KEY 2', px + 262, top + 10, 5, '#8a7f6a', 'center', { spacing: 1 });
  for (let r = 0; r < vis && S.off + r < n; r++) {
    const i = S.off + r, [act, label] = rows[i], y = top + 24 + r * rh, sel = i === S.sel;
    if (sel) uiSel(px + 4, y - 10, pw - 8, rh - 1);
    if (act === '__reset') { text(label, px + pw / 2, y, 6.4, sel ? '#f5e3b0' : UIC.gold, 'center', { weight: 600 }); continue; }
    text(label, px + 12, y, 6.2, sel ? '#f5e3b0' : '#d8cdb4', 'left', { weight: sel ? 600 : 400 });
    const codes = BINDINGS[act] || [];
    for (let c = 0; c < 2; c++) {
      const cx = px + (c ? 262 : 196), focus = sel && S.col === c, cap = focus && S.capture;
      const lbl = cap ? '…' : codes[c] ? keyLabel(codes[c]) : '—';
      const w = Math.max(26, textW(lbl, 6, 600) + 10);
      vctx.fillStyle = focus ? 'rgba(176,138,58,0.35)' : 'rgba(255,255,255,0.05)';
      vctx.fillRect(ox + (cx - w / 2) * scale, oy + (y - 8) * scale, w * scale, 11 * scale);
      if (focus) { vctx.strokeStyle = cap ? `rgba(255,208,112,${0.6 + 0.4 * Math.sin(time * 8)})` : '#b08a3a'; vctx.lineWidth = Math.max(1, scale * 0.5); vctx.strokeRect(ox + (cx - w / 2) * scale, oy + (y - 8) * scale, w * scale, 11 * scale); }
      text(lbl, cx, y, 6, codes[c] || cap ? '#f1e6c8' : '#6f6656', 'center', { weight: 600 });
    }
  }
  if (S.off > 0) text('▲', px + pw - 10, top + 16, 5, '#9a8f78', 'center');
  if (S.off + vis < n) text('▼', px + pw - 10, top + 12 + vis * rh, 5, '#9a8f78', 'center');
  if (S.capture) {
    const act = BINDABLE[S.sel];
    vctx.fillStyle = 'rgba(0,0,0,0.55)'; vctx.fillRect(ox, oy, W * scale, H * scale);
    vctx.fillStyle = 'rgb(12,9,16)'; vctx.fillRect(ox + 92 * scale, oy + 84 * scale, 200 * scale, 44 * scale);
    vctx.strokeStyle = '#b08a3a'; vctx.strokeRect(ox + 92 * scale, oy + 84 * scale, 200 * scale, 44 * scale);
    text(`Press a key for “${act[1]}”`, W / 2, 101, 7, '#f5e3b0', 'center', { weight: 600 });
    text('Esc cancel  ·  Backspace clear this slot', W / 2, 116, 5.6, '#b8ab90', 'center', { weight: 400 });
  }
  uiFooter([['↑↓', 'action'], ['←→', 'key slot'], ['Enter', S.sel === BINDABLE.length ? 'reset' : 'rebind'], ['Esc', 'back']]);
}

// the controls guide's key caps follow the bindings too (tokens in 29_ui2.js are the default keys)
(function followBindingsInGuide() {
  const TOK = { J: ['attack', 0], K: ['heavy', 0], I: ['parry', 0], L: ['roll', 0], O: ['art', 0], H: ['hook', 0], C: ['hook', 1], S: ['down', 1],
                Space: ['jump', 0], '↓': ['down', 0], U: ['cast', 0], Q: ['spell', 0], F: ['heal', 0], R: ['mana', 0], E: ['interact', 0] };
  for (const pg of GUIDE_PAGES) {
    if (!pg.rows || pg.name === 'Keyboard') continue;
    const orig = pg.rows;
    pg.rows = () => orig().map(r => [r[0].map(t => { const m = TOK[t]; if (!m) return t; const k = keysOf(m[0]); return k[m[1]] || k[0] || t; }), ...r.slice(1)]);
  }
})();

// Infinite FP (Cheats); god mode and infinite stamina live in 09_main.js
HOOKS.update.push(() => { if (P && D && SETTINGS.inffp) P.fp = D.maxFp; });

// ------------------------------------------------------------------ pause menu (equipment / inventory / status / settings), shop, forge
const SETTINGS_KEY = 'cinderhollow_settings';
const SETTINGS = { music: 0.7, sfx: 0.8, shake: 1, numbers: 1, god: 0, infst: 0, inffp: 0 };
try { Object.assign(SETTINGS, JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}')); } catch (e) {}
function saveSettings() { try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(SETTINGS)); } catch (e) {} if (master) master.gain.value = SETTINGS.sfx; }
const TABS = ['Equipment', 'Inventory', 'Status', 'Settings'];
function openPauseMenu() { menu = { screen: 'pause', tab: 0, sel: 0 }; state = 'menu'; clearBuffer(); sfx.menu(); }

function equipRows() {
  const rows = [{ k: 'weapon', label: 'Weapon' }, { k: 'art', label: 'Weapon Art' }];
  for (let i = 0; i < SAVE.spellSlots; i++) rows.push({ k: 'spell', i, label: `Spell ${i + 1}` });
  for (let i = 0; i < SAVE.charmSlots; i++) rows.push({ k: 'charm', i, label: `Charm ${i + 1}` });
  return rows;
}
function knownSpells() { return Object.keys(SPELLS).filter(spellKnown); }
function cycle(list, cur, d, allowNone) {
  const opts = allowNone ? [null, ...list] : list;
  if (!opts.length) return cur;
  const i = opts.indexOf(cur);
  return opts[(i + d + opts.length) % opts.length];
}
function changeEquip(row, d) {   // quick cycle (←→ on a slot); the picker grid lives in 29_ui2.js
  let nx;
  if (row.k === 'weapon') nx = cycle(Object.keys(WEAPONS).filter(id => SAVE.weapons[id] !== undefined), SAVE.weapon, d);
  else if (row.k === 'art') nx = cycle(Object.keys(ARTS).filter(id => SAVE.arts.includes(id)), SAVE.art, d);
  else {
    const key = row.k === 'spell' ? 'spellsEq' : 'charmsEq', others = SAVE[key].filter((s, j) => j !== row.i);
    const pool = row.k === 'spell' ? knownSpells() : Object.keys(CHARMS).filter(c => SAVE.charms.includes(c));
    nx = cycle(pool.filter(s => !others.includes(s)), SAVE[key][row.i] || null, d, true);
  }
  applyEquip(row, nx);
}
function invList() {
  const out = [];
  for (const id of Object.keys(SAVE.weapons)) out.push({ id: 'w:' + id, extra: SAVE.weapons[id] ? '+' + SAVE.weapons[id] : '' });
  for (const [id, n] of Object.entries(SAVE.inv)) if (n > 0) out.push({ id, extra: '×' + n });
  for (const id of SAVE.charms) out.push({ id });
  for (const id of SAVE.spellsOwned) out.push({ id: 'sp:' + id });
  for (const id of SAVE.arts) out.push({ id: 'art:' + id });
  for (const id of Object.keys(SAVE.items)) if (SAVE.items[id] && ITEMS[id]) out.push({ id });
  if (SAVE.flaskPot) out.push({ id: 'herb', extra: `flasks +${SAVE.flaskPot * 10}%` });
  return out;
}
const SETTING_ROWS = [
  { k: 'guide', label: 'Controls & techniques' }, { k: 'keys', label: 'Key bindings' },
  { k: 'music', label: 'Music volume', step: 0.1 }, { k: 'sfx', label: 'Effects volume', step: 0.1 },
  { k: 'shake', label: 'Screen shake', step: 0.5 }, { k: 'numbers', label: 'Damage numbers', toggle: true },
  { k: 'cheats', label: 'Cheats (test)' }, { k: 'quit', label: 'Save & quit to title' },
];

const SETTING_ACTIONS = ['guide', 'keys', 'cheats', 'quit'];
function pauseInput(a) {
  const M = menu, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  if (M.guide) return guideInput(M, a);
  if (M.sub) return settingsSubInput(M, a);
  if (M.tab === 0 && M.pick) return pickInput(M, a);
  if (a === 'pause' || a === 'back' || a === 'heavy') { menu = null; state = 'play'; clearBuffer(); saveGame(); return; }
  if (a === 'spell' || a === 'map') { M.tab = (M.tab + (a === 'spell' ? 3 : 1)) % 4; M.sel = 0; sfx.menu(); return; }
  if (M.tab === 0) equipInput(M, a);
  else if (M.tab === 1) invInput(M, a);
  else if (M.tab === 2) {
    if (a === 'left' || a === 'right') { M.tab = (M.tab + (a === 'left' ? 3 : 1)) % 4; M.sel = 0; }
  } else {
    M.n = SETTING_ROWS.length;
    if (a === 'up') { M.sel = (M.sel + M.n - 1) % M.n; sfx.menu(); } else if (a === 'down') { M.sel = (M.sel + 1) % M.n; sfx.menu(); }
    const R = SETTING_ROWS[M.sel];
    if (R.k === 'guide') { if (conf || a === 'right') { M.guide = { page: TOUCH_UI ? GUIDE_PAGES.length - 1 : 0, off: 0 }; sfx.menu(); } return; }
    if (R.k === 'quit' && conf) { menu = null; saveGame(); state = 'title'; titleSel = 0; return; }
    if (R.k === 'keys') { if (conf || a === 'right') { M.sub = { kind: 'keys', sel: 0, col: 0, off: 0 }; sfx.menu(); } return; }
    if (R.k === 'cheats') { if (conf || a === 'right') { M.sub = { kind: 'cheats', sel: 0 }; sfx.menu(); } return; }
    if ((a === 'left' || a === 'right' || conf) && !SETTING_ACTIONS.includes(R.k)) {
      const d = a === 'left' ? -1 : 1;
      if (R.toggle) SETTINGS[R.k] = SETTINGS[R.k] ? 0 : 1;
      else SETTINGS[R.k] = clamp(Math.round((SETTINGS[R.k] + d * R.step) * 10) / 10, 0, 1);
      saveSettings(); sfx.menu();
    }
  }
}
function statsLines() {
  const W = D.W, lv = D.wlv;
  return [
    ['Level', levelOf(SAVE.stats)], ['Cinders', SAVE.cinders], ['HP', `${Math.round(P.hp)} / ${D.maxHp}`], ['FP', `${Math.round(P.fp)} / ${D.maxFp}`], ['Stamina', D.maxSt],
    ['Attack', Math.round(D.light)], ['Heavy', Math.round(D.heavy * 2)], ['Spell power', Math.round(D.spell * 100)],
    ['Vigor', SAVE.stats.vig], ['Mind', SAVE.stats.mnd], ['Endurance', SAVE.stats.end], ['Strength', SAVE.stats.str], ['Dexterity', SAVE.stats.dex], ['Faith', SAVE.stats.fth],
    ['Deaths', SAVE.deaths], ['Time', fmtTime(SAVE.playTime)], ['Journey', (SAVE.ngp || 0) + 1],
  ];
}
function renderPauseMenu() {
  const M = menu;
  if (M.guide) return renderGuide(M);
  if (M.sub) return renderSettingsSub(M);
  uiBackdrop(0.84); uiStrips(); uiTabs(M.tab);
  if (M.tab === 0) renderEquipTab(M);
  else if (M.tab === 1) renderInvTab(M);
  else if (M.tab === 2) {
    panel(14, 30, 356, 172);
    const L = statsLines();
    L.forEach(([k, v], i) => {
      const col = Math.floor(i / 9), row = i % 9, x = 26 + col * 118, y = 48 + row * 15;
      text(k, x, y, 6.2, '#9a8f78', 'left', { weight: 500 }); text(String(v), x + 100, y, 6.8, '#e8dcc0', 'right');
    });
    text(`Skills ${SAVE.skills.length}/${SKILLS.length}  ·  Weapons ${Object.keys(SAVE.weapons).length}/${Object.keys(WEAPONS).length}  ·  Charms ${SAVE.charms.length}/${Object.keys(CHARMS).length}`, W / 2, 190, 6, '#b8ab90', 'center', { weight: 400 });
    uiFooter([['←→', 'tabs'], ...tabHint(), ['Esc', 'close']]);
  } else {
    const rh = Math.min(17, 158 / SETTING_ROWS.length);
    panel(92, 30, 200, 16 + SETTING_ROWS.length * rh);
    SETTING_ROWS.forEach((R, i) => {
      const y = 44 + i * rh, sel = i === M.sel;
      if (sel) uiSel(97, y - rh + 4, 190, rh - 1);
      text(R.label, 104, y, 6.8, sel ? '#f5e3b0' : ['guide', 'keys', 'cheats'].includes(R.k) ? UIC.gold : '#d8cdb4', 'left', { weight: sel || R.k === 'guide' ? 600 : 400 });
      if (['guide', 'keys', 'cheats'].includes(R.k)) { text('▸', 280 + (sel ? uiPulse(6) : 0), y, 6.8, UIC.gold, 'right'); uiFade(104, 280, y + rh / 2 - 2.5, UI_RGB.accent, 0.35); }
      if (SETTING_ACTIONS.includes(R.k)) return;
      const v = SETTINGS[R.k], label = R.toggle ? (v ? 'On' : 'Off') : R.k === 'shake' ? (v === 0 ? 'Off' : v < 1 ? 'Low' : 'Full') : Math.round(v * 100) + '%';
      text((sel ? '◂ ' : '') + label + (sel ? ' ▸' : ''), 280, y, 6.8, '#e8dcc0', 'right');
    });
    const R = SETTING_ROWS[M.sel];
    uiFooter(['guide', 'keys', 'cheats'].includes(R.k) ? [['↑↓', 'select'], ['Enter', 'open'], ...tabHint(), ['Esc', 'close']]
      : SETTING_ACTIONS.includes(R.k) ? [['↑↓', 'select'], ['Enter', 'confirm'], ...tabHint(), ['Esc', 'close']]
      : [['↑↓', 'select'], ['←→', 'change'], ...tabHint(), ['Esc', 'close']]);
  }
}

// ---- shops & forge
function shopList(id) { return SHOPS[id].filter(e => (SAVE.bought[id + ':' + e.item] || 0) < e.stock); }
function shopInput(a) {
  const M = menu, L = shopList(M.shop), conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  M.n = Math.max(1, L.length);
  if (a === 'up') { M.sel = (M.sel + M.n - 1) % M.n; sfx.menu(); } else if (a === 'down') { M.sel = (M.sel + 1) % M.n; sfx.menu(); }
  else if (['pause', 'back', 'heavy', 'roll'].includes(a)) return leaveShop();
  else if (conf && L[M.sel]) {
    const e = L[M.sel], owned = (ITEMS[e.item].weapon && SAVE.weapons[ITEMS[e.item].weapon] !== undefined) || (ITEMS[e.item].charm && SAVE.charms.includes(e.item)) || (ITEMS[e.item].spell && spellKnown(ITEMS[e.item].spell));
    if (owned) { sfx.deny(); toast('You already have that'); return; }
    if (SAVE.cinders < e.price) { sfx.deny(); toast('Not enough cinders'); return; }
    SAVE.cinders -= e.price; SAVE.bought[M.shop + ':' + e.item] = (SAVE.bought[M.shop + ':' + e.item] || 0) + 1;
    grantItem(e.item); M.sel = Math.min(M.sel, Math.max(0, shopList(M.shop).length - 1));
  }
}
function leaveShop() { menu = null; if (dialog && dialog.resume) { dialog.resume = false; state = 'dialog'; advanceDialog(); } else state = 'play'; clearBuffer(); }
function renderShop() {
  const M = menu, L = shopList(M.shop);
  vctx.fillStyle = 'rgba(5,4,8,0.6)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  panel(20, 22, 200, 176);
  text(M.shop === 'ashwright' ? 'ASHWRIGHT’S WARES' : 'THE SCRIBE’S TEACHINGS', 30, 38, 7.5, '#e6c77a', 'left', { spacing: 1 });
  icon('cinder', 180, 30, 10); text(String(SAVE.cinders), 212, 38, 7, '#e8dcc0', 'right');
  L.forEach((e, i) => {
    const d = ITEMS[e.item], y = 56 + i * 15, sel = i === M.sel, afford = SAVE.cinders >= e.price;
    if (sel) { vctx.fillStyle = 'rgba(176,138,58,0.16)'; vctx.fillRect(ox + 24 * scale, oy + (y - 10) * scale, 192 * scale, 14 * scale); }
    icon(d.icon, 28, y - 10, 12);
    text(d.name, 44, y - 1, 6.6, sel ? '#f5e3b0' : '#d8cdb4', 'left', { weight: sel ? 600 : 400 });
    text(String(e.price), 212, y - 1, 6.4, afford ? '#e6c77a' : '#8a6050', 'right');
  });
  if (!L.length) text('Sold out.', 30, 60, 6.5, '#9a8f78');
  const e = L[M.sel];
  panel(226, 22, 140, 176, 0.7);
  if (e) { const d = ITEMS[e.item]; icon(d.icon, 234, 30, 24); text(d.name, 234, 66, 7.2, '#e6c77a'); let y = 80; for (const l of wrap(d.desc, 124, 6)) { text(l, 234, y, 6, '#d8cdb4', 'left', { weight: 400 }); y += 8.2; } }
  text('Enter — buy    Esc — leave', 120, 192, 5.5, '#7f745f', 'center', { weight: 400 });
}
function forgeInput(a) {
  const M = menu, L = Object.keys(SAVE.weapons), conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  M.n = L.length;
  if (a === 'up') { M.sel = (M.sel + M.n - 1) % M.n; sfx.menu(); } else if (a === 'down') { M.sel = (M.sel + 1) % M.n; sfx.menu(); }
  else if (['pause', 'back', 'heavy', 'roll'].includes(a)) return leaveShop();
  else if (conf) {
    const id = L[M.sel], lv = SAVE.weapons[id];
    if (lv >= 5) { sfx.deny(); toast('It can take no more'); return; }
    const c = upgradeCost(lv);
    if ((SAVE.inv.emberstone || 0) < c.stones || SAVE.cinders < c.cinders) { sfx.deny(); toast(`Needs ${c.stones} Emberstone${c.stones > 1 ? 's' : ''} and ${c.cinders} cinders`); return; }
    SAVE.inv.emberstone -= c.stones; SAVE.cinders -= c.cinders; SAVE.weapons[id] = lv + 1;
    refreshDerived(); sfx.levelup(); tone(1500, 0.3, 0.08, 'square', 0.5); shake = 3; flashScreen = 0.2;
    toast(`${WEAPONS[id].name} tempered to +${lv + 1}`); saveGame();
  }
}
function renderForge() {
  const M = menu, L = Object.keys(SAVE.weapons);
  vctx.fillStyle = 'rgba(5,4,8,0.6)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  panel(20, 22, 344, 176);
  text('TEMPER A WEAPON', 30, 38, 7.5, '#e6c77a', 'left', { spacing: 1 });
  text(`Emberstones ${SAVE.inv.emberstone || 0}     Cinders ${SAVE.cinders}`, 354, 38, 6.2, '#e8dcc0', 'right');
  L.forEach((id, i) => {
    const w = WEAPONS[id], lv = SAVE.weapons[id], y = 58 + i * 16, sel = i === M.sel;
    if (sel) { vctx.fillStyle = 'rgba(176,138,58,0.16)'; vctx.fillRect(ox + 24 * scale, oy + (y - 11) * scale, 336 * scale, 15 * scale); }
    icon('w_' + id, 28, y - 11, 12);
    text(`${w.name}${lv ? ' +' + lv : ''}`, 44, y - 1, 6.6, sel ? '#f5e3b0' : '#d8cdb4', 'left', { weight: sel ? 600 : 400 });
    const a0 = Math.round(weaponAR(SAVE.stats, id, lv)), a1 = lv < 5 ? Math.round(weaponAR(SAVE.stats, id, lv + 1)) : null;
    text(a1 ? `Attack ${a0} → ${a1}` : `Attack ${a0}  (max)`, 230, y - 1, 6.2, '#b8ab90', 'left');
    if (lv < 5) { const c = upgradeCost(lv); text(`${c.stones}◆  ${c.cinders}`, 356, y - 1, 6.2, (SAVE.inv.emberstone || 0) >= c.stones && SAVE.cinders >= c.cinders ? '#e6c77a' : '#8a6050', 'right'); }
  });
  text('Enter — temper    Esc — leave', W / 2, 192, 5.5, '#7f745f', 'center', { weight: 400 });
}

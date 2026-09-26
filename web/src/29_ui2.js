// ------------------------------------------------------------------ UI v2 (agent U): shared widgets, equipment slots + item picker,
// inventory, controls & techniques guide, cinematic first-visit region titles, travel map with a shrine list.
// Everything draws onto vctx in low-res (384x216) coordinates through the helpers in 08_ui.js (text, box, icon, wrap, panel).
const UIC = { gold: '#e6c77a', hi: '#f5e3b0', text: '#e8dcc0', body: '#d8cdb4', muted: '#b8ab90', dim: '#9a8f78', faint: '#7f745f',
              line: '#6d5a3a', accent: '#b08a3a', up: '#8fd89a', down: '#e07a62', fp: '#8fb0e8' };
const UI_RGB = { gold: '230,199,122', accent: '176,138,58' };
const TOUCH_UI = (() => { try { return matchMedia('(pointer: coarse)').matches; } catch (e) { return false; } })();
const KEY_LABEL = TOUCH_UI ? { Enter: 'OK', Esc: 'Menu', Tab: 'Map', Q: '' } : {};
const kl = k => (k in KEY_LABEL ? KEY_LABEL[k] : k);

// ---- widgets
function uiRect(x, y, w, h, color, a = 1) { vctx.globalAlpha = a; vctx.fillStyle = color; vctx.fillRect(ox + x * scale, oy + y * scale, w * scale, h * scale); vctx.globalAlpha = 1; }
function uiHair(x, y, w, color = UIC.line, a = 1) { vctx.globalAlpha = a; vctx.fillStyle = color; vctx.fillRect(ox + x * scale, oy + y * scale, w * scale, Math.max(1, Math.round(scale * 0.5))); vctx.globalAlpha = 1; }
function uiFade(x0, x1, y, rgb = UI_RGB.accent, a = 1) {   // hairline that fades out from x0 toward x1 (either direction)
  const X0 = ox + x0 * scale, X1 = ox + x1 * scale; if (Math.abs(X1 - X0) < 1) return;
  const g = vctx.createLinearGradient(X0, 0, X1, 0);
  g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(1, `rgba(${rgb},0)`);
  vctx.fillStyle = g; vctx.fillRect(Math.min(X0, X1), oy + y * scale, Math.abs(X1 - X0), Math.max(1, Math.round(scale * 0.5)));
}
function uiDiamond(x, y, r, color, a = 1, stroke = false) {
  const X = ox + x * scale, Y = oy + y * scale, R = r * scale;
  vctx.globalAlpha = a; vctx.beginPath(); vctx.moveTo(X, Y - R); vctx.lineTo(X + R, Y); vctx.lineTo(X, Y + R); vctx.lineTo(X - R, Y); vctx.closePath();
  if (stroke) { vctx.strokeStyle = color; vctx.lineWidth = Math.max(1, scale * 0.5); vctx.stroke(); } else { vctx.fillStyle = color; vctx.fill(); }
  vctx.globalAlpha = 1;
}
const uiPulse = (sp = 5) => 0.5 + 0.5 * Math.sin(time * sp);
function uiSel(x, y, w, h, focus = true) {   // gold selection highlight for list rows
  const X = ox + x * scale, Y = oy + y * scale, g = vctx.createLinearGradient(X, 0, X + w * scale, 0), k = focus ? 0.2 + 0.08 * uiPulse(4) : 0.1;
  g.addColorStop(0, `rgba(176,138,58,${k})`); g.addColorStop(1, 'rgba(176,138,58,0.03)');
  vctx.fillStyle = g; vctx.fillRect(X, Y, w * scale, h * scale);
  vctx.fillStyle = focus ? UIC.gold : '#8a6d36'; vctx.fillRect(X, Y, Math.max(1, Math.round(scale * 0.7)), h * scale);
  uiFade(x, x + w * 0.8, y, UI_RGB.accent, focus ? 0.55 : 0.3); uiFade(x, x + w * 0.8, y + h - 0.4, UI_RGB.accent, focus ? 0.55 : 0.3);
}
function uiCell(x, y, s, o = {}) {   // item cell: o.sel (focused), o.eq (gold corner), o.dim
  vctx.fillStyle = o.sel ? 'rgba(58,44,24,0.96)' : 'rgba(16,12,18,0.92)';
  vctx.fillRect(ox + x * scale, oy + y * scale, s * scale, s * scale);
  if (o.sel) {   // soft inner glow
    const c = ox + (x + s / 2) * scale, d = oy + (y + s / 2) * scale, g = vctx.createRadialGradient(c, d, 0, c, d, s * 0.7 * scale);
    g.addColorStop(0, 'rgba(255,200,110,0.22)'); g.addColorStop(1, 'rgba(255,200,110,0)'); vctx.fillStyle = g; vctx.fillRect(ox + x * scale, oy + y * scale, s * scale, s * scale);
  }
  vctx.strokeStyle = o.sel ? `rgba(245,227,176,${0.6 + 0.4 * uiPulse(6)})` : o.eq ? '#8a6d36' : '#3d3326';
  vctx.lineWidth = Math.max(1, scale * (o.sel ? 0.7 : 0.5));
  vctx.strokeRect(ox + x * scale + 0.5, oy + y * scale + 0.5, s * scale - 1, s * scale - 1);
  if (o.eq) { vctx.fillStyle = UIC.gold; vctx.beginPath(); vctx.moveTo(ox + x * scale, oy + y * scale); vctx.lineTo(ox + (x + 4.5) * scale, oy + y * scale); vctx.lineTo(ox + x * scale, oy + (y + 4.5) * scale); vctx.fill(); }
}
function uiBadge(str, x, y, color = UIC.gold) {   // tiny label at the bottom-right corner (x, y = that corner)
  const w = textW(str, 4.2, 600) + 2.4;
  uiRect(x - w - 0.5, y - 5.2, w, 4.8, 'rgba(8,6,10,0.85)');
  text(str, x - 1.7, y - 1.2, 4.2, color, 'right', { shadow: false });
}
function uiKey(label, x, y, o = {}) {   // boxed key cap; y = text baseline; returns its width
  const sz = o.size || 5, w = Math.max(sz + 3, textW(label, sz, 600) + 5), X = o.align === 'right' ? x - w : o.align === 'center' ? x - w / 2 : x;
  vctx.fillStyle = 'rgba(34,27,20,0.95)'; vctx.fillRect(ox + X * scale, oy + (y - sz * 0.95 - 1) * scale, w * scale, (sz + 2.6) * scale);
  vctx.strokeStyle = o.dim ? '#4a3e2c' : '#8a6d36'; vctx.lineWidth = Math.max(1, scale * 0.5);
  vctx.strokeRect(ox + X * scale + 0.5, oy + (y - sz * 0.95 - 1) * scale + 0.5, w * scale - 1, (sz + 2.6) * scale - 1);
  text(label, X + w / 2, y + 0.2, sz, o.dim ? UIC.faint : UIC.gold, 'center', { shadow: false });
  return w;
}
const KEY_SEP = new Set(['+', '/', 'then', 'hold', 'in air', 'or']);
function uiKeysW(parts, sz = 5) { return parts.reduce((s, p) => s + (KEY_SEP.has(p) ? textW(p, sz - 0.6, 400) + 3 : Math.max(sz + 3, textW(p, sz, 600) + 5) + 1.5), 0); }
function uiKeys(parts, xr, y, o = {}) {   // key combo right-aligned at xr: ['↓', '+', 'J']
  const sz = o.size || 5; let x = xr - uiKeysW(parts, sz);
  for (const p of parts) {
    if (KEY_SEP.has(p)) { text(p, x + 1.5, y, sz - 0.6, UIC.faint, 'left', { weight: 400, shadow: false }); x += textW(p, sz - 0.6, 400) + 3; }
    else x += uiKey(p, x, y, { size: sz, dim: o.dim }) + 1.5;
  }
}
function uiPips(x, y, n, max = 5, color = UIC.gold) { for (let i = 0; i < max; i++) uiRect(x + i * 5, y, 4, 2, i < n ? color : '#3a3026'); }
function uiScroll(x, y, h, first, vis, total) {
  if (total <= vis) return;
  uiRect(x, y, 0.6, h, '#3a3026');
  const th = Math.max(6, h * vis / total), ty = y + (h - th) * first / Math.max(1, total - vis);
  uiRect(x - 0.4, ty, 1.4, th, UIC.accent);
}
function uiBackdrop(a = 0.84) {
  vctx.fillStyle = `rgba(5,4,8,${a})`; vctx.fillRect(ox, oy, W * scale, H * scale);
  const c = ox + W / 2 * scale, d = oy + H / 2 * scale, g = vctx.createRadialGradient(c, d, 70 * scale, c, d, 240 * scale);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,0.55)'); vctx.fillStyle = g; vctx.fillRect(ox, oy, W * scale, H * scale);
}
function uiStrips() {   // opaque header / footer bands so the HUD underneath never shows through the menu chrome
  const top = vctx.createLinearGradient(0, oy, 0, oy + 30 * scale);
  top.addColorStop(0, 'rgba(4,3,6,0.97)'); top.addColorStop(0.8, 'rgba(4,3,6,0.9)'); top.addColorStop(1, 'rgba(4,3,6,0)');
  vctx.fillStyle = top; vctx.fillRect(ox, oy, W * scale, 30 * scale);
  const bot = vctx.createLinearGradient(0, oy + 202 * scale, 0, oy + H * scale);
  bot.addColorStop(0, 'rgba(4,3,6,0)'); bot.addColorStop(0.35, 'rgba(4,3,6,0.95)'); bot.addColorStop(1, 'rgba(4,3,6,0.97)');
  vctx.fillStyle = bot; vctx.fillRect(ox, oy + 202 * scale, W * scale, 14 * scale);
}
function uiHead(label, x, y, w, extra) {   // small section heading with a fading rule
  const L = label.toUpperCase(); text(L, x, y, 4.7, UIC.dim, 'left', { spacing: 1.1, weight: 600 });
  const tw = textW(L, 4.7) + L.length * 1.1 + 3;
  if (extra) text(extra, x + w, y, 4.7, UIC.faint, 'right', { weight: 500 });
  uiFade(x + tw, x + w - (extra ? textW(extra, 4.7, 500) + 4 : 0), y - 1.7, UI_RGB.accent, 0.5);
}
function uiFooter(items, y = 211) {   // [[key, label], ...] centred key hints; keys are relabelled for touch screens
  const parts = items.filter(([k]) => kl(k) !== '').map(([k, l]) => { const K = kl(k), kw = Math.max(7.8, textW(K, 4.8, 600) + 5); return { K, l, kw, w: kw + 2.5 + textW(l, 5, 400) }; });
  const gap = 8, total = parts.reduce((s, p) => s + p.w, 0) + gap * (parts.length - 1); let x = W / 2 - total / 2;
  for (const p of parts) { uiKey(p.K, x, y, { size: 4.8 }); text(p.l, x + p.kw + 2.5, y, 5, UIC.faint, 'left', { weight: 400 }); x += p.w + gap; }
}
const tabHint = () => (kl('Q') ? [['Q', ''], ['Tab', 'tabs']] : [['Tab', 'tabs']]);
function uiFit(str, maxW, size, min = 4.5, weight = 600) { let s = size; while (s > min && textW(str, s, weight) > maxW) s -= 0.25; return s; }
function uiTitle(label, y = 17, size = 9) {
  const sp = 3, w = textW(label, size) + sp * label.length;
  text(label, W / 2, y, size, UIC.gold, 'center', { spacing: sp });
  uiDiamond(W / 2 - w / 2 - 6, y - size * 0.35, 1.3, UIC.accent); uiDiamond(W / 2 + w / 2 + 4, y - size * 0.35, 1.3, UIC.accent);
  uiFade(W / 2 - w / 2 - 10, W / 2 - w / 2 - 70, y - size * 0.35, UI_RGB.accent, 0.7); uiFade(W / 2 + w / 2 + 8, W / 2 + w / 2 + 68, y - size * 0.35, UI_RGB.accent, 0.7);
}
function uiTabs(cur) {
  const n = TABS.length, pitch = 80, x0 = W / 2 - pitch * (n - 1) / 2;
  TABS.forEach((t, i) => {
    const x = x0 + i * pitch, sel = i === cur;
    text(t.toUpperCase(), x, 18, 6.6, sel ? UIC.hi : UIC.faint, 'center', { spacing: 1.6, weight: sel ? 600 : 500 });
    if (sel) { uiDiamond(x, 22.5, 1.3, UIC.gold); uiFade(x - 3, x - 34, 22.2, UI_RGB.gold, 0.9); uiFade(x + 3, x + 34, 22.2, UI_RGB.gold, 0.9); }
    if (i < n - 1) uiDiamond(x + pitch / 2, 16, 0.9, '#5a4a30');
  });
  if (kl('Q')) { uiKey(kl('Q'), x0 - 44, 18.5, { size: 4.8, align: 'center' }); text('◂', x0 - 36, 18.3, 5, UIC.faint, 'center', { shadow: false }); }
  const xr = x0 + (n - 1) * pitch + 44; uiKey(kl('Tab'), xr, 18.5, { size: 4.8, align: 'center' }); text('▸', xr - (textW(kl('Tab'), 4.8) + 5) / 2 - 4, 18.3, 5, UIC.faint, 'center', { shadow: false });
}

// ---- gear entries (one shape for weapons, arts, spells, charms, key items and materials)
const WCLASS_NAME = { sword: 'Straight Sword', dagger: 'Dagger', spear: 'Spear', katana: 'Katana', staff: 'Staff', shield: 'Sword & Shield', twin: 'Twinblades', mirror: 'Mirror Blade' };
function wClassName(id) {
  const c = (typeof WEAPON_CLASS !== 'undefined' && WEAPON_CLASS[id]) || 'sword';
  if (c === 'great') return /maul|hammer/.test(id) ? 'Great Hammer' : /cleaver|rotmaw/.test(id) ? 'Great Cleaver' : 'Greatsword';
  return WCLASS_NAME[c] || 'Weapon';
}
function gearEntry(kind, id) {
  if (kind === 'weapon') { const w = WEAPONS[id]; return w && { kind, id, name: w.name, icon: 'w_' + id, desc: w.desc || '', lv: SAVE.weapons[id] || 0, eq: SAVE.weapon === id }; }
  if (kind === 'art') { const r = ARTS[id]; return r && { kind, id, name: r.name, icon: 'a_' + id, desc: r.desc || '', fp: r.fp, eq: SAVE.art === id }; }
  if (kind === 'spell') { const s = SPELLS[id]; if (!s) return null; const slot = SAVE.spellsEq.indexOf(id); return { kind, id, name: s.name, icon: s.icon || 's_' + id, desc: s.desc || (SPELL_DEFS[id] && SPELL_DEFS[id].desc) || '', fp: spellCost(id), slot, eq: slot >= 0 }; }
  if (kind === 'charm') { const c = CHARMS[id]; if (!c) return null; const slot = SAVE.charmsEq.indexOf(id); return { kind, id, name: c.name, icon: id, desc: c.desc || '', slot, eq: slot >= 0 }; }
  const d = ITEMS[id]; return d && { kind, id, name: d.name, icon: d.icon, desc: d.desc || '' };
}
function keyItemIds() { return Object.keys(ITEMS).filter(id => SAVE.items[id] && !ITEMS[id].weapon && !ITEMS[id].charm && !ITEMS[id].spell && !ITEMS[id].art); }
function materialEntries() {
  const L = [], n = flaskMax(), red = n - SAVE.flaskBlue;
  L.push({ kind: 'mat', id: 'flask_red', name: 'Crimson Flask', icon: 'flask_red', count: `${P ? P.flasksR : red}/${red}`, big: `${P ? P.flasksR : red} / ${red}`,
           desc: 'Restores HP. Press F to drink. The shrine flame refills every flask when you rest; share the charges between crimson and azure at a shrine.' });
  L.push({ kind: 'mat', id: 'flask_blue', name: 'Azure Flask', icon: 'flask_blue', count: `${P ? P.flasksB : SAVE.flaskBlue}/${SAVE.flaskBlue}`, big: `${P ? P.flasksB : SAVE.flaskBlue} / ${SAVE.flaskBlue}`,
           desc: 'Restores FP for spells and weapon arts. Press R to drink.' });
  L.push({ kind: 'mat', id: 'cinders', name: 'Cinders', icon: 'cinder', count: SAVE.cinders >= 10000 ? Math.floor(SAVE.cinders / 1000) + 'k' : String(SAVE.cinders), big: String(SAVE.cinders),
           desc: 'The ash of fallen grace. Spend them to level up at shrines, to temper weapons and on wares. Die, and they wait where you fell.' });
  for (const [id, c] of Object.entries(SAVE.inv)) if (c > 0 && ITEMS[id]) L.push({ ...gearEntry('mat', id), kind: 'mat', count: '×' + c, big: '×' + c });
  if (SAVE.shards) L.push({ ...gearEntry('mat', 'shard'), kind: 'mat', count: '×' + SAVE.shards, big: '×' + SAVE.shards });
  if (SAVE.flaskPot) L.push({ ...gearEntry('mat', 'herb'), kind: 'mat', count: `+${SAVE.flaskPot * 10}%`, big: `Flasks +${SAVE.flaskPot * 10}%` });
  return L.filter(e => e && e.name);
}
const INV_CATS = [
  { k: 'weapon', name: 'Weapons', icon: 'w_longsword', ids: () => Object.keys(WEAPONS).filter(id => SAVE.weapons[id] !== undefined), total: () => Object.keys(WEAPONS).length },
  { k: 'art', name: 'Weapon Arts', icon: 'a_crescent', ids: () => Object.keys(ARTS).filter(id => SAVE.arts.includes(id)), total: () => Object.keys(ARTS).length },
  { k: 'spell', name: 'Spells', icon: 'ash_bolt', ids: () => knownSpells(), total: () => Object.keys(SPELLS).length },
  { k: 'charm', name: 'Charms', icon: 'c_crimson', ids: () => Object.keys(CHARMS).filter(id => SAVE.charms.includes(id)), total: () => Object.keys(CHARMS).length },
  { k: 'key', name: 'Key Items', icon: 'i_bell', ids: keyItemIds },
  { k: 'mat', name: 'Materials', icon: 'i_emberstone', entries: materialEntries },
];
function catEntries(c) { return c.entries ? c.entries() : c.ids().map(id => gearEntry(c.k, id)).filter(Boolean); }

// ---- item detail panel (shared by the equipment slots, the picker and the inventory)
const pip5 = (v, lo, step) => clamp(Math.round((v - lo) / step) + 1, 1, 5);
function weaponTags(w) {
  const t = [];
  if (w.boss) t.push(['Boss weapon', '#f0a860']);
  if (w.bleed) t.push([`Bleed ${w.bleed}`, '#e06060']);
  if (w.frost) t.push([`Frost ${w.frost}`, '#9cc8f4']);
  if (w.fire) t.push([`Fire ${Math.round(w.fire * 100)}%`, '#ff9a50']);
  if (w.holy) t.push([`Spells +${Math.round(w.holy * 100)}%`, '#f2e2a8']);
  if (w.rot) t.push(['Rot', '#9ac860']);
  if (w.guard) t.push([`Guard ${Math.round(w.guard * 100)}%`, '#c4ccdc']);
  if (w.crit) t.push([`Criticals +${Math.round((w.crit - 1) * 100)}%`, UIC.gold]);
  if (w.armor) t.push(['Unflinching heavies', '#c9bda2']);
  return t;
}
function uiDelta(x, y, d, lowerIsBetter = false, size = 5.6) {
  if (!d) { text('=', x, y, size, UIC.faint, 'left'); return; }
  const good = lowerIsBetter ? d < 0 : d > 0;
  text(`${d > 0 ? '▲' : '▼'} ${Math.abs(d)}`, x, y, size, good ? UIC.up : UIC.down, 'left', { weight: 600 });
}
function drawDetail(e, px, py, pw, ph, cmp) {
  if (!e) { text('Nothing here yet.', px + pw / 2, py + ph / 2, 6, UIC.dim, 'center', { weight: 400 }); return; }
  const x = px + 9, R = px + pw - 9;
  if (e.empty) {
    uiCell(x, py + 9, 26); text('—', x + 13, py + 26, 8, UIC.faint, 'center');
    text(e.title, x + 33, py + 21, 7.6, UIC.gold); text(e.sub || '', x + 33, py + 30, 5, UIC.muted, 'left', { weight: 500 });
    uiHair(x, py + 40, pw - 18, UIC.line, 0.8);
    let y = py + 52; for (const l of wrap(e.desc || '', pw - 20, 5.8)) { text(l, x, y, 5.8, UIC.body, 'left', { weight: 400 }); y += 7.8; }
    return;
  }
  uiCell(x, py + 9, 26, { eq: e.eq }); icon(e.icon, x + 2, py + 11, 22);
  const nm = e.name + (e.kind === 'weapon' && e.lv ? ` +${e.lv}` : ''), ns = uiFit(nm, pw - 50, 8, 5.2);
  text(nm, x + 33, py + 21, ns, UIC.gold);
  const sub = { weapon: () => wClassName(e.id), art: () => 'Weapon Art', spell: () => 'Spell', charm: () => 'Charm', key: () => 'Key Item', mat: () => 'Material' }[e.kind]();
  const eqs = e.eq ? (e.slot >= 0 ? `Equipped · slot ${e.slot + 1}` : 'Equipped') : '';
  text(sub, x + 33, py + 30, 5, UIC.muted, 'left', { weight: 500 });
  if (eqs) text(eqs, R, py + 30, 5, UIC.gold, 'right', { weight: 600 });
  else if (cmp && cmp.kind === e.kind && cmp.id !== e.id && cmp.name) { const vs = `vs ${cmp.name}`; text(vs, R, py + 30, uiFit(vs, pw - 50 - textW(sub, 5, 500), 4.8, 3.8, 500), UIC.faint, 'right', { weight: 500 }); }
  uiHair(x, py + 39, pw - 18, UIC.line, 0.8);
  let y = py + 46;
  if (e.kind === 'weapon') {
    const w = WEAPONS[e.id], lv = e.lv, atk = Math.round(weaponAR(SAVE.stats, e.id, lv));
    text('ATTACK', x, y + 4, 4.6, UIC.faint, 'left', { spacing: 1 });
    text(String(atk), x, y + 16, 11, UIC.text, 'left');
    if (cmp && cmp.kind === 'weapon' && cmp.id !== e.id) uiDelta(x + textW(String(atk), 11) + 3, y + 15.5, atk - Math.round(weaponAR(SAVE.stats, cmp.id, cmp.lv)));
    text('SCALING', x + 74, y + 4, 4.6, UIC.faint, 'left', { spacing: 1 });
    [['str', 'Str'], ['dex', 'Dex'], ['fth', 'Fth']].forEach(([k, lab], i) => {
      const g = gradeWithLv(w.sc[k], lv), X = x + 74 + i * 36;
      text(lab, X, y + 15, 5.2, UIC.muted, 'left', { weight: 500 }); text(g === '-' ? '–' : g, X + 14, y + 15.5, 7.6, g === '-' ? UIC.faint : UIC.gold, 'left');
    });
    y += 24;
    const cw = cmp && cmp.kind === 'weapon' && cmp.id !== e.id ? WEAPONS[cmp.id] : null;
    [['Speed', pip5(w.speed, 0.7, 0.17), cw && pip5(cw.speed, 0.7, 0.17)], ['Reach', pip5(w.reach, 0.7, 0.17), cw && pip5(cw.reach, 0.7, 0.17)],
     ['Weight', pip5(w.stam, 0.6, 0.24), cw && pip5(cw.stam, 0.6, 0.24)]].forEach(([lab, n, c], i) => {
      const X = x + i * 62; text(lab.toUpperCase(), X, y + 4, 4.6, UIC.faint, 'left', { spacing: 1 }); uiPips(X, y + 7, n);
      if (c && c !== n) text(n > c ? '▲' : '▼', X + 27, y + 9.4, 4.6, (lab === 'Weight' ? n < c : n > c) ? UIC.up : UIC.down, 'left');
    });
    y += 16;
    const art = ARTS[w.art];
    if (art) { icon('a_' + w.art, x - 1, y - 1, 10); text(art.name, x + 12, y + 6.5, 5.8, UIC.body, 'left', { weight: 500 }); text(`${art.fp} FP`, R, y + 6.5, 5.2, UIC.fp, 'right', { weight: 600 }); text('ART', x + 12 + textW(art.name, 5.8, 500) + 4, y + 6.3, 4.4, UIC.faint, 'left', { spacing: 1 }); }
    y += 13;
    let tx = x; const tags = weaponTags(w);
    for (const [s, c] of tags) {
      const tw = textW(s, 4.8, 600) + 6; if (tx + tw > R + 0.5) { tx = x; y += 9.5; }
      vctx.strokeStyle = c; vctx.globalAlpha = 0.7; vctx.lineWidth = Math.max(1, scale * 0.5); vctx.strokeRect(ox + tx * scale + 0.5, oy + (y - 0.5) * scale, tw * scale, 7.5 * scale); vctx.globalAlpha = 1;
      text(s, tx + tw / 2, y + 5.1, 4.8, c, 'center', { shadow: false }); tx += tw + 3;
    }
    if (tags.length) y += 11;
  } else if (e.kind === 'art' || e.kind === 'spell') {
    text('FP COST', x, y + 4, 4.6, UIC.faint, 'left', { spacing: 1 });
    text(String(e.fp), x, y + 15, 9.5, UIC.fp, 'left');
    if (cmp && cmp.kind === e.kind && cmp.id !== e.id) uiDelta(x + textW(String(e.fp), 9.5) + 3, y + 14.5, e.fp - cmp.fp, true);
    text('USE', x + 74, y + 4, 4.6, UIC.faint, 'left', { spacing: 1 });
    let kx = x + 74; for (const [k, l] of e.kind === 'art' ? [['O', 'use'], ['hold O', 'charge']] : [['U', 'cast'], ['Q', 'switch']]) {
      kx += uiKey(k, kx, y + 14.5, { size: 5 }) + 2; text(l, kx, y + 14.5, 4.8, UIC.faint, 'left', { weight: 400 }); kx += textW(l, 4.8, 400) + 6;
    }
    y += 24;
  } else if (e.kind === 'mat' && e.big) {
    text('HELD', x, y + 4, 4.6, UIC.faint, 'left', { spacing: 1 }); text(e.big, x, y + 15, 9, UIC.text, 'left'); y += 24;
  }
  if (y > py + 50) { uiFade(x, x + pw - 18, y - 1, UI_RGB.accent, 0.35); y += 6; } else y += 3;
  for (const l of wrap(e.desc, pw - 18, 5.7)) { if (y > py + ph - 5) break; text(l, x, y, 5.7, UIC.body, 'left', { weight: 400 }); y += 7.6; }
}

// ---- equipment tab: slot list (left) · detail (right); OK opens the item picker
function slotEntry(r) {
  if (!r) return null;
  if (r.k === 'weapon') return gearEntry('weapon', SAVE.weapon);
  if (r.k === 'art') return SAVE.art ? gearEntry('art', SAVE.art) : { empty: true, title: 'Weapon Art', sub: 'Empty', desc: 'Choose an art for O.' };
  if (r.k === 'spell') { const s = SAVE.spellsEq[r.i]; if (s) return gearEntry('spell', s); const n = knownSpells().length; return { empty: true, title: `Spell slot ${r.i + 1}`, sub: 'Empty', desc: `You know ${n} spell${n === 1 ? '' : 's'}. Press ${kl('Enter')} to choose one. Learn more on the skill tree, from the Hollow Scribe, or from great foes.` }; }
  const c = SAVE.charmsEq[r.i]; if (c) return gearEntry('charm', c);
  return { empty: true, title: `Charm slot ${r.i + 1}`, sub: 'Empty', desc: `You carry ${SAVE.charms.length} charm${SAVE.charms.length === 1 ? '' : 's'}. Press ${kl('Enter')} to wear one.` };
}
function slotKind(r) { return r.k === 'weapon' ? 'weapon' : r.k; }
function pickIds(r) {
  if (r.k === 'weapon') return Object.keys(WEAPONS).filter(id => SAVE.weapons[id] !== undefined);
  if (r.k === 'art') return Object.keys(ARTS).filter(id => SAVE.arts.includes(id));
  if (r.k === 'spell') return [null, ...knownSpells()];
  return [null, ...Object.keys(CHARMS).filter(id => SAVE.charms.includes(id))];
}
function openPicker(M, r) {
  const list = pickIds(r), cur = r.k === 'weapon' ? SAVE.weapon : r.k === 'art' ? SAVE.art : r.k === 'spell' ? SAVE.spellsEq[r.i] || null : SAVE.charmsEq[r.i] || null;
  M.pick = { row: r, list, sel: Math.max(0, list.indexOf(cur)), off: 0 }; sfx.menu();
}
function applyEquip(r, id) {
  if (r.k === 'weapon') { if (!id) return; SAVE.weapon = id; const a = WEAPONS[id].art; if (SAVE.arts.includes(a) && !SAVE.artPinned) SAVE.art = a; }
  else if (r.k === 'art') { if (!id) return; SAVE.art = id; SAVE.artPinned = true; }
  else {
    const key = r.k === 'spell' ? 'spellsEq' : 'charmsEq', eq = [...SAVE[key]], j = id ? eq.indexOf(id) : -1, cur = eq[r.i] || null;
    if (!id) eq[r.i] = null;
    else { if (j >= 0 && j !== r.i) eq[j] = cur; eq[r.i] = id; }   // picking one worn in another slot swaps the two
    SAVE[key] = eq.filter(Boolean);
    if (r.k === 'spell' && !SAVE.spellsEq.includes(SAVE.spell)) SAVE.spell = SAVE.spellsEq[0] || null;
  }
  const hpFrac = P.hp / D.maxHp; refreshDerived(false); P.hp = Math.min(D.maxHp, Math.round(D.maxHp * hpFrac)); P.fp = Math.min(P.fp, D.maxFp);
  sfx.menu(); saveGame();
}
const PICK_COLS = 7, PICK_ROWS = 7, INV_COLS = 7, INV_ROWS = 6;
function gridMove(sel, n, cols, a) {   // returns the new index, or -1 when the move leaves the grid through that edge
  if (a === 'left') return sel > 0 ? sel - 1 : -1;
  if (a === 'right') return sel < n - 1 ? sel + 1 : -1;
  if (a === 'up') return sel >= cols ? sel - cols : -1;
  if (a === 'down') { if (sel + cols < n) return sel + cols; return Math.floor(sel / cols) < Math.floor((n - 1) / cols) ? n - 1 : -1; }
  return sel;
}
function pickInput(M, a) {
  const K = M.pick, n = K.list.length, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) { M.pick = null; sfx.menu(); return; }
  if (['left', 'right', 'up', 'down'].includes(a)) { const s = gridMove(K.sel, n, PICK_COLS, a); if (s >= 0 && s !== K.sel) { K.sel = s; sfx.menu(); } return; }
  if (conf) { applyEquip(K.row, K.list[K.sel]); M.pick = null; }
}
function equipInput(M, a) {
  const rows = equipRows(), n = rows.length, conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  M.sel = Math.min(M.sel, n - 1);
  if (a === 'up') { M.sel = (M.sel + n - 1) % n; sfx.menu(); } else if (a === 'down') { M.sel = (M.sel + 1) % n; sfx.menu(); }
  else if (a === 'left' || a === 'right') changeEquip(rows[M.sel], a === 'left' ? -1 : 1);   // quick cycle
  else if (conf) openPicker(M, rows[M.sel]);
}
function renderEquipTab(M) {
  const rows = equipRows(); M.sel = Math.min(M.sel, rows.length - 1);
  panel(12, 30, 152, 172);
  if (M.pick) renderPicker(M.pick); else renderSlots(M, rows);
  panel(170, 30, 202, 172, 0.8);
  if (M.pick) { const id = M.pick.list[M.pick.sel]; drawDetail(id ? gearEntry(slotKind(M.pick.row), id) : { empty: true, title: 'Remove', sub: M.pick.row.k === 'spell' ? `Spell slot ${M.pick.row.i + 1}` : `Charm slot ${M.pick.row.i + 1}`, desc: 'Leave this slot empty.' }, 170, 30, 202, 172, slotEntry(M.pick.row)); }
  else drawDetail(slotEntry(rows[M.sel]), 170, 30, 202, 172, null);
  if (M.pick) uiFooter([['↑↓←→', 'choose'], ['Enter', 'equip'], ['Esc', 'cancel']]);
  else uiFooter([['↑↓', 'slot'], ['Enter', 'choose'], ['←→', 'quick swap'], ...tabHint(), ['Esc', 'close']]);
}
function renderSlots(M, rows) {
  const lines = []; let last = null;
  rows.forEach((r, i) => {
    const g = r.k === 'weapon' || r.k === 'art' ? 'Armament' : r.k === 'spell' ? 'Spells' : 'Charms';
    if (g !== last) { lines.push({ head: g, extra: g === 'Spells' ? `${SAVE.spellsEq.length}/${SAVE.spellSlots}` : g === 'Charms' ? `${SAVE.charmsEq.length}/${SAVE.charmSlots}` : '' }); last = g; }
    lines.push({ r, i });
  });
  let y = 0; for (const L of lines) { L.y = y; y += L.head ? 10 : 13; }
  const top = 35, bottom = 199, selL = lines.find(L => L.i === M.sel), view = bottom - top;
  M.slotOff = clamp(M.slotOff || 0, Math.max(0, selL.y + 16 - view), Math.min(selL.y - (lines[lines.indexOf(selL) - 1].head ? 10 : 0), Math.max(0, y - view)));
  vctx.save(); vctx.beginPath(); vctx.rect(ox + 13 * scale, oy + (top - 1) * scale, 150 * scale, (view + 2) * scale); vctx.clip();
  for (const L of lines) {
    const Y = top + L.y - M.slotOff; if (Y < top - 14 || Y > bottom) continue;
    if (L.head) { uiHead(L.head, 18, Y + 6.5, 140, L.extra); continue; }
    const r = L.r, sel = L.i === M.sel, e = slotEntry(r);
    if (sel) uiSel(15, Y - 0.5, 146, 13);
    uiCell(19, Y + 0.5, 11, { eq: false });
    if (!e.empty) icon(e.icon, 20, Y + 1.5, 9);
    const nm = e.empty ? '— empty —' : e.name + (r.k === 'weapon' && e.lv ? ` +${e.lv}` : '');
    text(nm, 34, Y + 8.6, uiFit(nm, 104, 6.2, 4.8, sel ? 600 : 500), e.empty ? UIC.faint : sel ? UIC.hi : UIC.text, 'left', { weight: sel ? 600 : 500 });
    if (!e.empty && (r.k === 'spell' || r.k === 'art')) text(`${e.fp}`, 156, Y + 8.4, 5, UIC.fp, 'right', { weight: 600, alpha: sel ? 0 : 0.8 });
    if (sel) { const k = uiPulse(6); text('◂', 143.5 - k, Y + 8.6, 5.4, UIC.gold, 'center', { shadow: false }); text('▸', 155.5 + k, Y + 8.6, 5.4, UIC.gold, 'center', { shadow: false }); }
  }
  vctx.restore();
  uiScroll(161, top, view, M.slotOff, view, y);
}
function renderPicker(K) {
  const r = K.row, n = K.list.length, kind = slotKind(r);
  const title = { weapon: 'Weapons', art: 'Weapon Arts', spell: `Spell slot ${(r.i || 0) + 1}`, charm: `Charm slot ${(r.i || 0) + 1}` }[kind];
  text(title.toUpperCase(), 18, 41, 6, UIC.gold, 'left', { spacing: 1 });
  text(`${n - (kind === 'spell' || kind === 'charm' ? 1 : 0)} owned`, 158, 41, 5, UIC.faint, 'right', { weight: 500 });
  uiHair(18, 44.5, 140, UIC.line, 0.8);
  const rows = Math.ceil(n / PICK_COLS), sr = Math.floor(K.sel / PICK_COLS);
  K.off = clamp(K.off, Math.max(0, sr - PICK_ROWS + 1), sr);
  for (let i = K.off * PICK_COLS; i < Math.min(n, (K.off + PICK_ROWS) * PICK_COLS); i++) {
    const id = K.list[i], cx = 18 + (i % PICK_COLS) * 20, cy = 49 + (Math.floor(i / PICK_COLS) - K.off) * 21, sel = i === K.sel;
    const e = id ? gearEntry(kind, id) : null, here = id && (kind === 'weapon' ? SAVE.weapon === id : kind === 'art' ? SAVE.art === id : kind === 'spell' ? SAVE.spellsEq[r.i] === id : SAVE.charmsEq[r.i] === id);
    uiCell(cx, cy, 18, { sel, eq: here });
    if (!id) { text('✕', cx + 9, cy + 12, 7, UIC.faint, 'center', { shadow: false }); continue; }
    icon(e.icon, cx + 2, cy + 2, 14, e.slot >= 0 && !here ? 0.55 : 1);
    if (kind === 'weapon' && e.lv) uiBadge('+' + e.lv, cx + 18, cy + 18);
    else if ((kind === 'spell' || kind === 'charm') && e.slot >= 0 && !here) uiBadge(String(e.slot + 1), cx + 18, cy + 18, UIC.muted);
  }
  uiScroll(161, 49, PICK_ROWS * 21 - 3, K.off, PICK_ROWS, rows);
  const e = K.list[K.sel] ? gearEntry(kind, K.list[K.sel]) : null;
  if (e && e.slot >= 0 && !(kind === 'spell' ? SAVE.spellsEq[r.i] === e.id : SAVE.charmsEq[r.i] === e.id)) text(`Worn in slot ${e.slot + 1} — equipping swaps them`, 88, 199, 4.6, UIC.faint, 'center', { weight: 400 });
}

// ---- inventory tab: category bar · icon grid · detail
function invInput(M, a) {
  const conf = ['confirm', 'interact', 'attack', 'jump'].includes(a), nc = INV_CATS.length;
  M.cat = M.cat || 0; M.isel = M.isel || 0;
  const setCat = c => { M.cat = (c + nc) % nc; M.isel = 0; M.ioff = 0; sfx.menu(); };
  let L = catEntries(INV_CATS[M.cat]); if (!L.length) M.bar = true;
  if (M.bar) {
    if (a === 'left' || a === 'right') setCat(M.cat + (a === 'left' ? -1 : 1));
    else if ((a === 'down' || conf) && L.length) { M.bar = false; sfx.menu(); }
    return;
  }
  if (['left', 'right', 'up', 'down'].includes(a)) {
    const s = gridMove(M.isel, L.length, INV_COLS, a);
    if (s >= 0) { if (s !== M.isel) { M.isel = s; sfx.menu(); } }
    else if (a === 'up') { M.bar = true; sfx.menu(); }
    else if (a === 'left') { setCat(M.cat - 1); M.isel = Math.max(0, catEntries(INV_CATS[M.cat]).length - 1); }
    else if (a === 'right') setCat(M.cat + 1);
    return;
  }
  if (conf) {   // OK equips straight from the bag: weapons and arts replace, spells and charms fill a free slot (or come off)
    const e = L[M.isel]; if (!e) return;
    if (e.kind === 'weapon' || e.kind === 'art') { if (e.eq) { sfx.deny(); return; } applyEquip({ k: e.kind }, e.id); toast(`${e.name} equipped`, 1.6); }
    else if (e.kind === 'spell' || e.kind === 'charm') {
      const key = e.kind === 'spell' ? 'spellsEq' : 'charmsEq', slots = e.kind === 'spell' ? SAVE.spellSlots : SAVE.charmSlots;
      if (e.eq) { applyEquip({ k: e.kind, i: e.slot }, null); toast(`${e.name} removed`, 1.6); }
      else if (SAVE[key].length < slots) { applyEquip({ k: e.kind, i: SAVE[key].length }, e.id); toast(`${e.name} equipped`, 1.6); }
      else { sfx.deny(); toast(`All ${e.kind} slots are full — swap one in Equipment`, 2.4); }
    }
  }
}
function renderInvTab(M) {
  M.cat = M.cat || 0; M.isel = M.isel || 0;
  const C = INV_CATS[M.cat], L = catEntries(C); if (!L.length) M.bar = true; M.isel = Math.min(M.isel, Math.max(0, L.length - 1));
  panel(12, 30, 152, 172);
  INV_CATS.forEach((c, i) => {
    const x = 18 + i * 23.4, y = 35, sel = i === M.cat;
    uiCell(x, y, 19, { sel: sel && M.bar });
    icon(c.icon, x + 2.5, y + 2.5, 14, sel ? 1 : 0.42);
    if (sel && !M.bar) { uiHair(x + 1, y + 21, 17, UIC.gold); }
  });
  text(C.name.toUpperCase(), 18, 66, 6, UIC.gold, 'left', { spacing: 1 });
  text(C.total ? `${L.length} / ${C.total()}` : String(L.length), 158, 66, 5, UIC.faint, 'right', { weight: 500 });
  uiHair(18, 69.5, 140, UIC.line, 0.8);
  if (!L.length) text('Nothing yet.', 88, 110, 6, UIC.dim, 'center', { weight: 400 });
  const rows = Math.ceil(L.length / INV_COLS), sr = Math.floor(M.isel / INV_COLS);
  M.ioff = clamp(M.ioff || 0, Math.max(0, sr - INV_ROWS + 1), sr);
  for (let i = M.ioff * INV_COLS; i < Math.min(L.length, (M.ioff + INV_ROWS) * INV_COLS); i++) {
    const e = L[i], cx = 18 + (i % INV_COLS) * 20, cy = 74 + (Math.floor(i / INV_COLS) - M.ioff) * 21;
    uiCell(cx, cy, 18, { sel: i === M.isel && !M.bar, eq: e.eq });
    icon(e.icon, cx + 2, cy + 2, 14);
    if (e.kind === 'weapon' && e.lv) uiBadge('+' + e.lv, cx + 18, cy + 18);
    else if (e.count && e.kind === 'mat') uiBadge(e.count, cx + 18, cy + 18, UIC.text);
  }
  uiScroll(161, 74, INV_ROWS * 21 - 3, M.ioff, INV_ROWS, rows);
  panel(170, 30, 202, 172, 0.8);
  const e = M.bar ? null : L[M.isel];
  if (e) drawDetail(e, 170, 30, 202, 172, e.kind === 'weapon' ? gearEntry('weapon', SAVE.weapon) : e.kind === 'art' && SAVE.art ? gearEntry('art', SAVE.art) : null);
  else {   // category focused: a short summary of the category
    icon(C.icon, 250, 70, 40, 0.9);
    text(C.name, 271, 128, 8, UIC.gold, 'center');
    text(L.length ? `${L.length} held · ↓ to browse` : 'You carry none yet.', 271, 140, 5.4, UIC.muted, 'center', { weight: 400 });
  }
  const act = e && (e.kind === 'weapon' || e.kind === 'art') ? (e.eq ? '' : 'equip') : e && (e.kind === 'spell' || e.kind === 'charm') ? (e.eq ? 'remove' : 'equip') : '';
  uiFooter(M.bar ? [['←→', 'category'], ['↓', 'browse'], ...tabHint(), ['Esc', 'close']]
    : [['↑↓←→', 'browse'], ...(act ? [['Enter', act]] : []), ...tabHint(), ['Esc', 'close']]);
}

// ---- controls & techniques guide (Settings › Controls & techniques)
// rows: [keys, name, description, requiredItem]
const GUIDE_PAGES = [
  { name: 'Keyboard', rows: () => CONTROLS.map(([k, v]) => [k.split(/\s+/).filter(Boolean), v.split(' · ')[0], v.split(' · ').slice(1).join(' · ')]) },
  { name: 'Combat', rows: () => [
    [['J'], 'Attack', 'Chain light attacks into a combo. Hold ↑ to strike upward. Click works too.'],
    [['K', 'hold'], 'Charged heavy', 'Hold K (or right-click) to charge a stance-breaking heavy; release to swing.'],
    [['O', 'hold'], 'Weapon art', 'Spend FP on your weapon art. Hold O to charge it for a stronger version.'],
    [['I', 'then', 'J'], 'Parry → riposte', 'Parry just as a blow lands, then strike for a critical riposte.'],
    [['J'], 'Critical on stagger', 'Break a great foe’s stance with heavies and parries; when it staggers, strike for a critical.'],
    [['I', 'then', 'J'], 'Guard counter', 'Right after a parry or a shield block, attack for a heavy counter blow.'],
    [['I', 'hold'], 'Shield block', 'Shield weapons: hold I to raise the shield. A tap still parries.'],
    [['L', 'then', 'J'], 'Backstep strike', 'Roll away from the way you face, then attack as you land for a lunging cut.'],
    [['L'], 'Roll', 'Invulnerable for a moment. Roll through attacks, not away from them.'],
  ] },
  { name: 'Weapons', rows: () => [
    [['J'], 'Dagger backstab', 'Daggers: slip behind a foe that faces away and attack to open it up.'],
    [['Space', 'then', 'J'], 'Spear jump thrust', 'Spears: attack while still rising from a jump to dive in point first.'],
    [['K'], 'Staff spin', 'Staves: the heavy is an instant spin striking both sides; costs 80% stamina.'],
    [['I', 'then', 'J'], 'Katana counter', 'Katanas: guard counters strike 40% harder and come out faster.'],
    [['K', 'hold'], 'Unflinching heavies', 'Great weapons can’t be interrupted mid-heavy by weaker blows.'],
    [[], 'Boss weapons', 'Weapons taken from great foes carry signature effects; read them in Equipment.'],
    [['Enter'], 'Change gear', 'Esc › Equipment: pick a slot, press Enter, choose from the grid. ←→ quick-swaps.'],
  ] },
  { name: 'Traversal', rows: () => [
    [['↓', '+', 'J'], 'Pogo', 'In the air, strike downward to bounce off foes and hazards.'],
    [['K', 'in air'], 'Plunge', 'Heavy in the air dives down and crashes into whatever is below.'],
    [['S', '+', 'K'], 'Cinder Slam', 'In the air: slam down, shattering cracked floors. Two in a row at most.', 'slam'],
    [['Space', 'in air'], 'Double jump', 'Jump again in midair.', 'wings'],
    [['Space'], 'Wall-jump', 'Slide down a wall, then jump to leap off it.', 'talon'],
    [['↓', '+', 'Space'], 'Drop down', 'Fall through thin wooden floors.'],
    [['H', '/', 'C'], 'Root Hook', 'Near a golden ring, grapple and swing; jump to let go.', 'hook'],
    [['L'], 'Ember Dash', 'Roll into an ash veil to burn through it, untouchable.', 'emberdash'],
    [['Space', 'hold'], 'Gale Cloak', 'Hold jump while falling to glide; ride updrafts upward.', 'gale'],
    [['L', 'in air'], 'Air dash', 'Roll in the air to dash a short way.'],
  ] },
  { name: 'Touch', touch: true },
];
function guideInput(M, a) {
  const Gd = M.guide, n = GUIDE_PAGES.length;
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) { M.guide = null; sfx.menu(); return; }
  if (a === 'left' || a === 'spell') { Gd.page = (Gd.page + n - 1) % n; Gd.off = 0; sfx.menu(); }
  else if (a === 'right' || a === 'map' || ['confirm', 'interact', 'attack', 'jump'].includes(a)) { Gd.page = (Gd.page + 1) % n; Gd.off = 0; sfx.menu(); }
  else if (a === 'up') Gd.off = Math.max(0, Gd.off - 1);
  else if (a === 'down') Gd.off = Math.min(Gd.maxOff || 0, Gd.off + 1);
}
function renderGuide(M) {
  const Gd = M.guide, pg = GUIDE_PAGES[Gd.page];
  uiBackdrop(0.9); uiStrips();
  uiTitle('CONTROLS & TECHNIQUES', 16, 8);
  const pw = 72, x0 = W / 2 - pw * (GUIDE_PAGES.length - 1) / 2;
  GUIDE_PAGES.forEach((p, i) => {
    const x = x0 + i * pw, sel = i === Gd.page;
    text(p.name.toUpperCase(), x, 30, 5.6, sel ? UIC.hi : UIC.faint, 'center', { spacing: 1.2, weight: sel ? 600 : 500 });
    if (sel) { uiDiamond(x, 33.6, 1.1, UIC.gold); uiFade(x - 3, x - 26, 33.4, UI_RGB.gold, 0.9); uiFade(x + 3, x + 26, 33.4, UI_RGB.gold, 0.9); }
  });
  panel(10, 38, 364, 164);
  if (pg.touch) renderTouchGuide();
  else {
    const rows = pg.rows(), top = 44, bottom = 198, KX = 96, NX = 102, DX = 184, DW = 364 - DX;
    const laid = rows.map(([keys, name, desc, need]) => { const lines = wrap(desc || '', DW - 4, 5.3); return { keys, name, lines, need, h: Math.max(10, lines.length * 6.8 + 3.8) }; });
    let total = 0; for (const r of laid) { r.y = total; total += r.h; }
    const view = bottom - top; let maxOff = 0; while (maxOff < laid.length - 1 && total - laid[maxOff].y > view) maxOff++;
    Gd.maxOff = maxOff; Gd.off = Math.min(Gd.off, maxOff);
    const base = laid[Gd.off] ? laid[Gd.off].y : 0;
    laid.forEach((r, i) => {
      const y = top + r.y - base; if (i < Gd.off || y + r.h > bottom + 1) return;
      const locked = r.need && !SAVE.items[r.need];
      if (i % 2 === 0) uiRect(14, y, 356, r.h, 'rgba(176,138,58,0.045)');
      uiKeys(r.keys, KX, y + 7.6, { size: 4.9, dim: locked });
      if (locked) icon('lock', NX - 1, y + 1.8, 6, 0.7);
      text(r.name, NX + (locked ? 6 : 0), y + 7.6, uiFit(r.name, DX - NX - 6 - (locked ? 6 : 0), 5.8, 4.6), locked ? UIC.dim : UIC.hi, 'left', { weight: 600 });
      r.lines.forEach((l, k) => text(l, DX, y + 7.6 + k * 6.8, 5.3, locked ? UIC.faint : UIC.body, 'left', { weight: 400 }));
      if (locked && !r.lines.length) text('Not yet learned', DX, y + 7.6, 5, UIC.faint, 'left', { weight: 400 });
    });
    uiScroll(368, top, view, Gd.off, laid.length - maxOff, laid.length);
    if (rows.some(r => r[3] && !SAVE.items[r[3]])) { icon('lock', 16, 191, 6, 0.7); text('Not yet learned — found deeper in the Hallow', 24, 196, 4.8, UIC.faint, 'left', { weight: 400 }); }
  }
  // page dots
  GUIDE_PAGES.forEach((p, i) => uiDiamond(W / 2 - (GUIDE_PAGES.length - 1) * 4 + i * 8, 205.5, i === Gd.page ? 1.6 : 1.1, i === Gd.page ? UIC.gold : '#5a4a30'));
  uiFooter([['←→', 'page'], ...(pg.touch ? [] : [['↑↓', 'scroll']]), ['Esc', 'back']], 213);
}
function renderTouchGuide() {
  // a small phone with the on-screen buttons, and what they do in play and in menus
  const px = 20, py = 48, pw = 170, ph = 96;
  vctx.strokeStyle = '#8a6d36'; vctx.lineWidth = Math.max(1, scale * 0.6);
  vctx.beginPath(); vctx.roundRect ? vctx.roundRect(ox + px * scale, oy + py * scale, pw * scale, ph * scale, 8 * scale) : vctx.rect(ox + px * scale, oy + py * scale, pw * scale, ph * scale); vctx.stroke();
  uiRect(px + 4, py + 4, pw - 8, ph - 8, 'rgba(40,32,26,0.5)');
  const btn = (x, y, lab, r = 6.2) => {
    vctx.beginPath(); vctx.arc(ox + x * scale, oy + y * scale, r * scale, 0, 6.3); vctx.fillStyle = 'rgba(20,16,24,0.9)'; vctx.fill(); vctx.strokeStyle = UIC.accent; vctx.stroke();
    text(lab, x, y + 1.6, lab.length > 2 ? 3.3 : 4.8, UIC.text, 'center', { shadow: false });
  };
  btn(px + 22, py + ph - 38, '▲'); btn(px + 12, py + ph - 26, '◀'); btn(px + 22, py + ph - 14, '▼'); btn(px + 32, py + ph - 26, '▶');
  const right = ['Flask', 'Cast', 'Parry', 'Art', 'Hook', 'Use', 'Heavy', 'Roll', 'Strike', 'Jump'];
  right.forEach((l, i) => btn(px + pw - 76 + (i % 5) * 14.5, py + ph - 30 + Math.floor(i / 5) * 15, l));
  [['Map', 0], ['Menu', 1], ['OK', 2]].forEach(([l, i]) => { const x = px + pw - 58 + i * 18; vctx.strokeStyle = UIC.accent; vctx.strokeRect(ox + (x - 7) * scale, oy + (py + 7) * scale, 14 * scale, 7 * scale); text(l, x, py + 12.6, 3.8, UIC.text, 'center', { shadow: false }); });
  text('Your game', px + 60, py + 40, 5, UIC.faint, 'center', { weight: 400 });
  let fy = py + ph + 12; for (const l of wrap('Buttons act like held keys, so every technique in this guide works on touch.', pw, 5.2)) { text(l, px + pw / 2, fy, 5.2, UIC.muted, 'center', { weight: 400 }); fy += 7; }
  const notes = [
    ['Move & aim', 'Left pad. ▼ + Jump drops through thin floors; ▼ + Strike in the air pogos.'],
    ['Hold to charge', 'Hold Heavy or Art to charge; hold Jump while falling to glide; hold Parry to block.'],
    ['In the air', 'Heavy plunges; ▼ + Heavy is the Cinder Slam; Roll is an air dash.'],
    ['Menus', 'Arrows move, OK confirms, Menu goes back or closes, Map switches menu tabs.'],
    ['Travel', 'At a shrine, Map toggles the shrine list and the map cursor.'],
  ];
  let y = 50; for (const [h, d] of notes) {
    text(h, 202, y, 5.6, UIC.hi, 'left', { weight: 600 }); y += 6.8;
    for (const l of wrap(d, 162, 5.1)) { text(l, 202, y, 5.1, UIC.body, 'left', { weight: 400 }); y += 6.4; }
    y += 3.6;
  }
}

// ---- cinematic first-visit region title
let regionCard = null;   // { biome, name, sub, t }
const REGION_T = 3.8;
function regionEnter(def, prevBiome, opt = {}) {   // called from enterRoom; returns true when it took over the area card
  if (state === 'title' && opt.quiet) return false;   // title-screen backdrop
  if (!SAVE.seenAreas) {   // older saves: everything already explored counts as seen
    SAVE.seenAreas = {}; const v = Object.keys(SAVE.visited);
    if (v.length > 1) for (const id of v) if (ROOM_BY[id]) SAVE.seenAreas[ROOM_BY[id].biome] = 1;
  }
  if (regionCard && regionCard.biome !== def.biome) regionCard = null;
  if (def.test || !AREAS[def.biome] || SAVE.seenAreas[def.biome]) return false;
  SAVE.seenAreas[def.biome] = 1;
  regionCard = { biome: def.biome, name: AREAS[def.biome].name, sub: def.name, t: -0.5 };
  areaCard = null; return true;
}
HOOKS.update.push(dt => {   // runs only in play, so cutscenes, dialogue and menus hold the card
  const C = regionCard; if (!C) return;
  if (bossBanner) return;
  if (boss && boss.active && boss.alive) { if (C.t <= 0) { regionCard = null; return; } C.t = Math.max(C.t, REGION_T - 0.9); }
  if ((C.t += dt) > REGION_T) regionCard = null;
});
function renderRegionCard() {
  const C = regionCard; if (!C || C.t <= 0 || state !== 'play' || bossBanner) return;
  const t = C.t, a = clamp(Math.min(t / 0.9, (REGION_T - t) / 0.9), 0, 1), e = 1 - Math.pow(1 - clamp(t / 1.8, 0, 1), 3);
  band(a * 0.85, 62, 88);
  const cx = W / 2, cy = 102, X = ox + cx * scale, Y = oy + cy * scale, g = vctx.createRadialGradient(X, Y, 0, X, Y, 130 * scale);
  g.addColorStop(0, `rgba(230,160,80,${0.13 * a})`); g.addColorStop(1, 'rgba(230,160,80,0)'); vctx.fillStyle = g; vctx.fillRect(ox, oy + 62 * scale, W * scale, 88 * scale);
  const name = C.name.toUpperCase(); let size = 17, sp = 2 + 2.4 * e;
  while (size > 10 && textW(name, size, 500) + sp * name.length > 344) size -= 0.5;
  const half = (textW(name, size, 500) + sp * (name.length - 1)) / 2;
  text('REGION DISCOVERED', cx, 83, 4.8, '#b09a6a', 'center', { alpha: a * 0.85 * clamp(t / 1.2, 0, 1), spacing: 2.6, weight: 500 });
  text(name, cx + sp / 2, cy + 3, size, '#e6c77a', 'center', { alpha: a, spacing: sp, weight: 500 });
  const L = (half + 22) * e, ly = cy + 10;
  uiDiamond(cx, ly, 1.8, UIC.gold, a); uiDiamond(cx, ly, 3.4, UIC.accent, a * 0.6, true);
  uiFade(cx + 5, cx + 5 + L, ly - 0.2, UI_RGB.gold, 0.85 * a); uiFade(cx - 5, cx - 5 - L, ly - 0.2, UI_RGB.gold, 0.85 * a);
  text(C.sub, cx, cy + 22, 6.6, '#cfc2a4', 'center', { alpha: a * clamp((t - 0.5) / 0.8, 0, 1), weight: 400, spacing: 0.8 });
}

// ---- travel: shrine list grouped by region (left) + zooming world map (right)
function travelGroups() {
  const by = {}, order = [];
  for (const r of ROOMS) if (r.shrine && SAVE.shrines.includes(r.id)) { if (!by[r.biome]) { by[r.biome] = []; order.push(r.biome); } by[r.biome].push(r.id); }
  return order.map(b => ({ biome: b, ids: by[b] }));
}
function travelOpen(prev) {
  const flat = travelGroups().flatMap(g => g.ids);
  return { screen: 'travel', id: flat.includes(room.id) ? room.id : flat[0], prev, free: false, cam: null };
}
function travelMoveFree(M, flat, dir) {   // spatial: nearest shrine in that direction on the map
  const cur = shrinePos(M.id), [ux, uy] = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] }[dir];
  let best = null, bestScore = 1e9;
  for (const id of flat) {
    if (id === M.id) continue;
    const p = shrinePos(id), dx = p.x - cur.x, dy = p.y - cur.y, along = dx * ux + dy * uy, across = Math.abs(dx * uy - dy * ux);
    if (along <= 0.5) continue;
    const sc = along + across * 2.2; if (sc < bestScore) { bestScore = sc; best = id; }
  }
  if (!best) { sfx.deny(); return; }
  M.id = best; sfx.menu();
}
function travelInput(M, a) {
  const G_ = travelGroups(), flat = G_.flatMap(g => g.ids), conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  if (['pause', 'back', 'heavy', 'roll'].includes(a)) { menu = M.prev; sfx.menu(); return; }
  if (!flat.length) return;
  if (!flat.includes(M.id)) M.id = flat[0];
  if (a === 'map' || a === 'spell') { M.free = !M.free; sfx.menu(); return; }
  if (['up', 'down', 'left', 'right'].includes(a)) {
    if (M.free) return travelMoveFree(M, flat, a);
    const gi = G_.findIndex(g => g.ids.includes(M.id)), k = G_[gi].ids.indexOf(M.id);
    if (a === 'up' || a === 'down') { const i = flat.indexOf(M.id); M.id = flat[(i + (a === 'up' ? -1 : 1) + flat.length) % flat.length]; sfx.menu(); }
    else if (G_.length < 2) sfx.deny();
    else { const ng = G_[(gi + (a === 'left' ? -1 : 1) + G_.length) % G_.length]; M.id = ng.ids[Math.min(k, ng.ids.length - 1)]; sfx.menu(); }
    return;
  }
  if (conf) {
    const id = M.id;
    if (id === room.id) { sfx.deny(); toast('You are already here', 1.4); return; }
    sfx.kindle(); menu = null; state = 'play';
    fadeTo(() => { respawnAtShrine(id); setP('rise', pHas('rise') ? 'rise' : 'idle', false); });
  }
}
function mapColor(r) { return (AREAS[r.biome] && AREAS[r.biome].map) || MAP_COLS[r.biome] || '#5a5560'; }
function boundsOf(rooms) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const r of rooms) { x0 = Math.min(x0, r.gx); y0 = Math.min(y0, r.gy); x1 = Math.max(x1, r.gx + r.w); y1 = Math.max(y1, r.gy + r.h); }
  return { x0, y0, x1, y1 };
}
function fitAspect(b, ar, pad, minW) {
  let { x0, y0, x1, y1 } = b; x0 -= pad; y0 -= pad; x1 += pad; y1 += pad;
  if (x1 - x0 < minW) { const c = (x0 + x1) / 2; x0 = c - minW / 2; x1 = c + minW / 2; }
  const w = x1 - x0, h = y1 - y0;
  if (w / h < ar) { const nw = h * ar, c = (x0 + x1) / 2; x0 = c - nw / 2; x1 = c + nw / 2; } else { const nh = w / ar, c = (y0 + y1) / 2; y0 = c - nh / 2; y1 = c + nh / 2; }
  return { x0, y0, x1, y1 };
}
function renderTravel(M) {
  const G_ = travelGroups(), flat = G_.flatMap(g => g.ids);
  uiBackdrop(0.93);
  uiTitle('TRAVEL', 16, 9);
  if (!flat.length) { text('No shrine burns yet.', W / 2, 108, 7, UIC.dim, 'center'); uiFooter([['Esc', 'back']]); return; }
  if (!flat.includes(M.id)) M.id = flat[0];
  const gi = G_.findIndex(g => g.ids.includes(M.id)), grp = G_[gi], R = ROOM_BY[M.id];
  // ---- shrine list: every region as a header, the chosen region opened out to its shrines
  panel(8, 25, 124, 136);
  const lines = []; let ly0 = 0;
  for (const g of G_) {
    lines.push({ g, y: ly0 }); ly0 += 11;
    if (g === grp) for (const id of g.ids) { lines.push({ id, y: ly0 }); ly0 += 12.5; }
  }
  const top = 30, bot = 158, view = bot - top, selLine = lines.find(L => L.id === M.id), hdr = lines.find(L => L.g === grp);
  M.loff = clamp(M.loff || 0, Math.max(0, selLine.y + 12.5 - view), Math.min(hdr.y, Math.max(0, ly0 - view)));
  vctx.save(); vctx.beginPath(); vctx.rect(ox + 9 * scale, oy + (top - 1) * scale, 122 * scale, (view + 2) * scale); vctx.clip();
  for (const L of lines) {
    const y = top + L.y - M.loff; if (y < top - 13 || y > bot) continue;
    if (L.g) {
      const on = L.g === grp, an = (AREAS[L.g.biome] ? AREAS[L.g.biome].name : L.g.biome).replace(/^The /, '').toUpperCase();
      if (on) { const k = M.free ? 0 : uiPulse(5); text('◂', 14 - k * 0.7, y + 7.6, 5.4, UIC.gold, 'center', { alpha: M.free ? 0.35 : 1 }); text('▸', 126 + k * 0.7, y + 7.6, 5.4, UIC.gold, 'center', { alpha: M.free ? 0.35 : 1 }); }
      else uiDiamond(15, y + 5.6, 1.2, '#5a4a30');
      text(an, 20, y + 7.6, uiFit(an, 88, 5, 3.8, 600), on ? UIC.gold : UIC.faint, 'left', { spacing: 0.6, weight: 600 });
      if (!on) text(String(L.g.ids.length), 124, y + 7.4, 4.6, '#5f5646', 'right', { weight: 500 });
      if (on) uiFade(20, 120, y + 10, UI_RGB.accent, 0.6);
      continue;
    }
    const id = L.id, d = ROOM_BY[id], s = id === M.id, b = shrineBoss(id), here = id === room.id;
    if (s) uiSel(12, y, 116, 11.5, !M.free);
    icon('shrine', 17, y + 1.2, 9, s ? 1 : 0.75);
    const nm = d.shrine || d.name; text(nm, 29, y + 8.2, uiFit(nm, (b ? 76 : 90) - (here ? 12 : 0), 5.8, 4.4, s ? 600 : 500), s ? UIC.hi : UIC.body, 'left', { weight: s ? 600 : 500 });
    if (here) text('you', b ? 107 : 124, y + 8, 4.4, '#ff9070', 'right', { weight: 600 });
    if (b) drawBossMark(116, y + 2.2, b.done, 7);
  }
  vctx.restore();
  uiScroll(129.5, top, view, M.loff, view, ly0);
  // ---- map
  const bx = 136, by = 25, bw = 240, bh = 124, ib = { x: bx + 3, y: by + 3, w: bw - 6, h: bh - 6 };
  panel(bx, by, bw, bh, 0.55);
  const vis2 = mapVisible(), regionRooms = vis2.filter(r => r.biome === grp.biome);
  const world = fitAspect(boundsOf(vis2.length ? vis2 : [room.def]), ib.w / ib.h, 6, 60);
  const target = fitAspect(boundsOf(regionRooms.length ? regionRooms : [R]), ib.w / ib.h, 8, 64);
  const dt = M.camT !== undefined ? clamp(time - M.camT, 0, 0.5) : 0; M.camT = time;
  if (!M.cam) M.cam = { ...world };
  const kk = 1 - Math.exp(-dt * 6); for (const q of ['x0', 'y0', 'x1', 'y1']) M.cam[q] += (target[q] - M.cam[q]) * kk;
  const s = ib.w / (M.cam.x1 - M.cam.x0), X = gx => ib.x + (gx - M.cam.x0) * s, Y = gy => ib.y + (gy - M.cam.y0) * s;
  vctx.save(); vctx.beginPath(); vctx.rect(ox + ib.x * scale, oy + ib.y * scale, ib.w * scale, ib.h * scale); vctx.clip();
  const labels = {};
  for (const r of vis2) {
    const inR = r.biome === grp.biome, x = X(r.gx), y = Y(r.gy), w = r.w * s, h = r.h * s;
    vctx.fillStyle = r.id === room.id ? '#8a6a3a' : mapColor(r); vctx.globalAlpha = inR ? 0.62 : 0.2;
    vctx.fillRect(ox + x * scale, oy + y * scale, w * scale, h * scale);
    vctx.globalAlpha = inR ? 0.85 : 0.28; vctx.strokeStyle = inR ? '#d8cbb0' : '#8a806c'; vctx.lineWidth = Math.max(1, scale * 0.4);
    vctx.strokeRect(ox + x * scale, oy + y * scale, w * scale, h * scale); vctx.globalAlpha = 1;
    const L = labels[r.biome] || (labels[r.biome] = { x: 0, y: 0, n: 0 }); L.x += r.gx + r.w / 2; L.y += r.gy + r.h / 2; L.n++;
  }
  for (const [bio, L] of Object.entries(labels)) if (bio !== grp.biome && AREAS[bio]) text(AREAS[bio].name.replace(/^The /, ''), X(L.x / L.n), Y(L.y / L.n) + 2, 4.6, UIC.text, 'center', { alpha: 0.45, weight: 400 });
  // the way to the great foe ahead of the chosen shrine
  const sb = shrineBoss(M.id), sp = shrinePos(M.id);
  if (sb) for (const kind of sb.kinds) {
    const br = vis2.find(r => r.boss === kind); if (!br) continue;
    vctx.save(); vctx.setLineDash([2 * scale, 2 * scale]); vctx.strokeStyle = SAVE.flags['boss:' + kind] ? 'rgba(150,140,120,0.5)' : `rgba(224,96,80,${0.5 + 0.3 * uiPulse(4)})`; vctx.lineWidth = Math.max(1, scale * 0.6);
    vctx.beginPath(); vctx.moveTo(ox + X(sp.x) * scale, oy + Y(sp.y) * scale); vctx.lineTo(ox + X(br.gx + br.w / 2) * scale, oy + Y(br.gy + br.h / 2) * scale); vctx.stroke(); vctx.restore();
  }
  for (const r of vis2) if (r.boss && MAIN_BOSSES.has(r.boss)) drawBossMark(X(r.gx + r.w / 2) - 4, Y(r.gy + r.h / 2) - 4, !!SAVE.flags['boss:' + r.boss], 8);
  for (const id of flat) {
    const p = shrinePos(id), x = X(p.x), y = Y(p.y), selS = id === M.id, inR = ROOM_BY[id].biome === grp.biome;
    if (selS) {
      const rr = 7 + Math.sin(time * 6) * 1.2;
      vctx.beginPath(); vctx.arc(ox + x * scale, oy + (y - 2) * scale, rr * scale, 0, 6.3); vctx.fillStyle = 'rgba(255,190,90,0.18)'; vctx.fill();
      vctx.strokeStyle = '#ffd070'; vctx.lineWidth = Math.max(1, scale * 0.6); vctx.stroke();
    }
    icon('shrine', x - 4.5, y - 7, 9, selS ? 1 : inR ? 0.85 : 0.4);
  }
  const px = X(room.def.gx + P.x / TILE), py = Y(room.def.gy + P.y / TILE);
  vctx.fillStyle = Math.sin(time * 8) > 0 ? '#ff5050' : '#ffd0a0'; vctx.fillRect(ox + (px - 1.5) * scale, oy + (py - 3) * scale, 3 * scale, 3 * scale);
  vctx.restore();
  // overview inset: the whole explored world with the current view marked
  if ((M.cam.x1 - M.cam.x0) < (world.x1 - world.x0) * 0.8) {
    const iw = 52, ih = iw * (world.y1 - world.y0) / (world.x1 - world.x0), ix = ib.x + 2, iy = ib.y + ib.h - ih - 2, is = iw / (world.x1 - world.x0);
    uiRect(ix - 1, iy - 1, iw + 2, ih + 2, 'rgba(6,5,9,0.85)');
    for (const r of vis2) uiRect(ix + (r.gx - world.x0) * is, iy + (r.gy - world.y0) * is, Math.max(0.6, r.w * is), Math.max(0.6, r.h * is), r.biome === grp.biome ? '#c9a868' : '#6a6258', r.biome === grp.biome ? 0.9 : 0.6);
    vctx.strokeStyle = UIC.gold; vctx.lineWidth = Math.max(1, scale * 0.4);
    const vx0 = Math.max(ix, ix + (M.cam.x0 - world.x0) * is), vy0 = Math.max(iy, iy + (M.cam.y0 - world.y0) * is), vx1 = Math.min(ix + iw, ix + (M.cam.x1 - world.x0) * is), vy1 = Math.min(iy + ih, iy + (M.cam.y1 - world.y0) * is);
    vctx.strokeRect(ox + vx0 * scale, oy + vy0 * scale, (vx1 - vx0) * scale, (vy1 - vy0) * scale);
    vctx.strokeStyle = '#4a3e2c'; vctx.strokeRect(ox + (ix - 1) * scale, oy + (iy - 1) * scale, (iw + 2) * scale, (ih + 2) * scale);
  }
  if (M.free) text('MAP CURSOR', ib.x + ib.w - 3, ib.y + 7, 4.6, UIC.gold, 'right', { spacing: 1, alpha: 0.6 + 0.4 * uiPulse(4) });
  // ---- legend
  let lx = 140; const ly = 157;
  const leg = (draw, label) => { draw(lx); text(label, lx + 9, ly, 4.7, UIC.dim, 'left', { weight: 500 }); lx += 13 + textW(label, 4.7, 500); };
  leg(x => icon('shrine', x, ly - 7, 8), 'Shrine');
  leg(x => { vctx.beginPath(); vctx.arc(ox + (x + 3.5) * scale, oy + (ly - 2.2) * scale, 3.2 * scale, 0, 6.3); vctx.strokeStyle = '#ffd070'; vctx.lineWidth = Math.max(1, scale * 0.5); vctx.stroke(); }, 'Chosen');
  leg(x => uiRect(x + 2, ly - 4, 3, 3, '#ff5050'), 'You');
  leg(x => drawBossMark(x, ly - 6.5, false, 7), 'Great foe');
  leg(x => drawBossMark(x, ly - 6.5, true, 7), 'Vanquished');
  // ---- detail card
  panel(8, 165, 368, 36, 0.9);
  icon('shrine', 15, 170, 18);
  const nm = R.shrine || R.name; text(nm, 38, 180, uiFit(nm, 170, 7.4, 5), UIC.hi, 'left');
  text(`${R.name}  ·  ${AREAS[R.biome] ? AREAS[R.biome].name : ''}`, 38, 191, 5.3, UIC.muted, 'left', { weight: 400 });
  if (M.id === room.id) text('You rest here', 38 + textW(nm, uiFit(nm, 170, 7.4, 5)) + 6, 180, 5, '#ff9070', 'left', { weight: 600 });
  const b = shrineBoss(M.id);
  if (b) {
    drawBossMark(228, 172, b.done, 13);
    text(b.done ? 'Vanquished' : 'A great foe lies ahead', 246, 180, 6, b.done ? '#8a8070' : '#e06050', 'left', { weight: 600 });
    text(b.name, 246, 190, uiFit(b.name, 124, 5.3, 4.2, 400), b.done ? '#8a8070' : '#d8b0a0', 'left', { weight: 400 });
  } else text('No great foe stirs nearby', 368, 186, 5.2, UIC.faint, 'right', { weight: 400 });
  uiFooter(M.free ? [['←↑↓→', 'shrine on map'], ['Tab', 'list'], ['Enter', 'travel'], ['Esc', 'back']]
                  : [['↑↓', 'shrine'], ['←→', 'region'], ['Tab', 'map cursor'], ['Enter', 'travel'], ['Esc', 'back']]);
}

// ---- test hooks for the headless harness (tools/shots): region card / boss banner state and gear registration
window.__ui = { get regionCard() { return regionCard; }, set regionCard(v) { regionCard = v; }, set bossBanner(v) { bossBanner = v; }, registerGear, get menu() { return menu; } };

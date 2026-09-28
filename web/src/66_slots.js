// ------------------------------------------------------------------ save slots: the current journey + up to 3 old ones
// The current journey stays at SAVE_KEY (09_main.js). Starting a New Game moves it into the old-journeys list
// (localStorage OLD_KEY: [{ t, data }] newest first, at most OLD_MAX); when that list is full the title asks which old
// journey to forget. Title › Load Journey lists all of them: loading an old one swaps it with the current one.
const OLD_KEY = 'cinderhollow_old_saves_v1', OLD_MAX = 3;
function oldSaves() { try { const a = JSON.parse(localStorage.getItem(OLD_KEY) || '[]'); return Array.isArray(a) ? a.filter(o => o && typeof o.data === 'string') : []; } catch (e) { return []; } }
function setOldSaves(a) { try { localStorage.setItem(OLD_KEY, JSON.stringify(a.slice(0, OLD_MAX))); } catch (e) { toast('Not enough storage to keep that journey', 3); } }
function curSaveRaw() { try { return localStorage.getItem(SAVE_KEY); } catch (e) { return null; } }
function saveMeta(raw) {   // a short description of a stored journey
  let s = null; try { s = JSON.parse(raw); } catch (e) {}
  if (!s || !s.stats) return { ok: false, line1: 'Unreadable journey', line2: '' };
  const lv = levelOf(s.stats), R = ROOM_BY[s.shrine] || ROOM_BY.R1, area = AREAS[R.biome] ? AREAS[R.biome].name : R.name;
  const diff = typeof DIFFS !== 'undefined' ? (DIFFS[s.diff === 0 || s.diff === 2 ? s.diff : 1] || DIFFS[1]).name : '';
  const wpn = WEAPONS[s.weapon] ? WEAPONS[s.weapon].name : '';
  return { ok: true, lv, diff, line1: `Level ${lv}  ·  ${area}`, line2: `${fmtTime(s.playTime || 0)}  ·  ${diff}${s.ngp ? `  ·  Journey ${s.ngp + 1}` : ''}  ·  ${wpn}` };
}
// move the current journey into the old list (replacing index `rep` when the list is full)
function archiveCurrent(rep) {
  const raw = curSaveRaw(); if (!raw) return true;
  const a = oldSaves();
  if (a.length >= OLD_MAX) { if (rep === undefined || rep < 0) return false; a.splice(rep, 1); }
  a.unshift({ t: Date.now(), data: raw }); setOldSaves(a);
  return true;
}
function loadOld(i) {   // swap old journey i with the current one, then continue it
  const a = oldSaves(), o = a[i]; if (!o) return;
  const cur = curSaveRaw();
  a.splice(i, 1); if (cur) a.unshift({ t: Date.now(), data: cur });
  setOldSaves(a);
  try { localStorage.setItem(SAVE_KEY, o.data); } catch (e) { toast('Could not load that journey', 3); return; }
  _tsT = -9; TITLE_SLOTS.screen = null; sfx.kindle(); clearBuffer(); continueGame();
}
function forgetOld(i) { const a = oldSaves(); a.splice(i, 1); setOldSaves(a); _tsT = -9; }

// ---- title screens: 'load' (all journeys) and 'replace' (old list full on New Game)
const TITLE_SLOTS = { screen: null, sel: 0, pop: null, rep: undefined };
titleOptions = function () {
  const o = [];
  if (hasSave()) o.push('Continue');
  if (oldSaves().length) o.push('Load Journey');
  o.push('New Game');
  if (typeof trainingStart === 'function') o.push('Training Grounds');
  return o;
};
function titleNewGame() {   // New Game: make room for the current journey first, then choose a difficulty
  TITLE_SLOTS.rep = undefined;
  if (hasSave() && oldSaves().length >= OLD_MAX) { TITLE_SLOTS.screen = 'replace'; TITLE_SLOTS.sel = 0; TITLE_SLOTS.pop = null; sfx.menu(); return; }
  TITLE_DIFF.open = true; TITLE_DIFF.sel = 1;
}
function titleChoose(o) {
  if (o === 'Continue') { sfx.kindle(); clearBuffer(); continueGame(); }
  else if (o === 'Load Journey') { TITLE_SLOTS.screen = 'load'; TITLE_SLOTS.sel = 0; TITLE_SLOTS.pop = null; sfx.menu(); }
  else if (o === 'Training Grounds') { sfx.kindle(); clearBuffer(); trainingStart(); }
  else titleNewGame();
}
// the difficulty chooser starts the game: archive the current journey right then (not before, so backing out keeps it)
{ const _tdi = titleDiffInput; titleDiffInput = function (a) {
    const conf = ['confirm', 'attack', 'jump', 'interact'].includes(a);
    if (conf && TITLE_DIFF.open && !archiveCurrent(TITLE_SLOTS.rep)) { sfx.deny(); return; }
    return _tdi(a);
  }; }
function slotRows() {   // load screen rows: the current journey (if any) then the old ones
  const rows = [];
  const cur = curSaveRaw(); if (cur) rows.push({ cur: true, raw: cur });
  oldSaves().forEach((o, i) => rows.push({ old: i, raw: o.data, t: o.t }));
  return rows;
}
function titleSlotsInput(a) {
  const T = TITLE_SLOTS, conf = ['confirm', 'attack', 'jump', 'interact'].includes(a), back = ['pause', 'back', 'heavy', 'roll'].includes(a);
  const rows = T.screen === 'load' ? slotRows() : oldSaves().map((o, i) => ({ old: i, raw: o.data, t: o.t }));
  if (T.pop) {   // row actions / confirmation
    const P2 = T.pop, n = P2.opts.length;
    if (back) { T.pop = null; sfx.menu(); return; }
    if (['left', 'right', 'up', 'down'].includes(a)) { P2.sel = (P2.sel + (a === 'left' || a === 'up' ? n - 1 : 1)) % n; sfx.menu(); return; }
    if (!conf) return;
    const pick = P2.opts[P2.sel]; T.pop = null;
    if (pick === 'Load') loadOld(P2.row.old);
    else if (pick === 'Forget') { T.pop = { row: P2.row, opts: ['Forget it', 'Keep it'], sel: 1, ask: 'Forget this journey? It cannot be recovered.' }; sfx.menu(); }
    else if (pick === 'Forget it') {
      if (T.screen === 'replace') { T.rep = P2.row.old; T.screen = null; TITLE_DIFF.open = true; TITLE_DIFF.sel = 1; sfx.menu(); }   // forgotten once the new journey starts
      else { forgetOld(P2.row.old); sfx.crumble(); if (!oldSaves().length && !hasSave()) T.screen = null; T.sel = Math.max(0, Math.min(T.sel, slotRows().length - 1)); }
    } else sfx.menu();
    return;
  }
  if (back) { T.screen = null; sfx.menu(); return; }
  const n = rows.length + (T.screen === 'replace' ? 0 : 0);
  if (!n) { T.screen = null; return; }
  if (a === 'up' || a === 'down') { T.sel = (T.sel + (a === 'up' ? n - 1 : 1)) % n; sfx.menu(); return; }
  if (!conf) return;
  const r = rows[T.sel]; if (!r) return;
  if (T.screen === 'replace') { T.pop = { row: r, opts: ['Forget it', 'Keep it'], sel: 1, ask: 'Forget this old journey to make room for a new one?' }; sfx.menu(); return; }
  if (r.cur) { T.screen = null; sfx.kindle(); clearBuffer(); continueGame(); return; }
  T.pop = { row: r, opts: ['Load', 'Forget', 'Cancel'], sel: 0 }; sfx.menu();
}
function renderTitleSlots() {
  const T = TITLE_SLOTS, load = T.screen === 'load';
  const rows = load ? slotRows() : oldSaves().map((o, i) => ({ old: i, raw: o.data, t: o.t }));
  T.sel = Math.max(0, Math.min(T.sel, rows.length - 1));
  vctx.fillStyle = 'rgba(4,3,6,0.78)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  const px = 62, pw = 260, top = 44, rh = 28, ph = 30 + Math.max(1, rows.length) * rh;
  panel(px, top, pw, ph);
  text(load ? 'JOURNEYS' : 'OLD JOURNEYS ARE FULL', W / 2, top + 14, 7.5, '#e6c77a', 'center', { spacing: 1.5 });
  if (!load) text('Choose one to forget. Your current journey will take its place.', W / 2, top + 23, 5.2, '#b8ab90', 'center', { weight: 400 });
  rows.forEach((r, i) => {
    const y = top + (load ? 22 : 28) + i * rh, sel = i === T.sel, m = saveMeta(r.raw);
    if (sel) uiSel(px + 6, y, pw - 12, rh - 3, !T.pop);
    if (!T.pop) uiHit(px + 6, y, pw - 12, rh - 3, () => { T.sel = i; });
    const tag = r.cur ? 'CURRENT' : `ARCHIVED ${new Date(r.t || 0).toLocaleDateString()}`;
    text(m.line1, px + 14, y + 10, 6.6, sel ? '#f5e3b0' : '#d8cdb4', 'left', { weight: sel ? 600 : 500 });
    text(tag, px + pw - 12, y + 10, 4.6, r.cur ? '#ffd070' : '#8a7f6a', 'right', { spacing: 0.8, weight: 600 });
    text(m.line2, px + 14, y + 19.5, 5.2, '#9a8f78', 'left', { weight: 400 });
  });
  if (T.pop) {
    const P2 = T.pop, bw = 52, gap = 6, tw = P2.opts.length * bw + (P2.opts.length - 1) * gap, bx = W / 2 - tw / 2, by = top + ph + 6;
    UIM.hits.length = 0;   // only the popup is clickable
    panel(bx - 12, by, tw + 24, P2.ask ? 38 : 26);
    if (P2.ask) text(P2.ask, W / 2, by + 11, 5.4, '#f5e3b0', 'center', { weight: 500 });
    P2.opts.forEach((o, i) => {
      const x = bx + i * (bw + gap), y = by + (P2.ask ? 16 : 6), sel = i === P2.sel;
      if (sel) uiSel(x, y, bw, 13);
      uiHit(x, y, bw, 13, () => { P2.sel = i; });
      text(o, x + bw / 2, y + 9.2, 6.2, sel ? '#f5e3b0' : (o === 'Forget' || o === 'Forget it') ? '#d07060' : '#b8ab90', 'center', { weight: sel ? 600 : 400 });
    });
  }
  uiFooter(T.pop ? [['←→', 'choose'], ['Enter', 'confirm'], ['Esc', 'back']] : [['↑↓', 'journey'], ['Enter', load ? 'open' : 'choose'], ['Esc', 'back']], 206);
}

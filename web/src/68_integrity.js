// ------------------------------------------------------------------ Save integrity: signed saves and honest marks
// Every save carries a signature over its contents. A save edited by hand no longer matches and the journey is marked
// ✦ Tampered (it still loads and plays). Using the Cheats menu (or the #armory link) in a real journey marks it
// ✦ Cheated. Both marks are written into the save and survive. The Training Grounds never touch real saves.
// Not unbreakable -- the key ships with the game -- it keeps casual edits honest. Saves from before this have no
// signature and are accepted as clean; they are signed on their next save.
const SIG_SALT = 'cinder' + 'hollow' + ':kindle:7c3f';
function sigOf(str) {
  const s = SIG_SALT + str + SIG_SALT;
  let h1 = 0x811c9dc5 ^ 0x5bd1e995, h2 = 0x27d4eb2f;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 16777619);
    h2 = Math.imul(h2 ^ c, 2246822519); h2 ^= h2 >>> 13;
  }
  return (h1 >>> 0).toString(16).padStart(8, '0') + (h2 >>> 0).toString(16).padStart(8, '0');
}
function saveCheck(raw) {   // 'ok' | 'unsigned' | 'bad'
  let o = null; try { o = JSON.parse(raw); } catch (e) { return 'bad'; }
  if (!o || typeof o !== 'object') return 'bad';
  if (!o.sig) return 'unsigned';
  const sig = o.sig; delete o.sig;
  return sigOf(JSON.stringify(o)) === sig ? 'ok' : 'bad';
}
const inTraining = () => typeof TRAINING !== 'undefined' && TRAINING.on;
{ const _sg = saveGame; saveGame = function (...a) {
    if (SAVE && !inTraining()) { delete SAVE.sig; SAVE.at = room ? { room: room.id } : null; SAVE.sig = sigOf(JSON.stringify(SAVE)); }
    return _sg.apply(this, a);
  }; }
{ const _lg = loadGame; loadGame = function (...a) {
    const o = _lg.apply(this, a);
    if (o) { let raw = null; try { raw = localStorage.getItem(SAVE_KEY); } catch (e) {} if (raw && saveCheck(raw) === 'bad') o.tampered = 1; }
    return o;
  }; }
// ✦ Cheated: the cheat toggles on in a real journey, or the armory / techniques / shrine cheats used
const CHEAT_FLAGS = ['god', 'infst', 'inffp', 'nocd'];
function markCheated() { if (SAVE && !inTraining() && !SAVE.cheated) { SAVE.cheated = 1; saveGame(); } }
HOOKS.update.push(() => { if (state === 'play' && SAVE && !SAVE.cheated && !inTraining() && CHEAT_FLAGS.some(k => SETTINGS[k])) markCheated(); });
{ const _ga = giveArmory; giveArmory = function (...a) { const r = _ga.apply(this, a); markCheated(); return r; }; }
{ const _ss = settingsSubInput; settingsSubInput = function (M, a) {
    const S = M.sub, row = S && S.kind === 'cheats' ? CHEAT_ROWS[S.sel] : null;
    const conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
    const r = _ss.apply(this, [M, a]);
    if (row && !row.toggle && conf) markCheated();
    return r;
  }; }
function saveMarks(o) {   // the marks for a stored journey (object or raw string)
  let s = o, raw = null;
  if (typeof o === 'string') { raw = o; try { s = JSON.parse(o); } catch (e) { return ['✦ Tampered']; } }
  const m = [];
  if (s && (s.tampered || (raw && saveCheck(raw) === 'bad'))) m.push('✦ Tampered');
  if (s && s.cheated) m.push('✦ Cheated');
  return m;
}
// journey list: show the marks after the level / region line
{ const _sm = saveMeta; saveMeta = function (raw) { const m = _sm(raw), mk = saveMarks(raw); if (m.ok && mk.length) m.line1 += '  ' + mk.join(' '); return m; }; }
// Status tab: the marks under the character sheet
{ const _rs = renderStatusTab; renderStatusTab = function (M) {
    _rs(M);
    const mk = saveMarks(SAVE);
    if (mk.length) text(mk.join('  '), 82, 192.2, 4.6, '#d08060', 'center', { weight: 600 });
  }; }
// a tampered journey is re-signed with its mark straight away, so the mark sticks even if it is quit at once
{ const _cg = continueGame; continueGame = function (...a) { const r = _cg.apply(this, a); if (SAVE && SAVE.tampered && !inTraining()) saveGame(); return r; }; }

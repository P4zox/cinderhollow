// ------------------------------------------------------------------ Difficulty mode (per save: SAVE.diff 0 easy · 1 normal · 2 hard)
// Chosen when a new journey starts (title screen) and changeable in Settings. It sits on top of the journey curve in
// 59_difficulty.js and New Game+:
//   Easy   : bosses 0.65x HP / 0.7x damage, other foes 0.8x HP, everything else hurts 0.75x; dying drops only half your cinders
//   Normal : the game as tuned
//   Hard   : bosses 1.5x HP and 1.5x damage; the cinders you drop on death come back at half when you recover them
const DIFFS = [
  { name: 'Easy', bossHp: 0.65, bossDmg: 0.7, foeHp: 0.8, dmg: 0.75, cinders: 1, keepHalf: true,
    desc: 'Foes are weaker and hit softer. When you die, you keep half your cinders.' },
  { name: 'Normal', bossHp: 1, bossDmg: 1, foeHp: 1, dmg: 1, cinders: 1,
    desc: 'The journey as it was meant to be walked.' },
  { name: 'Hard', bossHp: 1.5, bossDmg: 1.5, foeHp: 1, dmg: 1, cinders: 1, halfRemnant: true,
    desc: 'Great foes are half again as strong. Cinders lost in death return only in half.' },
];
function diffIdx() { const d = SAVE && SAVE.diff; return d === 0 || d === 2 ? d : 1; }
function diffCfg() { return DIFFS[diffIdx()]; }
function setDiff(d) { SAVE.diff = clamp(d, 0, 2); diffRescale(); saveGame(); }

// HP: scale every boss body and foe once when it appears (and again by the ratio if the setting changes mid-fight)
function diffScaleHp(o, m) {
  if (!o || typeof o.hp !== 'number') return;
  const was = o._dm || 1; if (Math.abs(was - m) < 1e-6) return;
  const k = m / was; o._dm = m;
  for (const f of ['hp', 'maxHp', 'displayHp', 'fullMax']) if (typeof o[f] === 'number' && o[f] > 0) o[f] = Math.max(1, Math.round(o[f] * k));
}
function diffRescale() {
  if (!P) return;
  const C = diffCfg();
  if (boss) { diffScaleHp(boss, C.bossHp); if (boss.parts) for (const q of boss.parts) diffScaleHp(q, C.bossHp); }
  for (const e of enemies) if (e.alive !== false) diffScaleHp(e, e.boss ? C.bossHp : C.foeHp);
}
HOOKS.update.push(diffRescale);

// damage: boss fights use the boss factor for everything that hurts there; elsewhere the general one
{ const _hurt = hurtPlayer; hurtPlayer = function (dmg, ...rest) {
    const C = diffCfg(), inBoss = boss && boss.active && boss.alive;
    return _hurt.call(this, dmg * (inBoss ? C.bossDmg : C.dmg), ...rest);
  }; }
// cinders from foes, urns and bosses (recovering your own remnant is not affected)
{ const _gain = gainCinders; gainCinders = function (n, ...rest) { const k = diffCfg().cinders; return _gain.call(this, k < 1 ? Math.max(1, Math.round(n * k)) : n, ...rest); }; }
// Easy: you keep half of what you carried · Hard: the remnant left where you fell only holds half of it
{ const _fd = finishDeath; finishDeath = function () {
    const keep = diffCfg().keepHalf ? Math.floor(SAVE.cinders * 0.5) : 0;   // Easy: only half is left behind
    SAVE.cinders -= keep; _fd(); SAVE.cinders += keep;
    if (keep) { toast(`You kept ${keep} cinders`, 3); saveGame(); }
    if (diffCfg().halfRemnant && SAVE.remnant && !SAVE.remnant.halved) {
      SAVE.remnant.orig = SAVE.remnant.amount; SAVE.remnant.amount = Math.floor(SAVE.remnant.amount * 0.5); SAVE.remnant.halved = 1;
      if (SAVE.remnant.amount <= 0) SAVE.remnant = null;
      saveGame();
    }
  }; }
// New Game+ keeps the difficulty
{ const _ng = startNGPlus; startNGPlus = function (...a) { const d = SAVE.diff; const r = _ng.apply(this, a); SAVE.diff = d; saveGame(); return r; }; }

// ---- title: New Game asks for a difficulty first (TITLE_DIFF is read by 09_main.js's title input and 08_ui.js's renderTitle)
const TITLE_DIFF = { open: false, sel: 1 };
function titleDiffInput(a) {
  const conf = ['confirm', 'attack', 'jump', 'interact'].includes(a);
  if (a === 'up' || a === 'down') { TITLE_DIFF.sel = (TITLE_DIFF.sel + (a === 'up' ? 2 : 1)) % 3; sfx.menu(); }
  else if (['pause', 'back', 'heavy', 'roll'].includes(a)) { TITLE_DIFF.open = false; sfx.menu(); }
  else if (conf) { TITLE_DIFF.open = false; sfx.kindle(); clearBuffer(); newGame(); SAVE.diff = TITLE_DIFF.sel; saveGame(); }
}
function renderTitleDiff() {
  vctx.fillStyle = 'rgba(4,3,6,0.72)'; vctx.fillRect(ox, oy, W * scale, H * scale);
  panel(92, 70, 200, 104);
  text('CHOOSE YOUR PATH', W / 2, 86, 7.5, '#e6c77a', 'center', { spacing: 1.5 });
  DIFFS.forEach((d, i) => {
    const y = 104 + i * 14, sel = i === TITLE_DIFF.sel;
    if (sel) uiSel(100, y - 10, 184, 13);
    uiHit(100, y - 10, 184, 13, () => { TITLE_DIFF.sel = i; });
    text(d.name, W / 2, y, 7.5, sel ? '#f5e3b0' : '#b8ab90', 'center', { weight: sel ? 600 : 400 });
  });
  wrap(DIFFS[TITLE_DIFF.sel].desc, 180, 5.6).forEach((l, i) => text(l, W / 2, 152 + i * 7.5, 5.6, '#c9bda2', 'center', { weight: 400 }));
  text('You can change this later in Settings.', W / 2, 169, 5, '#7f745f', 'center', { weight: 400 });
}

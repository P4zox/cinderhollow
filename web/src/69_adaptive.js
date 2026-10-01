// ------------------------------------------------------------------ Bosses rise to meet you (SETTINGS.adapt, on by default)
// The journey curve (59_difficulty.js) assumes a typical build at each boss: level 5 + 6 per stage, the weapon at
// +min(5, stage/2), about half of the skill tree by the end. When a boss appears it measures YOUR build against that:
//   * your damage (weapon attack or spell power, whichever is higher, plus the skill tree's share) -> its HP
//   * your max HP -> its damage
// Stronger than expected (past a 10% grace) and it scales up in proportion, capped at x2.5 HP and x1.8 damage. It
// never gets easier for a weaker build. It stacks with difficulty mode and New Game+.
const BOSS_STAGE = { hound: 1, oswin: 2, coven: 2, warden: 2.5, omen: 3, vessel: 4, kalden: 4.5, librarian: 5, unwritten: 5.5,
  ferryman: 5.5, choir: 6, champion: 6, ice_warden: 6.5, twins: 7, butler: 7, sanguine: 7.5, executioners: 7.5, vael: 8,
  bellringer: 8, cindervane: 8.5, overseer: 9, colossus: 9.5, scarab: 9.5, pharaoh: 10, orrery: 10, astrel: 10.5, enforcer: 10.5,
  saint0: 11, sentinels: 11, sovereign: 12, first_ember: 13, venn: 13 };
const ADAPT_GRACE = 1.1, ADAPT_HP_MAX = 2.5, ADAPT_DMG_MAX = 1.8, ADAPT_SKILL = 0.4;
if (SETTINGS.adapt === undefined) SETTINGS.adapt = 1;
let SKILL_TOTAL = 0;
function adaptExpected(stage) {   // the typical build at this stage, with your current weapon (so weapon choice is neutral)
  const L = Math.round(5 + 6 * stage), U = Math.min(5, Math.round(stage / 2)), st = { ...BASE_STATS };
  const order = ['vig', 'str', 'dex', 'end', 'vig', 'str', 'dex', 'mnd'];
  for (let i = 0, n = L - levelOf(BASE_STATS); i < n; i++) st[order[i % order.length]]++;
  const w = SAVE.weapon, keep = SAVE.weapons[w];
  SAVE.weapons[w] = U; const d = derive(st, new Set()); SAVE.weapons[w] = keep;
  return { light: d.light, spell: d.spell, hp: d.maxHp, skill: 0.52 * Math.min(1, stage / 13) };   // share of the tree a typical run has learned
}
function adaptFor(kind) {   // -> { hp, dmg } multipliers for this boss against the current build
  if (!SETTINGS.adapt || !D || !SAVE) return { hp: 1, dmg: 1 };
  const stage = BOSS_STAGE[kind]; if (stage === undefined) return { hp: 1, dmg: 1 };
  if (!SKILL_TOTAL) SKILL_TOTAL = skillMaxLearnable() || 1;
  const X = adaptExpected(stage), frac = Math.min(1, SAVE.skills.length / SKILL_TOTAL);
  const power = Math.max(D.light / X.light, D.spell / X.spell) * (1 + ADAPT_SKILL * frac) / (1 + ADAPT_SKILL * X.skill);
  const tough = D.maxHp / X.hp;
  return { hp: clamp(power / ADAPT_GRACE, 1, ADAPT_HP_MAX), dmg: clamp(Math.pow(tough / ADAPT_GRACE, 0.85), 1, ADAPT_DMG_MAX) };
}
function adaptScale(o, m) {
  if (!o || typeof o.hp !== 'number' || o._am) return;
  o._am = m;
  if (m === 1) return;
  for (const f of ['hp', 'maxHp', 'displayHp', 'fullMax']) if (typeof o[f] === 'number' && o[f] > 0) o[f] = Math.max(1, Math.round(o[f] * m));
}
let adaptCur = { kind: null, hp: 1, dmg: 1, told: null };
HOOKS.update.push(() => {
  if (!boss || !P) return;
  if (!boss._am) {
    const a = adaptFor(boss.kind);
    adaptScale(boss, a.hp); if (boss.parts) for (const q of boss.parts) adaptScale(q, a.hp);
    adaptCur = { kind: boss.kind, hp: a.hp, dmg: a.dmg, told: adaptCur.kind === boss.kind ? adaptCur.told : null };
  }
  if (boss.active && adaptCur.told !== boss.kind && (adaptCur.hp > 1.05 || adaptCur.dmg > 1.05)) {
    adaptCur.told = boss.kind;
    toast(`It rises to meet your strength: +${Math.round((adaptCur.hp - 1) * 100)}% endurance, +${Math.round((adaptCur.dmg - 1) * 100)}% force`, 3.5);
  }
});
{ const _hurt = hurtPlayer; hurtPlayer = function (dmg, ...rest) {
    const on = boss && boss.active && boss.alive && adaptCur.kind === boss.kind;
    return _hurt.call(this, on ? dmg * adaptCur.dmg : dmg, ...rest);
  }; }

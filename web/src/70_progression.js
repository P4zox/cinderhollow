// ------------------------------------------------------------------ Progression costs (skills and levels are earned, not handed out)
//   * a skill point every 3 levels (was 2); Memory Shards still give one each
//   * every skill costs +1 point for each 15 skills you have already learned: the first fifteen cost their listed price,
//     the next fifteen +1, and so on. A learned skill keeps the price you paid for it.
//   * levels cost more cinders as they climb: unchanged up to level 10, +30% from level 40 on
// A typical run ends with about half of the tree, a thorough one with about 60%: builds are choices.
const SK_TAX_EVERY = 15, SK_PT_LEVELS = 3;
for (const s of SKILLS) {
  if (s._base !== undefined) continue;
  s._base = s.cost;
  Object.defineProperty(s, 'cost', { configurable: true, enumerable: true, get() {   // learned: what you paid; else: today's price
    const L = (SAVE && SAVE.skills) || [], i = L.indexOf(this.id);
    return this._base + Math.floor((i >= 0 ? i : L.length) / SK_TAX_EVERY);
  } });
}
skillBudget = function () { return Math.floor((levelOf(SAVE.stats) - 1) / SK_PT_LEVELS) + (SAVE.shards || 0); };
skillPoints = function () { return Math.max(0, skillBudget() - skillSpent()); };   // older journeys keep skills bought at the old rates
{ const _lc = levelCost; levelCost = function (L) { return Math.round(_lc(L) * (1 + 0.3 * clamp((L - 10) / 30, 0, 1))); }; }
// tell older journeys once
HOOKS.update.push(() => {
  if (state !== 'play' || !SAVE || SAVE.progv >= 3 || (typeof TRAINING !== 'undefined' && TRAINING.on)) return;
  const had = SAVE.skills.length > 0 || levelOf(SAVE.stats) > 12;
  SAVE.progv = 3;
  if (had) toast('Skills and levels now cost more as you grow: a skill point every 3 levels, and each skill costs more the more you know. What you have learned is kept.', 6);
});

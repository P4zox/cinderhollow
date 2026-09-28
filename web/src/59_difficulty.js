// ------------------------------------------------------------------ Difficulty curve (lead): the journey gets harder, not easier
// Player damage and HP each grow ~2.3x over a run and the skill tree roughly doubles damage again, while boss HP only
// grew ~3x and every boss hit for 20-50 whatever its place in the story. Measured and modelled in tools/shots/lead/
// (progress.js, bosshits.js): each boss gets [HP multiplier, damage multiplier] by where it sits in the journey.
// A smooth curve by stage (HP 1.3 + 0.14/stage, damage 1.05 + 0.045/stage), nudged per boss toward the model and capped
// at x3 HP and x1.6 damage: HP is the main lever, damage rises gently.
const BOSS_CURVE = {
  hound: [1.42, 1.10],   // stage 1
  oswin: [1.80, 1.25],   // stage 2
  coven: [1.80, 1.31],   // stage 2
  warden: [1.61, 1.21],   // stage 2.5
  omen: [1.53, 1.14],   // stage 3
  vessel: [1.90, 1.17],   // stage 4
  kalden: [2.31, 1.31],   // stage 4.5
  librarian: [2.50, 1.43],   // stage 5
  unwritten: [2.56, 1.32],   // stage 5.5
  ferryman: [2.57, 1.49],   // stage 5.5
  choir: [2.57, 1.50],   // stage 6
  champion: [2.62, 1.38],   // stage 6
  ice_warden: [2.66, 1.32],   // stage 6.5
  twins: [2.70, 1.23],   // stage 7
  butler: [2.70, 1.57],   // stage 7
  sanguine: [2.74, 1.60],   // stage 7.5
  executioners: [2.74, 1.53],   // stage 7.5
  vael: [2.78, 1.53],   // stage 8
  bellringer: [2.78, 1.54],   // stage 8
  cindervane: [2.82, 1.53],   // stage 8.5
  overseer: [2.86, 1.60],   // stage 9
  colossus: [2.90, 1.60],   // stage 9.5
  scarab: [2.90, 1.60],   // stage 9.5
  pharaoh: [2.94, 1.60],   // stage 10
  orrery: [2.94, 1.60],   // stage 10
  astrel: [2.98, 1.60],   // stage 10.5
  enforcer: [2.98, 1.60],   // stage 10.5
  saint0: [3.00, 1.60],   // stage 11
  sentinels: [3.00, 1.60],   // stage 11
  sovereign: [3.00, 1.60],   // stage 12
  first_ember: [3.00, 1.60],   // stage 13
  venn: [3.00, 1.60],   // stage 13
};
for (const [k, [h]] of Object.entries(BOSS_CURVE)) if (BOSS_INFO[k] && !BOSS_INFO[k]._curved) { BOSS_INFO[k].hp = Math.round(BOSS_INFO[k].hp * h); BOSS_INFO[k]._curved = 1; }
// damage: while a boss fight is on, whatever hurts you there (the boss, its projectiles, its arena hazards) is scaled
{ const _hurt = hurtPlayer; hurtPlayer = function (dmg, ...rest) { const c = boss && boss.active && boss.alive && BOSS_CURVE[boss.kind]; return _hurt.call(this, c ? dmg * c[1] : dmg, ...rest); }; }
// multi-body bosses (twins, coven, executioners, sentinels) give each body its own HP: they ask for the multiplier here
function bossHpMul(kind) { return (BOSS_CURVE[kind] || [1])[0]; }

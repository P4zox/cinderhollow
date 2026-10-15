// ------------------------------------------------------------------ Difficulty curve (lead): the journey gets harder, not easier
// Player damage and HP each grow ~2.3x over a run and the skill tree roughly doubles damage again, while boss HP only
// grew ~3x and every boss hit for 20-50 whatever its place in the story. Measured and modelled in tools/shots/lead/
// (progress.js, bosshits.js): each boss gets [HP multiplier, damage multiplier] by where it sits in the journey.
// A smooth curve by stage (HP 1.3 + 0.14/stage, damage 1.05 + 0.045/stage), nudged per boss toward the model and capped
// at x3 HP and x1.6 damage: HP is the main lever, damage rises gently.
// v15 (balance agent, docs/v15/balance.md): re-measured with the nine weapon types -- a scripted bot fights every boss with
// every type at the expected build of its stage (tools/shots/v15/balance/). Bosses that fell in about a minute for a
// handful of hits go past the x3 cap (Librarian, Butler, Scarab, Orrery, Enforcer, Sentinels, Champion); the ones that
// took 4-6 HP bars a fight hit softer or end sooner (Omen, Ice Warden, Pharaoh, Astrel; Unwritten, Overseer).
const BOSS_CURVE = {
  hound: [1.42, 1.10],   // stage 1
  oswin: [1.80, 1.25],   // stage 2
  coven: [1.80, 1.31],   // stage 2
  warden: [1.61, 1.21],   // stage 2.5
  omen: [1.40, 0.98],   // stage 3; v15: was 1.53 / 1.14 -- the hardest-hitting fight of the early game (bot: 4.8 HP bars a fight, 2.4 a minute)
  vessel: [1.90, 1.17],   // stage 4
  kalden: [2.31, 1.31],   // stage 4.5
  librarian: [3.00, 1.50],   // stage 5; v15: was 2.50 / 1.43 -- over in 47 s for 0.2 HP bars
  unwritten: [2.35, 1.32],   // stage 5.5; v15: was 2.56 -- the longest fight of its stage (200 s)
  ferryman: [2.57, 1.49],   // stage 5.5
  choir: [2.57, 1.50],   // stage 6
  champion: [2.90, 1.38],   // stage 6; v15: was 2.62 -- 68 s, 1.0 HP bars
  ice_warden: [2.66, 1.15],   // stage 6.5; v15: was 1.32 dmg -- the stomp took up to 47% of max HP
  twins: [2.70, 1.23],   // stage 7
  butler: [3.10, 1.57],   // stage 7; v15: was 2.70 -- 57 s, 0.7 HP bars
  sanguine: [2.74, 1.60],   // stage 7.5
  executioners: [2.74, 1.53],   // stage 7.5
  vael: [2.78, 1.53],   // stage 8
  bellringer: [2.78, 1.54],   // stage 8
  cindervane: [2.82, 1.53],   // stage 8.5
  overseer: [2.60, 1.60],   // stage 9; v15: was 2.86 -- 290 s, the longest fight in the game
  colossus: [2.90, 1.60],   // stage 9.5
  scarab: [3.30, 1.60],   // stage 9.5; v15: was 2.90 -- 57 s, 1.1 HP bars
  pharaoh: [2.80, 1.45],   // stage 10; v15: was 2.94 / 1.60 -- 4.4 HP bars a fight
  orrery: [3.20, 1.60],   // stage 10; v15: was 2.94 -- 78 s, 1.4 HP bars
  astrel: [2.80, 1.45],   // stage 10.5; v15: was 2.98 / 1.60 -- 5.6 HP bars a fight (the supernova fix takes ~0.2 off)
  enforcer: [3.30, 1.60],   // stage 10.5; v15: was 2.98 -- 61 s, 1.1 HP bars
  saint0: [3.00, 1.60],   // stage 11
  sentinels: [3.40, 1.60],   // stage 11; v15: was 3.00 -- 51 s, 0.7 HP bars
  sovereign: [3.00, 1.60],   // stage 12
  first_ember: [3.00, 1.60],   // stage 13
  venn: [3.00, 1.60],   // stage 13
};
for (const [k, [h]] of Object.entries(BOSS_CURVE)) if (BOSS_INFO[k] && !BOSS_INFO[k]._curved) { BOSS_INFO[k].hp = Math.round(BOSS_INFO[k].hp * h); BOSS_INFO[k]._curved = 1; }
// damage: while a boss fight is on, whatever hurts you there (the boss, its projectiles, its arena hazards) is scaled
// v15: except blows already sized to YOUR health (opt.pctHp, or Astrel's supernova: 82% of max HP). Scaled by x1.6 here,
// by 69's adapt and Hard mode they always killed outright, cover or no cover (the bot measured 1.00 max HP per nova).
function bossPctHit(dmg, opt) {
  if (opt && opt.pctHp) return true;
  const b = boss; return !!(b && b.kind === 'astrel' && b.state === 'nova' && b.nova && b.nova.st === 'blast' && D && dmg >= D.maxHp * 0.5);
}
{ const _hurt = hurtPlayer; hurtPlayer = function (dmg, dir, id, opt, ...rest) { const c = boss && boss.active && boss.alive && BOSS_CURVE[boss.kind]; return _hurt.call(this, c && !bossPctHit(dmg, opt) ? dmg * c[1] : dmg, dir, id, opt, ...rest); }; }
// multi-body bosses (twins, coven, executioners, sentinels) give each body its own HP: they ask for the multiplier here
function bossHpMul(kind) { return (BOSS_CURVE[kind] || [1])[0]; }

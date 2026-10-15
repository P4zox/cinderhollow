// ------------------------------------------------------------------ v15: Switch Axe (`saxe`, prefix sx_, weapon gravegrinder)
// SKELETON (platform agent). Spec: docs/WEAPON_REVAMP.md Part C, C1 (★★★★★). The saxe moveset agent owns this
// file and replaces the skeleton with the real moveset; nothing else in the game needs to change (docs/v15/platform.md).
// Intended identity:
// Blade mode earns the Switch Gauge (0-100) the hard way (+6 a landed blade hit, +10 on the beat, -10 a whiff,
// -25 when hit, bleeds 4/s after 2 s idle; hold K = Hone, +12/s rooted). At 100 the edge glows and I = Morph into the
// chainsaw Axe: slow, heavy, the real damage, draining 6/s + 4 a chainsaw hit; at 0 it vents back to the blade with a
// 0.6 s stagger. I in Axe mode = Full Release (>= 40 gauge, III) or morph back. HUD: the Switch Gauge (T.hud).
//
// The skeleton: a 3-hit light chain (J J J), K heavy, up J, air J, air down J (pogo), air K plunge, L roll, L -> J, and a
// rank-II L -> K (so the Mastery gating has something to gate). Every move lists its own tag first (sx_*, built by
// art/player_v15_saxe.py) and an existing fallback tag after it, so the art can land before or after the code.
mvRegister('saxe', {
  light: ['sx_1', 'sx_2', 'sx_3'], K: 'sx_heavy', up: 'sx_up', air: 'sx_air', down: 'sx_down',
  plunge: { dmg: 1.8, poise: 90, stam: 20 },
  dodge: MV_ROLL,
  rollJ: 'sx_rollj',
  rollK() { return mvHas(2) && mvStart('sx_rollk'); },
  // onI(ax) { ... }   I (default: the shared parry) -- the type's own button
  // tickAll(dt, cur) / tick(dt) / onHit(t, info, A, c) / hurt(c) / render() -- per-type state (see 76_mech_*.js)
  hud(x) { },   // the type's gauge goes here: x = the HUD column right of the stamina bar (mvHudX()), y ~ 18-26
  unlocks: [
    { rank: 2, id: 'sx_rollk', name: 'Turning cleave', input: 'L → K', desc: 'Placeholder (skeleton): a heavy blow out of the roll.' },
  ],
  combos: [
    { rank: 1, name: 'Rising edge · Falling edge · Double slash', input: 'J J J', desc: 'The skeleton light chain.' },
    { rank: 1, name: 'Phial thrust', input: 'K', desc: 'The heavy.' },
    { rank: 1, name: 'Skyward edge', input: '↑J', desc: 'Up attack.' },
    { rank: 1, name: 'Air slash', input: 'air J', desc: 'Air attack.' },
    { rank: 1, name: 'Plunge stab', input: 'air ↓J', desc: 'Pogo.' },
    { rank: 1, name: 'Plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 1, name: 'Lunging edge', input: 'L → J', desc: 'A cut out of the roll.' },
    { rank: 2, name: 'Turning cleave', input: 'L → K', desc: 'A heavy blow out of the roll.' },
  ],
}, {
  sx_1: { tags: ['sx_1', 'gs_1'], dmg: 0.9, poise: 10, stam: 10, wind: 140, total: 360, step: 0, next: { J: 'sx_2' }, fx: 'slash' },
  sx_2: { tags: ['sx_2', 'gs_2'], dmg: 0.95, poise: 10, stam: 10, wind: 140, total: 360, step: 1, next: { J: 'sx_3' }, fx: 'slash' },
  sx_3: { tags: ['sx_3', 'gs_3'], hits: [0.55, 0.55], poise: 16, stam: 12, wind: 160, total: 420, step: 2, fin: true, gap: 120, fx: 'slash' },
  sx_heavy: { tags: ['sx_heavy', 'gs_heavy'], dmg: 1.3, poise: 28, stam: 16, wind: 240, total: 600, kind: 'heavy', lunge: 14, fx: 'heavy' },
  sx_up: { tags: ['sx_up', 'gs_up'], dmg: 1.0, poise: 14, stam: 12, wind: 160, total: 400, up: true, reach: 30, fx: 'slash_up' },
  sx_air: { tags: ['sx_air', 'gs_air'], dmg: 1.0, poise: 12, stam: 12, wind: 150, total: 330, air: true, fx: 'slash_air' },
  sx_down: { tags: ['sx_down', 'gs_down'], dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300, down: true },
  sx_rollj: { tags: ['sx_rollj', 'attack1'], dmg: 1.1, poise: 14, stam: 12, wind: 140, total: 400, lunge: 18, fx: 'slash', next: { J: 'sx_2' } },
  sx_rollk: { tags: ['sx_rollk', 'gs_rollheavy'], dmg: 1.2, poise: 30, stam: 14, wind: 220, total: 600, rank: 2, kind: 'heavy', lunge: 16, fin: true, fx: 'heavy' },
});

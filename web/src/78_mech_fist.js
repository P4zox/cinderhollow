// ------------------------------------------------------------------ v15: Martial Arts (`fist`, prefix ft_, weapon penitent_knuckles)
// SKELETON (platform agent). Spec: docs/WEAPON_REVAMP.md Part C, C3 (★★★★). The fist moveset agent owns this
// file and replaces the skeleton with the real moveset; nothing else in the game needs to change (docs/v15/platform.md).
// Intended identity:
// Two styles, Swift (quick, light, evasive) and Iron (slow, armoured wind-ups, stance breaking). I from neutral
// switches style; I during a combo is a Shift strike that cancels on its hit into the other style's linking blow, so a
// combo runs Swift -> Iron -> Swift. Hits build Flow (5 pips); at 5, hold I = Ember palm (V). ~33 moves.
// HUD: the style + Flow pips (T.hud).
//
// The skeleton: a 3-hit light chain (J J J), K heavy, up J, air J, air down J (pogo), air K plunge, L roll, L -> J, and a
// rank-II L -> K (so the Mastery gating has something to gate). Every move lists its own tag first (ft_*, built by
// art/player_v15_fist.py) and an existing fallback tag after it, so the art can land before or after the code.
mvRegister('fist', {
  light: ['ft_1', 'ft_2', 'ft_3'], K: 'ft_heavy', up: 'ft_up', air: 'ft_air', down: 'ft_down',
  plunge: { dmg: 1.3, poise: 50, stam: 14 },
  dodge: {'stam': 8, 'total': 240, 'inv': 0.18, 'dist': 50, 'tags': ['roll']},
  rollJ: 'ft_rollj',
  rollK() { return mvHas(2) && mvStart('ft_rollk'); },
  // onI(ax) { ... }   I (default: the shared parry) -- the type's own button
  // tickAll(dt, cur) / tick(dt) / onHit(t, info, A, c) / hurt(c) / render() -- per-type state (see 76_mech_*.js)
  hud(x) { },   // the type's gauge goes here: x = the HUD column right of the stamina bar (mvHudX()), y ~ 18-26
  unlocks: [
    { rank: 2, id: 'ft_rollk', name: 'Sliding sweep', input: 'L → K', desc: 'Placeholder (skeleton): a heavy blow out of the roll.' },
  ],
  combos: [
    { rank: 1, name: 'Jab · Cross · Hook', input: 'J J J', desc: 'The skeleton light chain.' },
    { rank: 1, name: 'Snap kick', input: 'K', desc: 'The heavy.' },
    { rank: 1, name: 'Rising uppercut', input: '↑J', desc: 'Up attack.' },
    { rank: 1, name: 'Air kick', input: 'air J', desc: 'Air attack.' },
    { rank: 1, name: 'Stomp', input: 'air ↓J', desc: 'Pogo.' },
    { rank: 1, name: 'Plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 1, name: 'Shadow jab', input: 'L → J', desc: 'A cut out of the roll.' },
    { rank: 2, name: 'Sliding sweep', input: 'L → K', desc: 'A heavy blow out of the roll.' },
  ],
}, {
  ft_1: { tags: ['ft_1', 'dg_1'], dmg: 0.5, poise: 4, stam: 6, wind: 80, total: 220, step: 0, next: { J: 'ft_2' }, fx: 'slash' },
  ft_2: { tags: ['ft_2', 'dg_2'], dmg: 0.55, poise: 5, stam: 6, wind: 80, total: 220, step: 1, next: { J: 'ft_3' }, fx: 'slash' },
  ft_3: { tags: ['ft_3', 'dg_3'], dmg: 0.65, poise: 8, stam: 7, wind: 100, total: 260, step: 2, fin: true, fx: 'slash' },
  ft_heavy: { tags: ['ft_heavy', 'dg_heavy'], dmg: 0.9, poise: 12, stam: 9, wind: 140, total: 380, kind: 'heavy', lunge: 14, fx: 'heavy' },
  ft_up: { tags: ['ft_up', 'dg_up'], dmg: 0.8, poise: 16, stam: 9, wind: 120, total: 400, up: true, reach: 30, fx: 'slash_up' },
  ft_air: { tags: ['ft_air', 'dg_air'], dmg: 0.8, poise: 10, stam: 8, wind: 120, total: 300, air: true, fx: 'slash_air' },
  ft_down: { tags: ['ft_down', 'dg_down'], dmg: 0.8, poise: 10, stam: 8, wind: 100, total: 280, down: true },
  ft_rollj: { tags: ['ft_rollj', 'dg_1'], dmg: 0.8, poise: 10, stam: 8, wind: 100, total: 300, lunge: 18, fx: 'slash', next: { J: 'ft_2' } },
  ft_rollk: { tags: ['ft_rollk', 'dg_4'], dmg: 0.9, poise: 22, stam: 10, wind: 160, total: 420, rank: 2, kind: 'heavy', lunge: 16, fin: true, fx: 'heavy' },
});

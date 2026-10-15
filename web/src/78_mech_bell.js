// ------------------------------------------------------------------ v15: Warbell (`bell`, prefix wb_, weapon dirge_bell)
// SKELETON (platform agent). Spec: docs/WEAPON_REVAMP.md Part C, C5 (★★★). The bell moveset agent owns this
// file and replaces the skeleton with the real moveset; nothing else in the game needs to change (docs/v15/platform.md).
// Intended identity:
// Every blow rings a note into a 3-note staff: J = Ash, K = Ember, up J = Gold. Note sequences form tolls
// (Swiftness, Iron hymn, Fury, Mending, Echo); I = Perform plays every toll the staff holds as a ringing area blow and
// grants their buffs for 30 s. Bell hits are blunt (x1.3 stance damage). HUD: the 3-note staff (T.hud).
//
// The skeleton: a 3-hit light chain (J J J), K heavy, up J, air J, air down J (pogo), air K plunge, L roll, L -> J, and a
// rank-II L -> K (so the Mastery gating has something to gate). Every move lists its own tag first (wb_*, built by
// art/player_v15_bell.py) and an existing fallback tag after it, so the art can land before or after the code.
mvRegister('bell', {
  light: ['wb_1', 'wb_2', 'wb_3'], K: 'wb_heavy', up: 'wb_up', air: 'wb_air', down: 'wb_down',
  plunge: { dmg: 1.8, poise: 90, stam: 20 },
  dodge: {'stam': 18, 'total': 480, 'inv': 0.26, 'dist': 66, 'tags': ['roll']},
  rollJ: 'wb_rollj',
  rollK() { return mvHas(2) && mvStart('wb_rollk'); },
  // onI(ax) { ... }   I (default: the shared parry) -- the type's own button
  // tickAll(dt, cur) / tick(dt) / onHit(t, info, A, c) / hurt(c) / render() -- per-type state (see 76_mech_*.js)
  hud(x) { },   // the type's gauge goes here: x = the HUD column right of the stamina bar (mvHudX()), y ~ 18-26
  unlocks: [
    { rank: 2, id: 'wb_rollk', name: 'Bell drop', input: 'L → K', desc: 'Placeholder (skeleton): a heavy blow out of the roll.' },
  ],
  combos: [
    { rank: 1, name: 'Left swing · Right swing · Overhead clang', input: 'J J J', desc: 'The skeleton light chain.' },
    { rank: 1, name: 'Forward slam', input: 'K', desc: 'The heavy.' },
    { rank: 1, name: 'Peal uppercut', input: '↑J', desc: 'Up attack.' },
    { rank: 1, name: 'Air swing', input: 'air J', desc: 'Air attack.' },
    { rank: 1, name: 'Bell pogo', input: 'air ↓J', desc: 'Pogo.' },
    { rank: 1, name: 'Plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 1, name: 'Ringing lunge', input: 'L → J', desc: 'A cut out of the roll.' },
    { rank: 2, name: 'Bell drop', input: 'L → K', desc: 'A heavy blow out of the roll.' },
  ],
}, {
  wb_1: { tags: ['wb_1', 'ml_1'], dmg: 1.0, poise: 18, stam: 12, wind: 200, total: 500, step: 0, next: { J: 'wb_2' }, fx: 'slash' },
  wb_2: { tags: ['wb_2', 'ml_2'], dmg: 1.05, poise: 18, stam: 12, wind: 200, total: 500, step: 1, next: { J: 'wb_3' }, fx: 'slash' },
  wb_3: { tags: ['wb_3', 'ml_3'], dmg: 1.5, poise: 45, stam: 16, wind: 300, total: 760, step: 2, fin: true, fx: 'slash' },
  wb_heavy: { tags: ['wb_heavy', 'ml_pound'], dmg: 1.4, poise: 40, stam: 16, wind: 280, total: 700, kind: 'heavy', lunge: 14, fx: 'heavy' },
  wb_up: { tags: ['wb_up', 'ml_upswing'], dmg: 1.1, poise: 25, stam: 12, wind: 220, total: 560, up: true, reach: 30, fx: 'slash_up' },
  wb_air: { tags: ['wb_air', 'gs_air'], dmg: 1.0, poise: 18, stam: 12, wind: 160, total: 380, air: true, fx: 'slash_air' },
  wb_down: { tags: ['wb_down', 'gs_down'], dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300, down: true },
  wb_rollj: { tags: ['wb_rollj', 'ml_jab'], dmg: 1.0, poise: 20, stam: 12, wind: 160, total: 440, lunge: 18, fx: 'slash', next: { J: 'wb_2' } },
  wb_rollk: { tags: ['wb_rollk', 'ml_drop'], dmg: 1.4, poise: 45, stam: 16, wind: 260, total: 640, rank: 2, kind: 'heavy', lunge: 16, fin: true, fx: 'heavy' },
});

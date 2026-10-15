// ------------------------------------------------------------------ v15: Scythe (`scythe`, prefix sc_, weapon requiem_scythe)
// SKELETON (platform agent). Spec: docs/WEAPON_REVAMP.md Part C, C4 (★★★). The scythe moveset agent owns this
// file and replaces the skeleton with the real moveset; nothing else in the game needs to change (docs/v15/platform.md).
// Intended identity:
// Wide reaping arcs that hit in front and behind; the hooked tip pulls small foes in. A hit with the far half of
// an arc harvests a soul (max 3, wisps round the blade); hold K with souls = Reap (1.6 / 2.4 / 3.2, spends them).
// I = Hook step behind the foe (bosses from III). HUD: the souls (T.hud). The v9 scythe tags sc_1..sc_down already
// exist in the player sheet and the skeleton plays them (their hit boxes are now measured with the Requiem).
//
// The skeleton: a 3-hit light chain (J J J), K heavy, up J, air J, air down J (pogo), air K plunge, L roll, L -> J, and a
// rank-II L -> K (so the Mastery gating has something to gate). Every move lists its own tag first (sc_*, built by
// art/player_v15_scythe.py) and an existing fallback tag after it, so the art can land before or after the code.
mvRegister('scythe', {
  light: ['sc_1', 'sc_2', 'sc_3'], K: 'sc_heavy', up: 'sc_up', air: 'sc_air', down: 'sc_down',
  plunge: { dmg: 1.5, poise: 70, stam: 18 },
  dodge: MV_ROLL,
  rollJ: 'sc_rollj',
  rollK() { return mvHas(2) && mvStart('sc_rollk'); },
  // onI(ax) { ... }   I (default: the shared parry) -- the type's own button
  // tickAll(dt, cur) / tick(dt) / onHit(t, info, A, c) / hurt(c) / render() -- per-type state (see 76_mech_*.js)
  hud(x) { },   // the type's gauge goes here: x = the HUD column right of the stamina bar (mvHudX()), y ~ 18-26
  unlocks: [
    { rank: 2, id: 'sc_rollk', name: 'Leg sweep', input: 'L → K', desc: 'Placeholder (skeleton): a heavy blow out of the roll.' },
  ],
  combos: [
    { rank: 1, name: 'Low reap · High reap · Turning harvest', input: 'J J J', desc: 'The skeleton light chain.' },
    { rank: 1, name: 'Wide crescent', input: 'K', desc: 'The heavy.' },
    { rank: 1, name: 'Rising harvest', input: '↑J', desc: 'Up attack.' },
    { rank: 1, name: 'Air arc', input: 'air J', desc: 'Air attack.' },
    { rank: 1, name: 'Grave pogo', input: 'air ↓J', desc: 'Pogo.' },
    { rank: 1, name: 'Plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 1, name: 'Ghost slash', input: 'L → J', desc: 'A cut out of the roll.' },
    { rank: 2, name: 'Leg sweep', input: 'L → K', desc: 'A heavy blow out of the roll.' },
  ],
}, {
  sc_1: { tags: ['sc_1'], dmg: 0.9, poise: 10, stam: 10, wind: 160, total: 400, step: 0, next: { J: 'sc_2' }, back: 12, fx: 'slash' },
  sc_2: { tags: ['sc_2'], dmg: 0.95, poise: 12, stam: 10, wind: 160, total: 400, step: 1, next: { J: 'sc_3' }, back: 12, fx: 'slash' },
  sc_3: { tags: ['sc_3'], hits: [0.6, 0.6], poise: 20, stam: 12, wind: 200, total: 560, step: 2, fin: true, gap: 120, spin: true, backReach: 26, fx: 'slash' },
  sc_heavy: { tags: ['sc_heavy'], dmg: 1.3, poise: 30, stam: 16, wind: 280, total: 680, kind: 'heavy', lunge: 14, fx: 'heavy', spin: true, backReach: 30 },
  sc_up: { tags: ['sc_up'], dmg: 1.0, poise: 20, stam: 12, wind: 180, total: 460, up: true, reach: 30, fx: 'slash_up' },
  sc_air: { tags: ['sc_air'], dmg: 0.9, poise: 12, stam: 12, wind: 150, total: 360, air: true, fx: 'slash_air' },
  sc_down: { tags: ['sc_down'], dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300, down: true },
  sc_rollj: { tags: ['sc_rollj', 'sc_2'], dmg: 1.0, poise: 14, stam: 12, wind: 140, total: 400, lunge: 18, fx: 'slash', next: { J: 'sc_2' } },
  sc_rollk: { tags: ['sc_rollk', 'sc_heavy'], dmg: 1.1, poise: 30, stam: 14, wind: 200, total: 520, rank: 2, kind: 'heavy', lunge: 16, fin: true, fx: 'heavy' },
});

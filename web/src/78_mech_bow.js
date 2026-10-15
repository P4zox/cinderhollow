// ------------------------------------------------------------------ v15: Close-range Bow (`bow`, prefix bw_, weapon ashstring)
// SKELETON (platform agent). Spec: docs/WEAPON_REVAMP.md Part C, C2 (★★★). The bow moveset agent owns this
// file and replaces the skeleton with the real moveset; nothing else in the game needs to change (docs/v15/platform.md).
// Intended identity:
// Charge levels 1-3 (hold K draws up a level every 0.4 s; each shot in a chain raises the next one's) and the
// point-blank sweet spot (24-64 px x1.0, < 16 px x0.7, past 120 px x0.5). I = Limb deflect (a 150 ms parry, then an
// auto counter shot). HUD: the charge level (T.hud). The skeleton below is melee only (arrow stabs); the shots,
// levels and sweet spot are the moveset agent's.
//
// The skeleton: a 3-hit light chain (J J J), K heavy, up J, air J, air down J (pogo), air K plunge, L roll, L -> J, and a
// rank-II L -> K (so the Mastery gating has something to gate). Every move lists its own tag first (bw_*, built by
// art/player_v15_bow.py) and an existing fallback tag after it, so the art can land before or after the code.
mvRegister('bow', {
  light: ['bw_1', 'bw_2', 'bw_3'], K: 'bw_heavy', up: 'bw_up', air: 'bw_air', down: 'bw_down',
  plunge: { dmg: 1.5, poise: 60, stam: 16 },
  dodge: MV_ROLL,
  rollJ: 'bw_rollj',
  rollK() { return mvHas(2) && mvStart('bw_rollk'); },
  // onI(ax) { ... }   I (default: the shared parry) -- the type's own button
  // tickAll(dt, cur) / tick(dt) / onHit(t, info, A, c) / hurt(c) / render() -- per-type state (see 76_mech_*.js)
  hud(x) { },   // the type's gauge goes here: x = the HUD column right of the stamina bar (mvHudX()), y ~ 18-26
  unlocks: [
    { rank: 2, id: 'bw_rollk', name: 'Leaping point-blank', input: 'L → K', desc: 'Placeholder (skeleton): a heavy blow out of the roll.' },
  ],
  combos: [
    { rank: 1, name: 'Arrow stab · Second stab · Pinning thrust', input: 'J J J', desc: 'The skeleton light chain.' },
    { rank: 1, name: 'Point-blank lunge', input: 'K', desc: 'The heavy.' },
    { rank: 1, name: 'Rising stab', input: '↑J', desc: 'Up attack.' },
    { rank: 1, name: 'Aerial stab', input: 'air J', desc: 'Air attack.' },
    { rank: 1, name: 'Talon stomp', input: 'air ↓J', desc: 'Pogo.' },
    { rank: 1, name: 'Plunge', input: 'air K', desc: 'A falling slam.' },
    { rank: 1, name: 'Dash stab', input: 'L → J', desc: 'A cut out of the roll.' },
    { rank: 2, name: 'Leaping point-blank', input: 'L → K', desc: 'A heavy blow out of the roll.' },
  ],
}, {
  bw_1: { tags: ['bw_1', 'sp_1'], dmg: 0.8, poise: 8, stam: 9, wind: 120, total: 340, step: 0, next: { J: 'bw_2' }, fx: 'slash' },
  bw_2: { tags: ['bw_2', 'sp_2'], dmg: 0.85, poise: 8, stam: 9, wind: 120, total: 340, step: 1, next: { J: 'bw_3' }, fx: 'slash' },
  bw_3: { tags: ['bw_3', 'sp_3'], dmg: 1.3, poise: 30, stam: 12, wind: 200, total: 520, step: 2, fin: true, fx: 'slash' },
  bw_heavy: { tags: ['bw_heavy', 'sp_heavy'], dmg: 1.4, poise: 35, stam: 14, wind: 160, total: 520, kind: 'heavy', lunge: 14, fx: 'heavy' },
  bw_up: { tags: ['bw_up', 'sp_up'], dmg: 1.0, poise: 14, stam: 12, wind: 160, total: 400, up: true, reach: 30, fx: 'slash_up' },
  bw_air: { tags: ['bw_air', 'sp_air'], dmg: 0.9, poise: 12, stam: 10, wind: 150, total: 330, air: true, fx: 'slash_air' },
  bw_down: { tags: ['bw_down', 'sp_down'], dmg: 0.9, poise: 12, stam: 10, wind: 100, total: 300, down: true },
  bw_rollj: { tags: ['bw_rollj', 'sp_1'], dmg: 1.0, poise: 16, stam: 12, wind: 140, total: 400, lunge: 18, fx: 'slash', next: { J: 'bw_2' } },
  bw_rollk: { tags: ['bw_rollk', 'sp_hoplunge'], dmg: 1.5, poise: 36, stam: 16, wind: 200, total: 560, rank: 2, kind: 'heavy', lunge: 16, fin: true, fx: 'heavy' },
});

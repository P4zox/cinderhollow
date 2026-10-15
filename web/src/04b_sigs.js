// ------------------------------------------------------------------ shared swing helpers (the boss-weapon signatures are gone)
// Weapon revamp (agent WS, docs/WEAPON_REVAMP_CONTRACT.md): the 50 weapons became 9 types and the boss weapons, with their
// signature effects (SIGS), were removed. SIGS stays as an empty table so older call sites (04_player, 09_main, 61_feel)
// keep working; the helpers other files use (REACH_MUL, isFinisher, sigRect, sigTrail, burst, sigReach/sigLimit, hbOf) stay.
const REACH_MUL = 1.12;   // global forward-reach bonus for side attacks
function isFinisher(state) { const ms = moveset(); return state === ms.combo[ms.combo.length - 1] || state === 'attack4'; }
function sigRect(A) {
  const front = A.up || A.down ? A.reach[1] : A.reach[1] * (A.cls ? 1 : D.W.reach) * REACH_MUL;
  return rect(P.x + P.face * A.reach[0], P.y + A.ys[0], P.x + P.face * front, P.y + A.ys[1]);
}
function sigTrail(A, sg) {
  const r = sigRect(A);
  for (let i = 0; i < 3; i++) particles.push({ x: P.face > 0 ? r.x1 - rand(0, 10) : r.x0 + rand(0, 10), y: rand(r.y0, r.y1), vx: P.face * rand(10, 50), vy: -rand(0, 30), life: rand(0.2, 0.45), kind: Math.random() < 0.75 ? sg.pk : sg.pk2 });
  addLight((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, 46, sg.light, 0.8);
}
function burst(x, y, n, k1, k2, spd = 100) { for (let i = 0; i < n; i++) particles.push({ x: x + rand(-8, 8), y: y + rand(-12, 12), vx: P.face * rand(20, spd), vy: -rand(10, 70), g: 160, life: rand(0.3, 0.7), kind: Math.random() < 0.7 ? k1 : k2 }); }

// the weapon's own melee reach in px ahead of the player (its current moveset); 60_wbal's debug handle reads it
function sigReach() {
  const ms = moveset(); let r = 30;
  for (const tag of [...ms.combo, ms.heavy]) { const A = ATK[tag]; if (A) r = Math.max(r, A.reach[1] * (A.cls ? 1 : D.W.reach) * REACH_MUL); }
  return r;
}
const sigLimit = () => sigReach() * 1.5;

const SIGS = {};   // no weapon carries a boss signature any more

// bosses are big: give the player's blows a little more to hit
function hbOf(t) { const hb = t.hurtbox(); if (!hb || !t.boss) return hb; return rect(hb.x0 - 8, hb.y0 - 6, hb.x1 + 8, hb.y1); }

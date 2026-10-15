// feel checks: mash past finishers, turning inside a chain, lunge travel per move
const res = {};
arena();
// 1) mash: press J 5 times 90 ms apart (Longsword), count moves started
function mash(type, n, gapF) {
  W().reset(type, 5); arena(); W().reset(type, 5); E('D.maxSt = 1e6; P.st = 1e6');
  const seen = [];
  for (let i = 0; i < n; i++) { W().tap('attack', 1); for (let k = 0; k < gapF; k++) { W().frame(1); const s = E('P.state'); if (seen[seen.length - 1] !== s) seen.push(s); } }
  for (let k = 0; k < 150; k++) { W().frame(1); const s = E('P.state'); if (seen[seen.length - 1] !== s) seen.push(s); }
  return seen.join(' ');
}
for (const t of ['longsword', 'katana', 'sns', 'dual', 'greatsword', 'spear', 'staff', 'whip', 'maul']) res['mash5_' + t] = mash(t, 5, 6), res['mash9_' + t] = mash(t, 9, 6);
// 2) turn: J, J, then hold left during attack2 -> attack3 should face left
W().reset('longsword', 5); arena(); W().reset('longsword', 5);
W().tap('attack'); W().frame(10); W().tap('attack'); W().frame(5); W().down('left'); W().frame(40);
res.turn = E('P.state + " face " + P.face'); W().up('left');
// 3) lunge travel per move, standing still and holding forward
function travel(type, seq, fwd) {
  W().reset(type, 5); arena(); W().reset(type, 5); E('D.maxSt = 1e6; P.st = 1e6');
  if (fwd) W().down('right');
  const x0 = E('P.x'); const per = [];
  let last = x0;
  for (const b of seq) { W().tap(b === 'K' ? 'heavy' : 'attack'); for (let k = 0; k < 60; k++) { W().frame(1); if (E('!!ATK[P.state] && P.mvT > ATK[P.state].mv.total - 20')) break; } }
  W().frame(40); if (fwd) W().up('right');
  return Math.round(E('P.x') - x0);
}
res.ls_JJJJ_still = travel('longsword', ['J', 'J', 'J', 'J'], false);
res.ls_JJJK_still = travel('longsword', ['J', 'J', 'J', 'K'], false);
res.kt_JJJ_still = travel('katana', ['J', 'J', 'J'], false);
// 4) flash step distance and that it deals nothing
W().reset('katana', 5); arena(); W().reset('katana', 5); W().dummy(40);
E('P.sheathed = true'); const fx0 = E('P.x'); W().tap('roll'); W().frame(40);
res.flash = { state0: 'kt_flash', dist: Math.round(E('P.x') - fx0), hits: W().log.length };
return res;

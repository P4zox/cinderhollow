await boot();
const out = [];
G.SAVE.flags['cut:saint0'] = 1;
G.tp('NH7', 12, 10); G.step(10);
const B = G.boss; B.activate(); G.step(30); G.nhGod(true);
const orbs = () => G.props.filter(p => p.type === 'nh_orb');
// 1) melee deflection: face the white orb, strike when it is close
let reflected = 0, hp0 = B.hp, staggered = false, shots = 0;
for (let round = 0; round < 8 && !staggered; round++) {
  B.state = 'idle'; B.cool = 99; B.cancelMove(); G.P.x = 180; G.P.y = 176; B.x = 330; B.y = 110; B.tx = 330; B.ty = 110; G.step(20);
  // a single white orb straight at the player
  B.state = 'attack'; B.move = 'orbs'; B.mv = { v0: 1, v1: 1 }; B.mt = 5;
  const o = (function () { const a = Math.atan2(G.P.y - 14 - B.y, G.P.x - B.x); return window.__game.boss && null; })();
  G.step(1);
  B.state = 'idle'; B.cool = 99;
  // spawn via the fan helper through the move system
  B.startMove('orbs'); B.mv = { v0: 1, v1: 1, v2: 1 }; B.mt = 0;
  B.fx = B.fx; // keep
  const before = orbs().length; G.step(1);
  B.state = 'idle'; B.cool = 99;
  // fire exactly one white orb
  const fan = window.__nhFan; if (fan) fan(B, 1, [0]); else { B.startMove('orbs'); }
  shots++;
  for (let f = 0; f < 240; f++) {
    const w = orbs().find(p => p.kind === 'white' && !p.reflected);
    G.P.face = B.x > G.P.x ? 1 : -1;
    if (w && Math.hypot(w.x - G.P.x, w.y - (G.P.y - 14)) < 30) { G.step(1, [], ['attack']); } else G.step(1);
    if (G.boss.state === 'stagger') { staggered = true; break; }
  }
  reflected = hp0 - B.hp;
}
out.push(['melee deflect: boss hp lost', Math.round(hp0 - B.hp), 'staggered', staggered, 'shots', shots, 'critable', B.critable && B.critable(), 'y', Math.round(B.y)]);
// riposte while it is down
if (staggered) {
  for (let f = 0; f < 90 && !B.critable(); f++) G.step(1);
  G.P.x = B.x - 30; G.P.face = 1; const h = B.hp; G.step(2, [], ['attack']); G.step(60);
  out.push(['riposte dmg', Math.round(h - B.hp)]);
}
// 2) red orbs cannot be struck
B.state = 'idle'; B.cool = 99; B.cancelMove(); G.step(200);
const hpR = B.hp; window.__nhFan(B, 1, []);
for (let f = 0; f < 200; f++) { const r = orbs().find(p => p.kind === 'red'); G.P.face = B.x > G.P.x ? 1 : -1; if (r && Math.hypot(r.x - G.P.x, r.y - (G.P.y - 14)) < 30) G.step(1, [], ['attack']); else G.step(1); }
out.push(['red orb struck: boss hp change', Math.round(hpR - B.hp), 'any reflected red', orbs().some(p => p.kind === 'red' && p.reflected)]);
// 3) parry deflection
B.state = 'idle'; B.cool = 99; B.cancelMove(); B.stance = 0; G.step(200);
const hpP = B.hp; window.__nhFan(B, 1, [0]);
for (let f = 0; f < 240; f++) { const w = orbs().find(p => p.kind === 'white' && !p.reflected); G.P.face = B.x > G.P.x ? 1 : -1; if (w && Math.hypot(w.x - G.P.x, w.y - (G.P.y - 14)) < 22 && G.P.state !== 'parry') G.step(1, [], ['parry']); else G.step(1); }
out.push(['parry deflect: boss hp lost', Math.round(hpP - B.hp)]);
return out;

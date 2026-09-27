await boot(); G.SAVE.seenAreas = { hoarfrost: 1 }; G.give({ items: { talon: 1, hook: 1, emberdash: 1 } }); G.P.hp = 999;
const S = window.__sys, RB = window.__rb, sim = RB.sim, out = [];
G.tp('HF15', 28, 18); G.step(30);
const T = () => S.SYS.trial;
const P = G.P; sim(1, [], ['interact']); sim(20);
const found = [[-1,0,4,12],[-1,0,4,6],[-1,0,4,6],[-1,0,10,-1],[1,0,12,14],[1,0,12,9]];
for (let k = 0; k < found.length; k++) {
  const [dir, run, hold, dash] = found[k], d = dir < 0 ? 'left' : 'right';
  sim(1, [d, 'jump'], ['jump']); let air = false;
  for (let f = 1; f < 150; f++) {
    const hs = [d]; if (f < hold) hs.push('jump');
    sim(1, hs, f === dash ? ['roll'] : []);
    if (k === 5) out.push(`${f} ${P.state} ${P.anim.tag}:${P.anim.i} x${(P.x/16).toFixed(2)} y${(P.y/16).toFixed(2)} ad ${P.airDash} st ${Math.round(P.st)} lk ${P.ctrlLock}`);
    if (!P.ground) air = true; if (f > 3 && air && P.ground) break;
  }
  sim(10);
  out.push(`move ${k} -> ${(P.x/16).toFixed(2)},${(P.y/16).toFixed(2)} att ${T() && T().attempts}`);
}
return out.slice(0, 60);

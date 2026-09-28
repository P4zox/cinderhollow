await new Promise(r=>setTimeout(r,300));
const T = G.trn, out = []; T.start(); G.step(5);
for (const k of ['ferryman','saint0']) {
  T.summon(k); const b = G.boss;
  for (let i = 0; i < 10; i++) { const d = b.x - G.P.x; G.step(30, Math.abs(d) > 40 ? [d < 0 ? 'left' : 'right'] : [], Math.abs(d) <= 40 ? ['attack'] : []); G.P.hp = 9999;
    const hb = b.hurtbox ? b.hurtbox() : null; out.push(`${k} t${i} s=${b.state} hp=${Math.round(b.hp)} x=${Math.round(b.x)} y=${Math.round(b.y)} hb=${hb ? [hb.x0,hb.y0,hb.x1,hb.y1].map(Math.round).join(',') : null} P=${Math.round(G.P.x)},${Math.round(G.P.y)} ps=${G.P.state} tg=${G.trn.targets.length}`); }
  await snap('diag_' + k); T.clear(); G.step(3);
}
return out;

// agent W: the 10 Expansion-2 art bodies (logic by agent G) — tap and charged, release frame, end state, damage
await boot(); G.giveArmory(); G.tp('T0', 16, 16); G.step(20);
for (const e of G.enemies) e.die({ dir: 1 }); G.step(60);
const P = () => G.P, W = G.w, out = [];
const ARTS = [['reap', 'briar_scythe'], ['harvest_moon', 'antler_scythe'], ['lash', 'gravechain'], ['chain_drag', 'headsman_chain'],
  ['blood_frenzy', 'sanguine_rapier'], ['tidal_surge', 'choir_harpoon'], ['solar_flare', 'pharaoh_khopesh'], ['starfall', 'starblade'],
  ['overclock', 'plasma_katana'], ['pale_pyre', 'last_kindling']];
for (const [id, w] of ARTS) for (const charged of [false, true]) {
  G.give({ weapon: w, art: id }); G.tp('T0', 12, 16);
  const es = [W.spawn('hollow_soldier', 15, 16), W.spawn('hollow_soldier', 19, 16)]; es.forEach(e => { e.hp = e.maxHp = 3000; e.cool = 99; });
  G.step(3); P().face = 1; P().fp = G.D.maxFp; P().st = G.D.maxSt; P().hp = G.D.maxHp;
  if (charged) { G.step(1, ['art'], ['art']); let k = 0; while (P().artHold && k++ < 200) { G.step(1, ['art']); es.forEach(e => e.cool = 99); } G.step(1); }
  else G.step(1, [], ['art']);
  const seq = []; let relAt = null, own = P().artOwn, ch = P().artCharged, tag0 = P().anim.tag, frames = 0, snapped = false;
  for (let i = 0; i < 400 && P().state === 'art'; i++) {
    const wasRel = P().g2 && P().g2.rel;
    G.step(1); frames++; es.forEach(e => e.cool = 99);
    if (P().g2 && P().g2.rel && !wasRel && relAt === null) relAt = P().anim.i;
    if (P().state === 'art' && i % 4 === 0) seq.push(P().anim.i);
    if (!snapped && P().g2 && P().g2.rel && P().g2.t > 0.1) { snapped = true; await snap(`${id}_${charged ? 'ch' : 'tap'}`); }
  }
  out.push(`${id}${charged ? '*' : ' '} own=${own} tag=${tag0} charged=${ch} relAt=${relAt} frames=${frames} end=${P().state} dmg=${es.map(e => 3000 - Math.round(e.hp)).join('/')} i:${seq.join(',')}`);
  es.forEach(e => e.die({ dir: 1 })); G.step(20);
}
return out.join('\n');

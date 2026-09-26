// agent W, Expansion 2: scythe + whip classes, 21 weapons, 8 boss signatures
await boot(); G.giveArmory(); G.tp('T0', 16, 16); G.step(20);
for (const e of G.enemies) e.die({ dir: 1 }); G.step(60);
const P = () => G.P, W = G.w, out = [];
const st = () => `${P().state}/${P().anim.tag}:${P().anim.i}`;
const setup = (w, pos = [16, 19], hp = 3000) => { G.give({ weapon: w }); G.tp('T0', 13, 16); const es = pos.map(x => { const e = W.spawn('hollow_soldier', x, 16); e.hp = e.maxHp = hp; e.cool = 99; return e; }); G.step(3); P().face = 1; P().st = G.D.maxSt; return es; };
const run = async (n, es, snaps = {}) => { for (let i = 0; i < n; i++) { G.step(1); es.forEach(e => { e.cool = 99; }); P().st = G.D.maxSt; if (snaps[i]) await snap(snaps[i]); } };
const hp = es => es.map(e => Math.round(e.hp)).join('/');
// ---- scythe combo (pull) + heavy
let es = setup('briar_scythe', [16]); const x0 = Math.round(es[0].x); const seq = [];
for (let k = 0; k < 3; k++) { G.step(1, [], ['attack']); for (let i = 0; i < 26; i++) { G.step(1); es[0].cool = 99; if (i % 8 === 0) seq.push(st()); } }
out.push(`scythe combo: ${seq.join(' ')} | foe x ${x0}->${Math.round(es[0].x)} hp=${hp(es)}`);
G.step(40); es.forEach(e => e.die({ dir: 1 }));
// reap heal on kill
es = setup('briar_scythe', [15], 20); P().hp = 50; const h0 = P().hp; G.step(1, [], ['heavy']); await run(60, es, { 22: 'scythe_heavy' });
out.push(`scythe reap kill: alive=${es[0].alive} hp ${h0}->${Math.round(P().hp)}`);
// ---- whip combo + tip crack + chain pull
es = setup('gravechain', [15]); const wseq = []; const ex0 = Math.round(es[0].x);
for (let k = 0; k < 3; k++) { G.step(1, [], ['attack']); for (let i = 0; i < 16; i++) { G.step(1); es[0].cool = 99; es[0].x = ex0; if (i % 8 === 0) wseq.push(st()); if (k === 2 && i === 12) await snap('whip_finisher'); } }
out.push(`whip combo: ${wseq.join(' ')} hp=${hp(es)}`);
G.step(40); es.forEach(e => e.die({ dir: 1 }));
es = setup('headsman_chain', [16]); const px = Math.round(P().x), fx0 = Math.round(es[0].x);
G.step(1, [], ['heavy']); await run(50, es, { 14: 'whip_chain' });
out.push(`whip chain pull: foe x ${fx0}->${Math.round(es[0].x)} (player ${px}) hp=${hp(es)}`);
es.forEach(e => e.die({ dir: 1 }));
// ---- boss signatures: combo to the finisher + a heavy each
for (const w of ['antler_scythe', 'choir_harpoon', 'sanguine_rapier', 'vael_greatsword', 'pharaoh_khopesh', 'starblade', 'saint_lance', 'last_kindling']) {
  es = setup(w, [16, 19]); const n = W.moveset().combo.length;
  for (let k = 0; k < n; k++) { G.step(1, [], ['attack']); await run(k === n - 1 ? 40 : 22, es, k === n - 1 ? { 16: w + '_fin' } : {}); }
  const a = hp(es); G.step(30); P().x = es[0].x - 24; G.step(1, [], ['heavy']); await run(80, es, { 40: w + '_heavy' });
  out.push(`${w} (${W.wcls()}): after combo ${a}, after heavy ${hp(es)}, WFX=${W.WFX.length}`);
  es.forEach(e => e.die({ dir: 1 })); G.step(10);
}
// sanguine lifesteal on crit (dagger-free riposte via parry)
es = setup('sanguine_rapier', [15]); P().hp = 60; es[0].breakStance(); G.step(1, [], ['attack']); await run(40, es);
out.push(`rapier crit lifesteal: hp 60->${Math.round(P().hp)}`);
// every new weapon: combo + heavy without errors
for (const w of ['briar_scythe', 'thornwood_staff', 'tidecleaver', 'barnacle_fang', 'carving_knife', 'crimson_scythe', 'headsman_chain', 'gravechain', 'sun_sceptre', 'scarab_spear', 'meteor_maul', 'orrery_whip', 'plasma_katana']) {
  es = setup(w, [16]); for (let k = 0; k < 4; k++) { G.step(1, [], ['attack']); await run(20, es); } G.step(1, [], ['heavy']); await run(80, es);
  out.push(`${w}: ${W.wcls()} ok hp=${hp(es)}`); es.forEach(e => e.die({ dir: 1 }));
}
return out.join('\n');

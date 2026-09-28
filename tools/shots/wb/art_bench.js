// weapon-art bench (agent WB): one use of every art on a held boss, tapped and fully charged, on the weapon that carries it.
// SHOT_HTML=web/dist/wb.html node tools/shots/shot.js tools/shots/wb/art_bench.js tools/shots/wb/out
// Reports damage per use in "light hits" (damage / the weapon's light attack rating), per FP and per second of cooldown,
// the time spent untouchable (i-frames) and the time the art locks you in. Buff arts (War Cry, Cinder Blade, Overclock...)
// show ~0 here; their value is the art column of bench_real.js.
await boot(); G.giveArmory(); G.grantTechniques();
const E = G.sk.ev;
E(`(() => { if (window.__wbA) return; const W = window.__wbA = { ms: 0 }; performance.now = () => W.ms;
  W.step = (n, hold = [], tap = []) => { tap.forEach(press); hold.forEach(a => held.add(a)); for (let i = 0; i < n; i++) { W.ms += 1000 / 60; update(1 / 60); } hold.forEach(release); tap.forEach(release); }; })()`);
const I = () => window.__wbA;
const ST = { vig: 35, mnd: 25, end: 25, str: 30, dex: 30, fth: 25 };
const artOf = id => E(`(typeof wbArtOf === 'function' ? wbArtOf(${JSON.stringify(id)}) : WEAPONS[${JSON.stringify(id)}].art)`);
const weapons = E('Object.keys(WEAPONS)');
const carriers = {};
for (const w of weapons) { const a = artOf(w); (carriers[a] = carriers[a] || []).push(w); }
const arts = (typeof ONLY_ARTS !== 'undefined' && ONLY_ARTS) || E('Object.keys(ARTS)');
const out = {};
for (const art of arts) {
  const w = (carriers[art] && carriers[art][0]) || 'longsword';
  const res = { weapon: w, carriers: (carriers[art] || []).join(' '), fp: E(`ARTS.${art}.fp`), cd: +E(`cdBase('art', '${art}')`).toFixed(1) };
  for (const mode of ['tap', 'charged']) {
    { let seed = 777; Math.random = () => (seed = (seed * 16807) % 2147483647) / 2147483647; }
    G.SAVE.weapon = w; G.SAVE.weapons[w] = 5; G.SAVE.lastCls = 'sword';
    G.give({ stats: { ...ST }, charmsEq: [], skills: [] });
    delete G.SAVE.flags['boss:hound']; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + 'hound'] = 1;
    G.tp('C5', 6, 10); const b = G.boss;
    for (let i = 0; i < 200 && !b.active; i++) { I().step(4, ['right']); G.P.hp = 99999; if (G.state !== 'play') G.step(1, [], ['pause']); }
    const bx = b.x, by0 = b.y;
    b.update = function (dt) { this.x = bx; this.y = by0; this.commonUpdate(dt); if (this.state === 'stagger') { this.anim.update(dt); this.t -= dt; if (this.t <= 0) { this.state = 'idle'; this.anim.set('idle', true); } } };
    b.state = 'idle'; b.maxHp = 3500; b.hp = 1e7; b.stance = 0;
    G.SAVE.art = art;   // (after the lock lands this is what the weapon carries anyway)
    E('refreshDerived(false); P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt; P.cds = {}; hitstop = 0; slowmo = 0; clearBuffer(); P.fireT = 0; P.cryT = 0; if (P.g3) P.g3 = null');
    G.P.x = bx - 40; G.P.face = 1;
    I().step(2);
    G.SAVE.art = art;
    const fp0 = G.P.fp; let dealt = 0, iframes = 0, lock = 0;
    for (let f = 0; f < 60 * 5; f++) {
      const tap = f === 0 ? ['art'] : [], hold = mode === 'charged' && f < 66 ? ['art'] : [];
      const h0 = b.hp; G.SAVE.art = art;
      I().step(1, hold, tap);
      dealt += Math.max(0, h0 - b.hp);
      if (G.P.state === 'art') { lock++; if (E('iframes() || P.inv > 0')) iframes++; }
      if (G.state !== 'play') G.step(1, [], ['pause']);
    }
    const L = G.D.light, used = Math.round(fp0 - G.P.fp);
    res[mode] = { dmg: Math.round(dealt), hits: +(dealt / L).toFixed(2), fpUsed: used, iframeS: +(iframes / 60).toFixed(2), lockS: +(lock / 60).toFixed(2) };
  }
  res.perFp = +(res.tap.hits / Math.max(1, res.fp)).toFixed(3);
  res.perCd = +(res.tap.hits / Math.max(0.1, res.cd)).toFixed(3);
  out[art] = res;
}
return out;

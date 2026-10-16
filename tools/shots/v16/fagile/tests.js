// v16 fagile: the four agile fatalities (dual, staff, whip, fist) with real inputs (K on a staggered foe) in real boss
// arenas (one multi-body) and on regular foes: damage (5.0 x AR on bosses, 8 x AR / execute on foes), invulnerability,
// the hold (the other body never moves), the tag in use, a clean end + recovery, and every frame RENDERED (draw code runs).
G.SAVE.flags['sc:seal'] = 1; G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1;
const TYPES = window.__types || ['dual', 'staff', 'whip', 'fist'];
const ARENAS = window.__arenas || [['C5', 'hound', 6, 10], ['K4', 'omen', 6, 10], ['HF7', 'twins', 4, 13], ['NV5', 'executioners', 30, 10], ['SP5', 'bellringer', 3, 10]];
const out = {};
const runOut = (hurtAt) => {   // play it out, rendering every frame; try to hurt the player mid-way
  let f = 0, hurt = null, tags = new Set(), moved = false;
  const oth = () => JSON.stringify(E(`window.__q && boss && boss.parts ? boss.parts.filter(p => p !== __q).map(p => Math.round(p.x) + ':' + Math.round(p.y) + ':' + p.state) : []`));
  const o0 = oth();
  while (E('!!FAT.on') && f++ < 500) {
    W().frame(1); E('render()'); tags.add(E('P.anim.tag')); if (E('!!FAT.on') && oth() !== o0) moved = true;
    if (f === hurtAt) hurt = E(`(() => { const h0 = P.hp; const r = hurtPlayer(9999, P.face, 'fat_t', { parryable: true }); spikeHurt(); return { r, same: P.hp === h0, st: P.state }; })()`);
  }
  W().frame(3); const end = E('P.state');
  let rec = -1;
  for (let i = 0; i < 90; i++) { W().frame(1); E('P.hp = D.maxHp'); if (i % 3 === 0) E('render()'); if (rec < 0 && E('window.__q && (__q.alive === false || __q.state !== "stagger")')) rec = i; }   // lingering effects keep drawing
  return { f, hurt, tags: [...tags], end, rec, moved, multi: o0 !== '[]' };
};
for (const ty of TYPES) {
  const res = out[ty] = {};
  for (const [r, k, x, y] of ARENAS) {
    try {
      W().reset(ty, 1);
      delete G.SAVE.flags['boss:' + k]; for (const fl of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[fl + k] = 1;
      G.tp(r, x, y); W().frame(2); W().reset(ty, 1);
      const b = G.boss; if (!b) { res[k] = 'NO BOSS'; continue; }
      for (let j = 0; j < 300 && !b.active; j++) { E(`P.x += ${b.x < G.P.x ? -2 : 2}`); W().frame(1); E('P.hp = D.maxHp'); }
      W().frame(200); E('P.hp = D.maxHp');
      E(`window.__q = (boss.parts || [boss]).filter(p => p.alive !== false && typeof p.critable === 'function' && typeof p.stagger === 'function')[0] || boss; (__q.stagger || boss.stagger).call(__q.stagger ? __q : boss);`);
      let ok = false;
      for (let j = 0; j < 40 && !ok; j++) { W().frame(1); ok = E(`(() => { const q = __q; if (!q.critable()) return false; const side = P.x < q.x ? -1 : 1; P.y = q.floor ?? q.y; P.vy = 0; P.ground = true; P.x = q.x + side * Math.min((q.critRange || 34) - 8, 40); P.face = -side; P.state = 'idle'; P.anim.set('idle', true); return critTarget() === q; })()`); }
      if (!ok) { res[k] = 'not critable'; continue; }
      const others0 = E(`(boss.parts || []).filter(p => p !== __q).map(p => Math.round(p.x) + ':' + p.state)`);
      E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
      const started = E('P.state') === 'fatality', name = E('FAT.on && FAT.on.name');
      let moved = false;
      const R = runOut(25); let rec = R.rec;
      const others1 = E(`(boss.parts || []).filter(p => p !== __q).map(p => Math.round(p.x) + ':' + p.state)`);
      const L = E('FAT.last');
      const end = R.end, held = E('!!boss._fatHold || !!__q._fatHold');
      for (let j = 0; j < 300; j++) { W().frame(1); E('P.hp = D.maxHp'); if (rec < 0 && E('__q.alive === false ? "dead" : __q.state') !== 'stagger') rec = j; }
      res[k] = { started, name, ratio: +(L.dealt / L.unit).toFixed(2), beats: L.beats.map(q => q.at + ':' + q.share), frames: R.f, tags: R.tags, hurt: R.hurt, end, held, recover: rec,
        otherBody: R.multi ? (R.moved ? 'MOVED' : 'still') : '-', pass: !R.moved && started && Math.abs(L.dealt / L.unit - 5) < 0.1 && R.hurt && R.hurt.same && !held && ['idle', 'air'].includes(end) && rec >= 0 };
      G.SAVE.flags['boss:' + k] = 1;
    } catch (e) { res[k] = 'EXC ' + e.message; }
  }
  // regular foes: a tough one (8 x AR) and a weak one (executed)
  for (const [lab, hp] of [['foe8x', 30000], ['foeExec', 20]]) {
    try {
      G.tp('C5', 6, 10); G.SAVE.flags['boss:hound'] = 1; W().frame(30); W().reset(ty, 1); for (let j = 0; j < 60 && !G.P.ground; j++) W().frame(1);
      E(`window.__q = null; enemies = []; const e = makeEnemy('hollow_soldier', P.x + 26, P.y, 'fx_ag'); e.hp = e.maxHp = ${hp}; enemies.push(e); e.breakStance(); window.__t = e;`);
      W().frame(2); E('clearBuffer(); held.clear()'); W().tap('heavy', 1);
      const started = E('P.state') === 'fatality';
      const x0 = E('Math.round(__t.x)');
      const R = runOut(30);
      const L = E('FAT.last');
      res[lab] = { started, exec: L.exec, ratio: +(L.dealt / L.unit).toFixed(2), alive: E('__t.alive !== false && __t.hp > 0'), end: R.end, held: E('!!__t._fatHold'),
        foeMoved: E('Math.round(__t.x)') - x0, foeGround: E('!!__t.ground'), hurt: R.hurt, tags: R.tags,
        pass: started && (hp > 1000 ? Math.abs(L.dealt / L.unit - 8) < 0.05 : !E('__t.alive !== false && __t.hp > 0')) && R.end === 'idle' && !E('!!__t._fatHold') && R.hurt && R.hurt.same };
    } catch (e) { res[lab] = 'EXC ' + e.message; }
  }
  res.pass = Object.values(res).every(v => v && v.pass);
}
out.allPass = TYPES.every(t => out[t].pass);
return out;

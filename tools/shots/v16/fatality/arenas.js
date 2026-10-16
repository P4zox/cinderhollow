// v16 fatality in REAL boss arenas: stagger the boss (or one body of a duo), K from the riposte range, check damage,
// the hold (no body moves or attacks mid-fatality, no hits on the player), invulnerability, and a clean recovery after.
G.SAVE.flags['sc:seal'] = 1; G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1;
const CASES = window.__cases || [['C5','hound',6,10],['K4','omen',6,10],['M5','kalden',6,10],['HF7','twins',4,13],['NV5','executioners',30,10],['X3','sentinels',3,8],['NV7','vael',40,12],['TV8','warden',5,10],['HF4','ice_warden',31,10],['SP5','bellringer',3,10],['A3','librarian',20,10]];
const TYPE = window.__type || 'longsword';
const out = {};
for (const [r, k, x, y] of CASES) {
  try {
    W().reset(TYPE, 1);
    delete G.SAVE.flags['boss:' + k]; for (const f of ['cut:', 'cutp2:', 'cutp3:']) G.SAVE.flags[f + k] = 1;
    G.tp(r, x, y); W().frame(2);
    let b = G.boss; if (!b) { out[k] = 'NO BOSS'; continue; }
    for (let i = 0; i < 300 && !b.active; i++) { E(`P.x += ${b.x < G.P.x ? -2 : 2}`); W().frame(1); E('P.hp = D.maxHp'); }
    W().frame(200); E('P.hp = D.maxHp');
    if (!b.active) { out[k] = 'never active'; continue; }
    // stagger one body
    E(`window.__q = (boss.parts || [boss]).filter(p => p.alive !== false && typeof p.critable === 'function' && typeof p.stagger === 'function')[0] || boss;
       (__q.stagger || boss.stagger).call(__q.stagger ? __q : boss);`);
    let ok = false;
    for (let i = 0; i < 40; i++) {
      W().frame(1);
      ok = E(`(() => { const q = __q; if (!q.critable()) return false; const hb = q.hurtbox(); if (!hb) return false; const side = P.x < q.x ? -1 : 1;
        const fl = q.floor !== undefined ? q.floor : q.y; P.y = fl; P.vy = 0; P.ground = true; P.x = q.x + side * Math.min((q.critRange || 34) - 8, 40); P.face = -side; P.state = 'idle'; P.anim.set('idle', true);
        return critTarget() === q; })()`);
      if (ok) break;
    }
    if (!ok) { out[k] = 'not critable: ' + E('__q.state + " " + (__q.anim && __q.anim.i) + " crit=" + (critTarget() && critTarget().kind)'); continue; }
    const pre = E(`({ hp: __q.hp, bossHp: boss.hp, others: (boss.parts || []).filter(p => p !== __q).map(p => ({ x: Math.round(p.x), st: p.state, i: p.anim && p.anim.i })), bx: Math.round(boss.x), bst: boss.state, php: P.hp })`);
    E('clearBuffer(); held.clear()');
    W().tap('heavy', 1);
    const started = E('P.state') === 'fatality';
    if (!started) { out[k] = 'K did not start: ' + E('P.state'); continue; }
    let hurtTry = null, mid = null, snaps = 0, frames = 0, othersMoved = false;
    while (E('!!FAT.on') && frames < 400) {
      W().frame(1); frames++;
      if (frames === 20) {
        hurtTry = E(`(() => { const h0 = P.hp; const r = hurtPlayer(9999, P.face, 'fat_t', { parryable: true }); spikeHurt();
          projectiles.push({ owner: 'enemy', kind: 'test', x: P.x, y: P.y - 12, vx: 0, vy: 0, dmg: 500, life: 0.3, r: 8, hits: new Set(), t: 0 });
          return { r, same: P.hp === h0, st: P.state, otherDimmed: (boss.parts || []).filter(p => p !== __q).map(p => !!p._fatDim), bossHeld: !!boss._fatHold }; })()`);
      }
      const o = E(`(boss.parts || []).filter(p => p !== __q).map(p => Math.round(p.x) + ':' + p.state)`);
      if (E('!!FAT.on') && JSON.stringify(o) !== JSON.stringify(pre.others.map(p => p.x + ':' + p.st))) othersMoved = o;
      if ((frames === 30 || frames === 58 || frames === 75) && snaps < 3) { E('bannerMsg = null; toasts.length = 0; areaCard = null; render()'); await snap(`a_${k}_${snaps++}`); }
    }
    const last = E('FAT.last');
    const post = E(`({ php: P.hp, pst: P.state, bossHeld: !!boss._fatHold, qHeld: !!__q._fatHold, qOwnUpd: Object.prototype.hasOwnProperty.call(__q, 'update'), bst: boss.state, qst: __q.state, critDone: !!__q.critDone })`);
    // recovery: the boss leaves stagger and acts again
    const seen = new Set(); let recover = -1;
    for (let i = 0; i < 360; i++) { W().frame(1); E('P.hp = D.maxHp'); const s = E('__q.alive === false ? "dead" : __q.state'); seen.add(s); if (recover < 0 && s !== 'stagger') recover = i; }
    out[k] = { started, frames, dealtOverUnit: +(last.dealt / last.unit).toFixed(2), beats: last.beats.map(b => b.got), hurtTry, othersMoved, pre: { hp: pre.hp, others: pre.others }, post, recoverFrames: recover, statesAfter: [...seen].slice(0, 8), aliveAfter: E('boss && boss.alive') };
    G.SAVE.flags['boss:' + k] = 1;
  } catch (e) { out[k] = 'EXC ' + e.message + ' ' + (e.stack || '').split('\n')[1]; }
}
return out;

await boot();
G.SAVE.flags['cut:sanguine'] = 1;
G.tp('CM7', 6, 14); G.step(30, ['right']);
const B = G.boss, P = G.P, log = [];
for (let i = 0; i < 60 && !B.active; i++) G.step(5);
G.step(170);
log.push('roll frames ms: ' + JSON.stringify((() => { const s = G.P.anim.s; const t = s.tags.roll; const a = []; for (let i = t.from; i <= t.to; i++) a.push(s.frames[i].ms); return a; })()));
for (const phase of [1, 2]) {
  if (phase === 2) { B.hp = Math.floor(B.maxHp * 0.5) - 5; B.state = 'idle'; B.cool = 0.1; for (let i = 0; i < 600 && !(B.phase === 2 && B.state === 'idle'); i++) { G.step(1); if (G.state === 'cut') G.step(1, [], ['pause']); } }
  for (const strat of ['roll', 'jump']) {
    P.hp = G.D.maxHp; P.inv = 0; P.x = 330; P.y = 240; B.state = 'idle'; B.alt = 0; B.x = 500; B.reqCd = 0; B.cool = 99; window.__cm.CM.debris = []; window.__cm.CM.drops = [];
    window.__cm.force('requiem'); let hits = [], lastHp = P.hp, jh = 0;
    for (let k = 0; k < 500; k++) {
      const c = B.req && B.req.cur; let tap = [], hold = [];
      if (c && !c.reacted) {
        if (c.diag) { hold = [c.x1 > P.x ? 'left' : 'right']; if (c.t >= c.warn - 0.1) { c.reacted = true; tap = ['roll']; } }
        else if (c.t >= c.warn - (strat === 'roll' ? 0.06 : 0.12)) { c.reacted = true; tap = [strat]; if (strat === 'jump') jh = 18; }
      }
      if (jh > 0) { jh--; hold = hold.concat(['jump']); }
      G.step(1, hold, tap); B.cool = 50;
      if (P.hp < lastHp) hits.push(`${k}:${c ? (c.diag ? 'd' : 'h') + c.t.toFixed(2) : '-'}`); lastHp = P.hp;
      if (B.state !== 'requiem' && k > 40) break;
    }
    log.push({ phase, strat, hits });
  }
}
return log;

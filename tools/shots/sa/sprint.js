// TV15 Bramble Sprint: a phase-driven pilot. Pogo whenever falling onto brambles; hop the crumbling boughs low; wait out
// the thorn-log on the second crowned stump (pogo in place), then run for the goal bough.
await boot(); G.grantTechniques(); G.SAVE.items.talon = 1; G.SAVE.seenAreas = { thornveil: 1 };
const S = window.__sys, A = G.sa, log = [];
const T = 16, BR = 35;
const tile = (x, y) => A.tileAt(Math.floor(x / T), Math.floor(y / T));
function brambleBelow(p) {   // time until the pogo check point (feet+10) reaches a bramble tile top
  for (let d = 0; d <= 60; d += 2) for (const dx of [-5, 0, 5]) if (tile(p.x + dx, p.y + 10 + d) === BR) { const top = Math.floor((p.y + 10 + d) / T) * T, t = (top - p.y - 10) / Math.max(p.vy, 1); return t >= 0.03 && t <= 0.12; }
  return false;
}
const pend = () => { const o = A.KIT.objs.find(q => q.kind === 'pendulum'); return o ? o.at() : { a: 0, bx: 0 }; };
// phase: [target x (tiles, centre of the next footing), jump from x (on ground), jump hold frames]
const PH = [
  { to: 19.9, walk: true },               // off the ledge, pogo the first field, settle on the bare stump
  { to: 22.9, jx: 20.4, jh: 2 },          // hop to crumble 1 (low: thorns overhead)
  { to: 26.9, jx: 23.5, jh: 2 },          // crumble 2
  { to: 30.9, jx: 27.5, jh: 2 },          // crumble 3
  { to: 32.9, jx: 31.3, jh: 5 },          // leap to the first crowned stump (pogo)
  { to: 36.9, pogo: true },   // pogo in place on the first until the log's swing is right, then go
  { to: 40.9, pogo: true },
  { to: 47, pogo: true },                 // the goal bough
];
let ph = 0, jh = 0, waitGo = false, lastAtt = 1, prev = '', OFF = 0.0;
async function run(maxF = 6000) {
  for (let f = 0; f < maxF; f++) {
    const p = G.P, tx = p.x / T, hold = [], tap = [];
    if (!S.SYS.trial || S.SYS.result) { log.push(`EXIT f${f} trial ${!!S.SYS.trial} result ${JSON.stringify(S.SYS.result)} x${tx.toFixed(1)} y${(p.y/T).toFixed(2)}`); break; }
    if (S.SYS.trial.attempts !== lastAtt) { log.push(`RESET at ph${ph} off${OFF.toFixed(2)} prev ${prev} why ${S.SYS.trial.why}`); if (ph >= 5) OFF = (OFF + 0.08) % 1; lastAtt = S.SYS.trial.attempts; ph = 0; waitGo = false; jh = 0; }
    const P0 = PH[ph];
    // advance phases on footing
    if (p.ground && ph < 4 && Math.abs(tx - PH[ph].to) < 0.8 && ph + 1 < PH.length) ph++;
    const cur = PH[ph];
    let target = cur.to;
    if (cur.wait && !waitGo) {
      target = PH[ph - 1].to;   // keep bouncing on the previous stump
      const k = ((A.KIT.t / 2.4) % 1 + 1) % 1; if (Math.abs(k - OFF) < 0.03 && p.vy < -200) waitGo = true;
    }
    if (p.ground) {
      if (cur.jx !== undefined && tx >= cur.jx) { tap.push('jump'); jh = cur.jh; }
      hold.push('right');
    } else {
      const d = target - tx;
      if (d > 0.25) hold.push('right'); else if (d < -0.25) hold.push('left');
    }
    if (jh > 0) { hold.push('jump'); jh--; }
    if (!p.ground && p.vy > 20 && brambleBelow(p) && p.state !== 'attack_down') { hold.push('down'); tap.push('attack'); }
    // after a pogo off a crowned stump, move on to the next phase target
    if (ph >= 4 && p.vy < -200 && p.state === 'attack_down' && !cur.wait) { const next = PH[ph + 1]; if (next && Math.abs(tx - cur.to) < 1.2) ph++; }
    if (ph >= 4 && cur.wait && waitGo && p.vy < -200 && Math.abs(tx - PH[ph - 1].to) < 1.2) { ph++; }
    prev = `x${tx.toFixed(1)} y${(p.y / T).toFixed(2)} vy${p.vy.toFixed(0)} ${p.state} pend(${pend().bx.toFixed(0)},${(pend().by||0).toFixed(0)})`;
    G.step(1, hold, tap);
    if (f % 5 === 0) log.push(`${f} ph${ph} x${tx.toFixed(1)} y${(p.y / T).toFixed(2)} vy${p.vy.toFixed(0)} ${p.state}${p.ground ? ' G' : ''} att${S.SYS.trial ? S.SYS.trial.attempts : '-'} pa${pend().a.toFixed(2)}`);
  }
}
G.tp('TV15', 3, 10); G.step(10); G.step(1, [], ['interact']); G.step(3);
await run();
G.step(240); await snap('sprint_done'); log.push('OFF ' + OFF.toFixed(2) + ' RESULT ' + JSON.stringify(JSON.stringify(S.x3().trials)) + ' attempts ' + (S.SYS.trial ? S.SYS.trial.attempts : '-') + ' charm ' + G.SAVE.charms.includes('c_x3_thorn'));
// retry: the reward must not come twice
const n0 = G.SAVE.charms.length; G.tp('TV15', 3, 10); G.step(10); G.step(1, [], ['interact']); G.step(3); ph = 0; lastAtt = 1; await run(); G.step(240); log.push('second ' + JSON.stringify(S.x3().trials) + ' charms ' + n0 + '->' + G.SAVE.charms.length);
return log.filter(l => l.startsWith('RESET') || l.startsWith('OFF') || l.startsWith('EXIT') || /ph[67] /.test(l)).slice(0, 60);

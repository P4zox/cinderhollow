// DB16 Breathless Dive: swim the course on one breath with a waypoint pilot (8-way steering).
await boot(); G.grantTechniques(); G.SAVE.items.tidebreath = 1; G.SAVE.items.talon = 1; G.SAVE.seenAreas = { barrows: 1 };
const S = window.__sys, A = G.sa, log = [], T = 16;
const WP = [[5.6, 11.5], [8, 12.6], [43.4, 12.6], [43.6, 17.2], [46, 20.4], [55, 20.4], [57.2, 19.5], [57.2, 9.6]];
async function run(maxF = 1800) {
  let i = 0, lastAtt = 1, prev = '';
  for (let f = 0; f < maxF; f++) {
    const p = G.P; if (!S.SYS.trial || S.SYS.result) { log.push(`EXIT f${f} ${JSON.stringify(S.SYS.result && { t: S.SYS.result.time, first: S.SYS.result.first })}`); break; }
    if (S.SYS.trial.attempts !== lastAtt) { log.push(`RESET wp${i} prev ${prev} why ${S.SYS.trial.why}`); lastAtt = S.SYS.trial.attempts; i = 0; if (lastAtt > 3) break; }
    const tx = p.x / T, ty = p.y / T, hold = [], tap = [];
    if (i < WP.length) {
      const [wx, wy] = WP[i], dx = wx - tx, dy = wy - ty;
      if (Math.abs(dx) < 0.35 && Math.abs(dy) < 0.4) i++;
      if (dx > 0.2) hold.push('right'); else if (dx < -0.2) hold.push('left');
      if (dy > 0.2) hold.push('down'); else if (dy < -0.2) hold.push(A.DBS && A.DBS.inWater ? 'up' : 'jump');
    } else {   // surfaced in the goal chamber: leap out onto the ledge and walk to the goal
      if (A.DBS && A.DBS.inWater) { tap.push('jump'); hold.push('jump'); } else if (p.y / T < 8.2 || p.ground) hold.push('right'); else hold.push('jump');
    }
    prev = `x${tx.toFixed(1)} y${ty.toFixed(2)} ${p.state} br${A.DBS ? A.DBS.breath.toFixed(1) : '-'}`;
    G.step(1, hold, tap);
    if (f % 15 === 0) log.push(`${f} wp${i} ${prev}`);
  }
}
G.tp('DB16', 2, 9); G.step(10); G.step(1, [], ['interact']); G.step(3); log.push('trial ' + !!S.SYS.trial);
await run();
G.step(240); log.push('rec ' + JSON.stringify(S.x3().trials) + ' lung ' + G.SAVE.charms.includes('c_x3_lung'));
return log.filter(l => /EXIT|RESET|rec|trial/.test(l)).concat(log.slice(-30));

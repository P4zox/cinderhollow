await boot(); const S = window.__sys, log = [];
const R = () => S.roomObj, tile = (x, y) => R().grid[Math.floor(y / 16) * R().w + Math.floor(x / 16)];
// reactive autopilot: run right, jump at the last safe foothold, hold jump in the air
const pilot = () => {   // the course: a hop onto each pillar, the thin ledge, the goal ledge (steer to each target centre, then drop)
  for (const tx of [36.0, 41.0, 46.0, 51.5, 58.5]) {
    if (!S.SYS.trial) return;
    for (let i = 0; i < 40 && G.P.ground && G.P.x / 16 < tx - 3.3; i++) G.step(1, ['right']);
    G.step(1, ['right', 'jump'], ['jump']);
    for (let i = 0; i < 90 && S.SYS.trial; i++) { const d = tx - G.P.x / 16; G.step(1, Math.abs(d) < 0.25 ? ['jump'] : d > 0 ? ['right', 'jump'] : ['left', 'jump']); if (G.P.ground && i > 4) break; }
    G.step(4);
  }
  for (let i = 0; i < 60 && S.SYS.trial; i++) G.step(1, ['right']);
};
G.tp('T2', 32, 26); G.step(20); const hp0 = G.P.hp;
G.step(1, [], ['interact']); G.step(5); log.push('trial on: ' + !!S.SYS.trial + ' armed ' + S.SYS.trial.armed);
await snap('t01_sigil');
for (let i = 0; i < 20; i++) G.step(1, ['right']);
log.push('t=' + S.SYS.trial.t.toFixed(2) + ' armed ' + S.SYS.trial.armed);
await snap('t02_running');
for (let i = 0; i < 40 && S.SYS.trial.attempts === 1; i++) G.step(1, ['right']);
log.push('walked into spikes: attempts ' + S.SYS.trial.attempts + ' hp ' + G.P.hp + '/' + hp0 + ' why ' + S.SYS.trial.why + ' at ' + (G.P.x/16).toFixed(1));
await snap('t03_reset');
// an enemy-style blow mid-trial: straight back, no damage
G.step(20, ['right']); const r = G.P.hp; window.__game.P.inv = 0; 
log.push('first clean run...');
pilot();
log.push('done: ' + JSON.stringify(S.SYS.result && { t: +S.SYS.result.time.toFixed(2), gold: S.SYS.result.gold, first: S.SYS.result.first }) + ' x ' + (G.P.x/16).toFixed(1) + ',' + (G.P.y/16).toFixed(1));
for (let i = 0; i < 30; i++) G.step(1); await snap('t04_complete');
for (let i = 0; i < 100; i++) G.step(1); await snap('t05_after');
log.push('rec ' + JSON.stringify(S.x3().trials) + ' emberstones ' + (G.SAVE.inv.emberstone || 0) + ' cinders ' + G.SAVE.cinders);
// second run: reward must not repeat
const es = G.SAVE.inv.emberstone || 0; G.tp('T2', 32, 26); G.step(5); G.step(1, [], ['interact']); G.step(3); pilot(); for (let i = 0; i < 120; i++) G.step(1);
log.push('second clear rec ' + JSON.stringify(S.x3().trials) + ' emberstones ' + (G.SAVE.inv.emberstone || 0) + ' (was ' + es + ')');
// leaving the room aborts
G.tp('T2', 32, 26); G.step(5); G.step(1, [], ['interact']); G.step(3); G.tp('T2b', 12, 10); G.step(3); log.push('after leaving: trial ' + !!S.SYS.trial);
return log;

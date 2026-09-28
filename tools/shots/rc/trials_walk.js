// the Crucible and Gale trials run by the walk planner (real inputs, re-planning on the fly, no god mode): cleared, and how fast vs par.
// A failed run starts over from the sigil a little later (the Gale Trial's bolts fall on a beat the planner doesn't know).
await wlBoot(); const S = window.__sys, log = [];
for (const [room, sx, sy, goal, needs] of [['D16', 7, 61, [13, 4], 'talon'], ['SP16', 2, 33, [5, 4], 'talon,gale']]) {
  if (needs.includes('gale')) G.SAVE.items.gale = 1; else delete G.SAVE.items.gale;
  let k = 0;
  for (; k < 8 && !S.SYS.result; k++) {
    G.SETTINGS.god = 1; G.tp(room, sx, sy); idle(30); WL.last = G.room; G.SETTINGS.god = 0; G.P.hp = 999;
    G.step(1, [], ['interact']); idle(3 + 11 * k);   // the bolts keep the trial's clock: set off a little later each time
    if (room === 'SP16') {   // off the sigil ledge: leap east and glide into the first draught (the planner then steers the ride from mid-air)
      walkTo(4 * 16 + 8, room, 2); st1(1, true, true, false); for (let i = 0; i < 45; i++) st1(1, true, false, false);
      for (let i = 0; i < 40 && G.P.vy > -150; i++) st1(0, true, false, false);
    }
    if (room === 'SP16') {   // L1 by the planner; then the long ride is flown by hand: up U2 clear of its bolt, west over the roof of the storm
      await go([20, 20], needs, 12, true); const l1 = wlOn([18, 22, 21]); const pt = []; if (l1) {
        walkTo(22 * 16 + 8, room, 2); st1(1, true, true, false);
        for (let i = 0; i < 200 && G.P.x < 25 * 16; i++) st1(1, true, false, false);
        pt.push(`U2 in ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)}`);
        for (let i = 0; i < 400 && G.P.y > 3 * 16; i++) st1(G.P.x < 25 * 16 ? 1 : G.P.x > 26 * 16 ? -1 : 0, true, false, false);
        pt.push(`top ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state}`);
        for (let i = 0; i < 600 && G.P.x > 5 * 16 + 8 && !G.P.ground; i++) st1(-1, true, false, false);
        for (let i = 0; i < 120 && !G.P.ground; i++) st1(0, false, false, false);
        pt.push(`west ${(G.P.x/16).toFixed(1)},${(G.P.y/16).toFixed(1)} ${G.P.state} hp ${Math.round(G.P.hp)}`);
        walkTo(5 * 16 + 8, room, 3); idle(30);
      }
      log.push(`  run ${k}: L1 ${l1} ${pt.join(' | ')} trial ${!!S.SYS.trial}`);
    } else await go(goal, needs, 40, true);
    idle(60); G.P.hp = 999;
  }
  log.push(`${room}: runs ${k} result ${JSON.stringify(S.SYS.result && { t: +S.SYS.result.time.toFixed(2), gold: S.SYS.result.gold })} rec ${JSON.stringify(S.x3().trials)}`);
  await snap('trial_' + room); S.SYS.result = null;
}
return { log, fails: WL.fails.slice(-8), dev: WL.dev.slice(-8) };

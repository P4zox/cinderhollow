// Deep wing walk (talon): D6 ↓ D12 (runner-gate lever) → D11 → D10 → D9 ↑ D4, the side rooms (D15, D13, D16, D14), then back
// the whole way to D6 through the opened gate. Inputs only inside the wing.
await wlBoot();
G.SAVE.flags['dp:sluice'] = 1;   // the Sluice Stair escape (an old D6 event) is won: its grate is open
G.tp('D6', 7, 29); idle(30); wlWatch();
let ok = await walkTo2({ D6: [['S', '6:8'], 'D12'] }, 'D12');
ok = ok && await go([51, 7]); G.step(1, [], ['interact']); idle(30); WL.log.push('  lever bl: ' + JSON.stringify(G.xrc.kit().objs.filter(o => o.kind === 'lever').map(o => o.active)));
ok = ok && await walkTo2({ D12: [['S', '1:3'], 'D11'], D11: [['E', '12:15'], 'D10'], D10: [['E', '8:11'], 'D9'], D9: [async () => {   // ride the workers' lift up (stand on it; it climbs to the grate landing)
    await go([4, 31]); walkTo(10 * 16 + 8, 'D9', 3);
    for (let i = 0; i < 900 && !(G.P.ground && G.P.y <= 5 * 16 + 2); i++) st1(0, false, false, false);   // up to the top stop...
    for (let i = 0; i < 60 && G.P.x > 7 * 16; i++) st1(-1, false, false, false); idle(10);                // ...and step off before it goes back down
    WL.log.push(`  D9 lift ride: now at ${wlCell()}`); await go(['N', '5:7']); }, 'D4'] }, 'D4');
ok = ok && await walkTo2({ D4: [['S', '5:7'], 'D9'], D9: [['W', '28:31'], 'D10'], D10: [['W', '8:11'], 'D11'], D11: [['S', '3:6'], 'D15'] }, 'D15');
ok = ok && await walkTo2({ D15: [['N', '3:6'], 'D11'], D11: [['E', '12:15'], 'D10'], D10: [['S', '44:46'], 'D13'], D13: [['E', '1:4'], 'D16'] }, 'D16');
ok = ok && await walkTo2({ D16: [['W', '1:4'], 'D13'], D13: [['S', '34:36'], 'D14'] }, 'D14');
ok = ok && await walkTo2({ D14: [['N', '34:36'], 'D13'] }, 'D13');
ok = ok && await go([25, 4]) && (WL.log.push('  D13 lore rc_9 reached from the casting floor'), true);
ok = ok && await walkTo2({ D13: [['N', '28:30'], 'D10'], D10: [['W', '8:11'], 'D11'], D11: [async () => {   // ride the crane: board it from the dock, step off up the slot to the Belt Runner
    const crane = () => G.xrc.kit().objs.find(o => o.kind === 'mover' && Math.abs(o.d.y0 - 10 * 16) < 20);
    for (let n = 0; n < 6 && G.room === 'D11'; n++) {
      await go([68, 12]); if (G.room !== 'D11') break; walkTo(68 * 16 + 8, 'D11', 2);
      for (let i = 0; i < 3000 && !(crane().d.x0 > 63.8 * 16); i++) st1(0, false, false, false);   // wait for it at the dock
      st1(-1, true, true, false); for (let i = 0; i < 40 && !(G.P.ground && i > 3); i++) st1(-1, true, false, false);
      const c = crane(); if (!(G.P.ground && Math.abs(G.P.y - c.d.y0) < 4)) { WL.log.push(`  D11 crane: missed the board (P ${G.P.x.toFixed(0)},${G.P.y.toFixed(0)} g${G.P.ground} crane ${c.d.x0.toFixed(0)}-${c.d.x1.toFixed(0)},${c.d.y0.toFixed(0)})`); continue; }
      for (let i = 0; i < 900 && Math.abs((crane().d.x0 + crane().d.x1) / 2 - 38.5 * 16) > 5; i++) { const cc = crane(); st1(Math.abs(G.P.x - (cc.d.x0 + cc.d.x1) / 2) > 6 ? sgn((cc.d.x0 + cc.d.x1) / 2 - G.P.x) : 0, false, false, false); }
      WL.log.push(`  D11 crane: under the slot at ${wlCell()}`);
      st1(0, true, true, false); for (let i = 0; i < 12; i++) st1(0, true, false, false);
      await go(['N', '37:39']);
    }
  }, 'D12'], D12: [['N', '46:48'], 'D6'] }, 'D6');
await snap('walk_dp');
return { ok, log: WL.log, crossings: WL.crossings, fails: WL.fails, dev: WL.dev.slice(0, 25), at: G.room + ' ' + wlCell() };

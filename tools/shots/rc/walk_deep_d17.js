// Deep side walk (talon + Cinder Slam): D6 ↓ D12 → D11, slam through the cracked plug into the Vault (D17), climb back out, home to D6.
await wlBoot(); G.SAVE.items.slam = 1;
G.SAVE.flags['dp:sluice'] = 1;
G.tp('D6', 7, 29); idle(30); wlWatch();
let ok = await walkTo2({ D6: [['S', '6:8'], 'D12'] }, 'D12');
ok = ok && await go([51, 7]); G.step(1, [], ['interact']); idle(30);
ok = ok && await walkTo2({ D12: [['S', '1:3'], 'D11'] }, 'D11');
ok = ok && await go([71, 35]);
for (let n = 0; n < 4 && G.room === 'D11'; n++) {   // up, then ↓ + heavy: the slam cracks the plug
  walkTo(71.5 * 16, 'D11', 2); st1(0, true, true, false); for (let i = 0; i < 16; i++) st1(0, true, false, false);
  st1(0, false, false, false, ['down']); G.step(1, ['down'], ['heavy']); for (let i = 0; i < 90 && G.room === 'D11'; i++) st1(0, false, false, false, ['down']);
}
WL.log.push('  slam: now in ' + G.room);
ok = ok && G.room === 'D17' && await go([11, 11]) && (WL.log.push('  D17 chest reached'), true);
ok = ok && await walkTo2({ D17: [['N', '2:5'], 'D11'], D11: [async () => {   // ride the crane: board it from the dock, step off up the slot to the Belt Runner
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
return { ok, log: WL.log, crossings: WL.crossings, fails: WL.fails, dev: WL.dev.slice(0, 25), at: G.room + ' ' + wlCell() };

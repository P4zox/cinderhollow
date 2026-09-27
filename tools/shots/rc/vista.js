await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { spire: 1, crown: 1, lastfield: 1, deep: 1 }; const S = window.__sys, log = [];
for (const [r, x, y] of [['SP15', 11, 6], ['X11', 20, 19], ['LF1', 45, 15]]) {
  G.tp(r, x, y); G.step(240); await snap('v_' + r + '_0');
  G.step(1, [], ['interact']); for (let i = 0; i < 150; i++) G.step(1); await snap('v_' + r + '_1');
  log.push(r + ' seated ' + !!(S.SYS.vista && !S.SYS.vista.standing) + ' state ' + G.state);
  for (let i = 0; i < 4 && G.state !== 'play'; i++) { G.step(1, [], ['pause']); G.step(10); }
  G.step(1, [], ['jump']); G.step(60);
}
G.tp('LF1', 20, 16); G.step(200); for (let i = 0; i < 40; i++) G.step(1, ['right']); await snap('v_LF1_walk');
return log;

// v14 Dual Blades: in-game snapshots of the new moves mid-swing (real inputs)
// run: SHOT_HTML=web/dist/v14_dual.html sh tools/shots/wm/run.sh tools/shots/v14/dual/shots.js tools/shots/v14/dual/out
const go = async (name, rank, pre, seq, until, extra = 0) => {
  W().reset('dual', rank); arena(); W().reset('dual', rank); E('D.maxSt = 300; P.st = 300'); if (pre) E(pre); W().dummy(26);
  for (const a of seq) { if (typeof a === 'number') W().frame(a); else W().tap(a); }
  for (let i = 0; i < 120 && G.P.state !== until; i++) W().frame(1);
  W().frame(extra); E('render && render()'); await snap(name); return G.P.state + ' ' + G.P.anim.tag + ' f' + G.P.anim.i;
};
const out = {};
out.barrage = await go('tw_barrage', 1, '', ['attack', 14, 'attack', 30, 'attack'], 'tw_barrage', 12);
out.skyward = await go('tw_skyward', 1, '', ['attack', 14, 'attack', 14, 'attack', 14, 'heavy'], 'tw_skyward', 10);
out.crossfall = await go('tw_crossfall', 1, '', ['jump', 'attack', 10, 'attack'], 'tw_crossfall', 9);
out.dfin = await go('tw_dfin', 2, 'P.demon = true', ['attack', 11, 'attack', 11, 'attack', 11, 'attack', 20, 'attack', 11, 'attack', 8, 'heavy'], 'tw_dfin', 20);
out.reversal = await go('tw_reversal', 3, '', ['roll', 12, 'heavy'], 'tw_reversal', 7);
out.spiral = await go('tw_spiral', 1, '', ['heavy', 14, 'attack'], 'tw_spiral', 9);
out.pounce = await go('tw_pounce', 1, '', ['heavy', 14, 'heavy'], 'tw_pounce', 15);
out.hook = await go('tw_hook', 1, '', ['attack', 13, 'attack', 13, 'heavy'], 'tw_hook', 10);
out.bwheel = await go('tw_bwheel', 2, 'P.demon = true', ['heavy', 30, 'attack'], 'tw_bwheel', 8);
return out;

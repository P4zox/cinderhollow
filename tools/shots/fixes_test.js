await boot(); G.give({ stats: { vig: 60, mnd: 30, end: 60, str: 40, dex: 40, fth: 30, arc: 10 } }); G.grantTechniques(); G.SAVE.items.wings=1; G.SAVE.items.talon=1;
const out = {};
// 1. smash chain limit vs Morvain: spam plunges in the air
G.SAVE.flags['cut:omen']=1; delete G.SAVE.flags['boss:omen']; G.tp('K4', 6, 10);
for (let i=0;i<40 && !(G.boss&&G.boss.active);i++) G.step(5,['right']);
let starts = 0, prev = '', maxRun = 0, run = 0;
for (let i=0;i<600;i++) {
  const b = G.boss; if (b) { G.P.x = b.x - 20; }
  G.P.hp = 99999; G.P.st = 999;
  if (G.P.ground) G.step(1, [], ['jump']); else G.step(1, [], ['heavy']);
  const s = G.P.state; if (s === 'plunge' && prev !== 'plunge') { starts++; run++; maxRun = Math.max(maxRun, run); }
  if (G.P.ground && s !== 'plunge') run = 0;
  prev = s; if (G.state !== 'play') G.step(1, [], ['pause']);
}
out.plunge = { starts, maxInAirChain: maxRun };
// 2. Oswin stays in his arena
G.SAVE.flags['sc:seal']=1; G.SAVE.flags['cut:oswin']=1; delete G.SAVE.flags['boss:oswin'];
G.tp('H1', 20, 10); for (let i=0;i<60 && !(G.boss&&G.boss.active);i++) G.step(5,['left']);
let minX = 1e9, maxX = -1e9;
for (let i=0;i<900;i++) { const b=G.boss; if(!b||!b.alive) break; const d = b.x < G.P.x ? 'left':'right'; G.step(2, Math.abs(b.x-G.P.x)>30?[d]:[], i%20==0?['attack']:[]); G.P.hp=99999; minX=Math.min(minX,b.x); maxX=Math.max(maxX,b.x); if(G.state!=='play')G.step(1,[],['pause']); }
out.oswin = { minCol: +(minX/16).toFixed(1), maxCol: +(maxX/16).toFixed(1), fogCol: 27 };
// 3. gates: try to get past the closed K2 gate (col 44) from the west with wall-jumps + double jumps
for (const [r, gx, sx] of [['K2', 44, 40], ['X1', 12, 6]]) {
  G.tp(r, sx, 10); let best = 0;
  for (let i=0;i<400;i++) { const t = i % 24; G.step(2, ['right'], t===0||t===8||t===14 ? ['jump'] : []); G.P.hp=99999; best = Math.max(best, G.P.x/16); if (G.room !== r) break; }
  out['gate_'+r] = { gateCol: gx, furthestCol: +best.toFixed(1), room: G.room };
}
return out;

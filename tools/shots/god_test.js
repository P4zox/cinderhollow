await boot(); const o=[];
G.step(1,[],['pause']); G.step(1,[],['spell']);   // Settings tab
for (let i=0;i<4;i++){ G.step(1,[],['down']); } G.step(1,[],['confirm']); G.step(1,[],['down']); G.step(1,[],['confirm']);
await snap('settings'); G.step(1,[],['pause']);
G.SAVE.flags['cut:omen']=1; delete G.SAVE.flags['boss:omen']; G.tp('K4',6,10);
let minHp=1e9, minSt=1e9;
for (let i=0;i<400;i++){ const b=G.boss; const d=b && b.x<G.P.x?'left':'right'; G.step(3, b && Math.abs(b.x-G.P.x)>40?[d]:[], i%3?['roll']:['attack']); if(G.state==='cut') G.step(1,[],['pause']); minHp=Math.min(minHp,G.P.hp); minSt=Math.min(minSt,G.P.st); }
return {state:G.state, minHp:Math.round(minHp), maxHp:G.D.maxHp, minSt:Math.round(minSt), maxSt:G.D.maxSt, dead: G.P.state};

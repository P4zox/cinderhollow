await boot(); G.SAVE.flags['sc:seal']=1; G.SAVE.flags['cut:oswin']=1; delete G.SAVE.flags['boss:oswin'];
G.tp('H1', 20, 10); for (let i=0;i<60 && !(G.boss&&G.boss.active);i++) G.step(5,['left']);
const b = G.boss; let maxX = -1e9, minX = 1e9, minY = 1e9;
for (const px of [26.2, 25, 1.5, 2.5]) for (let k=0;k<6;k++) {
  G.P.x = px*16; G.step(2); b.state='idle'; b.cool=99; b.x = px < 10 ? 8*16 : 20*16; b.start(k%2 ? 'dash' : 'vault');
  for (let i=0;i<90;i++){ G.step(1); G.P.hp=99999; G.P.x = px*16; maxX=Math.max(maxX,b.x); minX=Math.min(minX,b.x); minY=Math.min(minY,b.y); if(G.state!=='play')G.step(1,[],['pause']); }
}
return { minCol: +(minX/16).toFixed(2), maxCol: +(maxX/16).toFixed(2), arena: [+(b.L/16).toFixed(2), +(b.R/16).toFixed(2)], floorY: b.floor, highestY: Math.round(minY) };

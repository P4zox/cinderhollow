await boot(); G.grantTechniques(); G.SAVE.flags['boss:cindervane']=1; G.tp('SP7',48,15); G.step(20);
const a=[G.room, Math.round(G.P.x), Math.round(G.P.y), G.P.ground];
G.step(2,['down'],['jump']); for (let i=0;i<30;i++){ G.step(3); if (i==10) G.step(2,['down'],['jump']); }
a.push(G.room, Math.round(G.P.x), Math.round(G.P.y));
return a;

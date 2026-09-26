await boot(); G.grantTechniques(); const o=[];
G.SAVE.flags['cut:pharaoh']=1; G.SAVE.flags['cutp2:pharaoh']=1;
G.tp('DU8', 30, 14); G.step(5); const b=G.boss; b.activate(); G.step(160);
async function force(m, frames, n) { G.P.x = b.x + 90; b.facePlayer(); b.setS('idle','idle'); b.cool=9; b.start(m); for (let i=0;i<frames;i++){ G.P.hp=G.D.maxHp; G.step(1); if (n.includes(i)) await snap(m+'_'+b.phase+'_'+i);} }
await force('beam', 150, [70, 95, 115]);
await force('coffin', 120, [80, 100]);
b.hp = b.maxHp*0.45; G.step(80); for (let i=0;i<30 && G.state==='cut';i++) G.step(20); G.step(120);
await force('eyes', 150, [60, 100]);
await force('sink', 150, [70, 110]);
await force('strike', 200, [40, 100, 140]);
o.push(b.state, b.phase);
return o;

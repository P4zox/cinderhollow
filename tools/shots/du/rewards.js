await boot(); const o=[];
G.SAVE.flags['cut:pharaoh']=1; G.SAVE.flags['cut:scarab']=1;
for (const [r,x] of [['DU8',30],['DU6',20]]) { G.tp(r, x, 14); G.step(5); const b=G.boss; b.activate(); G.step(10); b.hp=3; b.hit({dmg:50,poise:0,dir:1,kind:'light',x:b.x,y:b.y-30});
  for (let i=0;i<40;i++){ await new Promise(r=>setTimeout(r,250)); G.step(15); } }
o.push(JSON.stringify(Object.keys(G.SAVE.weapons)), JSON.stringify(G.SAVE.spellsOwned), JSON.stringify(G.SAVE.charms), JSON.stringify(G.SAVE.inv));
return o;

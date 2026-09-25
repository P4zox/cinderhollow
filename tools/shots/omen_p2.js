await boot(); G.SAVE.flags['cut:omen']=1; G.SAVE.flags['cutp2:omen']=1; delete G.SAVE.flags['boss:omen'];
G.tp('K4',6,10); for(let i=0;i<30 && !(G.boss&&G.boss.active);i++) G.step(5,['right']);
const b=G.boss; for(let i=0;i<40;i++){G.step(5); G.P.hp=99999;}
b.hp=Math.floor(b.maxHp*0.49); b.hit({dmg:5,poise:0,dir:1,kind:'light',x:b.x,y:b.y-40,melee:true});
for(let k=0;k<6;k++){ for(let i=0;i<30;i++){G.step(3); G.P.hp=99999; G.P.inv=1; if(G.state==='cut')G.step(1,[],['pause']);} await snap('om'+k); }
return [b.phase, b.state];

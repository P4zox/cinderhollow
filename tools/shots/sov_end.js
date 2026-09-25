await boot(); G.give({ stats: { vig: 60, mnd: 30, end: 40, str: 40, dex: 40, fth: 30, arc: 10 } });
G.SAVE.flags['cut:sovereign']=1; delete G.SAVE.flags['boss:sovereign'];
G.tp('X5',6,10); const b=G.boss; for(let i=0;i<150 && !b.active;i++){ G.step(4,['right']); G.P.hp=99999; }
const log=[];
for (let n=0;n<400 && G.boss && G.boss.alive;n++){
  for (const t of (G.boss.parts||[G.boss])) if (t.alive!==false && t.hit) t.hit({dmg:400,poise:0,dir:1,kind:'light',x:t.x,y:t.y-20,melee:true});
  G.step(30); G.P.hp=99999; G.P.inv=1;
  if (G.state==='cut'||G.state==='cine'||G.state==='dialog') { log.push('st:'+G.state+'@'+n+' ph'+(G.boss&&G.boss.phase)); G.step(1,[],['pause']); }
}
for (let i=0;i<120;i++){ G.step(10); G.P.hp=99999; if (i%20==0) log.push(G.state); if (G.state==='dialog') G.step(1,[],['confirm']); }
return { alive: G.boss && G.boss.alive, flag: !!G.SAVE.flags['boss:sovereign'], state: G.state, log: log.slice(0,20) };

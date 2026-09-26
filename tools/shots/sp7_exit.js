await boot(); G.grantTechniques(); const out=[];
async function tryExit(label) {
  const log=[];
  for (let i=0;i<120 && G.room==='SP7';i++){ 
    const x=G.P.x; 
    if (x < 44*16) G.step(4,['right'], i%6==0?['jump']:[]); else { G.step(2,['down'],['jump']); G.step(4,['right']); }
    G.P.hp=99999; if (G.state!=='play') G.step(1,[],['pause']);
    if (i%10==0) log.push(Math.round(G.P.x)+','+Math.round(G.P.y));
  }
  out.push(label+': room '+G.room+' pos '+Math.round(G.P.x)+','+Math.round(G.P.y)+' | '+log.join(' '));
}
// A: boss already dead on entry
G.SAVE.flags['boss:cindervane']=1; G.tp('SP7',20,15); G.step(30); await tryExit('deadOnEntry');
// B: fight then kill in-session
delete G.SAVE.flags['boss:cindervane']; G.SAVE.flags['cut:cindervane']=1; G.SAVE.flags['cutp2:cindervane']=1;
G.tp('SP7',46,15); for(let i=0;i<120 && !(G.boss&&G.boss.active);i++){ G.step(4,['left']); G.P.hp=99999; if(G.state==='cut')G.step(1,[],['pause']); }
const b=G.boss; out.push('boss active '+(b&&b.active)+' px '+Math.round(G.P.x));
for (let n=0;n<200 && b && b.alive;n++){ for (const t of (b.parts||[b])) if (t.hit) t.hit({dmg:400,poise:0,dir:1,kind:'light',x:t.x,y:t.y-20,melee:true}); G.step(30); G.P.hp=99999; G.P.inv=1; if(G.state!=='play')G.step(1,[],['pause']); }
out.push('boss alive '+(b&&b.alive)+' flag '+!!G.SAVE.flags['boss:cindervane']);
for (let i=0;i<60;i++){ G.step(10); G.P.hp=99999; if(G.state!=='play')G.step(1,[],['pause']); }
await snap('sp7_after'); await tryExit('afterKill');
return out;

await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.wings=1; G.SAVE.items.talon=1;
const acts=['left','right','jump','attack','heavy','roll','parry','spell','art','hook','down','up','interact'];
const errs=[]; window.addEventListener('error', e=>errs.push(String(e.message))); const out=[];
for (let f = 0; f < 5; f++) for (let x = 4; x < 96; x += 12) {
  try { G.tp('T1', x, f * 20 + 16); for (let i=0;i<60;i++){ const h=[acts[Math.floor(Math.random()*4)]]; const t=Math.random()<0.4?[acts[Math.floor(Math.random()*acts.length)]]:[]; G.step(5,h,t); if(G.state!=='play') G.step(1,[],['pause']); if(G.state==='dead'){G.step(200);} G.P.hp=Math.max(G.P.hp,50);} }
  catch(e){ out.push(f+','+x+': '+e.message+' '+(e.stack||'').split('\n')[1]); }
}
G.kitReset('T1', {all:true}); G.step(30);
return {exc: out, errs: errs.slice(0,10), state: G.state, room: G.room};

await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1; G.giveArmory && G.giveArmory();
const spots = [["SF16", 5, 10], ["SF10", 12, 12], ["SF10", 45, 11], ["SF13", 4, 21], ["SF13", 50, 6], ["SF11", 6, 14], ["SF11", 58, 20], ["SF11", 100, 26], ["SF11", 41, 3], ["SF14", 20, 28], ["SF14", 5, 7], ["SF12", 43, 7], ["SF12", 20, 17], ["SF15", 30, 21], ["SF17", 8, 11], ["SF18", 36, 44], ["SF18", 28, 3], ["SF19", 3, 7], ["NH9", 4, 12], ["NH9", 30, 12], ["NH10", 6, 10], ["NH10", 40, 10], ["NH8", 6, 60], ["NH8", 40, 42], ["NH8", 38, 3], ["NH8", 20, 24], ["NH17", 4, 9], ["NH14", 18, 14], ["NH13", 34, 16], ["NH13", 5, 16], ["NH11", 3, 14], ["NH11", 80, 14], ["NH16", 4, 20], ["NH16", 60, 5], ["NH12", 11, 38], ["NH12", 5, 24], ["NH15", 8, 12], ["E4", 4, 10], ["E4", 30, 10], ["E5", 10, 27], ["E5", 60, 27], ["E5", 85, 3], ["E5", 104, 27], ["E6", 10, 10], ["E7", 58, 37], ["E7", 20, 37], ["H2", 44, 10], ["H2", 5, 10], ["H3", 21, 10], ["H4", 8, 10], ["H1", 20, 10]]; const acts=['left','right','jump','attack','heavy','roll','parry','spell','art','hook','down','up'];
const errs=[]; window.addEventListener('error', e=>errs.push(String(e.message)));
const out=[];
for (const [r,x,y] of spots) {
  try { G.tp(r,x,y); for (let i=0;i<120;i++){ const h=[acts[Math.floor(Math.random()*4)]]; const t=Math.random()<0.4?[acts[Math.floor(Math.random()*acts.length)]]:[]; G.step(5,h,t); if(G.state==='cut'||G.state==='dialog'||G.state==='menu'||G.state==='cine') G.step(1,[],['pause']); if(G.state==='dead'){G.step(200);} G.P.hp=Math.max(G.P.hp,50);} }
  catch(e){ out.push(r+': '+e.message+' '+(e.stack||'').split('\n')[1]); }
}
return {exc: out, errs: errs.slice(0,10)};

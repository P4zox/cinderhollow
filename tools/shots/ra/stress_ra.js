await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1; G.giveArmory && G.giveArmory();
const spots = [["R5", 121, 8], ["R6", 20, 10], ["R7", 15, 10], ["R8", 30, 6], ["R9", 5, 25], ["R10", 3, 7], ["R11", 15, 5], ["R12", 10, 16], ["R13", 20, 10], ["R14", 8, 6], ["C7", 20, 12], ["C8", 40, 28], ["C9", 4, 7], ["C10", 10, 10], ["C11", 19, 27], ["C12", 20, 13], ["C13", 31, 10], ["C14", 8, 9], ["C15", 8, 9], ["W2", 2, 12], ["K5", 6, 10], ["K6", 15, 24], ["K7", 40, 26], ["K8", 20, 10], ["K9", 5, 10], ["K10", 15, 14], ["K11", 13, 16], ["K12", 4, 38], ["K13", 8, 10]]; const acts=['left','right','jump','attack','heavy','roll','parry','spell','art','hook','down','up'];
const errs=[]; window.addEventListener('error', e=>errs.push(String(e.message)));
const out=[];
for (const [r,x,y] of spots) {
  try { G.tp(r,x,y); for (let i=0;i<120;i++){ const h=[acts[Math.floor(Math.random()*4)]]; const t=Math.random()<0.4?[acts[Math.floor(Math.random()*acts.length)]]:[]; G.step(5,h,t); if(G.state==='cut'||G.state==='dialog'||G.state==='menu'||G.state==='cine') G.step(1,[],['pause']); if(G.state==='dead'){G.step(200);} G.P.hp=Math.max(G.P.hp,50);} }
  catch(e){ out.push(r+': '+e.message+' '+(e.stack||'').split('\n')[1]); }
}
return {exc: out, errs: errs.slice(0,10)};

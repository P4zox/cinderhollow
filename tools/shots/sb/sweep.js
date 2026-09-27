await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1; G.SAVE.items.talon=1; G.giveArmory && G.giveArmory();
const spots = [['NV8',40,10],['NV13',20,12],['NV9',10,11],['NV10',30,55],['NV10',20,22],['NV10',14,7],['NV14',20,10],['NV11',50,13],['NV12',16,13],['NV15',48,12],['NV16',8,12],
 ['DU9',50,11],['DU10',10,21],['DU10',62,17],['DU15',20,12],['DU17',8,11],['DU11',30,11],['DU14',16,16],['DU12',10,11],['DU13',20,17],['DU16',6,3],['DU18',8,11]];
const acts=['left','right','jump','attack','heavy','roll','parry','spell','art','hook','down','up'];
const errs=[]; window.addEventListener('error', e=>errs.push(String(e.message)));
const out=[]; const t0 = performance.now();
for (const [r,x,y] of spots) {
  try { G.tp(r,x,y); for (let i=0;i<150;i++){ const h=[acts[Math.floor(Math.random()*4)]]; const t=Math.random()<0.4?[acts[Math.floor(Math.random()*acts.length)]]:[]; G.step(5,h,t); if(G.state==='cut'||G.state==='dialog'||G.state==='menu'||G.state==='cine') G.step(1,[],['pause']); if(G.state==='dead'){G.step(200);} G.P.hp=Math.max(G.P.hp,50);} }
  catch(e){ out.push(r+': '+e.message+' '+(e.stack||'').split('\n')[1]); }
}
return {exc: out, errs: errs.slice(0,10), ms: Math.round(performance.now() - t0)};

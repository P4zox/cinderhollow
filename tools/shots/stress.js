await boot(); G.grantTechniques(); G.giveArmory && G.giveArmory();
const spots = [["R1", 24, 10], ["R2", 24, 6], ["R3", 12, 12], ["R4", 20, 10], ["C1", 8, 24], ["C2", 24, 10], ["C2s", 6, 10], ["C3", 32, 10], ["C4", 16, 10], ["C5", 18, 10], ["C6", 12, 38], ["K1", 24, 10], ["K2", 24, 10], ["K3", 12, 24], ["K3s", 8, 8], ["K4", 24, 10], ["M1", 12, 24], ["M2", 3, 10], ["M3", 12, 10], ["M6", 12, 10], ["M4", 24, 8], ["M5", 18, 10], ["X1", 12, 10], ["X2", 12, 26], ["X3", 24, 10], ["X4", 12, 10], ["X5", 24, 10], ["A1", 12, 26], ["A2", 24, 10], ["A3", 12, 10], ["A4", 12, 24], ["A5", 24, 10], ["A6", 18, 14], ["T0", 24, 16], ["A7", 8, 12], ["HF1", 3, 10], ["HF2", 16, 7], ["HF3", 9, 32], ["HF4", 18, 10], ["HF5", 16, 16], ["HF6", 24, 10], ["HF7", 19, 13], ["SP1", 10, 28], ["SP2", 30, 10], ["SP3", 12, 19], ["SP4", 24, 9], ["SP5", 18, 10], ["SP6", 8, 35], ["SP7", 26, 15], ["D1", 12, 10], ["D2", 6, 10], ["D3", 32, 10], ["D4", 8, 30], ["D5", 24, 10], ["D6", 12, 30], ["D7", 12, 14], ["D8", 26, 14], ["H1", 20, 10], ["E1", 12, 22], ["E2", 41, 10], ["E3", 24, 10]]; const acts=['left','right','jump','attack','heavy','roll','parry','spell','art','hook','down','up'];
const errs=[]; window.addEventListener('error', e=>errs.push(String(e.message)));
const out=[];
for (const [r,x,y] of spots) {
  try { G.tp(r,x,y); for (let i=0;i<120;i++){ const h=[acts[Math.floor(Math.random()*4)]]; const t=Math.random()<0.4?[acts[Math.floor(Math.random()*acts.length)]]:[]; G.step(5,h,t); if(G.state==='cut'||G.state==='dialog'||G.state==='menu'||G.state==='cine') G.step(1,[],['pause']); if(G.state==='dead'){G.step(200);} G.P.hp=Math.max(G.P.hp,50);} }
  catch(e){ out.push(r+': '+e.message+' '+(e.stack||'').split('\n')[1]); }
}
return {exc: out, errs: errs.slice(0,10)};

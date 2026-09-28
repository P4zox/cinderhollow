await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1; G.giveArmory && G.giveArmory();
const spots = [["M7", 72, 6], ["M7", 36, 16], ["M7", 10, 20], ["M8", 20, 8], ["M13", 12, 10], ["M10", 40, 8], ["M10", 14, 10], ["M14", 13, 8], ["M11", 6, 5], ["M11", 30, 5], ["M9", 10, 10], ["M9", 30, 10], ["M12", 5, 5], ["M12", 20, 22], ["A10", 5, 46], ["A10", 18, 10], ["A8", 21, 44], ["A8", 8, 30], ["A8", 56, 32], ["A8", 30, 6], ["A9", 20, 10], ["A13", 19, 14], ["A12", 17, 11], ["A11", 4, 10], ["A11", 40, 9], ["A14", 10, 9], ["A16", 2, 8], ["A15", 3, 28], ["HF10", 5, 9], ["HF10", 40, 9], ["HF8", 10, 52], ["HF8", 24, 30], ["HF8", 38, 4], ["HF11", 72, 11], ["HF11", 30, 11], ["HF14", 14, 14], ["HF15", 28, 18], ["HF15", 40, 5], ["HF12", 19, 14], ["HF12", 36, 10], ["HF9", 10, 12], ["HF9", 35, 12], ["HF13", 13, 6], ["HF13", 20, 20], ["M2", 40, 10], ["M4", 3, 10], ["A5", 8, 10], ["A2", 25, 10], ["HF6", 37, 9], ["HF2", 4, 14], ["HF16", 3, 6], ["W3", 8, 23], ["W3", 3, 43], ["W5", 3, 30], ["M1", 16, 3], ["A5", 30, 6], ["A4", 4, 24], ["HF6", 8, 12]]; const acts=['left','right','jump','attack','heavy','roll','parry','spell','art','hook','down','up'];
const errs=[]; window.addEventListener('error', e=>errs.push(String(e.message)));
const out=[];
for (const [r,x,y] of spots) {
  try { G.tp(r,x,y); for (let i=0;i<120;i++){ const h=[acts[Math.floor(Math.random()*4)]]; const t=Math.random()<0.4?[acts[Math.floor(Math.random()*acts.length)]]:[]; G.step(5,h,t); if(G.state==='cut'||G.state==='dialog'||G.state==='menu'||G.state==='cine') G.step(1,[],['pause']); if(G.state==='dead'){G.step(200);} G.P.hp=Math.max(G.P.hp,50);} }
  catch(e){ out.push(r+': '+e.message+' '+(e.stack||'').split('\n')[1]); }
}
return {exc: out, errs: errs.slice(0,10)};

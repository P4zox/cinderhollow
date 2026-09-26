await boot(); G.SAVE.flags['cut:saint0']=1; delete G.SAVE.flags['boss:saint0'];
G.tp('NH7',8,10); let b=G.boss; for(let i=0;i<200 && !(b&&b.active);i++){ G.step(4,['right']); G.P.hp=99999; if(G.state==='cut')G.step(1,[],['pause']); b=G.boss; }
const out={active:b&&b.active, state:b&&b.state}; let hits=0, atks={};
for(let i=0;i<900;i++){ const d=b.x<G.P.x?'left':'right'; const prev=G.P.hp; G.step(2, Math.abs(b.x-G.P.x)>50?[d]:[]); if(G.P.hp<prev) hits++; G.P.hp=99999; G.P.inv=0; if(G.state==='cut')G.step(1,[],['pause']); atks[b.state+':'+(b.atk||b.move||'')]=(atks[b.state+':'+(b.atk||b.move||'')]||0)+1; }
out.hits=hits; out.atks=JSON.stringify(atks).slice(0,300); out.bx=Math.round(b.x); out.px=Math.round(G.P.x); return out;

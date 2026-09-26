await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1; G.SAVE.flags['sc:seal']=1;
const cases=[['DU6','scarab',36,11],['DU8','pharaoh',20,14],['NH7','saint0',8,10]];
const out=[];
for (const [r,k,x,y] of cases) {
  try {
    delete G.SAVE.flags['boss:'+k]; for (const f of ['cut:','cutp2:','cutp3:']) G.SAVE.flags[f+k]=1;
    G.tp(r,x,y); let b=G.boss; if(!b){out.push(k+': NO BOSS');continue;}
    for(let i=0;i<200 && !b.active;i++){ G.step(4,[b.x<G.P.x?'left':'right']); G.P.hp=99999; G.P.inv=5; if(G.state!=='play')G.step(1,[],['pause']); }
    const seen=new Set(); let hurt=0;
    for(let i=0;i<500;i++){ const prev=G.P.hp; G.step(2, Math.abs(b.x-G.P.x)>60?[b.x<G.P.x?'left':'right']:[]); if(G.P.hp<prev)hurt++; G.P.hp=99999; G.P.inv=0; if(G.state!=='play')G.step(1,[],['pause']); seen.add(b.state); }
    const ok = [...seen].some(s=>!['dormant','intro','idle','sleep','wait'].includes(s));
    out.push((ok?'OK  ':'BAD ')+k+' active='+b.active+' hurt='+hurt+' states='+[...seen].join(','));
  } catch(e){ out.push('EXC '+k+' '+e.message); }
}
return out;

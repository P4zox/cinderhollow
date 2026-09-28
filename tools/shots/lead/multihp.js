await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1; G.SETTINGS.god = 1;
const cases=[['HF7','twins',4,13],['X3','sentinels',3,8],['TV4','coven',31,10],['NV5','executioners',30,10],['DU6','scarab',6,12],['DU8','pharaoh',8,14]];
const out=[];
for (const [r,k,x,y] of cases) {
  try {
    delete G.SAVE.flags['boss:'+k]; for (const f of ['cut:','cutp2:','cutp3:']) G.SAVE.flags[f+k]=1;
    G.tp(r,x,y); const b=G.boss; if(!b){out.push(k+': no boss'); continue;}
    for(let i=0;i<200 && !b.active;i++){ G.step(4,[b.x<G.P.x?'left':'right']); if(G.state!=='play')G.step(1,[],['pause']); }
    const parts = b.parts ? b.parts.map(q => Math.round(q.maxHp)).join('+') : '';
    out.push(`${k}: total ${Math.round(b.maxHp)} ${parts ? '(parts ' + parts + ')' : ''} active ${b.active}`);
  } catch(e){ out.push('EXC '+k+' '+e.message); }
}
return out;

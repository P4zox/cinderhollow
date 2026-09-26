await boot(); G.grantTechniques(); G.SAVE.items.tidebreath=1; G.SAVE.items.moonstep=1; G.SAVE.flags['sc:seal']=1;
const cases=[['C5','hound',6,10],['K4','omen',6,10],['M5','kalden',6,10],['M6','vessel',6,10],['X5','sovereign',6,10],['A3','librarian',20,10],['A6','unwritten',3,14],['HF4','ice_warden',31,10],['HF7','twins',4,13],['SP5','bellringer',3,10],['SP7','cindervane',46,15],['D5','overseer',40,10],['D8','colossus',46,14],['H1','oswin',30,10],['X3','sentinels',3,8],['E3','first_ember',10,10],['TV4','coven',31,10],['TV8','warden',5,10],['DB5','ferryman',8,7],['DB6','choir',3,15],['CM6','butler',3,9],['CM7','sanguine',6,14],['NV5','executioners',30,10],['NV7','vael',40,12],['SF5','orrery',5,12],['SF7','astrel',5,16],['NH5','enforcer',6,12],['NH7','saint0',8,10]];
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

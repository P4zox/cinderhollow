await boot(); G.SAVE.flags['cut:omen']=1; delete G.SAVE.flags['boss:omen'];
G.tp('K4', 6, 10); for (let i=0;i<5;i++) G.step(5,['right']);
const o=[]; for(let i=0;i<34;i++){G.P.inv=9; G.step(5); G.P.hp=99999; if(G.room!=='K4'){o.push('left at '+i+' '+G.room+' '+G.state); break;}}
const b=G.boss; if(!b) return 'noboss '+G.room+' '+o;
for (const side of [-1, 1]) {
  G.P.x = b.x + side*70; G.P.hp=99999; b.state='idle'; b.cool=99; G.step(2);
  b.start('combo'); for (let i=0;i<14;i++){ G.step(4); G.P.hp=99999; G.P.inv=5; if ([3,7,11].includes(b.anim.i)) await snap('omen_side'+side+'_f'+b.anim.i); }
}
return o;

await boot(); const o=[];
G.SAVE.flags['cut:pharaoh']=1; G.SAVE.flags['cut:scarab']=1;
async function run(room, x, moves) {
  G.tp(room, x, room === 'DU6' ? 11 : 14); G.step(5); const b=G.boss; b.activate(); G.step(200);
  for (const m of moves) { let hitsNo=0, hitsRoll=0;
    for (const roll of [false, true]) for (let rep=0; rep<3; rep++) {
      G.P.x = b.x + b.face * 34; G.P.y = b.floor; G.P.inv = 0; G.P.hp = G.D.maxHp; b.facePlayer(); b.setS('idle','idle'); b.cool=9; b.start(m); const h0 = G.P.hp; let hit=false;
      for (let i=0;i<150 && b.state==='attack';i++) { if (G.P.hp < h0) hit=true; G.P.hp = Math.max(G.P.hp, 60); const w = b.sh.meta.attacks[m]; const wins = w.windows || [w];
        const soon = wins.some(W => b.anim.i === W.active[0]-1); G.step(1, [], roll && soon && G.P.state!=='roll' ? ['roll'] : []); }
      if (hit || G.P.hp < h0) { if (roll) hitsRoll++; else hitsNo++; }
    }
    o.push(`${b.kind} ${m}: standing hit ${hitsNo}/3, rolling hit ${hitsRoll}/3`); }
}
await run('DU8', 30, ['combo']);
await run('DU6', 20, ['thrust', 'sweep']);
return o;

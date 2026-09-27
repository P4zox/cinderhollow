await boot(); G.giveArmory(); G.grantTechniques();
const ids = (typeof ONLY !== 'undefined' && ONLY) || ['longsword', ...Object.keys(G.SAVE.weapons)];
const out = {};
for (const id of ids) {
  G.SAVE.weapon = id; G.SAVE.weapons[id] = 5; G.give({});
  delete G.SAVE.flags['boss:hound']; for (const f of ['cut:','cutp2:','cutp3:']) G.SAVE.flags[f+'hound']=1;
  G.tp('C5', 6, 10); const b = G.boss;
  for (let i=0;i<200 && !b.active;i++){ G.step(4,['right']); G.P.hp=99999; if(G.state!=='play')G.step(1,[],['pause']); }
  const bx = b.x, by = b.y; b.update = function(){ this.x = bx; this.y = by; };
  b.state = 'idle'; let nh = 0; const oh = b.hit.bind(b); b.hit = i => { nh++; return oh(i); };
  const res = {};
  for (const mode of ['attack','heavy']) {
    let dealt = 0; b.hp = b.maxHp;
    G.P.x = bx - 34; G.P.face = 1; G.P.fp = 999; G.P.st = 999;
    for (let f = 0; f < 60*12; f += 3) {
      const h0 = b.hp;
      G.step(3, [], (f % 18 === 0) ? [mode] : []);
      if (b.hp < h0) dealt += h0 - b.hp;
      if (b.hp < b.maxHp*0.3) b.hp = b.maxHp;
      G.P.hp = 99999; G.P.st = 999; if (G.P.ground && Math.abs(G.P.x-(bx-34))>4 && ['idle','run'].includes(G.P.state)) G.P.x = bx-34; G.P.face = 1;
      if (G.state!=='play') G.step(1,[],['pause']);
    }
    res[mode] = Math.round(dealt/12) + '(' + nh + 'h)'; nh = 0;
  }
  const W = G.D.W || {}; out[id] = `L ${res.attack}/s  H ${res.heavy}/s  light=${Math.round(G.D.light)} heavy=${Math.round(G.D.heavy)}`;
}
return out;

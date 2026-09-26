await boot(); const o=[];
for (const [lab, items] of [['talon', {talon:1}], ['talon+wings', {talon:1, wings:1}], ['wings', {wings:1}]]) {
  G.SAVE.items.talon = items.talon||0; G.SAVE.items.wings = items.wings||0;
  G.tp('D1', 10, 1); G.step(10); let ok=false, best=1e9;
  let dir = 'right';
  for (let i=0;i<400 && !ok;i++) {
    // wall-jump climb: hold toward a wall, jump when sliding; flip direction after each kick
    const onWall = G.P.state === 'wall';
    if (onWall) { G.step(1, [dir], ['jump']); dir = dir === 'right' ? 'left' : 'right'; G.step(8, [dir]); }
    else if (G.P.ground) { G.step(1, [dir], ['jump']); G.step(6, [dir]); G.step(1, [dir], ['jump']); }
    else G.step(2, [dir]);
    if (G.room === 'M4') { best = Math.min(best, G.P.y); if (G.P.ground && G.P.y <= 11*16) ok = true; }
    if (G.room === 'M4' && G.P.y < 11*16 && !G.P.ground) { G.step(10, [G.P.x < 42*16 ? 'left' : 'right']); if (G.P.ground && G.P.y <= 11*16) ok = true; }
  }
  o.push(lab+': '+ok+' '+G.room+' '+Math.round(G.P.x/16)+','+Math.round(G.P.y/16)+' state '+G.P.state);
}
return o;

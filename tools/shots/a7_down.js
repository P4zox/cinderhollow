await boot(); G.SAVE.flags['boss:unwritten']=1; const o=[];
// come down from the secret room: drop through A7's thin floor into the shaft, land on the top ink step
G.tp('A7', 6, 12); G.step(20); G.step(2,['down'],['jump']); for (let i=0;i<40;i++) G.step(2);
o.push('landed: '+G.room+' '+(G.P.x/16).toFixed(1)+','+(G.P.y/16).toFixed(1)+' ground '+G.P.ground);
// try to walk off both ways (the old bug: stuck)
const x0 = G.P.x; G.step(30,['left']); const xl = G.P.x; G.step(30,['right']); o.push('walk moved: '+Math.round(Math.abs(xl-x0))+' '+Math.round(Math.abs(G.P.x-xl))+' y '+(G.P.y/16).toFixed(1));
// drop through
G.step(2,['down'],['jump']); for (let i=0;i<40;i++) G.step(2);
o.push('after drop: '+G.room+' '+(G.P.x/16).toFixed(1)+','+(G.P.y/16).toFixed(1)+' ground '+G.P.ground);
// and the stair still works going up: stand on the 3rd step and climb
return o;

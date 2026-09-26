await boot(); const o=[]; G.SAVE.items.talon=0; G.SAVE.items.wings=0;
// down: walk left off the Sunken Road ledge
G.tp('M4', 45, 10); G.step(10); for (let i=0;i<60 && G.room==='M4';i++) G.step(3,['left']); o.push('down -> '+G.room);
// up with no abilities: from the D1 platform under the opening, jump to the ledge (col 43), then onto the road
G.tp('D1', 10, 1); G.step(10);
G.step(1,[],['jump']); for (let i=0;i<14;i++) G.step(1,['jump']); for (let i=0;i<20;i++) G.step(1,['jump','right']); G.step(15);
o.push('after jump 1: '+G.room+' '+(G.P.x/16).toFixed(1)+','+(G.P.y/16).toFixed(1)+' ground '+G.P.ground);
G.step(1,[],['jump']); for (let i=0;i<10;i++) G.step(1,['jump']); for (let i=0;i<25;i++) G.step(1,['jump','right']); G.step(15);
o.push('after jump 2: '+G.room+' '+(G.P.x/16).toFixed(1)+','+(G.P.y/16).toFixed(1)+' ground '+G.P.ground);
return o;

await new Promise(r=>setTimeout(r,300));
return G.trn.bosses().map(b => `${b.kind} ${b.room} wall=${b.wall} air=${b.air}`).concat(G.trn.enemies().map(e => e.type + ' ' + e.region));

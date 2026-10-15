const out = [];
arena();
const go = (r = 1) => { W().reset('scythe', r); E('P.x = 120; P.y = 304; P.vx = 0; P.vy = 0; P.ground = true; P.face = 1; P.scySouls = 0'); W().frame(2); };
go(); W().dummy(34);
for (let i = 0; i < 4; i++) { W().tap('attack', 2); W().frame(12); }
W().frame(90);
out.push('JJJJ: ' + W().log.map(l => l.st + ':' + (l.dmg / l.light).toFixed(2)).join(' ') + ' souls=' + E('P.scySouls'));
out.push('meta: ' + JSON.stringify(E("['scy_1','scy_2','scy_3','scy_4','scy_heavy'].map(id => [id, mvResolve(ATK[id]).tag, ATK[id].reach, ATK[id].ys])")));
go(); W().dummy(34); W().down('heavy'); W().frame(60); W().up('heavy'); W().frame(70);
out.push('hold K 0 souls: ' + W().log.map(l => l.st + ':' + (l.dmg / l.light).toFixed(2)).join(' '));
go(); E('P.scySouls = 3'); W().dummy(34); W().down('heavy'); W().frame(20); W().up('heavy'); W().frame(70);
out.push('hold K 3 souls: ' + W().log.map(l => l.st + ':' + (l.dmg / l.light).toFixed(2) + '/' + l.poise.toFixed(0)).join(' ') + ' souls=' + E('P.scySouls'));
go(); W().dummy(30); const x0 = E('P.x'); W().tap('parry', 2); W().frame(40);
out.push('hook step: x ' + x0 + ' -> ' + E('P.x.toFixed(1)') + ' face ' + E('P.face') + ' dummy at ' + E('enemies.find(e=>e.wmDummy).x'));
return out;

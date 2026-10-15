W().reset('longsword', 5); arena(); W().reset('longsword', 5);
const log = [];
W().tap('attack'); W().frame(10); W().tap('attack'); W().frame(5); W().down('left');
for (let k = 0; k < 40; k++) { W().frame(1); const s = E('P.state + ":" + P.face'); if (log[log.length - 1] !== s) log.push(s); }
W().up('left');
return log;

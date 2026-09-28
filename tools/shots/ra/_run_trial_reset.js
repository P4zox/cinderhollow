window.__spots = "[[\"R5\",121,8],[\"R6\",20,10],[\"R7\",15,10],[\"R8\",30,6],[\"R9\",5,25],[\"R10\",3,7],[\"R11\",15,5],[\"R12\",10,16],[\"R13\",20,10],[\"R14\",8,6], [\"C7\",20,12],[\"C8\",40,28],[\"C9\",4,7],[\"C10\",10,10],[\"C11\",19,27],[\"C12\",20,13],[\"C13\",31,10],[\"C14\",8,9],[\"C15\",8,9],[\"W2\",2,12], [\"K5\",6,10],[\"K6\",15,24],[\"K7\",40,26],[\"K8\",20,10],[\"K9\",5,10],[\"K10\",15,14],[\"K11\",13,16],[\"K12\",4,38],[\"K13\",8,10]]";
await boot(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; const S = window.__sys, out = [];

G.tp('K12', 20, 38); G.step(10); G.step(1, [], ['interact']); G.step(5); const hp = G.P.hp;
out.push('trial on: ' + !!S.SYS.trial);
G.P.x = 21 * 16 + 8; G.P.y = 20 * 16; G.step(1); for (let i = 0; i < 60; i++) G.step(1, ['right']);
out.push(`after touching the wall spikes: attempts ${S.SYS.trial && S.SYS.trial.attempts}, hp ${G.P.hp}/${hp}, at ${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)}`);
return out;

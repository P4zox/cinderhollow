window.__spots = "[[\"R5\",121,8],[\"R6\",20,10],[\"R7\",15,10],[\"R8\",30,6],[\"R9\",5,25],[\"R10\",3,7],[\"R11\",15,5],[\"R12\",10,16],[\"R13\",20,10],[\"R14\",8,6], [\"C7\",20,12],[\"C8\",40,28],[\"C9\",4,7],[\"C10\",10,10],[\"C11\",19,27],[\"C12\",20,13],[\"C13\",31,10],[\"C14\",8,9],[\"C15\",8,9],[\"W2\",2,12], [\"K5\",6,10],[\"K6\",15,24],[\"K7\",40,26],[\"K8\",20,10],[\"K9\",5,10],[\"K10\",15,14],[\"K11\",13,16],[\"K12\",4,38],[\"K13\",8,10]]";
await boot(); G.SAVE.items.talon = 1; G.tp('R11', 19, 5); G.step(400); const out = [];

for (const [r, x, y] of [['R11', 19, 5], ['K11', 11, 16]]) {
  G.tp(r, x, y); G.step(30); G.step(1, [], ['interact']); G.step(150);
  const S = window.__sys; out.push(r + ' seated: ' + !!(S && S.SYS.vista) + ' vistas ' + JSON.stringify(Object.keys(S.x3().vistas || {})) + ' lore ' + JSON.stringify(Object.keys(S.x3().lore || {})));
  await snap('vista_' + r);
  G.step(1, [], ['jump']); G.step(60);
}
return out;

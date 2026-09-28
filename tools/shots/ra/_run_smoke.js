window.__spots = "[[\"R5\",121,8],[\"R6\",20,10],[\"R7\",15,10],[\"R8\",30,6],[\"R9\",5,25],[\"R10\",3,7],[\"R11\",15,5],[\"R12\",10,16],[\"R13\",20,10],[\"R14\",8,6], [\"C7\",20,12],[\"C8\",40,28],[\"C9\",4,7],[\"C10\",10,10],[\"C11\",19,27],[\"C12\",20,13],[\"C13\",31,10],[\"C14\",8,9],[\"C15\",8,9],[\"W2\",2,12], [\"K5\",6,10],[\"K6\",15,24],[\"K7\",40,26],[\"K8\",20,10],[\"K9\",5,10],[\"K10\",15,14],[\"K11\",13,16],[\"K12\",4,38],[\"K13\",8,10]]";
await boot(); G.grantTechniques(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1;

const S = JSON.parse(window.__spots), out = [], errs = [];
window.addEventListener('error', e => errs.push(String(e.message)));
for (const [r, x, y] of S) {
  try { G.tp(r, x, y); for (let i = 0; i < 20; i++) { G.step(6, [['left', 'right'][i % 2]], i % 5 ? [] : ['attack']); G.P.hp = Math.max(G.P.hp, 60); if (G.state !== 'play') G.step(1, [], ['pause']); }
    out.push(r + ' ok ' + G.enemies.length + ' foes, props ' + G.props.length); }
  catch (e) { out.push(r + ' EXC ' + e.message + ' ' + (e.stack || '').split('\n')[1]); }
}
return { out, errs: errs.slice(0, 10) };

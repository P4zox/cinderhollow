// every edge link of the RA rooms, both ways: [room, tx, ty, hold, tap, expected room]
await boot(); G.grantTechniques(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; G.SETTINGS.god = true;
const L = [
 ['R5',10,0,['jump'],['jump'],'R9'], ['R9',10,25,['down','jump'],['jump'],'R5'], ['R9',20,7,['right'],[],'R10'], ['R10',2,7,['left'],[],'R9'],
 ['R10',61,7,['right'],[],'R11'], ['R11',2,7,['left'],[],'R10'], ['R5',57,18,[],[],'R6'], ['R6',9,0,['jump'],['jump'],'R5'],
 ['R6',2,9,['left'],[],'R7'], ['R7',45,5,['right'],[],'R6'], ['R7',5,10,[],[],'R8'], ['R8',5,0,['jump'],['jump'],'R7'],
 ['R8',45,6,['right'],[],'R12'], ['R12',2,10,['left'],[],'R8'], ['R6',43,10,[],[],'R13'], ['R13',3,0,['jump'],['jump'],'R6'],
 ['R14',7,0,['jump'],['jump'],'R5'],
 ['C7',2,9,['left'],[],'C8'], ['C8',93,17,['right'],[],'C7'], ['C8',65,28,[],[],'C9'], ['C9',9,0,['jump'],['jump'],'C8'],
 ['C8',2,27,['left'],[],'C11'], ['C11',21,27,['right'],[],'C8'], ['C11',21,5,['right'],[],'C8'], ['C8',2,5,['left'],[],'C11'],
 ['C9',2,9,['left'],[],'C13'], ['C13',34,9,['right'],[],'C9'], ['C9',2,29,['left'],[],'C12'], ['C12',38,13,['right'],[],'C9'],
 ['C9',22,33,['right'],[],'C10'], ['C10',1,10,['left'],[],'C9'], ['C15',2,3,['left'],[],'C9'],
 ['K6',5,24,[],[],'K5'], ['K6',17,0,['jump'],['jump'],'K7'], ['K7',25,32,[],[],'K6'], ['K6',22,24,['right'],[],'K9'], ['K9',2,10,['left'],[],'K6'],
 ['K9',49,0,['jump'],['jump'],'K8'], ['K8',29,10,[],[],'K9'], ['K7',93,32,[],[],'K8'], ['K8',41,0,['jump'],['jump'],'K7'],
 ['K7',5,0,['jump'],['jump'],'K10'], ['K10',6,16,['right'],[],'K7'], ['K7',55,0,['jump'],['jump'],'K11'], ['K11',20,18,[],[],'K7'],
 ['K7',89,0,['jump'],['jump'],'K12'], ['K12',10,54,[],[],'K7'],
];
const out = [];
for (const [r, x, y, hold, tap, want] of L) {
  G.tp(r, x, y); G.step(2); let got = null;
  for (let i = 0; i < 150 && !got; i++) { G.step(1, hold, i === 0 ? tap : []); if (G.room !== r) got = G.room; }
  let st = '';
  if (got) { for (let i = 0; i < 90; i++) G.step(1, hold.filter(h => h !== 'jump' && h !== 'down')); st = ` -> at ${(G.P.x / 16).toFixed(1)},${(G.P.y / 16).toFixed(1)} ground=${G.P.ground}`; }
  out.push(`${got === want ? 'OK ' : 'BAD'} ${r}(${x},${y}) ${hold.join('+')} -> ${got}${st}`);
}
return out;

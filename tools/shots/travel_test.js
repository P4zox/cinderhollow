await boot(); const ids=['R1','C2','C3','K1','K2','A2','A5','HF1','HF6','SP3','SP6','D3','D7','X4','E2','M3','H1'];
for (const r of Object.keys(window.__game.SAVE.visited)) {}
const ALL = ["R1","R2","R3","R4","C1","C2","C3","C4","C5","C6","K1","K2","K3","K4","A1","A2","A3","A4","A5","A6","M1","M2","M3","M4","M5","M6","X1","X2","X3","X4","X5","HF1","HF2","HF3","HF4","HF5","HF6","HF7","SP1","SP2","SP3","SP4","SP5","SP6","SP7","D1","D2","D3","D4","D5","D6","D7","D8","H1","E1","E2","E3"];
for (const r of ALL) G.SAVE.visited[r]=1;
for (const r of ['C2','C4','K1','M3','X4','A2','A5','HF1','HF6','SP3','SP6','D3','D7','E2']) if (!G.SAVE.shrines.includes(r)) G.SAVE.shrines.push(r);
G.tp('R1',8,10); G.step(10); G.step(2,[],['interact']); await new Promise(r=>setTimeout(r,800)); G.step(2); await snap('shrine_R1');
for (let i=0;i<3;i++){ G.step(1,[],['down']); } G.step(1,[],['confirm']); G.step(2); await snap('travel_0');
G.step(1,[],['right']); G.step(1,[],['right']); G.step(1,[],['right']); G.step(2); await snap('travel_1');
G.step(1,[],['down']); G.step(1,[],['right']); G.step(1,[],['down']); G.step(2); await snap('travel_2');
return [G.state];

await boot(); for (const id of ['R1','R2','R3','R4','C1','C2','C3','C4','C5','C6','K1','K2','K3','K4','A1','A2','A3','M1','M2','M4','M5','X1','X2','X3']) G.SAVE.visited[id]=1;
G.step(1,[],['map']); G.step(2); await snap('map'); return G.state;

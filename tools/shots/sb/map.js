for (const r of ['NV8','NV9','NV10','NV11','NV12','NV13','NV14','NV15','NV16','NV3','NV4','NV6','DU9','DU10','DU11','DU12','DU13','DU14','DU15','DU16','DU17','DU18','DU4','DU5']) G.SAVE.visited[r] = 1;
G.tp('NV10', 20, 22); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
G.step(1, [], ['map']); G.step(30); await snap('map_nv');
G.step(1, [], ['map']); G.step(10);
G.tp('DU10', 60, 17); for (let i = 0; i < 4; i++) { G.step(10); settle(); }
G.step(1, [], ['map']); G.step(30); await snap('map_du');
return G.state;

// Barrows wing: DB3 -> DB11 -> DB10 -> DB12 -> DB4 and back, no teleports after the first.
G.tp('DB3', 12, 9); wait(30); here('start');
run(17, { tol: 0.4 }); hop(17, 7); hop(19, 4); here('ledges'); climb(11.2, 'right', { room: 'DB11' }); here('causeway');
run(31, { tol: 0.4 }); here('mound2'); hop(34.8, 6); hop(37, 4); here('tomb top'); run(42, { tol: 0.5 }); here('east landing'); hop(43.5, 8); hop(39.8, 5); hop(43.5, 2); here('up ledges');
climb(12.5, 'right', { room: 'DB10' }); here('nave stair');
for (let y = Math.floor(S().y / 3) * 3; y >= 12; y -= 3) if (y < S().y - 0.5) hop(((39 - y) / 3) % 2 === 0 ? 79.5 : 75.5, y);
here('stair top'); hop(73, 11); here('triforium');
for (const [x, y] of [[65, 11], [59, 11], [50, 11], [46, 12], [41, 14], [35, 12], [31, 11], [22, 11], [14, 11]]) { hop(x, y); here('raft ' + x); }
run(5.5, { noJump: true, noGap: true, tol: 0.3 }); here('stairwell'); 
for (let i = 0; i < 12 && G.room === 'DB10'; i++) { drop(); }
here('down'); fall(); here('galleries?');
drop(); drop(); fall(); here('galleries floor'); run(10.6, { tol: 0.3 }); use(); wait(60); here('lever');
run(15.5, { noJump: true, noGap: true, room: 'DB4' }); fall(); here('DB4 ledge'); for (let i = 0; i < 4 && S().y < 11.5; i++) drop(); here('DB4 floor');
// back
hop(15.5, 9); hop(17.5, 6); hop(15.5, 3); hop(17.5, 0); here('top ledge'); hop(14, 10, { tries: 3 }); here('galleries again?');
run(4, { tol: 0.4 }); hop(2.5, 7); hop(4.5, 4); hop(2.5, 1); here('galleries stair'); jump(null, { to: 4.6, hold: 22 }); here('nave?');
for (let y = 36; y >= 12; y -= 3) hop(((39 - y) / 3) % 2 === 0 ? 4.5 : 2.5, y);
hop(8, 11); here('west triforium');
for (const [x, y] of [[22, 11], [31, 11], [35, 12], [41, 14], [46, 12], [50, 11], [59, 11], [65, 11], [71, 11]]) { hop(x, y); here('raft ' + x); }
run(78.5, { noJump: true, noGap: true, tol: 0.3 }); for (let i = 0; i < 14 && G.room === 'DB10'; i++) drop(); fall(); here('causeway?');
for (let i = 0; i < 4 && S().y < 10.5; i++) drop(); here('landing');
hop(43.5, 8); hop(39.8, 5); hop(37.2, 4); here('tomb'); hop(34.8, 6); hop(30, 8); run(7, { tol: 0.4 }); here('west');
run(3.2, { noJump: true, noGap: true, room: 'DB3' }); fall(); here('DB3!');

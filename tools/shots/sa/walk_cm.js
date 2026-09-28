// Crimson wing: CM4 -> CM9 -> CM11 -> CM10 -> CM8 and back, no teleports after the first.
G.tp('CM4', 45, 10); wait(30); here('start');
run(53, { tol: 0.4 }); jump('right', { room: 'CM9', hold: 14 }); fall('right'); here('east wing');
run(3.5, { tol: 0.4 }); here('stair foot'); climb(12.5, 'left', { room: 'CM11', maxF: 1200 }); here('corridor');
run(-3, { room: 'CM10' }); run(17, { tol: 0.5 }); here('lower landing'); hop(12, 28); here('rail'); run(10.5, { tol: 0.4, noJump: true }); fall(); run(13.2, { tol: 0.3, noJump: true }); here('at lever'); use(); wait(60);
run(18.5, { noJump: true, noGap: true, room: 'CM8' }); fall(); here('CM8!');
// back
for (let i = 0; i < 3 && S().y < 10.5; i++) drop(); here('CM8 floor');
hop(7.5, 8); hop(5.5, 5); hop(7.5, 2); here('CM8 top'); climb(29.5, 'right', { room: 'CM10' }); here('chamber');
run(10.5, { tol: 0.5 }); hop(12, 28); hop(16, 26); here('landing'); run(27, { room: 'CM11' }); here('corridor');
run(45, { noJump: true, noGap: true, room: 'CM9' }); fall(); for (let i = 0; i < 12 && S().y < 26.5; i++) { fall(); if (S().y < 26.5) drop(); } here('EW floor');
run(-3, { room: 'CM4' }); fall(); here('CM4!');

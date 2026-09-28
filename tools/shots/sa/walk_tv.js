G.tp('TV2', 5, 10); wait(30); here('start');
run(9, { noJump: true, room: 'TV10' }); fall(); here('in the trail');
run(11, { noGap: true, noJump: true, room: 'TV9' }); fall(); here('canopy');
hop(101, 9); hop(104, 12); hop(105, 16); hop(100, 19); hop(100, 23); hop(100, 26); here('ground');
run(69, { tol: 0.5 }); here('mound'); hop(73, 22); here('f'); hop(68, 19); here('g'); hop(67, 16); here('h'); hop(62, 13); here('i'); hop(62, 11); here('j');
run(44, { tol: 0.5 }); here('k'); hop(42, 8); hop(39, 5); hop(39, 2); here('l');
climb(12.5, 'right', { room: 'TV11' }); here('roots floor');
run(24, { tol: 0.4 }); here('lever'); use(); wait(60); here('pulled');
run(15, { tol: 0.4 }); here('vestibule'); hop(15, 9); here('ledge');
climb(24.2, 'right', { room: 'TV5' }); here('TV5!');
// and back
run(11, { tol: 0.3, noJump: true }); here('on the lid'); drop(); fall(); here('vestibule again');
run(38, { tol: 0.6 }); here('east'); run(39.5, { noJump: true, noGap: true, room: 'TV9' }); fall(); here('canopy again');
hop(42, 8); hop(44, 11); here('high walkway'); run(62, { tol: 0.5 }); here('through the elder');
hop(66, 16); hop(68, 19); hop(73, 22); hop(69, 25); here('down east of the elder'); run(103, { tol: 0.5 }); here('east ground');
hop(100, 23); hop(103, 21); hop(104, 19); hop(105, 16); hop(101, 14); hop(104, 12); hop(102, 9); hop(99, 6); hop(99, 3); here('top ledge');
climb(12.5, 'left', { room: 'TV10' }); here('trail');
run(33, { tol: 0.4 }); hop(33, 9); here('step'); climb(11.2, 'right', { room: 'TV2' }); here('TV2!');

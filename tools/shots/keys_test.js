await boot(); const o = [];
const key = (code, type='keydown') => window.dispatchEvent(new KeyboardEvent(type, { code, bubbles: true }));
const tap = async code => { key(code); G.step(1); key(code, 'keyup'); G.step(1); };
localStorage.removeItem('cinderhollow_keys');
// open Settings tab: Esc, then Q (spell) switches tab backwards to Settings
await tap('Escape'); await tap('KeyQ'); G.step(2); await snap('k0_settings');
// row 1 = Key bindings
await tap('ArrowDown'); await tap('Enter'); G.step(2); await snap('k1_keys');
// jump is row 4 (left,right,up,down,jump): go down 4, Enter, then press X
for (let i = 0; i < 4; i++) await tap('ArrowDown'); await tap('Enter'); G.step(2); await snap('k2_capture');
await tap('KeyX'); G.step(2); await snap('k3_bound');
await tap('Escape'); await tap('Escape'); G.step(2); o.push('state after close ' + G.state);
// X should now jump, Space should not
G.step(20); let y0 = G.P.y; key('KeyX'); G.step(8); o.push('X jumps: ' + (G.P.y < y0 - 4)); key('KeyX', 'keyup'); G.step(40);
y0 = G.P.y; key('Space'); G.step(8); o.push('Space still jumps: ' + (G.P.y < y0 - 4)); key('Space', 'keyup'); G.step(40);
o.push('saved: ' + localStorage.getItem('cinderhollow_keys').slice(0, 80));
// cheats: open menu, settings, go to Cheats row (index 6), enter, toggle infinite FP (row 2)
await tap('Escape'); await tap('KeyQ'); for (let i = 0; i < 8; i++) await tap("ArrowDown"); await tap("Enter"); G.step(2);
await tap('ArrowDown'); await tap('ArrowDown'); await tap('Enter'); G.step(2); await snap('k4_cheats');
await tap('Escape'); await tap('Escape'); G.step(2);
G.P.fp = 1; G.step(5); o.push('inffp: fp ' + Math.round(G.P.fp) + '/' + G.D.maxFp);
// title controls reflect the binding
return o;

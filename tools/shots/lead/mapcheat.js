await boot(); const o = [];
const key = (code, type='keydown') => window.dispatchEvent(new KeyboardEvent(type, { code, bubbles: true }));
const tap = async code => { key(code); G.step(1); key(code, 'keyup'); G.step(1); };
o.push('visited before: ' + Object.keys(G.SAVE.visited).length + ', shrines ' + G.SAVE.shrines.length);
await tap('Escape'); await tap('KeyQ');                       // Settings tab
for (let i = 0; i < 8; i++) await tap('ArrowDown'); await tap('Enter'); G.step(2);   // Cheats
const rows = 7; for (let i = 0; i < rows - 1; i++) await tap('ArrowDown'); await tap('Enter'); G.step(5);   // last row: shrines + map
o.push('visited after: ' + Object.keys(G.SAVE.visited).length + ', shrines ' + G.SAVE.shrines.length + ', state ' + G.state);
await tap('Tab'); G.step(10); await snap('mapcheat_map');
await tap('Tab'); G.step(5);
return o;

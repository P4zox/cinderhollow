await boot(); const o = [];
// ---- fake controller
const pad = { id: 'Xbox Wireless Controller (STANDARD GAMEPAD)', connected: true, buttons: Array.from({ length: 17 }, () => ({ pressed: false, value: 0 })), axes: [0, 0, 0, 0] };
navigator.getGamepads = () => [pad];
const frame = n => { for (let i = 0; i < n; i++) { G.pad(1/60); G.step(1); } };
const btn = async (i, hold = 3) => { pad.buttons[i].pressed = true; frame(hold); pad.buttons[i].pressed = false; frame(2); };
frame(2);
o.push('pad seen: ' + G.PAD.seen + ' name=' + G.PAD.name);
G.step(30); let y0 = G.P.y; pad.buttons[0].pressed = true; frame(8); o.push('A jumps: ' + (G.P.y < y0 - 4)); pad.buttons[0].pressed = false; frame(50);
await btn(2); o.push('X attack state: ' + G.P.state);
frame(40);
pad.axes[0] = 1; frame(20); o.push('stick right moves: vx=' + Math.round(G.P.vx)); pad.axes[0] = 0; frame(20);
await btn(9); o.push('Start -> ' + G.state);
await btn(13); await btn(13); o.push('dpad down in menu sel=' + (G.menu && G.menu.sel));
await btn(5); o.push('RB tab=' + (G.menu && G.menu.tab));
await btn(1); o.push('B -> ' + G.state);
frame(10); o.push('state stays play: ' + G.state + ' pstate=' + G.P.state);
// ---- air attack limit: jump, then mash attack
G.P.st = 999; pad.buttons[0].pressed = true; frame(4); let starts = 0, last = G.P.state;
for (let k = 0; k < 5; k++) { pad.buttons[2].pressed = true; frame(2); pad.buttons[2].pressed = false; for (let j = 0; j < 12; j++) { frame(1); if (G.P.state !== last && G.P.state === 'air_attack') starts++; last = G.P.state; } }
pad.buttons[0].pressed = false;
o.push('air attacks started in one jump (max 2): ' + starts + ' lock=' + G.P.airLock);
frame(90); o.push('after landing lock=' + G.P.airLock + ' n=' + G.P.airN);
// ---- shaders
o.push('shaders setting=' + G.SETTINGS.shaders + ' gl ok=' + G.GFX.ok);
await snap('v19_cinematic');
for (const [name, v] of G.GFX_PRESETS) { Object.assign(G.SETTINGS, v); G.SETTINGS.shaders = 1; G.step(2); await snap('v19_' + name.replace(/\W/g, '')); }
G.SETTINGS.shaders = 0; G.step(2); await snap('v19_noshader');
Object.assign(G.SETTINGS, G.GFX_PRESETS[0][1]); G.SETTINGS.shaders = 1;
// settings screens
await btn(9); await btn(4);   // LB: back one tab, onto Settings
o.push('tab=' + G.menu.tab);
await btn(13); await btn(13); await btn(13); await btn(0); frame(3); await snap('v19_gfxmenu'); o.push('sub=' + (G.menu.sub && G.menu.sub.kind));
await btn(1); await btn(12); await btn(0); frame(3); await snap('v19_padmenu'); o.push('sub=' + (G.menu.sub && G.menu.sub.kind));
await btn(1); await btn(1); frame(4);
return o;

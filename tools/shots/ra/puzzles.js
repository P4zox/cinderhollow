await boot(); G.grantTechniques(); G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; G.SETTINGS.god = true;
const out = [], K = () => G.KIT;
const mv = (x, y) => { G.P.x = x * 16 + 8; G.P.y = (y + 1) * 16; G.P.vx = G.P.vy = 0; G.step(3); };
const hit = (r, x, y) => { if (G.room !== r) G.tp(r, x, y); mv(x, y); G.step(1, [], ['interact']); G.step(20); };
// ---- Crypt of Lanterns: three wrong tries (hint), then the right order
const toasts = []; const T0 = window.toast;
for (let n = 0; n < 3; n++) { hit('C12', 18, 13); hit('C12', 24, 13); G.step(60); }
out.push('C12 after 3 wrong tries, seq active: ' + K().byId.crypt.active);
await snap('p_c12_wrong');
for (const x of [18, 30, 12, 24]) hit('C12', x - 1, 13);
G.step(60); out.push('C12 solved: ' + K().byId.crypt.active + ' vault open: ' + K().byId.vault.on);
await snap('p_c12_solved');
mv(8, 13); for (let i = 0; i < 60; i++) G.step(1, ['left']); out.push('C12 into the vault: x=' + (G.P.x / 16).toFixed(1));
G.tp('C12', 20, 13); G.step(10); out.push('C12 re-entered, still solved: ' + K().byId.vault.on);
// ---- Organ Loft: the hymn Sun, Bell, Moon, Root
for (const x of [14, 11, 20, 17]) hit('K10', x, 14);
G.step(60); out.push('K10 solved: ' + K().byId.hymn.active + ' gate: ' + K().byId.vestry.on);
await snap('p_k10_solved');
// ---- Winch House: low winch, then run for the high one
hit('R12', 27, 16); out.push('R12 wA on: ' + K().byId.wA.active);
hit('R12', 7, 4); G.step(10); out.push('R12 wB on: ' + K().byId.wB.active + ' port open: ' + K().byId.port.on);
G.step(600); out.push('R12 timers out, port still open (persist): ' + K().byId.port.on);
await snap('p_r12');
return out;

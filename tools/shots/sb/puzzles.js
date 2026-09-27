const K = G.KIT, out = []; G.SETTINGS.god = 1;
const at = (r, x, y) => { if (G.room !== r) { G.tp(r, x, y); for (let i = 0; i < 4; i++) { G.step(10); settle(); } } else { G.P.x = x * 16 + 8; G.P.y = (y + 1) * 16; G.P.vx = G.P.vy = 0; G.step(24); } G.enemies.length = 0; };
const jumpHit = (face, fr = 12) => { if (face) G.step(1, [face]); G.step(1, ['jump'], ['jump']); for (let i = 0; i < fr; i++) G.step(1, ['jump']); G.step(1, ['jump'], ['attack']); for (let i = 0; i < 30; i++) G.step(1); };
const hit = (face) => { if (face) G.step(1, [face]); G.step(1, [], ['attack']); for (let i = 0; i < 30; i++) G.step(1); };
// ---- the Dirge: a wrong order three times (hint), then the dirge
const bell = { b1: [9, 10, 4], b2: [13, 13, 12], b3: [17, 10, 12], b4: [21, 13, 12], b5: [25, 10, 8] };
at('NV12', 16, 13);
for (let k = 0; k < 3; k++) for (const b of ['b1', 'b2']) { const [x, y, f] = bell[b]; at('NV12', x, y); jumpHit(0, f); }
out.push('dirge wrong count ' + (G.sb.wrong.NV12 || 0) + ' solved ' + K.byId.dirge.active);
{ const [x, y, f] = bell.b5; at('NV12', x, y); jumpHit(0, f); }
const hl = []; { const q = K.byId.dirge, h0 = q.hit; q.hit = m => { hl.push(m.id + '@' + q.prog); return h0(m); }; }
for (const b of ['b2', 'b1', 'b4', 'b3', 'b5', 'b2']) { const [x, y, f] = bell[b]; at('NV12', x, y); jumpHit(0, f); out.push(' rang ' + b + ' prog ' + K.byId.dirge.prog + ' lit ' + K.byId[b].lit); }
for (let i = 0; i < 200; i++) G.step(1);
out.push('hits ' + hl.join(' ')); out.push('dirge solved ' + K.byId.dirge.active + ' gw ' + K.byId.gw.on + ' gc ' + K.byId.gc.on + ' flag ' + G.SAVE.flags['x3:NV12:dirge']);
await snap('pz_dirge');
// ---- the Seal: g3 g1 g6 g4
const gl = { g1: [12, 16, 0], g3: [25, 16, 0], g6: [25, 6, 'right'], g4: [27, 10, 'right'] };
at('DU14', 16, 16);
at('DU14', 12, 16); jumpHit(0, 4); at('DU14', 25, 16); jumpHit(0, 4); at('DU14', 12, 16); jumpHit(0, 4);   // wrong: g1 first
at('DU14', 16, 11); hit('right'); at('DU14', 12, 16); jumpHit(0, 4);   // decoy g2 is hit? then g1 (wrong) resets
for (const k of ['g3', 'g1', 'g6', 'g4']) { const [x, y, f] = gl[k]; at('DU14', x, y); if (f) hit(f); else jumpHit(0, 4); out.push(' touched ' + k + ' prog ' + K.byId.titles.prog); }
for (let i = 0; i < 200; i++) G.step(1);
out.push('seal solved ' + K.byId.titles.active + ' gate ' + K.byId.seal.on + ' wrong ' + (G.sb.wrong.DU14 || 0));
await snap('pz_seal');
// ---- the Sun Dial: M1 x3, M2 x3, M3 x1
at('DU13', 20, 17);
const strike = (x, y, n, jump) => { for (let k = 0; k < n; k++) { at('DU13', x, y); if (jump) jumpHit(); else hit('right'); } };
strike(26, 17, 3, true); out.push(' M1 rot ' + K.byId.M1.rot);
strike(14, 17, 3, true); out.push(' M2 rot ' + K.byId.M2.rot);
at('DU13', 13, 8); for (let k = 0; k < 1; k++) { at('DU13', 13, 8); hit('right'); } out.push(' M3 rot ' + K.byId.M3.rot);
for (let i = 0; i < 200; i++) G.step(1);
out.push('sundial socket ' + K.byId.so.active + ' door ' + K.byId.door.on);
await snap('pz_sundial');
// persistence: re-enter the rooms
G.tp('NV8', 10, 10); G.step(20); at('NV12', 16, 13); G.step(60); out.push('dirge after re-entry ' + K.byId.dirge.active + ' gw ' + K.byId.gw.on);
G.tp('NV8', 10, 10); G.step(20); at('DU13', 20, 17); G.step(60); out.push('sundial after re-entry ' + K.byId.so.active + ' door ' + K.byId.door.on + ' M1 ' + K.byId.M1.rot);
return out;

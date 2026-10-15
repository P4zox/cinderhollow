const R = {};
const P = () => G.P, st = () => G.P.state;
const setup = (type, rank = 1, far = 26, o = {}) => { W().reset(type, rank); arena(); W().reset(type, rank); E('P.lastHit = null'); W().dummy(far, o); };
const seq = (n) => { const a = []; for (let i = 0; i < n; i++) { W().frame(1); if (a[a.length - 1] !== st()) a.push(st()); } return a.join(' '); };
const dmgs = () => W().log.map(h => h.st + ':' + (h.dmg / G.D.light).toFixed(2)).join(' ');
const air = (fn) => { const y0 = P().y; let top = 0, f = 0; const t0 = W().ms; fn && fn(); for (f = 0; f < 200; f++) { W().frame(1); top = Math.max(top, y0 - P().y); if (f > 12 && P().ground) break; } return { top: Math.round(top), airMs: Math.round(W().ms - t0) }; };
setup('staff', 1, 300); R.jump_full = air(() => { W().down('jump'); W().frame(14); W().up('jump'); });
setup('staff', 1, 300); { const x0 = P().x; R.vault = air(() => W().tap('parry')); R.vault.dx = Math.round(P().x - x0); }
setup('staff', 1, 300); { const x0 = P().x; W().down('right'); R.vault_fwd = air(() => W().tap('parry')); W().up('right'); R.vault_fwd.dx = Math.round(P().x - x0); }
// full jump + K + K at rank III
setup('staff', 3, 26, { tall: 90 }); E('window.__wm.follow = 26'); W().down('jump'); W().frame(8); W().tap('heavy'); W().frame(8); W().tap('heavy'); W().frame(6); W().up('jump'); R.aspin2_jump = seq(70) + ' | ' + dmgs();
setup('staff', 3, 26, { tall: 90 }); E('window.__wm.follow = 26'); W().tap('parry'); W().frame(14); W().tap('heavy'); W().frame(8); W().tap('heavy'); R.aspin2_vault = seq(70) + ' | ' + dmgs();
// vault + J + K (the doc's cycle) timing: is there air time for both?
setup('staff', 1, 26, { tall: 90 }); E('window.__wm.follow = 26'); W().tap('parry'); W().frame(14); W().tap('attack'); W().frame(6); W().tap('heavy'); R.vault_J_K = seq(80) + ' | ' + dmgs();
// dive kick loop with proper fall timing
setup('staff', 1, 0, { tall: 60 }); E('window.__wm.follow = 0; D.maxSt = 999; P.st = 999'); W().down('jump'); W().frame(14); W().up('jump');
{ let n = 0; for (let i = 0; i < 900 && !P().ground; i++) { if (!E('!!ATK[P.state]') && P().vy > 30) { W().down('down'); W().tap('attack'); W().up('down'); n++; } else W().frame(1); } R.divekick_loop = { presses: n, kicks: W().log.filter(h => h.st === 'st_down').length, landed: P().ground, secs: 0 }; }
// same for the longsword (reference)
setup('longsword', 1, 0, { tall: 60 }); E('window.__wm.follow = 0; D.maxSt = 999; P.st = 999'); W().down('jump'); W().frame(14); W().up('jump');
{ let n = 0; for (let i = 0; i < 900 && !P().ground; i++) { if (!E('!!ATK[P.state]') && P().vy > 30) { W().down('down'); W().tap('attack'); W().up('down'); n++; } else W().frame(1); } R.ls_divekick_loop = { presses: n, kicks: W().log.length, landed: P().ground }; }
// double vault (IV) after J + K from a full jump next to a dummy
setup('staff', 4, 20, { tall: 40 }); E('window.__wm.follow = 20'); W().down('jump'); W().frame(8); W().tap('attack'); W().frame(10); W().up('jump'); W().frame(10); W().tap('heavy'); W().frame(12); const n0 = E('P.airN'); W().tap('parry'); R.dvault = 'airN ' + n0 + ' -> ' + seq(30) + ' airN ' + E('P.airN') + ' lock ' + E('P.airLock') + ' | ' + dmgs();
// gale (V) vs a dummy at 30 / 50 / 70
for (const d of [30, 50, 70]) { setup('staff', 5, d); E('P.mom = 3'); W().tap('heavy'); W().frame(90); R['gale_' + d] = dmgs(); }
// whip: zip to a large foe and press J on arrival
setup('whip', 1, 50, { half: 18, tall: 50 }); W().tap('parry'); R.wh_zip = seq(40);
// whip: J J J J at rank I
setup('whip', 1, 70); E('window.__wm.follow = 70'); for (let i = 0; i < 4; i++) { W().tap('attack'); W().frame(10); } R.wh_JJJJ = seq(60);
// whip: up close dps J J J (dummy 16)
return R;

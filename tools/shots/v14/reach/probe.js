// exploratory probe: staff + whip through real inputs (dev tool, v14 reach pass)
const R = {};
const P = () => G.P, st = () => G.P.state;
const setup = (type, rank = 1, far = 26, o = {}) => { W().reset(type, rank); arena(); W().reset(type, rank); E('P.lastHit = null'); W().dummy(far, o); };
const tr = (n) => { const a = []; for (let i = 0; i < n; i++) { W().frame(1); a.push(st() + '@' + Math.round(P().x) + ',' + Math.round(P().y)); } return a; };
const seq = (n) => { const a = []; for (let i = 0; i < n; i++) { W().frame(1); if (a[a.length - 1] !== st()) a.push(st()); } return a.join(' '); };
const dmgs = () => W().log.map(h => h.st + ':' + (h.dmg / G.D.light).toFixed(2)).join(' ');
// ---- STAFF
// vault trajectory
setup('staff', 1, 200); const x0 = P().x, y0 = P().y; W().tap('parry'); let top = 0, f = 0, land = null, free = null;
for (f = 1; f < 90; f++) { W().frame(1); top = Math.max(top, y0 - P().y); if (free === null && st() !== 'vault') free = f; if (land === null && f > 5 && P().ground) { land = f; break; } }
R.st_vault = { top: +top.toFixed(1), dx: Math.round(P().x - x0), freeMs: Math.round(free * 16.7), landMs: Math.round(land * 16.7), stamUsed: Math.round(G.D.maxSt - P().st) };
// vault -> J immediately, at apex
setup('staff', 1, 60, { tall: 90 }); W().tap('parry'); W().frame(3); W().tap('attack'); R.st_vaultJ_early = seq(60);
setup('staff', 1, 60, { tall: 90 }); W().tap('parry'); W().frame(16); W().tap('attack'); R.st_vaultJ_apex = seq(60);
// vault cycle I, J, K, down+J against a tall dummy that follows
setup('staff', 1, 30, { tall: 90 }); E('window.__wm.follow = 20'); W().tap('parry'); W().frame(16); W().tap('attack'); W().frame(18); W().tap('heavy'); W().frame(26); W().down('down'); W().tap('attack'); W().up('down'); R.st_cycle = seq(80) + ' | mom ' + E('P.mom') + ' | ' + dmgs();
// dive kick loop on a tall dummy below
setup('staff', 1, 0, { tall: 60 }); E('window.__wm.follow = 0; D.maxSt = 999; P.st = 999'); W().tap('jump'); W().frame(4);
let kicks = 0, k0 = 0; for (let i = 0; i < 600 && !P().ground; i++) { if (!E('!!ATK[P.state]') && st() !== 'roll') { W().down('down'); W().tap('attack'); W().up('down'); } else W().frame(1); }
R.st_divekick_loop = { kicks: W().log.filter(h => h.st === 'st_down').length, airborneFrames: W().ms / 16.7 | 0, mom: E('P.mom'), landed: P().ground };
// spin cost and the denial
setup('staff'); const s0 = P().st; W().tap('heavy'); W().frame(50); R.st_spin = { cost: Math.round(s0 - P().st + 0), maxSt: G.D.maxSt, hits: dmgs() };
setup('staff'); E('P.st = 25'); W().tap('heavy'); R.st_spin_low = seq(20);
// spin hits behind?
setup('staff', 1, -26); W().tap('heavy'); W().frame(50); R.st_spin_behind = dmgs();
// J J J J with dummy behind
setup('staff', 1, -12); for (let i = 0; i < 4; i++) { W().tap('attack'); W().frame(22); } W().frame(40); R.st_JJJJ_behind12 = dmgs();
// aerial spin -> K (III)
setup('staff', 3, 26, { tall: 90 }); W().tap('jump'); W().frame(6); W().tap('heavy'); W().frame(8); W().tap('heavy'); R.st_aspin2 = seq(60) + ' | ' + dmgs();
// gale (V)
setup('staff', 5, 30); E('P.mom = 3'); W().tap('heavy'); R.st_gale_seq = seq(80); R.st_gale_hits = dmgs();
setup('staff', 5, 100); E('P.mom = 3; window.__wm.follow = 0'); W().tap('heavy'); W().frame(90); R.st_gale_far100 = dmgs();
// double vault (IV): jump next to a dummy, I
setup('staff', 4, 20, { tall: 40 }); W().tap('jump'); W().frame(10); W().tap('attack'); W().frame(20); W().tap('heavy'); W().frame(10); const n0 = E('P.airN'); W().tap('parry'); R.st_dvault = 'airN before ' + n0 + ' ' + seq(20) + ' airN ' + E('P.airN') + ' lock ' + E('P.airLock');
// ---- WHIP
// tip band
const band = [];
for (let d = 20; d <= 96; d += 4) { setup('whip', 1, d); W().tap('attack'); W().frame(30); const h = W().log[0]; band.push(d + ':' + (h ? (h.dmg / G.D.light).toFixed(2) : '-')); }
R.wh_tipband_J = band.join(' ');
// thousand: hold J durations (rank V)
for (const ms of [100, 200, 260, 300, 400, 600]) { setup('whip', 5, 70); W().down('attack'); W().frame(Math.round(ms / 16.7)); W().up('attack'); R['wh_holdJ_' + ms] = seq(80); }
// mash J at rank V: 10 taps 5 frames apart (tap 2 frames)
setup('whip', 5, 70); { const a = []; for (let i = 0; i < 12; i++) { W().down('attack'); W().frame(3); W().up('attack'); for (let k = 0; k < 4; k++) { W().frame(1); if (a[a.length - 1] !== st()) a.push(st()); } } R.wh_mash_r5 = a.join(' '); }
// mash K at rank IV
setup('whip', 4, 70); { const a = []; for (let i = 0; i < 10; i++) { W().down('heavy'); W().frame(4); W().up('heavy'); for (let k = 0; k < 4; k++) { W().frame(1); if (a[a.length - 1] !== st()) a.push(st()); } } R.wh_mashK_r4 = a.join(' '); }
// thunderclap at close and far
setup('whip', 1, 20); E('P.crack = 100'); W().tap('heavy'); W().frame(50); R.wh_thunder_close = dmgs();
setup('whip', 1, 70); E('P.crack = 100'); W().tap('heavy'); W().frame(50); R.wh_thunder_tip = dmgs();
// grapple small foe: breakStance count and spam
setup('whip', 1, 50); E(`(() => { const d = enemies.find(e => e.wmDummy); d.bs = 0; d.breakStance = () => { d.bs++; }; })()`);
for (let i = 0; i < 6; i++) { W().tap('parry'); W().frame(125); E('(() => { const d = enemies.find(e => e.wmDummy); d.x = P.x + 50; })()'); }
R.wh_grapple_spam = { staggers: E('enemies.find(e => e.wmDummy).bs'), secs: 6 * 126 / 60, stamLeft: Math.round(P().st) };
// snap: mash I with grapple on cooldown (rank II): how much of the time is a snap armed, and stamina cost
setup('whip', 2, 40); E('P.whCd = 99'); { let armed = 0; const s0 = P().st; for (let i = 0; i < 120; i++) { if (i % 6 === 0) W().tap('parry'); else W().frame(1); if (E('P.snapT > 0')) armed++; } R.wh_snap_mash = { armedFrac: +(armed / 120).toFixed(2), stam: Math.round(s0 - P().st) }; }
// overhead hold
for (const ms of [150, 300, 500, 700]) { setup('whip', 1, 70); W().down('heavy'); W().frame(Math.round(ms / 16.7)); W().up('heavy'); R['wh_holdK_' + ms] = seq(80) + ' | ' + dmgs(); }
// J J K, K K
setup('whip', 1, 70); W().tap('attack'); W().frame(8); W().tap('attack'); W().frame(8); W().tap('heavy'); R.wh_JJK = seq(90);
return R;

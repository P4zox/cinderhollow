// v14 reach: every new combo (and every fixed input) starts from real inputs -- staff + whip
// run: SHOT_HTML=web/dist/v14_reach.html sh tools/shots/wm/run.sh tools/shots/v14/reach/routes.js <outdir>
const R = [];
const T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const P = () => G.P, st = () => G.P.state;
const setup = (type, rank = 1, far = 26, o = {}) => { W().reset(type, rank); arena(); W().reset(type, rank); E('P.lastHit = null; D.maxSt = 999; P.st = 999; P.momLand = null; P.momKeep = null; P.snapCd = 0; P.snapT = 0; P.whPull = null; P.dvUsed = false; P.stRefTrip = false'); W().dummy(far, o); };
E(`(() => { const W = window.__wm; W.starts = []; const ms = mvStart; mvStart = function (id, o = {}) { const r = ms.call(this, id, o); if (r) W.starts.push(id); return r; }; })()`);
const started = () => W().starts.slice();
const clr = () => { W().starts = []; W().log = []; };
const hitsOf = id => W().log.filter(h => h.st === id);
const dm = id => hitsOf(id).map(h => (h.dmg / G.D.light).toFixed(2)).join('/');
const run = n => { for (let i = 0; i < n; i++) W().frame(1); };
const jumpHi = () => { W().down('jump'); W().frame(8); };
const tapDown = b => { W().down('down'); W().tap(b); W().up('down'); };
// ================================================================ STAFF
// J J K -> pole launcher, rides into the air, then air J
setup('staff', 1, 24, { tall: 40 }); E('window.__wm.follow = 24'); clr();
W().tap('attack'); run(8); W().tap('attack'); run(8); W().tap('heavy'); let top = 0; const y0 = P().y; for (let i = 0; i < 70 && st() !== 'air'; i++) { W().frame(1); top = Math.max(top, y0 - P().y); }
W().tap('attack'); run(40);
T('ST J J K = pole launcher, carries you up, air J follows', started().includes('st_rise') && hitsOf('st_rise').length === 1 && top > 30 && started().includes('st_air'), `${started().join(' ')} rise ${top.toFixed(0)} px dmg ${dm('st_rise')}`);
// I -> J (pressed at once, during the plant) = vault kick
setup('staff', 1, 60, { tall: 90 }); E('window.__wm.follow = 0'); clr(); W().tap('parry'); run(2); W().tap('attack'); run(60);
T('ST I -> J (pressed during the plant) = vault kick', started().includes('st_vkick'), started().join(' '));
setup('staff', 1, 30, { tall: 90 }); E('window.__wm.follow = 30'); clr(); W().tap('parry'); run(12); W().tap('attack'); run(40);
T('ST I -> J at the top hits', hitsOf('st_vkick').length === 1, `${started().join(' ')} ${dm('st_vkick')}`);
setup('staff', 1, 30, { tall: 90 }); E('window.__wm.follow = 30'); clr(); W().tap('parry'); run(3); W().tap('heavy'); run(50);
T('ST I -> K = aerial spin out of the vault, lands both hits of the string', started().includes('st_aspin') && hitsOf('st_aspin').length === 1, `${started().join(' ')} ${dm('st_aspin')}`);
// vault, J, K -- the doc's cycle fits one vault now
setup('staff', 1, 26, { tall: 90 }); E('window.__wm.follow = 26'); clr(); W().tap('parry'); run(4); W().tap('attack'); run(14); W().tap('heavy'); run(60);
T('ST I J K: vault kick + aerial spin both land in one vault', hitsOf('st_vkick').length === 1 && hitsOf('st_aspin').length === 1, `${started().join(' ')} | ${W().log.map(h => h.st).join(' ')}`);
// air J J = cartwheel (2 hits, the first behind)
setup('staff', 1, 24, { tall: 90 }); E('window.__wm.follow = 24'); clr(); jumpHi(); W().tap('attack'); run(6); W().tap('attack'); W().up('jump'); run(50);
T('ST air J J = cartwheel', started().includes('st_air2') && hitsOf('st_air2').length >= 1, `${started().join(' ')} ${dm('st_air2')}`);
setup('staff', 1, -22, { tall: 90 }); E('window.__wm.follow = -22'); clr(); jumpHi(); W().tap('attack'); run(6); W().tap('attack'); W().up('jump'); run(50);
T('ST cartwheel hits behind', hitsOf('st_air2').length >= 1, dm('st_air2'));
// dive kick -> K = pole drop (II): off the dive kick's bounce on a foe's head; at I the K is the aerial spin
const pdrop = (rank, far) => { setup('staff', rank, 0, { tall: 44 }); E('window.__wm.follow = 0'); clr(); jumpHi(); W().up('jump'); for (let i = 0; i < 60 && P().vy < 40; i++) W().frame(1); tapDown('attack'); run(3); W().tap('heavy'); run(8); if (far !== undefined) E(`enemies.find(e => e.wmDummy).x = P.x + ${far}; window.__wm.follow = ${far}`); run(80); };
pdrop(2); const pd2 = started().join(' '), pdh = dm('st_pdrop');
pdrop(1); const pd1 = started().join(' ');
T('ST II: dive kick -> K = pole drop (I: the aerial spin)', pd2.includes('st_down st_pdrop') && !pd1.includes('st_pdrop'), `${pd2} / ${pd1}`);
pdrop(2, 26); T('ST pole drop: a shock on landing hits a foe beside you', hitsOf('st_pdrop').length === 1, dm('st_pdrop'));
pdrop(2, -26); T('ST pole drop hits behind too', hitsOf('st_pdrop').length === 1, dm('st_pdrop'));
setup('staff', 2, 0, { tall: 30 }); E('window.__wm.follow = 0'); clr(); W().down('jump'); run(14); W().up('jump'); for (let i = 0; i < 60 && P().vy < 40; i++) W().frame(1); E('mvStart("st_pdrop")'); const bnc = []; for (let i = 0; i < 40; i++) { W().frame(1); bnc.push(Math.round(P().vy)); }
T('ST pole drop on a head bounces off it', hitsOf('st_pdrop').length === 1 && bnc.some(v => v < -100), dm('st_pdrop'));
// aerial spin -> K from a vault at III (the glide makes room for it)
setup('staff', 3, 26, { tall: 90 }); E('window.__wm.follow = 26'); clr(); W().tap('parry'); run(3); W().tap('heavy'); run(10); W().tap('heavy'); run(70);
T('ST III: I -> K -> K, the spin finisher lands from a vault', hitsOf('st_aspin2').length === 1, `${started().join(' ')} ${dm('st_aspin2')}`);
// dive kick refund: once per trip
setup('staff', 1, 0, { tall: 60 }); E('window.__wm.follow = 0'); clr(); jumpHi(); W().up('jump');
let kicks = 0; for (let i = 0; i < 400 && !P().ground; i++) { if (!E('!!ATK[P.state]') && P().vy > 20) { tapDown('attack'); } else W().frame(1); }
kicks = hitsOf('st_down').length;
T('ST dive kick pogo: the refund works once per trip (no endless pogo)', kicks >= 2 && kicks <= 3, `${kicks} kicks then landed`);
// spin: flat 24 stamina
setup('staff'); E('D.maxSt = 142; P.st = 142'); const s0 = P().st; W().tap('heavy'); run(2); const sc = s0 - P().st; run(50);
T('ST spin costs a flat 24 (was 30% of the bar)', Math.abs(sc - 24) < 0.5, sc.toFixed(1));
// double vault (IV): cancels an air move once its hit is out
setup('staff', 4, 20, { tall: 40 }); E('window.__wm.follow = 20'); clr(); jumpHi(); W().tap('attack'); run(10); W().tap('parry'); W().up('jump'); run(4); const dv = st(), dvN = E('P.airN'); run(60);
T('ST IV: I during an air move (near a foe) = double vault, air attacks refunded', dv === 'vault' && dvN === 0, `${dv} airN ${dvN}`);
// gale (V): 3 hits on a foe standing in front at 30 and 50 px
for (const d of [30, 50]) { setup('staff', 5, d); E('P.mom = 3'); clr(); W().tap('heavy'); run(90); T(`ST V gale: 3 hits on a foe at ${d} px`, W().log.length === 3, W().log.map(h => (h.dmg / G.D.light).toFixed(2)).join(' ')); }
// mash J (staff) stops at the finisher
setup('staff'); clr(); for (let i = 0; i < 9; i++) { W().tap('attack'); run(5); } run(80);
T('ST mash J x9 = one chain', started().join(' ') === 'st_1 st_2 st_3 st_4', started().join(' '));
// ================================================================ WHIP
// J J K = trip lash, tipped trips a small foe
setup('whip', 1, 70, { breakStance: null }); E(`(() => { const d = enemies.find(e => e.wmDummy); d.bs = 0; d.breakStance = () => { d.bs++; }; window.__wm.follow = 70; })()`); clr();
W().tap('attack'); run(8); W().tap('attack'); run(8); W().tap('heavy'); run(60);
T('WH J J K = trip lash, a tip hit trips a small foe', started().includes('wh_trip') && hitsOf('wh_trip').length === 1 && E('enemies.find(e => e.wmDummy).bs') === 1, `${started().join(' ')} ${dm('wh_trip')}`);
setup('whip', 1, 70); E('window.__wm.follow = 70; P.crack = 100'); clr(); W().tap('attack'); run(8); W().tap('attack'); run(8); W().tap('heavy'); run(60);
T('WH J J K at 100 crack = thunderclap (not the trip lash)', started().includes('wh_thunder') && !started().includes('wh_trip'), started().join(' '));
// L -> K = coil spin, shoves a close small foe out to the tip
setup('whip', 1, 96); clr(); W().tap('roll'); run(14); const dx0 = E('enemies.find(e => e.wmDummy).x - P.x'); W().tap('heavy'); run(50); const dx1 = E('enemies.find(e => e.wmDummy).x - P.x');
T('WH L -> K = coil spin, the close foe ends up at the tip', started().includes('wh_coil') && hitsOf('wh_coil').length === 2 && Math.abs(dx1) > 60, `${started().join(' ')} ${dm('wh_coil')} dist ${dx0.toFixed(0)} -> ${dx1.toFixed(0)}`);
setup('whip', 1, 52); clr(); W().tap('roll'); run(14); W().tap('heavy'); run(50);
T('WH coil spin hits behind', hitsOf('wh_coil').length >= 1, dm('wh_coil'));
// air J J = skyfall crack, hits a grounded foe ahead from the air
setup('whip', 1, 60, { tall: 40 }); clr(); jumpHi(); W().tap('attack'); run(8); W().tap('attack'); W().up('jump'); run(50);
T('WH air J J = skyfall crack, reaches a grounded foe ahead', started().includes('wh_air2') && hitsOf('wh_air2').length === 1, `${started().join(' ')} ${dm('wh_air2')}`);
// grapple -> J = reel kick (II); not at I
setup('whip', 2, 50); clr(); W().tap('parry'); run(12); W().tap('attack'); run(50); const rkDist = E('enemies.find(e => e.wmDummy).x - P.x');
T('WH II grapple -> J (pressed in the grapple) = reel kick, foe kicked out to the tip', started().includes('wh_reelkick') && hitsOf('wh_reelkick').length === 1 && rkDist > 56, `${started().join(' ')} dist ${rkDist.toFixed(0)}`);
setup('whip', 1, 50); clr(); W().tap('parry'); run(12); W().tap('attack'); run(50);
T('WH rank I: grapple -> J is a plain lash', !started().includes('wh_reelkick'), started().join(' '));
setup('whip', 3, 50); clr(); W().tap('parry'); run(10); W().tap('heavy'); run(50);
T('WH III grapple -> K (pressed in the grapple) = slam', started().includes('wh_slam'), started().join(' '));
setup('whip', 2, 50, { half: 18, tall: 50 }); clr(); W().tap('parry'); run(6); W().tap('attack'); run(60);
T('WH II zip to a large foe + J on the way = reel kick on arrival', started().includes('wh_reelkick'), started().join(' '));
// thousand lashes: hold J >= 240 ms (V); a mash never triggers it
setup('whip', 5, 70); clr(); W().down('attack'); run(17); W().up('attack'); run(70);
T('WH V hold J 280 ms = thousand lashes', started().includes('wh_thousand'), started().join(' '));
setup('whip', 5, 70); clr(); W().down('attack'); run(24); W().up('attack'); run(70);
T('WH V hold J 400 ms = thousand lashes', started().includes('wh_thousand'), started().join(' '));
let mashBad = 0; for (const [tap, gap] of [[2, 4], [3, 4], [3, 6], [4, 5], [5, 3], [6, 6], [8, 4]]) { setup('whip', 5, 70); clr(); for (let i = 0; i < 10; i++) { W().down('attack'); run(tap); W().up('attack'); run(gap); } run(80); if (started().includes('wh_thousand')) mashBad++; }
T('WH V mashing J never triggers thousand lashes (7 mash rhythms)', mashBad === 0, `${mashBad} rhythms triggered it`);
let mashK = 0; for (const [tap, gap] of [[2, 4], [3, 6], [5, 3], [6, 6], [8, 4]]) { setup('whip', 4, 70); clr(); for (let i = 0; i < 8; i++) { W().down('heavy'); run(tap); W().up('heavy'); run(gap); } run(80); if (started().includes('wh_overhead_hold')) mashK++; }
T('WH mashing K never starts the overhead charge', mashK === 0, `${mashK} rhythms`);
setup('whip', 1, 70); clr(); W().down('heavy'); run(40); W().up('heavy'); run(60);
T('WH hold K 660 ms = overhead crack', started().includes('wh_overhead'), started().join(' '));
// tip zone: last 30%
const tipAt = d => { setup('whip', 1, d); W().tap('attack'); run(30); const h = W().log[0]; return h ? +(h.dmg / G.D.light).toFixed(2) : 0; };
const t66 = tipAt(66), t60 = tipAt(60);
T('WH tip zone = last 30% of the reach (near edge >= 56 px)', t66 > 1 && t60 < 0.9, `foe centre at 66: ${t66}, at 60: ${t60}`);
// thunderclap: 2.5 close, 3.25 at the tip; crack +20 per tipped heavy
setup('whip', 1, 20); E('P.crack = 100'); clr(); W().tap('heavy'); run(50); const thc = W().log[0] && W().log[0].dmg / G.D.light;
setup('whip', 1, 70); E('P.crack = 100'); clr(); W().tap('heavy'); run(50); const tht = W().log[0] && W().log[0].dmg / G.D.light;
T('WH thunderclap 2.5 close / 3.25 at the tip', Math.abs(thc - 2.5) < 0.05 && Math.abs(tht - 3.25) < 0.05, `${thc && thc.toFixed(2)} / ${tht && tht.toFixed(2)}`);
setup('whip', 1, 70); E('window.__wm.follow = 70'); W().tap('heavy'); run(50); T('WH a tipped heavy fills 20 crack', E('P.crack') === 20, String(E('P.crack')));
// grapple: a short stagger, not a lock
setup('whip', 1, 50); const gs = E(`(() => { const d = enemies.find(e => e.wmDummy); d.breakStance = function () { this.state = 'stagger'; this.t = 1.8; }; return 1; })()`); W().tap('parry'); run(3); const stT = E('enemies.find(e => e.wmDummy).t');
T('WH grapple: the pulled foe staggers 0.6 s (was 1.8: a perma-lock every 2 s)', Math.abs(stT - 0.6) < 0.05, String(stT));
// snap counter: a mash of I can't keep it armed; costs stamina without a grapple
setup('whip', 2, 40); E('P.whCd = 99; P.st = 100'); { let armed = 0; for (let i = 0; i < 120; i++) { if (i % 6 === 0) W().tap('parry'); else W().frame(1); if (E('P.snapT > 0')) armed++; } T('WH II snap: mashing I keeps it armed <= 35% of the time', armed / 120 <= 0.35, (armed / 120).toFixed(2)); }
setup('whip', 2, 40); E('P.whCd = 99'); W().tap('parry'); run(3); const sn0 = P().hp; E(`hurtPlayer(30, -1, 'snapA', { src: enemies.find(e => e.wmDummy) })`); W().frame(1);
T('WH II snap still negates a hit inside 150 ms (no grapple)', P().hp === sn0 && st() === 'wh_snap', `${sn0 - P().hp} ${st()}`);
// the lash extension draws (no errors) during a lash
setup('whip', 1, 70); W().tap('attack'); run(10); E('render()'); T('WH lash extension renders', true);

// ================================================================ v14c J/K mixes
// staff J K = back vault: kicks the foe in front, flips you back and up (+1 momentum: the hit is airborne)
setup('staff', 1, 24, { tall: 40 }); E('P.x = 220; enemies.find(e => e.wmDummy).x = 244'); clr(); { W().tap('attack'); run(6); W().tap('heavy'); for (let i = 0; i < 40 && st() !== 'st_bvault'; i++) W().frame(1); const x0 = P().x; let top = 0; for (let i = 0; i < 60; i++) { W().frame(1); top = Math.max(top, 304 - P().y); } run(40);
T('ST J K = back vault: hits, flips back and up, +1 momentum', started().includes('st_bvault') && hitsOf('st_bvault').length === 1 && P().x < x0 - 20 && top > 25 && W().log.length >= 2, `${started().join(' ')} ${dm('st_bvault')} dx ${(P().x - x0).toFixed(0)} up ${top.toFixed(0)}`); }
setup('staff', 1, 24, { tall: 40 }); clr(); W().tap('attack'); run(6); W().tap('heavy'); for (let i = 0; i < 40 && st() !== 'st_bvault'; i++) W().frame(1); run(14); const bvMom = E('P.mom'); run(60);
T('ST back vault builds a momentum stack', bvMom === 1, String(bvMom));
// staff K -> J = spin vault (J pressed early in the spin is kept)
setup('staff', 1, 30, { tall: 40 }); E('window.__wm.follow = 30'); clr(); { const x0 = P().x; W().tap('heavy'); run(8); W().tap('attack'); run(90);
T('ST K -> J = spin vault: hop over, chop from above', started().join(' ') === 'st_heavy st_svault' && hitsOf('st_svault').length === 1, `${started().join(' ')} ${dm('st_svault')} dx ${(P().x - x0).toFixed(0)}`); }
setup('staff', 1, 30, { tall: 40 }); clr(); W().tap('heavy'); run(70); W().tap('attack'); run(60);
T('ST K, then J well after the spin = a plain strike', started().join(' ') === 'st_heavy st_1', started().join(' '));
// staff air K -> J = comet: spends momentum on the impact
const comet = (mom) => { setup('staff', 1, 40, { tall: 40 }); clr(); W().down('jump'); run(10); W().tap('heavy'); run(6); W().tap('attack'); W().up('jump'); E('P.mom = ' + mom + '; P.momLand = null'); run(80); };
comet(0); const c0 = dm('st_comet'), cs0 = started().join(' ');
comet(3); const c3 = dm('st_comet'), cm3 = E('P.mom');
T('ST air K -> J = comet, x1.75 with 3 stacks spent', cs0.includes('st_aspin st_comet') && +c0 > 1 && Math.abs(+c3 / +c0 - 1.75) < 0.03 && cm3 <= 1, `${cs0} | ${c0} -> ${c3}, mom after ${cm3} (a bounce off the foe may build 1)`);
setup('staff', 1, 200); clr(); { W().down('jump'); run(14); W().up('jump'); run(4); E('mvStart("st_comet")'); const x0 = P().x; for (let i = 0; i < 80 && st() === 'st_comet'; i++) W().frame(1); T('ST comet dives at most ~64 px forward', P().x - x0 <= 68, (P().x - x0).toFixed(0)); }
// whip J K = tip flick: tip only, +15 crack
setup('whip', 1, 70); E('window.__wm.follow = 70'); clr(); W().tap('attack'); run(8); W().tap('heavy'); run(40);
T('WH J K = tip flick: tipped, fills 10 + 15 crack', started().join(' ') === 'wh_1 wh_flick' && hitsOf('wh_flick').length === 1 && E('P.crack') === 25, `${started().join(' ')} ${dm('wh_flick')} crack ${E('P.crack')}`);
setup('whip', 1, 40); E('window.__wm.follow = 40'); clr(); W().tap('attack'); run(8); W().tap('heavy'); run(40);
T('WH tip flick misses entirely off the tip', started().includes('wh_flick') && hitsOf('wh_flick').length === 0, dm('wh_flick'));
setup('whip', 1, 70); E('window.__wm.follow = 70; P.crack = 100'); clr(); W().tap('attack'); run(8); W().tap('heavy'); run(50);
T('WH J K at 100 crack = thunderclap', started().includes('wh_thunder'), started().join(' '));
setup('whip', 1, 70); clr(); W().tap('attack'); run(8); W().tap('heavy'); run(8); W().tap('attack'); run(40);
T('WH J K J = flick then Lash II', started().join(' ') === 'wh_1 wh_flick wh_2', started().join(' '));
// whip K -> J = wrench: drags a small foe in, staggers it; a boss takes the poise
setup('whip', 1, 70); E(`(() => { const d = enemies.find(e => e.wmDummy); d.breakStance = function () { this.state = 'stagger'; this.t = 1.8; }; })()`); clr(); W().tap('heavy'); run(14); W().tap('attack'); run(60); const wd = E('enemies.find(e => e.wmDummy).x - P.x');
T('WH K -> J = wrench: the tipped foe is dragged in to ~30 px, staggered 0.5 s', started().join(' ') === 'wh_heavy wh_wrench' && hitsOf('wh_wrench').length === 1 && wd < 36, `${started().join(' ')} ${dm('wh_wrench')} dist ${wd.toFixed(0)}`);
setup('whip', 1, 78, { boss: true }); E('enemies.find(e => e.wmDummy).boss = true'); clr(); W().tap('heavy'); run(14); W().tap('attack'); run(60);
T('WH wrench on a boss: no drag, the poise lands', hitsOf('wh_wrench').length === 1 && Math.abs(E('enemies.find(e => e.wmDummy).x - P.x') - 78) < 2 && hitsOf('wh_wrench')[0].poise >= 39, `poise ${hitsOf('wh_wrench')[0] && hitsOf('wh_wrench')[0].poise.toFixed(0)}`);
// whip J J J K = cyclone (II): a tip ahead and behind; rank I = heavy
setup('whip', 2, 70); clr(); E(`window.__wm.follow = 0; window.__wm.d2 = enemies.find(e => e.wmDummy)`); W().tap('attack'); run(8); W().tap('attack'); run(8); W().tap('attack'); run(8); W().tap('heavy'); for (let i = 0; i < 30 && st() !== 'wh_cyclone'; i++) W().frame(1); E('enemies.find(e => e.wmDummy).x = P.x - P.face * 70'); W().log = []; run(60);
T('WH II J J J K = cyclone: tipped behind (the back lash has a tip)', started().includes('wh_cyclone') && hitsOf('wh_cyclone').length === 2 && hitsOf('wh_cyclone').every(h => h.dmg / G.D.light > 1), `${started().join(' ')} ${dm('wh_cyclone')}`);
setup('whip', 1, 70); clr(); W().tap('attack'); run(8); W().tap('attack'); run(8); W().tap('attack'); for (let i = 0; i < 90 && !(st() === 'wh_3' && E('ATK.wh_3.mv.total - P.mvT') < 100); i++) W().frame(1); W().tap('heavy'); run(80);
T('WH rank I: J J J (late K) = whirl then heavy crack', !started().includes('wh_cyclone') && started().includes('wh_heavy'), started().join(' '));
setup('whip', 4, 70); clr(); W().tap('heavy'); run(10); W().tap('heavy'); run(60);
T('WH IV: K K is still the double crack', started().join(' ') === 'wh_heavy wh_double', started().join(' '));
return { pass: R.filter(r => r.startsWith('OK')).length, n: R.length, R };

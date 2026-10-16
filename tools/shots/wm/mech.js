// each type's mechanic, rank gating, the input buffer, roll-cancel / commit, mastery XP calls, WEAPON_UNLOCKS
const R = [];
const T = (name, pass, detail = '') => R.push(`${pass ? 'OK ' : 'BAD'} ${name}${detail ? '  [' + detail + ']' : ''}`);
const P = () => G.P;
let hid = 0;
const hurt = (dmg, o = {}) => E(`(() => { const d = enemies.find(e => e.wmDummy); return hurtPlayer(${dmg}, ${o.dir ?? -1}, 'mh${++hid}${o.same ? '' : ''}', { src: d, parryable: ${!!o.parryable} }); })()`);
const hurtId = (dmg, id) => E(`(() => { const d = enemies.find(e => e.wmDummy); return hurtPlayer(${dmg}, -1, '${id}', { src: d }); })()`);
const setup = (type, rank = 1, far = 26, o = {}) => { W().reset(type, rank); arena(); W().reset(type, rank); E('P.lastHit = null'); W().dummy(far, o); };
const st = () => G.P.state, mvT = () => E('P.mvT');
const untilState = (s, max = 120) => { for (let i = 0; i < max && st() !== s; i++) W().frame(1); return st() === s; };
// ---- universal rules
setup('longsword');
E("setP('hurt', 'hurt')"); W().frame(10); W().tap('attack'); for (let i = 0; i < 30 && st() === 'hurt'; i++) W().frame(1); W().frame(1);
T('buffer: J pressed 150 ms before you can act is played', st() === 'attack1' || E("MV.last") === 'attack1' || W().log.length > 0, 'state ' + st());
setup('longsword'); E("setP('hurt', 'hurt'); P.anim.speed = 0.6"); W().tap('attack'); W().frame(13); E("setP('idle','idle',true)"); W().frame(2);
T('buffer: a press older than 180 ms is dropped', st() === 'idle' || st() === 'run', 'state ' + st());
setup('longsword'); W().tap('attack'); W().frame(4); W().tap('roll'); W().frame(2);
T('roll-cancel: not before the hit lands', st() === 'attack1', st());
setup('longsword'); W().tap('attack'); W().frame(11); W().tap('roll'); W().frame(1);
T('roll-cancel: L after the hit cancels into the roll', st() === 'roll', st());
setup('longsword'); E("mvStart('attack4')"); W().frame(22); W().tap('roll'); W().frame(1);
T('commit: the critical slash cannot be roll-cancelled', st() === 'attack4', st());
// ---- Longsword
setup('longsword'); W().tap('parry'); W().frame(2); const g0 = E('MV.gains || 0'); hurt(30, { parryable: true }); const parried = E('P.parried'); W().tap('attack'); W().frame(14);
T('LS: parry -> riposte (I -> J) and a mastery call', parried && st() === 'ls_riposte' && E('MV.gains') > g0, `parried ${parried} state ${st()} gains ${E('MV.gains') - g0} last ${E('MV.lastGain')}`);
setup('longsword', 1); W().down('right'); W().tap('roll'); W().up('right'); W().frame(2); W().tap('attack'); W().frame(30);
T('LS rank gate: L forward -> J is the quick slash below rank II', E('MV.last') === 'ls_quick', E('MV.last'));
setup('longsword', 3); W().tap('parry'); W().frame(3); W().tap('heavy'); W().frame(2); const fs = st(); const hp0 = P().hp; W().frame(3); hurt(40); W().frame(1);
T('LS III: I -> K foresight stance negates a blow and answers with the 2.8 cut', fs === 'ls_fore' && P().hp === hp0 && st() === 'ls_fore_cut', `${fs} hp ${hp0}->${P().hp} ${st()}`);
setup('longsword', 1); W().tap('parry'); W().frame(3); W().tap('heavy'); W().frame(2);
T('LS rank gate: no foresight below rank III', st() !== 'ls_fore', st());
setup('longsword', 5); E('window.__wm.follow = 26');
W().tap('attack'); W().frame(6); W().tap('attack'); W().frame(20); W().tap('attack'); untilState('attack3'); for (let i = 0; i < 40 && E('P.mvT') < 330; i++) W().frame(1); W().tap('attack'); W().frame(70);
const ember = W().log.filter(h => h.st === 'attack4').map(h => (h.dmg / h.light).toFixed(2));
T('LS V: ember edge -- a perfectly timed 4th J adds a burning 1.2 hit', ember.length === 2 && Math.abs(ember[1] - 1.2) < 0.12, ember.join('/'));
// ---- Katana
setup('katana', 1); E('P.sheathed = true'); W().down('right'); W().frame(40); const v1 = Math.abs(P().vx); W().up('right'); W().frame(20);
setup('katana', 2); E('P.sheathed = true'); W().down('right'); W().frame(40); const v2 = Math.abs(P().vx); W().up('right');
T('KT: sheathed walk at 70% (II: full speed)', Math.abs(v1 / 122 - 0.7) < 0.05 && Math.abs(v2 / 122 - 1) < 0.05, `${(v1 / 122).toFixed(2)} / ${(v2 / 122).toFixed(2)}`);
setup('katana', 1); E('P.sheathed = true'); W().tap('parry'); W().frame(4); const hk0 = P().hp, gk = E('MV.gains || 0'); hurt(30, { parryable: true }); W().frame(1);
T('KT: Iai parry (I sheathed, parryable hit in the 150 ms window) negates and counter-cuts', P().hp === hk0 && st() === 'kt_iaicut' && E('MV.gains') > gk, `hp ${hk0}->${P().hp} ${st()}`);
// v15 (balance): a blow that can't be parried is only turned aside: stamina like a shield block, no counter-cut
setup('katana', 1); E('P.sheathed = true'); W().tap('parry'); W().frame(4); const hk2 = P().hp, ks2 = P().st, gk2 = E('MV.gains || 0'); hurt(30); const kst2 = st(); W().frame(1);
T('KT v15: an unparryable blow in the Iai window is deflected for stamina, no counter-cut', P().hp === hk2 && kst2 !== 'kt_iaicut' && Math.abs(ks2 - P().st - (6 + 30 * 0.8) * E('mvGuardScale()')) < 1.5 && E('MV.gains || 0') === gk2, `hp ${hk2}->${P().hp} ${kst2} stam ${(ks2 - P().st).toFixed(1)}`);
setup('katana', 1); E('P.sheathed = true'); W().tap('parry'); W().frame(12); const hk1 = P().hp; hurt(30); W().frame(1);
T('KT: a blow after the 150 ms window is not parried', P().hp < hk1, `hp ${hk1}->${P().hp}`);
setup('katana', 5); E('window.__wm.follow = 26; P.sheathed = true'); W().tap('parry'); W().frame(2); hurt(30, { parryable: true }); W().frame(60); /* v14: K is only kept in a finisher's last 120 ms */ const ml = E('P.moonlit');
E('P.sheathed = true'); E("window.__wm.log = []"); W().tap('heavy'); W().frame(30); const mi = W().log.filter(h => h.st === 'kt_iai').map(h => (h.dmg / h.light).toFixed(2));
T('KT V: a perfect Iai parry readies the moonlit Iai (3.0)', ml && mi.length && Math.abs(mi[0] - 3.0) < 0.15, `moonlit ${ml} iai ${mi}`);
setup('katana', 1); W().tap('roll'); W().frame(8); const hs0 = P().hp; hurt(20); const hs1 = P().hp; W().frame(30); W().tap('roll'); W().frame(13); hurt(20);
T('KT: sidestep invulnerable 0.16 s, not after', hs1 === hs0 && P().hp < hs1, `${hs0}->${hs1}->${P().hp}`);
setup('katana', 4); E('window.__wm.follow = 26'); W().tap('attack'); W().frame(6); W().tap('attack'); W().frame(6); W().tap('attack'); untilState('kt_3'); W().frame(4); W().tap('parry'); W().frame(80);
const echo = W().log.filter(h => h.melee).map(h => (h.dmg / h.light).toFixed(2));
T('KT IV: thousand cuts -- each flurry hit echoes (+0.3 x3)', echo.filter(x => Math.abs(x - 0.3) < 0.03).length === 3 && E('P.sheathed'), echo.join('/'));
// ---- Greatsword
setup('greatsword'); W().down('heavy'); W().frame(20); const gh0 = P().hp; hurt(Math.round(E('D.maxHp') * 0.2)); const gst = st(); const gdl = gh0 - P().hp; W().up('heavy'); W().frame(60);
T('GS: charging is flinch-proof under 30% max HP, damage x0.7 (v15, was x0.8)', gst === 'gs_charge' && Math.abs(gdl / (E('D.maxHp') * 0.2) - 0.7) < 0.06, `${gst} took ${gdl}`);
setup('greatsword'); W().down('heavy'); W().frame(20); hurt(Math.round(E('D.maxHp') * 0.4)); const gst2 = st(); W().up('heavy'); W().frame(60);
T('GS: a blow over 30% max HP still flinches the charge', gst2 === 'hurt', gst2);
setup('greatsword'); W().down('parry'); W().frame(4); const gb0 = P().hp, gs0 = P().st; hurt(40); const gbl = gb0 - P().hp, gsl = gs0 - P().st; W().up('parry'); W().frame(10);
T('GS: blade guard -- 1.2 x dmg stamina (x v15 guard scale), 25% chip', Math.abs(gsl - 48 * E('mvGuardScale()')) < 2 && Math.abs(gbl - 10) <= 1, `stam ${gsl.toFixed(1)} chip ${gbl}`);
setup('greatsword', 2); W().down('heavy'); W().frame(36); W().tap('roll'); W().frame(2); const tk = st(); W().frame(30); const back = st(), bank = E('P.gsMs'); W().up('heavy'); W().frame(60);
T('GS II: shoulder tackle out of a charge keeps the charge', tk === 'gs_tackle' && back === 'gs_charge' && bank > 600, `${tk} -> ${back} ${Math.round(bank)} ms`);
setup('greatsword', 1); W().down('heavy'); W().frame(36); W().tap('roll'); W().frame(2); const tk1 = st(); W().up('heavy'); W().frame(60);
T('GS rank gate: L while charging rolls (drops the charge) below II', tk1 === 'roll', tk1);
setup('greatsword', 4); W().down('parry'); W().frame(4); W().tap('heavy'); W().frame(2); const gt = st(); W().down('heavy'); W().frame(25); const gtb = E('P.gsMs'); W().up('heavy'); W().up('parry'); W().frame(60);
T('GS IV: guard tackle -> a level 2 charge', gt === 'gs_tackle' && gtb >= 400, `${gt} bank ${Math.round(gtb)}`);
// ---- Maul
setup('maul'); W().tap('parry'); W().frame(3); const mb0 = P().hp, ms0 = P().st; hurt(40); W().frame(1);
T('ML: brace -- the blow lands at 50% and cannot flinch you (15 + 0.5 x dmg stamina)', st() === 'brace' && mb0 - P().hp === 20 && Math.abs(ms0 - P().st - 20) < 1.5, `${st()} hp -${mb0 - P().hp} stam -${(ms0 - P().st).toFixed(1)} (15 paid at raise)`);
setup('maul'); W().down('right'); W().down('heavy'); W().frame(20); const mvx = Math.abs(P().vx); W().up('right'); W().tap('roll'); W().frame(30); const afterRoll = st(); W().up('heavy'); W().frame(60);
T('ML: walk-charge at 60%; the roll releases the charge (rank I)', Math.abs(mvx / 122 - 0.6) < 0.05 && afterRoll !== 'ml_charge', `${(mvx / 122).toFixed(2)} after roll ${afterRoll}`);
setup('maul', 2); W().down('heavy'); W().frame(20); W().tap('roll'); W().frame(32); const ar2 = st(), mb = E('P.mlMs'); W().up('heavy'); W().frame(60);
T('ML II: charge step keeps the charge', ar2 === 'ml_charge' && mb > 300, `${ar2} ${Math.round(mb)} ms`);
setup('maul', 5); W().down('heavy'); W().frame(90); const eq = E('MV.last'); W().up('heavy'); W().frame(60);
T('ML V: earthshaker -- level 3 held still for 1.4 s (v14 wave 1.0)', eq === 'ml_quake' && W().log.some(h => Math.abs(h.dmg / h.light - 1.0) < 0.1), eq + ' ' + W().log.map(h => (h.dmg / h.light).toFixed(2)).join('/'));
// ---- Sword & Shield
setup('sns'); W().down('parry'); W().frame(20); const sb0 = P().hp, ss0 = P().st; hurt(30); W().frame(2); W().up('parry');
T('SnS: block -- 6 + 0.8 x dmg stamina (x v15 guard scale), no chip', P().hp === sb0 && Math.abs(ss0 - P().st - 30 * E('mvGuardScale()')) < 1, `hp ${sb0 - P().hp} stam ${(ss0 - P().st).toFixed(1)}`);
setup('sns'); W().tap('parry'); W().frame(8); hurt(30, { parryable: true }); const sp1 = E('P.parried');
setup('sns'); W().tap('parry'); W().frame(12); hurt(30, { parryable: true }); const sp2 = E('P.parried');
T('SnS: parry window 170 ms', sp1 === true && sp2 !== true, `${sp1} ${sp2}`);
setup('sns'); E('P.flasksR = 3; P.hp = 50'); W().down('right'); W().tap('heal'); W().frame(20); const hv = Math.abs(P().vx), hsp = E('P.anim.speed'); W().up('right'); W().frame(60);
T('SnS: flasks with the weapon out -- 30% faster, walking', Math.abs(hsp - 1.3) < 0.01 && hv > 25, `speed ${hsp} vx ${hv.toFixed(0)}`);
setup('sns'); const sx0 = P().x; W().tap('roll'); W().frame(5); const bh0 = P().hp; hurt(20); const bh1 = P().hp; W().frame(30);
T('SnS: backhop goes backwards, 0.14 s invulnerable', P().x < sx0 - 25 && bh1 === bh0, `dx ${(P().x - sx0).toFixed(0)}`);
setup('sns', 5); E('window.__wm.follow = 26'); W().down('parry'); W().frame(2); const pg0 = P().st; hurt(30); W().frame(2); const pgc = pg0 - P().st, bonus = E('P.counterBonus'); W().up('parry'); W().frame(2); E('window.__wm.log = []'); W().tap('attack'); W().frame(30);
const pgd = W().log.filter(h => h.st === 'sh_counter').map(h => (h.dmg / h.light).toFixed(2));
T('SnS V: perfect guard -- no stamina, the next counter +50%', pgc < 0.5 && bonus === 1.5 && pgd.length && Math.abs(pgd[0] - 2.85) < 0.15, `stam ${pgc} counter ${pgd}`);
// ---- Dual Blades
setup('dual'); E('P.st = 80'); W().tap('parry'); W().frame(60); const dd = 80 - P().st;
T('DB: Demon Mode drains 12 stamina/s, no regeneration', E('P.demon') && Math.abs(dd - 12) < 1.5, dd.toFixed(1));
setup('dual', 4); E('P.st = 80'); W().tap('parry'); W().frame(60); const dd4 = 80 - P().st;
T('DB IV: iron lungs -- 8/s', Math.abs(dd4 - 8) < 1.2, dd4.toFixed(1));
setup('dual'); E('P.st = 5'); W().tap('parry'); W().frame(40); const ex = E('P.demon'), exT = E('P.exhT'); const s0 = P().st; W().frame(30); const s1 = P().st; W().frame(60);
T('DB: out of stamina drops Demon Mode, exhausted 1.5 s', !ex && exT > 0.5 && s1 - s0 < 0.5 && P().st > s1, `demon ${ex} exh ${exT.toFixed(2)} regen ${(s1 - s0).toFixed(1)} then ${(P().st - s1).toFixed(1)}`);
setup('dual'); E('P.demon = true'); E('window.__wm.follow = 22'); for (let i = 0; i < 6; i++) { W().tap('attack'); W().frame(18); } const gg = E('P.gauge');
T('DB: each hit in Demon Mode fills the gauge 3%', Math.abs(gg / 0.03 - W().log.filter(h => h.melee).length) < 0.5, `gauge ${(gg * 100).toFixed(0)}% hits ${W().log.filter(h => h.melee).length}`);
setup('dual'); E('P.demon = true; P.gauge = 0.99; P.st = 999'); E('window.__wm.follow = 22'); W().tap('attack'); W().frame(20); const ar = E('P.arch'); W().frame(60); const gd = E('P.gauge');
T('DB: a full gauge = Archdemon; it drains 5%/s', ar && Math.abs((1 - gd) - 0.05 * 80 / 60) < 0.02, `arch ${ar} gauge ${gd.toFixed(3)}`);
setup('dual'); E('P.st = 50'); W().tap('roll'); W().frame(4); const g1 = E('MV.gains || 0'); hurtId(20, 'atkA'); const pd = E('P.pdT'), st1 = P().st, sp = E('mvSpeed(ATK.tw_1)');
T('DB: perfect dodge (roll, hit 67 ms in) -- +25 stamina, +0.1 speed for 6 s, mastery call', pd === 6 && Math.abs(st1 - (50 - 16 + 25)) < 1 && Math.abs(sp - 1.1) < 1e-6 && E('MV.gains') > g1, `pdT ${pd} st ${st1} speed ${sp}`);
W().frame(30); W().tap('roll'); W().frame(3); hurtId(20, 'atkA'); const again = E('P.dg && P.dg.perfect');
T('DB: one perfect dodge per enemy attack', !again, String(again));
setup('dual'); W().tap('roll'); W().frame(8); hurtId(20, 'atkB'); const late = E('P.pdT');
T('DB: a roll hit 133 ms in is not perfect (100 ms window)', late === 0, String(late));
setup('dual'); E('P.demon = true; P.st = 60'); W().tap('roll'); W().frame(9); hurtId(20, 'atkC'); const dash = E('P.pdT');
T('DB: a demon dash hit 150 ms in is perfect (175 ms window)', dash === 6, String(dash));
setup('dual'); E('P.st = 60'); W().tap('roll'); W().frame(3); hurtId(10, 'a1'); E('P.pdT = 3'); W().frame(30); W().tap('roll'); W().frame(3); hurtId(10, 'a2'); E('P.demon = true'); const sp2b = E('mvSpeed(ATK.tw_1)'), pd2 = E('P.pdT');
T('DB: the buff refreshes to 6 s, never stacks (+30% max with Demon Mode)', pd2 === 6 && Math.abs(sp2b - 1.3) < 1e-6, `pdT ${pd2} speed ${sp2b}`);
setup('dual'); E('P.st = 60; window.__wm.follow = 20'); W().tap('roll'); W().frame(3); hurtId(10, 'a3'); W().tap('attack'); W().frame(2); const cf = st(); W().frame(30);
T('DB: L (perfect) -> J = counter flurry, at once', cf === 'tw_cflurry', cf);
// ---- Spear
setup('spear'); W().down('parry'); W().frame(10); const pb0 = P().hp, ps0 = P().st, px0 = P().x; hurt(Math.round(E('D.maxHp') * 0.4)); W().frame(14); const chip = pb0 - P().hp, pst = ps0 - P().st, push = px0 - P().x;
T('SP: heavy guard -- 5 + 0.5 x dmg (x v15 guard scale), big hits chip 10%, hard pushback', Math.abs(pst - (5 + 0.5 * E('D.maxHp') * 0.4) * E('mvGuardScale()')) < 1.5 && Math.abs(chip - E('D.maxHp') * 0.04) <= 1 && push > 6, `stam ${pst.toFixed(1)} chip ${chip} push ${push.toFixed(1)}`);
W().down('right'); W().frame(20); const gw = Math.abs(P().vx); W().up('right'); W().up('parry');
T('SP: walk slowly while guarding', gw > 20 && gw < 60 && (st() === 'guard' || st() === 'block'), `${gw.toFixed(0)} ${st()}`);
setup('spear', 4); W().down('parry'); W().frame(10); W().tap('heavy'); W().frame(2); const pp0 = P().hp, px1 = P().x; hurt(Math.round(E('D.maxHp') * 0.4)); W().frame(6);
T('SP IV: power guard -- no pushback, no chip', P().hp === pp0 && Math.abs(P().x - px1) < 1, `chip ${pp0 - P().hp} push ${(px1 - P().x).toFixed(1)}`); W().up('parry');
setup('spear', 1); let hops = 0; for (let i = 0; i < 3; i++) { W().tap('roll'); W().frame(10); } hops = E('(P.dg && P.dg.n) || 0');
const n1 = W(); setup('spear', 1); W().tap('roll'); W().frame(10); W().tap('roll'); W().frame(10); W().tap('roll'); W().frame(2); const third1 = E('P.dg ? P.dg.n : 0');
setup('spear', 2); W().tap('roll'); W().frame(10); W().tap('roll'); W().frame(10); W().tap('roll'); W().frame(2); const third2 = E('P.dg ? P.dg.n : 0');
T('SP: hops chain 2 (II: 3)', third1 !== 3 && third2 === 3, `${third1} / ${third2}`);
setup('spear'); E('P.st = 100; window.__wm.follow = 34'); W().down('right'); W().down('heavy'); W().frame(24); const rs0 = P().st; W().frame(60); const rs1 = P().st; W().up('heavy'); W().up('right'); W().frame(40);
T('SP: charge dash -- 400 ms wind-up, then 8 stamina/s while running', Math.abs((rs0 - rs1) - 8) < 1.5, (rs0 - rs1).toFixed(1));
// ---- Staff
setup('staff'); const vy0 = P().y; W().tap('parry'); W().frame(4); const vh0 = P().hp; hurt(20); const vinv = P().hp === vh0; let top = 0; for (let i = 0; i < 40; i++) { W().frame(1); top = Math.max(top, vy0 - P().y); }
T('ST: vault -- invulnerable at first, about 2.2 tiles up, 15 stamina', vinv && top > 28 && top < 46, `inv ${vinv} height ${top.toFixed(0)}`);
setup('staff'); W().tap('parry'); untilState('air', 40); W().tap('attack'); W().frame(3); W().tap('heavy'); W().frame(30); const lockV = E('P.airLock'), airN = E('P.airN'), seqV = E('MV.last');
T('ST: the vault is not an attack -- 2 air attacks after it count 2 (staff limit 5: no lock yet)', !lockV && airN === 2 && seqV === 'st_aspin', `lock ${lockV} n ${airN} last ${seqV}`);
for (let i = 0; i < 120 && !G.P.ground; i++) W().frame(1); W().frame(20);
setup('staff', 1, 0, { tall: 90 }); E('window.__wm.follow = 0'); W().down('jump'); W().frame(4); W().tap('attack'); W().frame(14); W().up('jump'); const m1 = E('P.mom'); W().down('up'); W().tap('attack'); W().up('up'); W().frame(16); const m2 = E('P.mom');
T('ST: each air hit adds a momentum stack (+8%)', m1 === 1 && m2 === 2, `${m1} ${m2}`);
for (let i = 0; i < 120 && !G.P.ground; i++) W().frame(1); W().frame(40); const m3 = E('P.mom');
T('ST: momentum ends 0.5 s after landing', m3 === 0, String(m3));
setup('staff', 1, 0, { tall: 70 }); E('P.mom = 2'); W().tap('jump'); W().frame(6); for (let i = 0; i < 80 && G.P.vy <= 20; i++) W().frame(1); E('P.airN = 1; P.airLock = false'); E('mvStart("st_down")'); const rf0 = E('P.airN'); W().frame(12); const rf = E('P.airN');
T('ST: the dive kick bounce refunds one air attack', rf0 === 2 && rf === 1, `${rf0} -> ${rf}`);
// ---- Whip
setup('whip', 1, 70); E('window.__wm.follow = 70'); W().tap('attack'); W().frame(45); const c1 = E('P.crack'); W().tap('heavy'); W().frame(50); const c2 = E('P.crack');   /* v14c: J K is the tip flick, so K waits out the lash */
T('WH: tip hits fill the crack meter (+10 light, +20 heavy)', c1 === 10 && c2 === 30, `${c1} ${c2}`);
setup('whip', 1, 20); E('window.__wm.follow = 20'); W().tap('attack'); W().frame(30);
T('WH: a close hit (not the tip) adds no crack', E('P.crack') === 0, String(E('P.crack')));
setup('whip', 1, 40); const sm = E(`(() => { const d = enemies.find(e => e.wmDummy); d.breakStance = () => { d.st2 = 1; }; return d.x; })()`); W().tap('parry'); W().frame(20); const smx = E('enemies.find(e => e.wmDummy).x');
T('WH: grapple pulls a small foe to you, stunned', Math.abs(smx - (P().x + 16)) < 4 && E('enemies.find(e => e.wmDummy).st2') === 1, `${sm.toFixed(0)} -> ${smx.toFixed(0)} (player ${P().x.toFixed(0)})`);
W().tap('parry'); W().frame(2); const cdn = st(); W().frame(130); W().tap('parry'); W().frame(2);
T('WH: grapple cooldown 2 s', cdn !== 'grapple' && st() === 'grapple', `${cdn} / ${st()}`);
setup('whip', 1, 50, { half: 18, tall: 50 }); const lx0 = P().x; W().tap('parry'); W().frame(40);
T('WH: grapple on a large foe pulls you in', P().x > lx0 + 20, `${lx0.toFixed(0)} -> ${P().x.toFixed(0)}`);
setup('whip', 1, 50, { boss: true }); E('enemies.find(e => e.wmDummy).boss = true'); const bx0 = P().x, bdx = E('enemies.find(e => e.wmDummy).x'); W().tap('parry'); W().frame(40);
T('WH: the grapple never takes a boss', Math.abs(P().x - bx0) < 4 && E('enemies.find(e => e.wmDummy).x') === bdx, `${(P().x - bx0).toFixed(1)}`);
setup('whip', 2, 40); W().tap('parry'); W().frame(3); const sn0 = P().hp; hurt(30); W().frame(1);
T('WH II: snap counter -- I within 150 ms of a hit negates it', P().hp === sn0 && st() === 'wh_snap', `${sn0 - P().hp} ${st()}`);
setup('whip', 1, 40); W().tap('parry'); W().frame(3); const sn1 = P().hp; hurt(30);
T('WH rank gate: no snap counter below II', P().hp < sn1, `${sn1 - P().hp}`);
// ---- mastery API and unlock lists
const U = E('JSON.stringify(Object.fromEntries(Object.entries(WEAPON_UNLOCKS).map(([k, v]) => [k, v.map(u => u.rank + ":" + u.id)])))');
const UU = JSON.parse(U);
// v15: 14 types registered; the nine must unlock something at every rank II-V (the five v15 skeletons are checked by
// tools/shots/v15/platform/ and their own moveset tests)
const NINE = ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip'];
T('WEAPON_UNLOCKS: every type registered, the nine unlock something at every rank II-V', Object.keys(UU).length === E('WTYPES.length') && NINE.every(t => [2, 3, 4, 5].every(r => (UU[t] || []).some(x => +x[0] === r))), U.slice(0, 200));
E('MV.rank = null'); const rk = E("(SAVE.mastery = SAVE.mastery || {}, SAVE.mastery.longsword = 950, mvRank('longsword'))");
T("rank gating reads WS's masteryRank (950 XP = III)", rk === 3, String(rk));
return { pass: R.filter(r => r.startsWith('OK')).length, n: R.length, R };

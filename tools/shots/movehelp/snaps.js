// MOVEHELP: the combo hint during real combos (run with tools/shots/wm/run.sh), in a real room (C4) with a dummy.
// SHOT_HTML=web/dist/movehelp.html sh tools/shots/wm/run.sh tools/shots/movehelp/snaps.js tools/shots/movehelp/out
// montage: python3 tools/shots/movehelp/montage.py tools/shots/movehelp/out hint_ tools/shots/movehelp/hint_montage.png 3 0.5
const out = [];
const B = { J: 'attack', K: 'heavy', I: 'parry', L: 'roll' };
const until = (cond, max = 90) => { for (let i = 0; i < max; i++) { if (E(cond)) return i; W().frame(1); } return -1; };
const setup = (type, rank = 5) => { W().reset(type, rank); G.tp('C4', 8, 10); W().frame(4); W().reset(type, rank); E("P.face = 1; MH.show = []; MH.alpha = 0; MH.press = -9; MH.ctxT = -9"); W().dummy(34); W().frame(2); };
const shot = async name => { E('areaCard = null; regionCard = null; bannerMsg = null; toasts.length = 0; hitstop = 0; render()'); out.push(name + ': ' + E('MH.head') + ' | ' + E('MH.show.map(c => c.parts.join(".") + " " + c.name).join(" / ")')); await snap('hint_' + name); };
const chain = (keys, last) => { keys.forEach((k, i) => { W().tap(B[k], 2); if (i < keys.length - 1) W().frame(6); }); if (last) until(`P.state === '${last}'`); W().frame(6); };
setup('longsword'); chain(['J', 'J'], 'attack2'); await shot('01_longsword_JJ'); W().frame(90);
setup('longsword'); W().tap('roll', 2); W().frame(5); await shot('02_longsword_roll'); W().frame(90);
setup('katana'); W().tap('parry', 2); until('P.sheathed', 60); W().frame(30); await shot('03_katana_sheathed'); W().frame(90);
setup('dual'); W().tap('parry', 2); until('P.demon', 30); W().frame(20); await shot('04_dual_demon');
W().tap('heavy', 2); until("P.state === 'tw_dflurry'"); W().frame(4); await shot('05_dual_demon_K'); W().frame(120);
setup('fist'); E("P.ftStyle = 'iron'"); chain(['J'], 'ft_palm'); await shot('06_fist_iron_J'); W().frame(90);
setup('spear'); chain(['J', 'J'], 'sp_2'); await shot('07_spear_JJ'); W().frame(90);
setup('greatsword'); chain(['J'], 'gs_1'); await shot('08_greatsword_J'); W().frame(90);
setup('scythe'); chain(['J', 'J'], 'scy_2'); await shot('09_scythe_JJ'); W().frame(90);
setup('bell'); chain(['J', 'J'], 'wb_2'); await shot('10_bell_JJ'); W().frame(90);
setup('saxe'); E('P.sxG = 100; P.sxLock = true'); W().tap('parry', 2); until('P.sxAxe && P.state === "idle"', 120); W().frame(24); await shot('11_saxe_axe'); W().frame(90);
setup('longsword'); W().down('jump'); W().frame(8); W().up('jump'); W().frame(3); await shot('12_longsword_air'); W().frame(90);
setup('maul'); E("(() => { const d = enemies.find(e => e.wmDummy); d.x = P.x + 20; d.state = 'stagger'; d.critable = function () { return this.state === 'stagger'; }; })()"); W().frame(10); await shot('13_maul_fatality');
E("enemies.find(e => e.wmDummy).state = 'idle'"); W().frame(60);
// rebound keys: J -> F, K -> G
E("bindKey('attack', 0, 'KeyF'); bindKey('heavy', 0, 'KeyG')");
setup('longsword'); chain(['J'], 'attack1'); await shot('14_rebound_keys');
E('BINDINGS = defaultBindings(); saveBindings()');
return out;

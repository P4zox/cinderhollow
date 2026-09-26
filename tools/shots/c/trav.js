await boot();
const P = () => G.P, log = {};
const walk = (dir, n) => { for (let i = 0; i < n; i++) G.step(1, [dir]); };
const jump = (dir, n = 30) => { G.step(1, dir ? [dir, 'jump'] : ['jump'], ['jump']); for (let i = 0; i < n; i++) G.step(1, dir ? [dir, 'jump'] : ['jump']); };
const where = () => `${G.room}@${Math.round(P().x)},${Math.round(P().y)}`;
// 1) the veil without Ember Dash
G.SAVE.flags['boss:kalden'] = 1;
G.tp('M5', 30, 10); walk('right', 120); log.m5_to_cm1 = where();
walk('right', 200); log.veil_blocked = where();
G.step(1, ['right'], ['roll']); G.step(40, ['right']); log.veil_roll_no_dash = where();
// 2) with Ember Dash
G.give({ items: { emberdash: 1 } });
G.tp('CM1', 4, 10); G.step(10); G.step(1, ['right'], ['roll']); G.step(30, ['right']); log.veil_roll_dash = where();
G.step(1, ['left'], ['roll']); G.step(30, ['left']); log.veil_back = where();
walk('left', 200); log.cm1_to_m5 = where();
// 3) CM1 -> CM2 and back
G.tp('CM1', 36, 10); walk('right', 120); log.cm1_to_cm2 = where();
G.step(1,['left','jump'],['jump']); walk('left', 200); log.cm2_to_cm1 = where();
// 4) CM2 bottom -> cellars and back
G.tp('CM2', 20, 36); walk('right', 120); log.cm2_to_cm5 = where();
walk('left', 140); log.cm5_to_cm2 = where();
// 5) CM2 climb to the foyer balcony: platforms (34,3..6) (31,8..11) (28,12..15) then balcony 16..22 @27
G.tp('CM2', 5, 33); G.step(10); jump('right', 22); jump('right', 22); jump('right', 30); walk('right', 150); log.climb_foyer = where();
// 6) CM3 foyer -> butler hall (butler felled) and back
G.SAVE.flags['boss:butler'] = 1;
G.tp('CM3', 20, 9); walk('right', 100); log.cm3_to_cm6 = where();
walk('left', 100); log.cm6_to_cm3 = where();
walk('left', 260); log.cm3_to_cm2 = where();
// 7) butler shaft up into the gallery
G.tp('CM6', 27, 9); G.step(5); for (let k = 0; k < 6; k++) jump(null, 30); log.shaft_up = where();
// back down: drop through the platforms
for (let k = 0; k < 6; k++) { G.step(1, ['down', 'jump'], ['jump']); G.step(30, ['down']); } log.shaft_down = where();
// 8) gallery: lever, gate, out onto the court balcony and back
G.tp('CM4', 4, 10); G.step(10); G.step(1, [], ['interact']); G.step(40); log.lever = !!G.SAVE.flags['lever:CM4'];
walk('left', 120); log.gallery_to_court = where();
walk('right', 120); log.court_to_gallery = where();
// 9) gallery -> vestibule shaft
G.tp('CM4', 8, 10); G.step(5); for (let k = 0; k < 6; k++) jump(null, 30); walk('left', 20); log.to_vestibule = where();
// 10) vestibule -> ballroom and back (Countess felled)
G.SAVE.flags['boss:sanguine'] = 1;
G.tp('CM8', 4, 10); walk('right', 160); log.cm8_to_cm7 = where();
walk('left', 160); log.cm7_to_cm8 = where();
return log;

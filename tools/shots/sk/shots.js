// screenshots of the visible keystone / arsenal effects
await boot(); G.giveArmory(); G.grantTechniques();
G.give({ stats: { vig: 30, mnd: 25, end: 25, str: 25, dex: 25, fth: 25 }, shards: 200 });
const E = G.sk.ev;
const arena = (skills, weapon = 'longsword') => { G.SAVE.weapon = weapon; G.SAVE.weapons[weapon] = 3; E(`SAVE.skills = ${JSON.stringify(skills)}; refreshDerived(false)`); G.tp('R2', 3, 10); E('enemies.length = 0; P.cds = {}; P.fp = D.maxFp; P.st = D.maxSt; areaCard = null; bannerMsg = null; P.skRel = 0'); G.step(2); };
const dummy = (dx, hp = 3000) => E(`(() => { const e = makeEnemy('hollow_soldier', P.x + ${dx}, P.y, 'x' + Math.random()); e.maxHp = e.hp = ${hp}; e.update = function (dt) { this.flash = Math.max(0, this.flash - dt * 6); }; enemies.push(e); return enemies.length; })()`);
// Relentless: a stacked combo, HUD readout
arena(['keen_edge', 'fourth_strike', 'charged_arts', 'executioner', 'tireless', 'relentless']); dummy(30);
for (let i = 0; i < 70; i++) G.step(1, [], i % 6 === 0 ? ['attack'] : []);
await snap('relentless');
// Kindled: Bloodstep leaves fire
arena(['ember_focus', 'kindling', 'lingering_flame', 'swift_arts', 'searing_arts', 'kindled'], 'dagger'); dummy(70); dummy(110);
G.SAVE.art = 'bloodstep'; G.step(1, [], ['art']); for (let i = 0; i < 45; i++) { G.step(1); if (E('SKW.trail.length') >= 4) break; } await snap('kindled');
// Shadowstep: step out behind a foe
arena(['quickstep', 'riposte_mastery', 'steadfast', 'second_wind', 'light_feet', 'shadowstep']); dummy(36);
G.step(1, [], ['roll']); G.step(2); E(`runHooks('negated', 30, -1, { src: enemies[0] })`); G.step(3); await snap('shadowstep');
// Crimson Pact: a bleed burst heals
arena(['bloodthirst', 'hemorrhage', 'last_stand', 'frenzy', 'leech', 'crimson_pact'], 'dagger'); dummy(28);
E('P.hp = D.maxHp * 0.5'); for (let i = 0; i < 90; i++) G.step(1, [], i % 6 === 0 ? ['attack'] : []); await snap('crimson_pact');
// Cinder Quake shockwaves
arena(['way_slam']); dummy(90); E("P.y -= 40; P.ground = false; setP('air', 'jump_fall'); startSlam()"); for (let i = 0; i < 60; i++) { G.step(1); if (E('SKW.waves.length') && E('SKW.waves[0].t') > 0.18) break; } await snap('way_slam');
// Earthshaker
arena(['m_great'], 'greatsword'); dummy(90); G.step(1, [], ['heavy']); for (let i = 0; i < 90; i++) { G.step(1); if (E("fx.some(f => f.name === 'shockwave')")) break; } G.step(4); await snap('m_great');
return 'ok';

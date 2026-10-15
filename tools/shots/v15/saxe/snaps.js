// v15 Switch Axe in game: key moments as screenshots (HUD + the two weapon forms + the morph). Plain shot.js script:
//   SHOT_HTML=web/dist/v15_saxe.html node tools/shots/shot.js tools/shots/v15/saxe/snaps.js tools/shots/v15/saxe/out/snaps
// Writes <name>.png plus the player's screen position per shot (montage.py crops them).
await boot(); G.SETTINGS.god = 1;
const E = G.mv.ev, o = [];
G.tp('R2', 6, 10); G.step(40);
E("regionCard = null; enemies.length = 0; wmEquip('saxe', { quiet: true }); MV.rank = 5; P.vx = 0; P.face = 1; sxReset()");
G.step(10);
const pos = () => E('[Math.round((P.x - cam.x) * scale + ox), Math.round((P.y - cam.y) * scale + oy), scale, P.state, P.anim.tag, P.anim.i]');
const shot = async (name, setup, steps = 0, keys = []) => { if (setup) E(setup); if (steps) G.step(steps, keys); await snap(name); o.push(name + ' ' + JSON.stringify(pos())); };
const dummy = "enemies = enemies.filter(e => !e.sxD); enemies.push({ sxD: true, type: 'sx_dummy', alive: true, x: P.x + 34, y: P.y, w: 16, h: 40, ground: true, cfg: {}, face: -1, state: 'idle', hp: 1e9, vx: 0, vy: 0, half: 8, tall: 30, update() {}, draw() {}, hurtbox() { return rect(this.x - 8, this.y - 30, this.x + 8, this.y); }, hit() {} })";
await shot('01_blade_idle_g60', 'P.sxG = 60', 20);
await shot('02_blade_locked', 'P.sxG = 100; P.sxLock = true', 30);
await shot('03_morph_a', "mvStart('sx_morph')", 6);
await shot('04_morph_b', null, 5);
await shot('05_morph_c', null, 5);
await shot('06_morph_hit', null, 4);
await shot('07_axe_idle', null, 50);
await shot('08_axe_walk', null, 14, ['right']);
await shot('09_axe_a1', "P.sxG = 100; mvStart('sx_a1')", 24);
await shot('10_grind', dummy + "; P.sxG = 100; mvStart('sx_grind'); held.add('heavy')", 12);
E("held.delete('heavy')"); G.step(10);
await shot('11_release', "sxSetAxe(true); P.sxG = 90; mvStart('sx_release', { mul: 1.8, g: 90 })", 46);
await shot('12_release_fold', null, 40);
await shot('13_vent', "sxSetAxe(true); P.sxG = 0.5; P.state = 'idle'", 14);
await shot('14_hone', "sxReset(); P.sxG = 40; mvStart('sx_hone'); held.add('heavy')", 20);
E("held.delete('heavy')"); G.step(10);
await shot('15_axe_roll', "sxSetAxe(true); P.sxG = 100; mvDodgeStart(1)", 8);
await shot('16_axe_jump', "P.state = 'idle'; doJump(JUMP_V)", 10);
await shot('17_blade_run', "sxReset()", 12, ['right']);
return o;

// ------------------------------------------------------------------ game state, rooms, save, loop
const SAVE_KEY = 'cinderhollow_save_v1';
let SAVE = null, state = 'title', stateT = 0, paused = false, killed = new Set();
let fadeT = 0, fadeCb = null, fadePhase = 0;
const NGP = { hp: 1, dmg: 1, cinders: 1 };
function updNGP() { const n = SAVE.ngp || 0; NGP.hp = 1 + 0.6 * n; NGP.dmg = 1 + 0.35 * n; NGP.cinders = 1 + 0.5 * n; }
function newSave() {
  return { v: 1, stats: { ...BASE_STATS }, cinders: 0, skills: [], shards: 0, spell: null, items: {}, flags: {}, flaskBase: 4, flaskBlue: 1,
           shrine: 'R1', shrines: [], remnant: null, visited: {}, deaths: 0, playTime: 0, hints: {},
           weapon: 'longsword', weapons: { longsword: 0 }, arts: ['crescent'], art: 'crescent', spellsOwned: [], spellSlots: 2, spellsEq: [],
           charms: [], charmSlots: 1, charmsEq: [], inv: {}, flaskPot: 0, bought: {}, ngp: 0, endings: {} };
}
function hasSave() { try { return !!localStorage.getItem(SAVE_KEY); } catch (e) { return false; } }
function saveGame() { try { SAVE.at = room ? { room: room.id } : null; localStorage.setItem(SAVE_KEY, JSON.stringify(SAVE)); } catch (e) {} }
function loadGame() { try { const s = JSON.parse(localStorage.getItem(SAVE_KEY)); if (s && s.v === 1) { const o = Object.assign(newSave(), s); for (const id of ['ash_bolt', 'sunspear', 'emberburst']) if (o.skills.includes(id) && !o.spellsEq.includes(id) && o.spellsEq.length < o.spellSlots) o.spellsEq.push(id); return o; } } catch (e) {} return null; }
SAVE = newSave();
const playing = () => state === 'play';
const ENEMY_CHARS = { s: 'hollow_soldier', w: 'shield_warden', c: 'rot_crawler', f: 'gloom_wisp', a: 'hollow_archer', e: 'ember_acolyte', K: 'grave_knight',
  h: 'rot_hulk', p: 'bog_spitter', m: 'mire_witch', n: 'gilded_sentinel', o: 'root_spawn', y: 'sun_seraph', q: 'grimoire', d: 'ink_hound', j: 'lantern_monk' };

// ---- extension registries (region/boss files add to these; see docs/EXPANSION_CONTRACT.md)
const ROOM_CHARS = {};        // ch -> ({x,y,cx,fy,key,def,id}) => void
const SPAWNS = {};            // def.spawns[i].t -> (spec, {cx,fy,key,def,id}) => void
const ENEMY_CLASSES = {};     // enemy type -> subclass of Enemy
// test settings (Esc › Settings): god mode and infinite stamina
HOOKS.update.push(() => {
  if (!P || !D) return;
  if (SETTINGS.god) { P.hp = D.maxHp; P.rot = 0; P.rotT = 0; }
  if (SETTINGS.infst) P.st = D.maxSt;
});
const BOSS_SPAWN = {};        // boss kind -> (cx, fy, spec) => boss object
SPAWNS.boss = (s, c) => { if (!SAVE.flags['boss:' + s.kind] && BOSS_SPAWN[s.kind]) boss = BOSS_SPAWN[s.kind](c.cx, c.fy, s); };
const makeEnemy = (type, x, y, key) => new (ENEMY_CLASSES[type] || Enemy)(type, x, y, key);
function spawnDefEnemies(def, have) {
  (def.spawns || []).forEach((s, i) => { if (s.t !== 'enemy') return; const key = `${def.id}:sp${i}`; if (!killed.has(key) && !(have && have.has(key))) enemies.push(makeEnemy(s.type, s.x * TILE + 8, (s.y + 1) * TILE, key)); });
}

function targets() {
  const t = enemies.filter(e => e.alive);
  if (boss && boss.alive && boss.active) { if (boss.parts) t.push(...boss.parts.filter(q => q.alive !== false)); else t.push(boss); }   // multi-part / duo bosses expose .parts
  for (const p of props) if (propHurtbox(p)) t.push(propTarget(p));
  return t;
}

// ---- rooms
function enterRoom(id, px, py, opt = {}) {
  const def = ROOM_BY[id];
  const prevBiome = room && room.def.biome;
  room = buildRoom(def); darkT = 0; bossBanner = null; if (P) { P.fric = 1; P.pushVx = 0; }
  props = []; enemies = []; projectiles = []; hazards = []; fx = fx.filter(f => f.follow === P); boss = null; particles = particles.filter(p => !p.amb);
  const chests = [...(def.chests || [])], items = [...(def.items || [])];
  let ci = 0, ii = 0, ni = 0, gi = 0;
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) {
    const ch = def.map[y][x], cx = x * TILE + 8, fy = (y + 1) * TILE, key = `${id}:${x},${y}`;
    switch (ch) {
      case 'S': props.push(makeProp('shrine', cx, fy, { lit: SAVE.shrines.includes(id), name: def.shrine, key: 'shrine:' + id })); break;
      case 's': case 'w': case 'c': case 'f': case 'a': case 'e': case 'K': case 'h': case 'p': case 'm': case 'n': case 'o': case 'y': case 'q': case 'd': case 'j': {
        const type = ENEMY_CHARS[ch];
        if (!killed.has(key)) enemies.push(makeEnemy(type, cx, fy, key));
        break;
      }
      case 'u': props.push(makeProp('urn', cx, fy)); break;
      case 'l': props.push(makeProp('lantern', cx, y * TILE)); break;
      case 'k': props.push({ type: 'candle', x: cx, y: fy, anim: { update() {} } }); break;
      case 'C': { const k = `chest:${id}:${ci}`; props.push(makeProp('chest', cx, fy, { key: k, item: chests[ci], open: !!SAVE.flags[k] })); ci++; break; }
      case 'i': { const k = `item:${id}:${ii}`; if (!SAVE.flags[k]) props.push(makeProp('item', cx, fy - 4, { key: k, item: items[ii] })); ii++; break; }
      case 'L': { const k = `lever:${id}`; props.push(makeProp('lever', cx, fy, { key: k, on: !!SAVE.flags[k] })); break; }
      case 'G': {
        const k = `lever:${id}`, gp = makeProp('gate', cx, (y + 4) * TILE, { key: 'gate:' + id, open: !!SAVE.flags[k] || (id === 'X1' && !!SAVE.flags['bell:rung']) });
        props.push(gp); room.dyn.push({ x0: x * TILE + 3, x1: x * TILE + 13, y0: y * TILE, y1: (y + 4) * TILE, on: () => !gp.open });
        break;
      }
      case 'F': {
        if (SAVE.flags['boss:' + def.boss]) break;
        const exit = def.entry === 'E' ? x < def.w / 2 : x > def.w / 2, fp = makeProp('fog', cx, fy, { exit });
        fp.on = () => boss && boss.alive && (boss.active || exit);
        props.push(fp); room.dyn.push({ x0: x * TILE, x1: x * TILE + 16, y0: (y - 4) * TILE, y1: fy, on: fp.on });
        break;
      }
      case 'H': if (!SAVE.flags['boss:hound']) boss = new Hound(cx, fy); break;
      case 'Q': if (!SAVE.flags['boss:kalden']) boss = makeKalden(cx, fy); break;
      case 'V': if (!SAVE.flags['boss:vessel']) boss = makeVessel(cx, fy); break;
      case 'Z': if (!SAVE.flags['boss:sovereign']) boss = makeSovereign(cx, fy); break;
      case 'J': if (!SAVE.flags['boss:librarian'] && sheet('head_librarian').ok) boss = makeLibrarian(cx, fy); break;
      case 'N': { const nid = (def.npcs || [])[ni++]; if (nid && npcPresent(nid, id)) props.push(makeNpc(nid, cx, fy)); break; }
      case 'A': props.push(makeProp('anvil', cx, fy)); break;
      case 'E': props.push(makeProp('lectern', cx, fy)); break;
      case 'I': props.push(makeProp('candelabra', cx, fy)); break;
      case 'R': props.push(makeProp('shelfcage', cx, y * TILE)); break;
      case 'O': props.push(makeProp('bell', cx, fy)); break;
      case 'T': props.push(makeProp('throne', cx, fy)); break;
      case 'g': props.push(makeProp('grave', cx, fy, { lore: (def.graves || [])[gi++] })); break;
      case 'M': if (!SAVE.flags['boss:omen']) boss = new Omen(cx, fy); break;
      default: if (ROOM_CHARS[ch]) ROOM_CHARS[ch]({ x, y, cx, fy, key, def, id });
    }
  }
  spawnDefEnemies(def);
  (def.spawns || []).forEach((s, i) => { if (s.t !== 'enemy' && SPAWNS[s.t]) SPAWNS[s.t](s, { cx: s.x * TILE + 8, fy: (s.y + 1) * TILE, key: `${id}:sp${i}`, def, id }); });
  buildTraversalProps(def);
  if (SAVE.remnant && SAVE.remnant.room === id) props.push(makeProp('remnant', SAVE.remnant.x, SAVE.remnant.y));
  if (px !== undefined) { P.x = px; P.y = py; P.safe = { x: clamp(px, 24, room.pw - 24), y: py }; P.safeT = 0.4; }
  if (!SAVE.visited[id]) { SAVE.visited[id] = 1; if (def.secret) toast('You discovered a secret'); }
  if (regionEnter(def, prevBiome, opt)) {}   // first visit to a region: cinematic title (29_ui2.js; seen regions persist in SAVE.seenAreas)
  else if (def.biome !== prevBiome || opt.card) areaCard = { name: AREAS[def.biome].name, sub: def.name, t: 0 };
  else if (!opt.quiet) areaCard = null;
  updateCamera(0, true);
  hints(id);
  runHooks('enter', def);
  sheetHousekeeping(n => n === 'player' || n === 'wpn_' + (SAVE.weapon || 'longsword'));
  warmSheets();
}
function hints(id) {
  const H = SAVE.hints, once = (k, m) => { if (!H[k]) { H[k] = 1; setTimeout(() => toast(m, 4.5), 1200); } };
  if (id === 'R1') once('move', 'A/D move · Space jump · J attack · L roll');
  if (id === 'R2') once('heavy', 'Hold K for a charged heavy · I to parry, then J to riposte');
  if (id === 'R3') once('down', 'In the air, hold S and attack to strike downward — bounce off foes and thorns');
  if (id === 'C2') once('rest', 'Resting at a shrine restores you — but revives your foes');
  if (id === 'C5') once('boss', 'Something vast breathes in the dark…');
  if (id === 'A1') once('archives', 'Pages drift down from the dark above. Something is still writing up there.');
  if (id === 'M1') once('rot', 'Rot water poisons you — drink a crimson flask or rest to cure it');
  if (id === 'M3') once('trap', 'Hold ↓ and press Space to drop through thin floors');
  if (id === 'C2') once('smith', 'A smith works an anvil near the shrine. Press E to talk');
  if (id === 'R2') once('menu', 'Esc opens your equipment: weapons, arts, spells, charms');
}
function checkRoomExit() {
  const cy = P.y - 13;
  if (P.x >= 0 && P.x < room.pw && cy >= 0 && P.y <= room.ph + 4) return;
  const gx = room.def.gx * TILE + P.x, gy = room.def.gy * TILE + cy;
  const n = roomAtGlobal(Math.floor(gx / TILE), Math.floor(gy / TILE));
  if (!n || n.id === room.id) { P.x = clamp(P.x, 6, room.pw - 6); if (cy < 0 && room.def.indoor) P.y = 30; return; }
  const nx = gx - n.gx * TILE, ny = gy - n.gy * TILE + 13;
  const goingUp = cy < 0;
  enterRoom(n.id, nx, ny, { quiet: true });
  if (goingUp) P.vy = Math.min(P.vy, -260);
  fadeT = 0.12; fadePhase = 2;
}

// ---- shrines, death, respawn
function useShrine(p) {
  if (!p.lit) {
    p.lit = true; p.anim.set('kindle', false); SAVE.shrines.push(room.id); sfx.kindle(); flashScreen = 0.3;
    toast('Shrine kindled'); spawnFx(fxOr('levelup', 'heal'), p.x, p.y, 1);
  }
  rest(p);
}
function rest(p) {
  P.x = clamp(P.x, p.x - 12, p.x + 12); P.vx = 0; P.face = 1;
  setP('rest', pHas('rest') ? 'rest' : 'heal', false);
  refreshDerived(); P.hp = D.maxHp; P.fp = D.maxFp; P.st = D.maxSt; refillFlasks();
  SAVE.shrine = room.id; killed.clear(); respawnEnemies(); runHooks('rest', p);
  saveGame(); sfx.heal();
  setTimeout(() => { if (state === 'play') openShrineMenu(p); }, 450);
}
function respawnEnemies() {
  const def = room.def, have = new Set(enemies.map(e => e.key));
  const T = ENEMY_CHARS;
  for (let y = 0; y < def.h; y++) for (let x = 0; x < def.w; x++) {
    const ch = def.map[y][x], key = `${def.id}:${x},${y}`;
    if (T[ch] && !have.has(key)) enemies.push(makeEnemy(T[ch], x * TILE + 8, (y + 1) * TILE, key));
  }
  spawnDefEnemies(def, have);
}
function respawnAtShrine(id) {
  const def = ROOM_BY[id]; let sx = 64, sy = 176;
  for (let y = 0; y < def.h; y++) { const x = def.map[y].indexOf('S'); if (x >= 0) { sx = x * TILE + 8; sy = (y + 1) * TILE; } }
  if (!def.map.some(r => r.includes('S'))) for (let y = 0; y < def.h; y++) { const x = def.map[y].indexOf('P'); if (x >= 0) { sx = x * TILE + 8; sy = (y + 1) * TILE; } }
  newPlayer(sx, sy);
  enterRoom(id, sx + 14, sy, { card: true });
  SAVE.shrine = id;
}
function onPlayerDeath() {
  state = 'dead'; stateT = 0;
}
function finishDeath() {
  SAVE.deaths++;
  if (SAVE.remnant) toast(`${SAVE.remnant.amount} cinders were lost forever`, 4);
  SAVE.remnant = SAVE.cinders > 0 ? { room: room.id, x: P.safe.x, y: P.safe.y, amount: SAVE.cinders } : null;
  SAVE.cinders = 0; killed.clear();
  saveGame();
  fadeTo(() => { respawnAtShrine(SAVE.shrine || 'R1'); state = 'play'; setP('rise', pHas('rise') ? 'rise' : 'idle', false); });
}
function fadeTo(cb) { fadeCb = cb; fadePhase = 1; fadeT = 0; }
function startNGPlus() {
  const keep = SAVE;
  const n = newSave();
  for (const k of ['stats', 'skills', 'shards', 'weapon', 'weapons', 'arts', 'art', 'spellsOwned', 'spellSlots', 'spellsEq', 'spell', 'charms', 'charmSlots', 'charmsEq', 'inv', 'flaskPot', 'flaskBase', 'flaskBlue', 'cinders', 'deaths', 'playTime', 'endings', 'hints'])
    n[k] = keep[k];
  n.items = { talon: keep.items.talon, wings: keep.items.wings };
  if (keep.x3) n.x3 = { lore: keep.x3.lore, trials: keep.x3.trials, vistas: keep.x3.vistas };   // the Chronicle, best times and found vistas outlive the journey
  n.ngp = (keep.ngp || 0) + 1; n.bought = {};
  SAVE = n; updNGP(); killed.clear();
  const def = ROOM_BY.R1; let sx = 72, sy = 176;
  for (let y = 0; y < def.h; y++) { const x = def.map[y].indexOf('P'); if (x >= 0) { sx = x * TILE + 8; sy = (y + 1) * TILE; } }
  newPlayer(sx, sy); enterRoom('R1', sx, sy, { card: true });
  state = 'play'; stateT = 0; saveGame(); toast(`Journey ${SAVE.ngp + 1} begins. The Hallow grows crueler.`, 4);
}

function newGame(skipIntro) {
  if (!skipIntro) { playCine(INTRO, () => newGame(true)); return; }
  SAVE = newSave(); killed.clear(); updNGP();
  const def = ROOM_BY.R1; let sx = 72, sy = 176;
  for (let y = 0; y < def.h; y++) { const x = def.map[y].indexOf('P'); if (x >= 0) { sx = x * TILE + 8; sy = (y + 1) * TILE; } }
  newPlayer(sx, sy); enterRoom('R1', sx, sy, { card: true });
  state = 'play'; stateT = 0; saveGame(); applyPendingArmory();
}
function continueGame() {
  const s = loadGame(); if (!s) return newGame();
  SAVE = s; killed.clear(); updNGP();
  respawnAtShrine(SAVE.shrines.includes(SAVE.shrine) ? SAVE.shrine : (SAVE.shrines[0] || 'R1'));
  state = 'play'; stateT = 0; applyPendingArmory();
}

// ---- test armory: open the game with #armory, or Settings › Armory
let wantArmory = false;
try { wantArmory = location.hash === '#armory'; } catch (e) {}
function giveArmory() {
  for (const id of Object.keys(WEAPONS)) { if (SAVE.weapons[id] === undefined) SAVE.weapons[id] = 0; const a = WEAPONS[id].art; if (!SAVE.arts.includes(a)) SAVE.arts.push(a); }
  for (const id of Object.keys(ARTS)) if (!SAVE.arts.includes(id)) SAVE.arts.push(id);
  for (const id of Object.keys(SPELL_DEFS)) if (!SAVE.spellsOwned.includes(id)) SAVE.spellsOwned.push(id);
  for (const id of Object.keys(CHARMS)) if (!SAVE.charms.includes(id)) SAVE.charms.push(id);
  SAVE.spellSlots = Math.max(SAVE.spellSlots, 4); SAVE.charmSlots = Math.max(SAVE.charmSlots, 4);
  SAVE.items.wings = 1; SAVE.items.talon = 1;   // double jump + wall-jump for testing
  saveGame(); sfx.levelup(); flashScreen = 0.3;
  banner('The Armory', 'Every weapon, art, spell and charm is yours, plus wall-jump and double jump. Swap gear in the menu (Esc › Equipment).', 'w_greatsword');
}
function applyPendingArmory() { if (wantArmory) { wantArmory = false; setTimeout(giveArmory, 900); } }

// ---- input routing
onPressHook = (a, repeat) => {
  audio();
  if (a === 'mute') { muted = !muted; toast(muted ? 'Sound off' : 'Sound on'); return; }
  if (state === 'title') {
    const n = titleOptions().length;
    if (a === 'up' || a === 'down') { titleSel = (titleSel + (a === 'up' ? -1 : 1) + n) % n; sfx.menu(); }
    else if (['confirm', 'attack', 'jump', 'interact'].includes(a)) { const o = titleOptions()[titleSel]; sfx.kindle(); clearBuffer(); if (o === 'Continue') continueGame(); else newGame(); }
    return;
  }
  if (state === 'menu') { menuInput(a); buffered.delete(a); return; }
  if (state === 'dialog') { dialogInput(a); buffered.delete(a); return; }
  if (state === 'cut') { cutInput(a); buffered.delete(a); return; }
  if (state === 'cine') { cineInput(a); return; }
  if (state === 'map') { if (['map', 'pause', 'back'].includes(a)) { state = 'play'; clearBuffer(); } return; }
  if (state === 'ending') {
    if (stateT < 2.5) return;
    if (['confirm', 'attack', 'interact'].includes(a)) startNGPlus();
    else if (['pause', 'back'].includes(a)) { state = 'play'; clearBuffer(); }
    return;
  }
  if (state === 'play' && !repeat) {
    if (a === 'pause') { openPauseMenu(); return; }
    if (a === 'map') { state = 'map'; clearBuffer(); return; }
    if (a === 'spell') {
      const eq = SAVE.spellsEq.filter(spellKnown);
      if (!eq.length) { toast('No spells equipped — open the menu (Esc)'); return; }
      SAVE.spell = eq[(eq.indexOf(SAVE.spell) + 1) % eq.length]; sfx.menu(); toast(SPELLS[SAVE.spell].name);
    }
  }
};

// ---- update
function update(rawDt) {
  let dt = rawDt;
  time += rawDt; stateT += rawDt;
  if (slowmo > 0) { slowmo -= rawDt; dt = rawDt * 0.35; }
  flashScreen = Math.max(0, flashScreen - rawDt * 2); cinderFlash -= rawDt; if (cinderFlash <= 0) cinderGain = 0;
  for (const t of toasts) { t.life -= rawDt; t.t += rawDt; } toasts = toasts.filter(t => t.life > 0);
  if (areaCard && (areaCard.t += rawDt) > 3.6) areaCard = null;
  if (bossBanner && (bossBanner.t += rawDt) > 3) bossBanner = null;
  if (bannerMsg && (bannerMsg.t += rawDt) > 3.8) bannerMsg = null;
  if (victoryBanner && (victoryBanner.t += rawDt) > 5) { const end = victoryBanner.ending; victoryBanner = null; if (end) beginEnding(); }
  if (fadePhase === 1) { fadeT += rawDt; if (fadeT >= 0.3) { fadePhase = 2; fadeT = 0.3; const cb = fadeCb; fadeCb = null; cb && cb(); } return; }
  if (fadePhase === 2) { fadeT -= rawDt; if (fadeT <= 0) { fadePhase = 0; fadeT = 0; } }
  if (state === 'cine') { if (cine) cine.t += rawDt; return; }
  if (state === 'cut') { for (const p of popups) p.life -= rawDt; updateCutscene(rawDt); return; }
  if (state === 'dialog') { updateDialog(rawDt); lights = []; updateProps(dt); updateParticles(dt); updateFx(dt); return; }
  if (state === 'title') { if (room) { lights = []; updateProps(dt); ambientParticles(dt); updateParticles(dt); updateFx(dt); } return; }
  if (state === 'dead') { if (stateT > 2.6 && fadePhase === 0 && !fadeCb) finishDeath(); updateParticles(dt); updateFx(dt); return; }
  if (state !== 'play' || paused) return;
  if (hitstop > 0) { hitstop -= rawDt; return; }
  SAVE.playTime += rawDt;
  lights = [];
  shake = Math.max(0, shake - rawDt * 22);
  for (const gh of ghosts) gh.life -= dt; ghosts = ghosts.filter(gh => gh.life > 0);
  for (const p of popups) { p.life -= rawDt; p.y -= 14 * rawDt; } popups = popups.filter(p => p.life > 0);
  updatePlayer(dt);
  if (state !== 'play' && state !== 'dead') return;
  for (const e of enemies) e.update(dt);
  enemies = enemies.filter(e => !e.gone);
  if (boss) boss.update(dt);
  updateProjectiles(dt); updateHazards(dt); updateProps(dt); updateFx(dt);
  runHooks('update', dt);
  if (darkT > 0) { darkT -= dt; lights = lights.filter(L => L.snuffProof); if (boss && boss.ambient) boss.ambient(dt); }
  ambientParticles(dt); updateParticles(dt);
  if (P.state !== 'dead') checkRoomExit();
  updateCamera(dt);
}

// ---- render
let frameLights = [];
// Dynamic lighting (41_light.js): lit scene -> `low`, emitters -> `lowFx` (drawGlow), overlays -> `lowTop`, lit on the GPU.
// Classic / shaders off: g stays on `low` the whole way and renderLighting() darkens it, exactly as before.
function renderWorld() {
  const dyn = lxBegin();
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1;
  g.clearRect(0, 0, W, H);
  if (!room) { g.fillStyle = '#0a0810'; g.fillRect(0, 0, W, H); return; }
  drawParallax();
  const sk = shake * SETTINGS.shake, sx = sk ? rand(-sk, sk) * 0.5 : 0, sy = sk ? rand(-sk, sk) * 0.5 : 0;
  const cx = Math.round(cam.x - sx), cy = Math.round(cam.y - sy);
  LX.cx = cx; LX.cy = cy;
  g.setTransform(1, 0, 0, 1, -cx, -cy);
  g.drawImage(room.back, 0, 0);
  const p2tint = boss && boss.phase === 2 && boss.alive;
  if (p2tint && !dyn) { g.fillStyle = `rgba(255,150,50,${0.05 + 0.03 * Math.sin(time * 3)})`; g.fillRect(cx, cy, W, H); }
  g.drawImage(room.front, 0, 0);
  for (const p of props) if (p.type !== 'fog' && p.type !== 'veil') lxDrawProp(p);
  for (const f of fx) if (f.name === 'ground_crack') drawFx(f);
  // shadows
  const shadow = (x, y, w, a) => { g.fillStyle = `rgba(6,4,10,${a})`; g.beginPath(); g.ellipse(Math.round(x), Math.round(y) + 1, Math.max(2, w), 2.5, 0, 0, 6.3); g.fill(); };
  if (P.ground) shadow(P.x, P.y, 8, 0.45);
  for (const e of enemies) if (e.ground && !e.cfg.flying) shadow(e.x, e.y, e.w * 0.6, 0.4);
  if (boss && boss.state !== 'dormant') shadow(boss.x, boss.floor, boss.kind === 'hound' ? 55 : 34, 0.5);
  if (boss) boss.draw();
  for (const e of enemies) e.draw();
  for (const h of hazards) if (h.pool) { g.fillStyle = `rgba(110,170,50,${0.45 * Math.min(1, h.life)})`; g.beginPath(); g.ellipse(Math.round(h.x), Math.round(h.y) - 1, h.w / 2, 3, 0, 0, 6.3); g.fill(); }
  const rw = fxSheet('rot_wave');
  drawGlow(() => {
    for (const h of hazards) if (h.wave && h.color === 'rot' && rw.ok) { const t = rw.tag('rot_wave'); drawSprite(rw, t.from + Math.floor(time * 12) % (t.to - t.from + 1), h.x, h.y, h.dir || 1, { bottom: true }); addLight(h.x, h.y - 8, 30, '150,210,90', 0.6); }
    for (const h of hazards) if (h.wave && !(h.color === 'rot' && rw.ok)) {
      const c = h.color === 'root' ? ['255,160,70', '255,220,160'] : h.color === 'rot' ? ['110,180,60', '190,230,120'] : ['255,200,90', '255,240,190'];
      g.fillStyle = `rgba(${c[0]},0.85)`; g.fillRect(Math.round(h.x - 3), Math.round(h.y) - 10, 6, 10);
      g.fillStyle = `rgba(${c[1]},0.9)`; g.fillRect(Math.round(h.x - 1), Math.round(h.y) - 14, 2, 14);
    }
  });
  for (const gh of ghosts) drawSprite(sheet('player'), gh.f, gh.x, gh.y, gh.face, { alpha: gh.life / 0.22 * 0.45, flash: 1, flashColor: gh.red ? '#c02030' : '#5a2a4a' });
  if (!(P.inv > 0 && P.state !== 'hurt' && P.state !== 'dead' && P.state !== 'rise' && Math.floor(time * 20) % 2)) {
    const op = P.flash > 0 ? { flash: P.flash * 0.55, flashColor: '#ff3030' } : P.empower > 0 ? { flash: 0.15 + 0.1 * Math.sin(time * 12), flashColor: '#ffd070' } : {};
    drawSprite(sheet('player'), P.anim.frame, P.x, P.y, P.face, op);
    const ws = sheet('wpn_' + (SAVE.weapon || 'longsword'));
    const sgl = SIGS[SAVE.weapon], sigGlow = sgl && ATK[P.state] && P.anim.i >= ATK[P.state].active[0] - 1 && P.anim.i <= ATK[P.state].active[1];
    drawSprite(ws.ok ? ws : sheet('wpn_longsword'), P.anim.frame, P.x, P.y, P.face, P.fireT > 0 ? { flash: 0.35 + 0.15 * Math.sin(time * 20), flashColor: '#ff8a30' } : sigGlow ? { flash: 0.45, flashColor: sgl.glow } : op);
    if (sgl && !ATK[P.state] && Math.random() < 0.08) particles.push({ x: P.x + P.face * rand(4, 16), y: P.y - rand(8, 24), vx: 0, vy: -rand(5, 15), life: 0.5, kind: sgl.pk });
    if (P.fireT > 0) addLight(P.x + P.face * 12, P.y - 18, 40, '255,150,60', 0.8);
  }
  drawWater();
  drawHookLine();
  for (const p of props) if (p.type === 'fog' || p.type === 'veil') lxDrawProp(p);
  lxDrawProjectiles();
  runHooks('render');
  for (const f of fx) if (f.name !== 'ground_crack') lxDrawFx(f);
  const saved = lights; lights = frameLights = [];
  lxDrawParticles();
  lights = saved.concat(frameLights);
  addLight(P.x, P.y - 16, 100, '255,210,170', 0.9, LX_PLAYER);
  if (dyn) lxCollect(lights); else renderLighting();
  lights = saved;
  g.setTransform(1, 0, 0, 1, 0, 0);
  if (dyn) { g = gTop; if (p2tint) { g.fillStyle = `rgba(255,150,50,${0.04 + 0.02 * Math.sin(time * 3)})`; g.fillRect(0, 0, W, H); } }
  runHooks('renderTop');
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  if (flashScreen > 0) { g.fillStyle = `rgba(255,236,190,${flashScreen * 0.35})`; g.fillRect(0, 0, W, H); }
  if (P.hp < D.maxHp * 0.25 && P.state !== 'dead') { g.fillStyle = `rgba(120,0,10,${0.12 + 0.06 * Math.sin(time * 5)})`; g.fillRect(0, 0, W, H); }
  const vg = g.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 250);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.6)');
  g.fillStyle = vg; g.fillRect(0, 0, W, H);
  g = gLow;
}
function render() {
  renderWorld();
  vctx.fillStyle = '#050407'; vctx.fillRect(0, 0, view.width, view.height);
  presentWorld();   // 40_gfx.js: straight blit, or through the post-process shader
  if (state === 'title') renderTitle();
  else {
    if (P && D && state !== 'cut') { renderHUD(); runHooks('hud'); }
    if (state === 'cut') renderCutsceneOverlay();
    if (state === 'menu') renderMenu();
    if (state === 'map') renderMap();
    if (state === 'dead') renderDeath();
    if (state === 'dialog') renderDialog();
    if (state === 'ending') renderEnding();
  }
  if (state === 'cine' && cine) renderCine();
  if (fadeT > 0) { vctx.fillStyle = `rgba(0,0,0,${clamp(fadeT / 0.3, 0, 1)})`; vctx.fillRect(ox, oy, W * scale, H * scale); }
}

// ---- main loop
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  try { padPoll(dt); update(dt); render(); updateMusic(); } catch (e) { console.error(e); }
  requestAnimationFrame(frame);
}
function titleBackdrop() {
  // the title screen shows the first room behind it
  newPlayer(9999, 0);
  enterRoom('R1', 200, 176, { quiet: true }); areaCard = null;
  cam.x = 120; cam.y = 0; P.x = -999;
}
function boot() {
  resize(); grabFocus(); titleBackdrop();
  window.__loadDone && window.__loadDone();
  requestAnimationFrame(t => { last = t; frame(t); });
}
// preload only the small sheets (tiles, props, UI, fx, most enemies) + the player; bosses and weapon overlays load on demand
const allSheetNames = Object.keys(ASSETS).filter(k => ASSETS[k] && ASSETS[k].png);
const preloadNames = allSheetNames.filter(n => { const s = sheet(n); return s.ok && (!s.big || n === 'player' || n === 'wpn_longsword'); });
window.__loadProgress && window.__loadProgress(0.92, 'Waking the Hallow…');
Promise.all(preloadNames.map(n => { const s = sheet(n); return s.img.decode ? s.img.decode().catch(() => {}) : null; }))
  .then(() => document.fonts && document.fonts.load ? document.fonts.load('600 20px Cinzel').catch(() => {}) : null)
  .then(boot);

// ---- debug hooks (used by automated testing)
window.__game = {
  get P() { return P; }, get boss() { return boss; }, get enemies() { return enemies; }, get room() { return room && room.id; }, get state() { return state; },
  get SAVE() { return SAVE; }, get menu() { return menu; }, get SETTINGS() { return SETTINGS; }, get D() { return D; }, get props() { return props; }, get cut() { return cut; },
  newGame, continueGame, giveArmory, grantTechniques,
  tp(id, tx, ty) { if (state === 'menu') { menu = null; state = 'play'; } enterRoom(id, tx * TILE + 8, (ty + 1) * TILE, { card: true }); P.vx = P.vy = 0; setP('idle', 'idle', true); },
  give(o = {}) { Object.assign(SAVE, o); if (o.items) SAVE.items = { ...SAVE.items, ...o.items }; refreshDerived(); },
  step(n = 60, hold = [], tap = []) {
    tap.forEach(press); hold.forEach(a => held.add(a));
    for (let i = 0; i < n; i++) update(1 / 60);
    hold.forEach(release); tap.forEach(release);
    render();
    return { state, room: room && room.id, p: { x: Math.round(P.x), y: Math.round(P.y), hp: Math.round(P.hp), st: Math.round(P.st), s: P.state, a: P.anim.tag, g: P.ground },
             enemies: enemies.filter(e => e.alive).map(e => `${e.type}:${e.state}:${Math.round(e.x)},${Math.round(e.y)}:${e.hp}`),
             boss: boss ? { s: boss.state, hp: boss.hp, x: Math.round(boss.x), ph: boss.phase } : null };
  },
};

// ------------------------------------------------------------------ story: NPCs, dialogue, lore, cinematics
const NPC_INFO = {
  venn: { name: 'Sister Venn', sheet: 'npc_venn', portrait: 'portrait_venn' },
  ashwright: { name: 'Old Ashwright', sheet: 'npc_ashwright', portrait: 'portrait_ashwright' },
  scribe: { name: 'The Hollow Scribe', sheet: 'npc_scribe', portrait: 'portrait_scribe' },
  kalden: { name: 'Ser Kalden', sheet: 'npc_kalden', portrait: 'portrait_kalden' },
};
const F = k => !!SAVE.flags[k];
const setF = k => { SAVE.flags[k] = 1; };
// where each NPC stands, by room + story state
function npcPresent(id, roomId) {
  const hound = F('boss:hound'), omen = F('boss:omen'), kaldenDead = F('boss:kalden');
  if (id === 'venn') return (roomId === 'R1' && !hound) || (roomId === 'C4' && hound && !omen) || (roomId === 'X4' && omen);
  if (id === 'kalden') return !kaldenDead && ((roomId === 'R4' && !F('k_met2')) || (roomId === 'C4' && hound && F('k_met1') && !F('k_left')));
  return true;
}

// ---- the new regions: Venn's beats after each of their bosses, and where she points you next
const VENN_BEATS = [
  ['unwritten', 'v_ink', ['There is ink under your nails. You climbed into the Archives.',
    'The Scribe wrote so the Root would be remembered. I think he forgot that stories are meant to end.',
    'That golden root you carry reaches for anchors, the way the Root once reached for light. Past the Rampart Summit the old span is broken. You could cross it now.']],
  ['twins', 'v_twins', ['You came back cold, and you smell of smoke. The Aqueduct’s twins… Ser Hael and Dame Rime.',
    'They swore to keep the water rising to the Root. When it fell, they kept swearing — at each other.',
    'Your roll burns now. There is a wall of ash on the sea wall above the Gatehouse. Nothing else could pass it.']],
  ['cindervane', 'v_drake', ['The storm over the Spire has broken. I heard the drake’s last cry all the way down here.',
    'Cindervane was the Root’s last wind. Its wings carried the seeds, once. Now its cloak carries you.',
    'Below the Sunken Road the mire runs hot. There is a chasm there no one can cross — unless they can fall slowly.']],
  ['colossus', 'v_forge', ['The ground has stopped shaking. Ashwright’s great fire is out, isn’t it?',
    'Be gentle with him. He made that thing out of grief, and out of the Root’s own heart.',
    'Your step is heavy now — heavy enough to break floors that have waited a long time to be broken. The Crown Shrine’s floor sounds hollow when I kneel.']],
  ['oswin', 'v_oswin', ['You found the pilgrim in the hollow west of the cliffs. Oswin walked the Hallow before any shrine was lit.',
    'He told me once that the wind remembers every road. I didn’t understand him. I think you do now.']],
  ['first_ember', 'v_first', ['It wore your face. The fire beneath the Crown — it wore your face, and it burned before anything.',
    'Whatever you are, Ashbound, you were made from it. And you put it out.',
    '…Or it let you. I don’t know which frightens me more.']],
];
const seen = prefix => !!SAVE && Object.keys(SAVE.visited).some(k => k.startsWith(prefix) && !(prefix === 'H' && k.startsWith('HF')));
function vennHint() {
  const visited = p => Object.keys(SAVE.visited).some(k => k.startsWith(p));
  if (SAVE.items.talon && !visited('A')) return 'Pages have been drifting down the Bell Ascent. Something up there is still writing.';
  if (F('boss:unwritten') && !F('boss:twins')) return 'Past the Rampart Summit the old span is broken. A golden root could cross it.';
  if (F('boss:twins') && !F('boss:cindervane')) return 'The sea wall above the Gatehouse is choked with ash. Your roll burns now — go through it.';
  if (F('boss:cindervane') && !F('boss:colossus')) return 'Under the Sunken Road there is heat, and a chasm you would have to drift across.';
  if (F('boss:colossus') && !F('boss:first_ember')) return 'The floor of the Crown Shrine sounds hollow. So do some of the old roads, if you strike them hard enough.';
  return null;
}

// dialogue scripts: arrays of steps. {w: speaker, t: text} | {choice: [[label, steps]...]} | {do: fn} | {give: id} | {shop: id} | {forge: true}
function npcScript(id) {
  const P1 = 'player';
  if (id === 'venn') {
    if (!F('v_met')) return [
      { w: 'venn', t: 'Oh — you’re awake. The ash doesn’t let many of you rise twice.' },
      { w: 'venn', t: 'I am Venn. I keep the shrines, what few still burn. Kneel at one and it will remember you when you fall.' },
      { w: 'venn', t: 'You feel it too, don’t you? The pull toward the Crown. The Pale Root fell, but its heart still beats up there… wrong. Hungry.' },
      { w: 'venn', t: 'The way up is barred. The roots below are guarded by a beast, and the Cathedral by the Omen. Go carefully, Ashbound.' },
      { do() { setF('v_met'); } },
    ];
    if (F('boss:omen') && !F('v_truth')) return [
      { w: 'venn', t: 'You felled the Omen. I felt it — like a door opening in my chest.' },
      { w: 'venn', t: 'I should tell you what I am. I was the Root’s last seed. When it fell, I woke in a shrine flame, the way you woke in the ash.' },
      { w: 'venn', t: 'The Sovereign up there was its heart once. Now she drinks the grace of everything below. If she is not stopped, the Hallow withers to nothing.' },
      { w: 'venn', t: 'Take this. It was mine when I was more than a seedling. Where I go, you’ll need your strength more than I will.' },
      { give: 'c_grace' }, { do() { setF('v_truth'); } },
    ];
    if (F('boss:hound') && !F('v_tear')) return [
      { w: 'venn', t: 'You came through the Hound’s den. The roots are quieter now.' },
      { w: 'venn', t: 'Here — a Pale Tear. If the path you chose for yourself chafes, weep it at a shrine and begin again. (Rebirth)' },
      { give: 'tear' }, { do() { setF('v_tear'); } },
    ];
    // one beat per conversation, as the Hallow's other regions fall quiet (first unheard wins)
    for (const [boss, flag, lines] of VENN_BEATS) if (F('boss:' + boss) && !F(flag)) return [...lines.map(t => ({ w: 'venn', t })), { do() { setF(flag); } }];
    const hint = vennHint();
    return [{ w: 'venn', t: hint && Math.random() < 0.6 ? hint : ['Rest when you can. The flame is patient.', 'The ash remembers everyone who walks through it.', 'I will be near the shrines. I always am.'][irand(0, 2)] }];
  }
  if (id === 'ashwright') {
    const first = !F('a_met');
    return [
      ...(first ? [
        { w: 'ashwright', t: 'Hah! A walking one. Good. The dead make terrible customers.' },
        { w: 'ashwright', t: 'Name’s Ashwright. I smith. Bring me Emberstones and I’ll temper your blade till it sings. Got wares too, if you’ve the cinders.' },
        { do() { setF('a_met'); } }] : [{ w: 'ashwright', t: ['What’ll it be?', 'Anvil’s hot.', 'Back again? Still breathing. Good.'][irand(0, 2)] }]),
      ...(F('boss:colossus') && !F('a_colossus') ? [{ w: 'ashwright', t: 'Felt it go out, down in the deep. Quiet as a banked forge. …Thank you, Ashbound.' }, { do() { setF('a_colossus'); } }] : []),
      { choice: [['Temper a weapon', [{ forge: true }]], ['Browse wares', [{ shop: 'ashwright' }]], ['Ask about the Root', [
        { w: 'ashwright', t: 'I forged the gold for its crown once, when it still stood. Beautiful thing. Should’ve let it rot in peace.' },
        { w: 'ashwright', t: 'Now there’s a queen up there with my gold on her head, drinking the whole Hallow dry. Don’t get sentimental about her.' }]],
        ...(F('boss:colossus') || seen('D') ? [['Ask about the Deep', F('boss:colossus') ? [
          { w: 'ashwright', t: 'Hah. You put it out. My finest fire.' },
          { w: 'ashwright', t: 'I built it to lift the hammer when my arm gave out. It never learned to set the hammer down. Worked the whole Deep into slag.' },
          ...(!F('a_heart') ? [{ w: 'ashwright', t: 'Here. The last of the heartwood I kept back. Better in your blade than in another of my mistakes.' }, { give: 'emberstone' }, { give: 'emberstone' }, { do() { setF('a_heart'); } }] : [])] : [
          { w: 'ashwright', t: 'Down there? My old forge. Don’t go poking the big furnace.' },
          { w: 'ashwright', t: '…You will anyway. If it wakes — and it will — go for the plates, not the fire. The plates come off.' }]]] : []),
        ...(F('boss:twins') || seen('HF') ? [['Ask about the Twins', [
          { w: 'ashwright', t: 'Hael and Rime. Forged their blades from one ingot — flame for him, frost for her. Told ’em it’d keep ’em together.' },
          { w: 'ashwright', t: F('boss:twins') ? 'Worst prophecy I ever made. …Did they go together, at least?' : 'Last I heard they were still at it on the Aqueduct, trying to kill each other and never quite managing. Family.' }]]] : []),
        ...(seen('SP') ? [['Ask about the Spire', [
          { w: 'ashwright', t: 'The hamlet on the sea wall bought every bell I ever cast. Every one of ’em rang for a funeral in the end.' },
          { w: 'ashwright', t: F('boss:cindervane') ? 'And the drake’s gone quiet. Sky’s the wrong colour without it.' : 'There’s a drake up top, the last of ’em. Don’t fight it in the open.' }]]] : []),
        ...(F('boss:oswin') ? [['Ask about Oswin', [
          { w: 'ashwright', t: 'Oswin? That old wind-bag’s still walking? He owes me for a staff.' },
          { w: 'ashwright', t: 'Tell him— no. Don’t tell him anything. He’ll talk for a week, and every word of it’ll be about roads.' }]]] : []),
        ['Leave', []]] },
    ];
  }
  if (id === 'scribe') {
    const first = !F('s_met');
    return [
      ...(first ? [
        { w: 'scribe', t: '…Another page walks in. Hold still. I must record you.' },
        { w: 'scribe', t: 'I am the Hollow Scribe. I write down everything the ash forgets. In exchange for cinders, I teach what I have written.' },
        { do() { setF('s_met'); } }] : []),
      { choice: [['Learn spells', [{ shop: 'scribe' }]], ['Ask about the Omen', [
        { w: 'scribe', t: 'Morvain was the Root’s demigod warden. He guards the stair to the Crown, and he has forgotten why.' }]],
        ['Ask about Kalden', [{ w: 'scribe', t: 'A knight who swore to guard the Ashen Bell until someone worthy came to ring it. His oath has outlived his sanity. Oaths do that.' }]],
        ...(F('boss:unwritten') ? [['Ask about the Unwritten', [
          { w: 'scribe', t: '…So it found its ending. And it was you.' },
          { w: 'scribe', t: 'I wrote the Root down so it would never be forgotten. I never wrote how it ends. A story without an ending gets hungry.' },
          { w: 'scribe', t: 'Thank you, reader. The last page is yours now. I have left the rest of my notes above the Inkwell.' }]]] : []),
        ...(!F('boss:unwritten') && (SAVE.items.talon || seen('A')) ? [['Ask about the Archives', [
          { w: 'scribe', t: 'Above the Bell Ascent stand my Archives. Every page of the Root’s story is kept there. I kept it. I keep it still.' },
          { w: 'scribe', t: 'One book I left unfinished, open, in the Inkwell at the top. Do not read it. …You will read it. Everyone reads the last page first.' }]]] : []),
        ...(F('boss:bellringer') || seen('SP') ? [['Ask about the Spire', [
          { w: 'scribe', t: 'The hamlet on the sea wall drowned the night the wall broke. Its ringer tolled one name for every body the sea gave back.' },
          { w: 'scribe', t: F('boss:bellringer') ? 'He ran out of names before he ran out of bodies. Now he is out of both. I have written him down; that will have to do.' : 'He ran out of names before he ran out of bodies. He tolls anyway.' }]]] : []),
        ...(F('boss:first_ember') || seen('E') ? [['Ask about the First Ember', [
          { w: 'scribe', t: 'Before the Root there was a fire. I have one line about it, from the oldest tablet in the Archives: “The ash made it first.”' },
          { w: 'scribe', t: F('boss:first_ember') ? 'I know now what it made after. It made you. I have written that down too — forgive me, it is a habit.' : 'The tablet does not say what the ash made after. I have my suspicions. They are standing in front of me.' }]]] : []),
        ['Leave', []]] },
    ];
  }
  if (id === 'kalden') {
    if (!F('k_met1')) return [
      { w: 'kalden', t: 'Stand back. That knight in black does not tire, and neither do I — but I have been at this a very long time.' },
      { w: 'kalden', t: 'Ser Kalden, of the Bell. My oath is to guard the Ashen Bell until one worthy comes to ring it. None have. You won’t either.' },
      { w: 'kalden', t: '…Still. You have steady hands. If you live long enough to reach the roots, look for me.' },
      { do() { setF('k_met1'); } },
    ];
    if (room.id === 'C4') return [
      { w: 'kalden', t: 'You killed the Hound. Then perhaps you are the one.' },
      { w: 'kalden', t: 'I hid the Bell in the Mire, below the Hall of Roots. The rot there gets into you. I can feel it in my arm already.' },
      { w: 'kalden', t: 'If I am not myself when you find me… do what must be done. And take this. A knight should not face rot unarmored.' },
      { give: 'c_horn' }, { do() { setF('k_left'); setF('k_met2'); } },
    ];
    const kl = ['The Bell must not fall to the unworthy.'];
    if (F('boss:champion')) kl.push('You beat the rampart’s champion. I sparred with him, when he still had a face.');
    if (F('boss:twins')) kl.push('Hael and Rime… we swore our oaths on the same morning. I had hoped theirs would outlast mine.');
    if (F('boss:unwritten')) kl.push('You came down from the Archives. The Scribe asked to write my oath down once. I told him some things should not be kept.');
    if (F('boss:oswin')) kl.push('The old pilgrim taught me to hold a blade when I was a boy. If you bested him, he let you. Or he is older than I thought.');
    return [{ w: 'kalden', t: kl[kl.length > 1 ? irand(1, kl.length - 1) : 0] }];
  }
  return [{ w: 'venn', t: '…' }];
}
const LORE = {
  r1: ['A knight’s grave. The inscription is half-eaten by ash:', '“Here lies one who waited for the Root to rise again. It did not. Neither did he.”'],
  k1: ['A cathedral headstone, gilded and cracked:', '“We prayed to the Pale Root for a thousand years. When it fell, we learned it had been praying too — to be allowed to die.”'],
  m3: ['A drowned shrine marker, slick with rot:', '“The Vessel was made of those who could not bear to leave. It is still making itself.”'],
  m5: ['A small grave, carefully tended:', '“Dame Iselle, sister of the Bell. Kalden kept watch here. He always will.”'],
  a5: ['A lectern, its book chained shut. One line is legible:', '\u201CWhat is never written cannot die. What is never written cannot rest.\u201D — the Scribe'],
  x4: ['Carved into living white bark:', '“The crown was never meant to be worn. It was meant to be given away.”'],
  // the new regions (graves placed by tools/regions/60_oldsecrets.py)
  hf1: ['An aqueduct-keeper’s marker, furred with rime:', '“The water ran uphill to the Root for a thousand years. We had only to keep it from freezing. We failed on the one night it mattered.”'],
  hf2: ['Two names on one stone — one scorched, one frozen over:', '“Hael and Rime, who swore to guard the Aqueduct together. They are keeping half of that promise still.”'],
  sp1: ['A hamlet grave crusted with salt. A small bell hangs from it:', '“When the sea wall broke, the ringer tolled once for each of us. Someone should toll once for him.”'],
  sp2: ['A marker carved from a drake’s rib:', '“The drakes carried the Root’s seeds on the storm. When the Root fell, the last of them carried the storm instead.”'],
  dp1: ['An iron plate riveted to the slag, stamped by a smith’s hammer:', '“Here lie the forge-hands. We fed the fire. The fire was never full.” — A.'],
  dp2: ['A stake of heartwood driven into the ash, still warm to the touch:', '“It was meant to lift the hammer when my arm failed. It never learned to set the hammer down.”'],
  e1: ['A bare stone. The ash around it has settled into the shape of someone kneeling:', '“Before the Root. Before the grace. A fire, alone, and very patient.”'],
};

// ---- dialogue runtime
let dialog = null;   // {steps, i, npc, chars, sel}
function startDialogue(steps, npc) {
  dialog = { steps: [...steps], i: -1, npc, chars: 0, sel: 0 }; state = 'dialog'; clearBuffer();
  if (npc) { npc.face = P.x < npc.x ? -1 : 1; npc.anim.set(npc.sh.has('talk') ? 'talk' : 'idle', true); P.face = npc.x < P.x ? -1 : 1; }
  advanceDialog();
}
function advanceDialog() {
  while (true) {
    dialog.i++; dialog.chars = 0; dialog.sel = 0;
    const s = dialog.steps[dialog.i];
    if (!s) return endDialog();
    if (s.do) { s.do(); continue; }
    if (s.give) { grantItem(s.give, P.x, P.y - 20); continue; }
    if (s.shop) { menu = { screen: 'shop', shop: s.shop, sel: 0, back: 'dialog' }; state = 'menu'; dialog.resume = true; return; }
    if (s.forge) { menu = { screen: 'forge', sel: 0, back: 'dialog' }; state = 'menu'; dialog.resume = true; return; }
    if (s.w || s.choice || s.lore) { sfx.menu(); return; }
  }
}
function endDialog() {
  if (dialog && dialog.npc) dialog.npc.anim.set('idle', true);
  const after = dialog && dialog.after; dialog = null; state = 'play'; clearBuffer(); saveGame();
  after && after();
  if (dialogAfterEnding && SAVE.ending) { dialogAfterEnding = false; finishStory(); }
}
function dialogInput(a) {
  const s = dialog.steps[dialog.i]; if (!s) return;
  const conf = ['confirm', 'interact', 'attack', 'jump'].includes(a);
  if (s.choice) {
    if (a === 'up') { dialog.sel = (dialog.sel + s.choice.length - 1) % s.choice.length; sfx.menu(); }
    else if (a === 'down') { dialog.sel = (dialog.sel + 1) % s.choice.length; sfx.menu(); }
    else if (conf) { const picked = s.choice[dialog.sel][1]; dialog.steps.splice(dialog.i + 1, 0, ...picked); advanceDialog(); }
    else if (['pause', 'back'].includes(a)) endDialog();
    return;
  }
  const text = s.t || '';
  if (conf) { if (dialog.chars < text.length) dialog.chars = text.length; else advanceDialog(); }
  else if (['pause', 'back'].includes(a)) endDialog();
}
function updateDialog(dt) { if (dialog) { dialog.chars += dt * 55; if (dialog.npc) dialog.npc.anim.update(dt); } }
function portrait(id, x, y, size = 48) {
  const sh = sheet(id);
  if (sh.ok) { const f = sh.frames[0]; vctx.imageSmoothingEnabled = false; vctx.drawImage(sh.img, f.x, f.y, f.w, f.h, ox + x * scale, oy + y * scale, size * scale, size * scale); }
  else { vctx.fillStyle = '#2a2230'; vctx.fillRect(ox + x * scale, oy + y * scale, size * scale, size * scale); }
}
function renderDialog() {
  const s = dialog.steps[dialog.i]; if (!s) return;
  const bx = 20, by = 148, bw = 344, bh = 60;
  panel(bx, by, bw, bh);
  const who = s.w ? (s.w === 'player' ? 'You' : NPC_INFO[s.w].name) : dialog.npc ? NPC_INFO[dialog.npc.id].name : '';
  const pid = s.w ? (s.w === 'player' ? 'portrait_player' : NPC_INFO[s.w].portrait) : dialog.npc ? NPC_INFO[dialog.npc.id].portrait : null;
  let tx = bx + 10;
  if (pid && !s.lore) { portrait(pid, bx + 6, by + 6, 48); tx = bx + 62; }
  if (who && !s.lore) text(who, tx, by + 14, 7.5, '#e6c77a', 'left', { spacing: 0.5 });
  if (s.choice) {
    // long menus scroll: four rows are visible, the selection stays in view, arrows show what's hidden
    const n = s.choice.length, vis = 4, top = clamp(dialog.sel - 1, 0, Math.max(0, n - vis));
    s.choice.slice(top, top + vis).forEach(([label], k) => {
      const i = top + k, y = by + 26 + k * 9.5, sel = i === dialog.sel;
      text((sel ? '▸ ' : '  ') + label, tx, y, 6.8, sel ? '#f5e3b0' : '#b8ab90', 'left', { weight: sel ? 600 : 400 });
    });
    if (top > 0) text('▴', bx + bw - 10, by + 14, 6, '#b08a3a', 'center');
    if (top + vis < n) text('▾', bx + bw - 10, by + bh - 6, 6, '#b08a3a', 'center');
  } else {
    const shown = (s.t || '').slice(0, Math.floor(dialog.chars));
    wrap(shown, bw - (tx - bx) - 12, 6.8).slice(0, 4).forEach((l, i) => text(l, tx, by + (s.lore ? 16 : 26) + i * 9, 6.8, s.lore ? '#d8cdb4' : '#e8dcc0', 'left', { weight: 400 }));
    if (dialog.chars >= (s.t || '').length) text('▾', bx + bw - 10, by + bh - 6, 7, '#b08a3a', 'center', { alpha: 0.5 + 0.5 * Math.sin(time * 6) });
  }
}
function panel(x, y, w, h, a = 0.9) {
  box(x, y, w, h, a);
  vctx.strokeStyle = 'rgba(176,138,58,0.35)'; vctx.lineWidth = Math.max(1, scale * 0.4);
  vctx.strokeRect(ox + (x + 2) * scale, oy + (y + 2) * scale, (w - 4) * scale, (h - 4) * scale);
  for (const [cx, cy] of [[x, y], [x + w, y], [x, y + h], [x + w, y + h]]) { vctx.fillStyle = '#b08a3a'; vctx.fillRect(ox + (cx - 1.5) * scale, oy + (cy - 1.5) * scale, 3 * scale, 3 * scale); }
}
function readGrave(key) { const L = LORE[key] || ['…']; startDialogue(L.map(t => ({ t, lore: true })), null); }

// ---- cinematics: sequences of illustrated panels with captions
let cine = null;
const INTRO = [
  { img: 'story_1', lines: ['Once, the Pale Root stood over the Hallow,', 'and its golden sap was grace, and grace was life.'] },
  { img: 'story_2', lines: ['Then the Root fell.', 'Its grace curdled into ash — into cinders — and rained upon the land.'] },
  { img: 'story_3', lines: ['The knights of the Hallow hollowed, one by one,', 'and only the shrine flames remembered their names.'] },
  { img: 'story_4', lines: ['But the ash does not let everything rest.', 'Rise, Ashbound. The Crown is calling.'] },
];
const ENDINGS = {
  kindle: [{ img: 'story_end_kindle', lines: ['You took the Sovereign’s place upon the root throne.', 'The Pale Root drank from your ember — and, slowly, it began to glow again.'] },
           { img: 'story_end_kindle', lines: ['Below, the shrines burned brighter for a thousand years.', 'Venn tended every one of them, and never once forgot your name.'] }],
  ash: [{ img: 'story_end_ash', lines: ['You let the last of the grace go out.', 'No one would rule the Hallow now. No one would feed on it, either.'] },
        { img: 'story_end_ash', lines: ['In the ash, something green took root.', 'Venn walked beside you into a morning no tree had promised.'] }],
  // the fourth ending (agent V): refuse the choice, and take the last flame from the one who would have carried it
  venn: [{ img: 'story_end_venn_1', lines: ['Venn’s ashes settled around your feet. In your hand the last flame burned —', 'small, and white, and yours alone.'] },
         { img: 'story_end_venn_2', lines: ['One by one, the shrines of the Hallow went dark.', 'No one came to light them again.'] },
         { img: 'story_end_venn_3', lines: ['The Pale Root rotted into the ash, and you walked on through the long dark,', 'carrying the only fire left in the world. It never once felt warm.'] }],
};
function playCine(slides, after) { cine = { slides, i: 0, t: 0, after }; state = 'cine'; clearBuffer(); }
function cineInput(a) {
  if (!cine) return;
  if (['pause', 'back'].includes(a)) { const f = cine.after; cine = null; f && f(); return; }
  if (['confirm', 'attack', 'jump', 'interact'].includes(a) && cine.t > 0.6) { cine.i++; cine.t = 0; if (cine.i >= cine.slides.length) { const f = cine.after; cine = null; f && f(); } }
}
function renderCine() {
  const s = cine.slides[cine.i]; if (!s) return;
  const a = clamp(cine.t / 1.0, 0, 1);
  vctx.fillStyle = '#000'; vctx.fillRect(0, 0, view.width, view.height);
  const sh = sheet(s.img);
  vctx.globalAlpha = a;
  if (sh.ok) {
    const f = sh.frames[0], zoom = 1 + cine.t * 0.012;
    const w = W * scale * zoom, h = H * scale * zoom;
    vctx.imageSmoothingEnabled = false;
    vctx.drawImage(sh.img, f.x, f.y, f.w, f.h, ox - (w - W * scale) / 2, oy - (h - H * scale) / 2, w, h);
  }
  vctx.globalAlpha = 1;
  const gr = vctx.createLinearGradient(0, oy + 150 * scale, 0, oy + H * scale);
  gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.85)');
  vctx.fillStyle = gr; vctx.fillRect(ox, oy + 150 * scale, W * scale, 66 * scale);
  s.lines.forEach((l, i) => text(l, W / 2, 186 + i * 11, 7.5, '#f1e6c8', 'center', { alpha: clamp((cine.t - 0.4 - i * 0.5) * 1.5, 0, 1), weight: 500 }));
  if (cine.t > 1.4) text('Enter — continue    Esc — skip', W - 10, 211, 5, '#8a7f6a', 'right', { alpha: 0.7 });
}

// ---- the ending: Venn appears at the throne, the player chooses (agent V: + the refusal -> web/src/37_venn.js)
function beginEnding() {
  // only in the Heart of the Root; if you wandered off, she waits there for you (37_venn.js enter hook)
  if (!room || room.id !== 'X5' || SAVE.ending || F('venn_betrayed')) return;
  const npc = props.find(p => p.vnEnd) || vnEndingNpc();
  sfx.kindle();
  setTimeout(() => { if (state === 'play' && props.includes(npc)) vnOfferEnding(npc); }, 600);
}
function vnOfferEnding(npc) {
  if (SAVE.ending || F('venn_betrayed')) return;
  const first = !npc.told; npc.told = true;
  dialogAfterEnding = true;
  startDialogue([
    ...(first ? [
      { w: 'venn', t: 'It’s over. She’s… at peace. I can feel the Root listening, for the first time since it fell.' },
      { w: 'venn', t: 'The throne is empty. The Root needs a heart, or it will finish dying — and all its grace with it.' },
      { w: 'venn', t: 'You could sit. Your ember would feed it for an age. Or you could walk away, and let the ash have the last word.' },
    ] : [{ w: 'venn', t: 'The throne is still empty, Ashbound. Choose.' }]),
    vnChoiceStep(npc),
  ], npc);
}
function vnChoiceStep(npc) {
  return { choice: [
    ['Take the throne — rekindle the Root', [{ do() { SAVE.ending = 'kindle'; } }]],
    ['Let the ash settle — walk away', [{ do() { SAVE.ending = 'ash'; } }]],
    ['Refuse — keep the last flame for yourself', [
      { w: 'venn', t: '…For yourself? The Root is dying. Every shrine I ever lit goes out with it.' },
      { w: 'venn', t: 'Please. Whatever the ash made you, it did not make you that.' },
      { choice: [
        ['The flame is mine. I will not give it up.', [
          { w: 'player', t: 'The flame is mine.' },
          { w: 'venn', t: '…' },
          { w: 'venn', t: 'Then the flame goes to one who will carry it.' },
          { do() { dialogAfterEnding = false; dialog.after = () => vnBetray(npc); } },
        ]],
        ['…No. Let me choose again.', [{ do() { dialog.steps.splice(dialog.i + 1, 0, vnChoiceStep(npc)); } }]],
      ] },
    ]],
  ] };
}
let dialogAfterEnding = false;
function finishStory() {
  const which = SAVE.ending || 'ash';
  SAVE.endings = SAVE.endings || {}; SAVE.endings[which] = 1; saveGame();
  playCine(ENDINGS[which], () => { state = 'ending'; stateT = 0; });
}

// ------------------------------------------------------------------ skill tree v2 (agent SK): five branches with forks and
// keystones, the Arsenal masteries, the Wayfarer ring, the point economy, respec and save migration (docs/SKILLTREE_CONTRACT.md).
// DATA (read by the tree screen in 58_skilltree_ui.js):
//   node  { id, br, name, desc, cost, x, y, req: [ids] (all), excl: [ids] (fork partners), key?: true, cls?: weapon class,
//           icon: 'sk_<id>', stat?: () => [[label, before, after], ...] }
//   layout: the five branches radiate from (0, 0), one node step ~= 1 unit; the Wayfarer ring sits at radius 9 around them;
//           the Arsenal page has its own frame (x -4..4, y -1.1..1.1).
//   SKILL_BRANCHES [{ id, name, color, desc }]; skillLearnable(id) -> { ok, why }; learnSkill(id) -> { ok, why };
//   skillBuildSummary() -> [strings]; skillOn(id) = learned and (for arsenal nodes) that class in hand.
const SKILL_BRANCHES = [
  { id: 'blade', name: 'Blade', color: '#e0cf9a', desc: 'Combos, heavy blows and critical hits.' },
  { id: 'ash', name: 'Ash', color: '#7fb0ff', desc: 'Sorcery and incantations, and the FP that feeds them.' },
  { id: 'veil', name: 'Veil', color: '#a79ce0', desc: 'Rolls, parries, stamina and defence.' },
  { id: 'blood', name: 'Blood', color: '#e0505a', desc: 'Bleed, lifesteal and fighting on the edge of death.' },
  { id: 'flame', name: 'Flame', color: '#ff9d4a', desc: 'Weapon arts, buffs and cooldowns.' },
  { id: 'arsenal', name: 'Arsenal', color: '#c9a45a', desc: 'One mastery per weapon class. Each works only while that class is in your hand.' },
  { id: 'way', name: 'Wayfarer', color: '#9cc78e', desc: 'Techniques and the road: better traversal, and more from what you find.' },
];
const SK_ANG = { blade: -90, ash: -18, veil: 54, blood: 126, flame: 198 };
// every branch shares one shape: a -> b -> c -> d -> e -> keystone, a side leaf off a (s1) and c (s2), a fork off b and d
const SK_SLOT = { a: [1.5, 0], s1: [2.3, 1.0], b: [2.6, 0], f1a: [3.5, -1.15], f1b: [3.5, 1.15], c: [3.7, 0], s2: [4.5, -1.15], d: [4.8, 0],
  f2a: [5.8, -1.25], f2b: [5.8, 1.25], e: [5.95, 0], k: [7.2, 0] };
const SK_REQ = { a: [], s1: ['a'], b: ['a'], f1a: ['b'], f1b: ['b'], c: ['b'], s2: ['c'], d: ['c'], f2a: ['d'], f2b: ['d'], e: ['d'], k: ['e'] };
const pct = (v, p) => Math.round(v * (1 + p / 100));
const dOr = (f, v = 0) => { try { return D && P ? f() : v; } catch (e) { return v; } };
// [slot, id, name, cost, desc, stat?]
const SK_BRANCH_NODES = {
  blade: [
    ['a', 'keen_edge', 'Keen Edge', 1, 'Melee damage +12%.', () => [['Light attack', dOr(() => Math.round(D.light)), dOr(() => pct(D.light, 12))]]],
    ['s1', 'heavy_hand', 'Heavy Hand', 1, 'Heavy attacks deal +15% damage and +25% stance damage.', () => [['Heavy attack', dOr(() => Math.round(D.heavy * 2)), dOr(() => pct(D.heavy * 2, 15))]]],
    ['b', 'fourth_strike', 'Fourth Strike', 1, 'Your light combo gains an extra finishing strike.', () => [['Combo length', dOr(() => moveset().combo.length), dOr(() => moveset().combo.length + 1)]]],
    ['f1a', 'measured_cut', 'Measured Cut', 2, 'The opening blow of a combo deals +30%.', () => [['Opening blow', 100, 130]]],
    ['f1b', 'flowing_form', 'Flowing Form', 2, 'Each blow after the first in a combo costs 35% less stamina.', () => [['Follow-up stamina', 100, 65]]],
    ['c', 'charged_arts', 'Charged Arts', 2, 'Heavy attacks charge 35% faster. A fully charged heavy looses a crescent of ash.', () => [['Charge time', 0.55, 0.35]]],
    ['s2', 'sunder', 'Sunder', 1, 'All your blows deal +25% stance damage: foes break open sooner.', () => [['Stance damage', 100, 125]]],
    ['d', 'executioner', 'Executioner', 2, 'Critical hits (ripostes, backstabs, stagger crits) deal +30% and refund 30 stamina.', () => [['Critical damage', 100, 130]]],
    ['f2a', 'blade_dancer', 'Blade Dancer', 2, 'Light attacks swing 15% faster.', () => [['Light swing speed', 100, 115]]],
    ['f2b', 'crushing_weight', 'Crushing Weight', 2, 'Charged heavy attacks can’t be interrupted and deal +20%.', () => [['Charged heavy', 100, 120]]],
    ['e', 'tireless', 'Tireless', 2, 'Light and heavy attacks cost 20% less stamina.', () => [['Attack stamina', 100, 80]]],
    ['k', 'relentless', 'Relentless', 4, 'KEYSTONE. Each hit in an unbroken combo deals +5% more, stacking to +25%. The stack is lost if you are hit or stop attacking for 1.2 s.', () => [['Damage at full stack', 100, 125]]],
  ],
  ash: [
    ['a', 'kindled_mind', 'Kindled Mind', 1, 'Spell damage +15%.', () => [['Spell power', dOr(() => Math.round(D.spell * 100)), dOr(() => pct(D.spell * 100, 15))]]],
    ['s1', 'deep_well', 'Deep Well', 1, 'Maximum FP +15%.', () => [['Max FP', dOr(() => D.maxFp), dOr(() => pct(D.maxFp, 15))]]],
    ['b', 'azure_thrift', 'Azure Thrift', 1, 'All spells cost 30% less FP.', () => [['Ash Bolt FP', 10, 7]]],
    ['f1a', 'quick_recall', 'Quick Recall', 2, 'Spell cooldowns are 30% shorter, and spells cost 10% less FP.', () => [['Spell cooldown', 100, 70], ['Spell FP', 100, 90]]],
    ['f1b', 'overcharge', 'Overcharge', 2, 'Spells deal +20% damage, but their cooldowns are 35% longer.', () => [['Spell damage', 100, 120], ['Spell cooldown', 100, 135]]],
    ['c', 'soul_siphon', 'Soul Siphon', 2, 'Melee hits restore 2 FP. Kills restore 8 FP and 3% HP.', () => [['FP per hit', 0, 2]]],
    ['s2', 'mana_font', 'Mana Font', 1, 'FP slowly refills on its own: 1.5 FP per second.', () => [['FP per second', 0, 1.5]]],
    ['d', 'memory_palace', 'Memory Palace', 2, 'One more spell slot.', () => [['Spell slots', dOr(() => SAVE.spellSlots, 2), dOr(() => SAVE.spellSlots + (has('memory_palace') ? 0 : 1), 3)]]],
    ['f2a', 'steady_cast', 'Steady Casting', 2, 'Blows can’t interrupt your casting, and you take 20% less damage while casting.', () => [['Damage while casting', 100, 80]]],
    ['f2b', 'swift_incant', 'Swift Incantation', 2, 'Spells are cast 25% faster.', () => [['Cast speed', 100, 125]]],
    ['e', 'resonance', 'Resonance', 2, 'A spell that strikes a foe makes your next melee blow within 3 s deal +30%.', () => [['Next melee blow', 100, 130]]],
    ['k', 'spellblade', 'Spellblade', 4, 'KEYSTONE. Every melee hit shaves 0.4 s off all your spell cooldowns.', () => [['Cooldown per hit', 0, 0.4]]],
  ],
  veil: [
    ['a', 'quickstep', 'Quickstep', 1, 'Rolling costs 30% less stamina and stays invulnerable a frame longer.', () => [['Roll stamina', 20, 14]]],
    ['s1', 'iron_flask', 'Iron Flask', 2, '+1 flask charge.', () => [['Flasks', dOr(() => flaskMax(), 4), dOr(() => flaskMax() + (has('iron_flask') ? 0 : 1), 5)]]],
    ['b', 'riposte_mastery', 'Riposte Mastery', 1, 'Wider parry window. Critical hits deal +50% and restore 5% HP.', () => [['Parry window (s)', 0.17, 0.24]]],
    ['f1a', 'deflect', 'Deflect', 2, 'A clean parry restores 30 stamina and 5% HP.', () => [['Stamina per parry', 0, 30]]],
    ['f1b', 'evasive_strike', 'Evasive Strike', 2, 'Attacks out of a roll deal +15% and cost no stamina.', () => [['Roll attack', 100, 115]]],
    ['c', 'steadfast', 'Steadfast', 2, 'Greater poise, and damage taken is reduced by 10%.', () => [['Poise', dOr(() => Math.round(D.poise)), dOr(() => Math.round(D.poise + (has('steadfast') ? 0 : 25)))]]],
    ['s2', 'enduring', 'Enduring', 1, 'Maximum stamina +10%.', () => [['Max stamina', dOr(() => D.maxSt), dOr(() => pct(D.maxSt, 10))]]],
    ['d', 'second_wind', 'Second Wind', 2, 'Rolling through an attack slows time, restores 30 stamina and empowers your next strike.', () => [['Stamina on a dodge', 0, 30]]],
    ['f2a', 'ironskin', 'Ironskin', 2, 'The first blow after 6 s unhurt deals 40% less damage.', () => [['First blow taken', 100, 60]]],
    ['f2b', 'featherfoot', 'Featherfoot', 2, 'After you roll through an attack, your next roll within 2 s costs no stamina.', () => [['Follow-up roll stamina', 14, 0]]],
    ['e', 'light_feet', 'Light Feet', 2, 'Stamina recovers 15% faster.', () => [['Stamina recovery', 100, 115]]],
    ['k', 'shadowstep', 'Shadowstep', 4, 'KEYSTONE. Roll through an attack at the last moment and you step out behind the attacker.', () => [['Last-moment dodge', 'stay', 'behind']]],
  ],
  blood: [
    ['a', 'bloodthirst', 'Bloodthirst', 1, 'Melee hits build Bleed (+16 per hit). A full bleed meter bursts for heavy damage.', () => [['Bleed per hit', dOr(() => Math.round(D.W.bleed || 0)), dOr(() => Math.round((D.W.bleed || 0) + 16))]]],
    ['s1', 'open_wounds', 'Open Wounds', 1, 'Bleed buildup on foes fades 60% slower.', () => [['Bleed fade', 100, 40]]],
    ['b', 'hemorrhage', 'Hemorrhage', 1, 'Bleed bursts deal +35% damage.', () => [['Bleed burst', 100, 135]]],
    ['f1a', 'vein_burst', 'Vein Burst', 2, 'When a foe’s bleed bursts, foes near it take half the burst too.', () => [['Burst spread', 0, 50]]],
    ['f1b', 'blood_drinker', 'Blood Drinker', 2, 'Killing a bleeding foe, or a critical hit on one, heals 5% HP.', () => [['Heal', 0, 5]]],
    ['c', 'last_stand', 'Last Stand', 2, 'Below 30% HP you deal 25% more damage.', () => [['Damage below 30% HP', 100, 125]]],
    ['s2', 'wrath', 'Wrath', 1, 'Taking a blow grants +10% damage for 3 s.', () => [['Damage after a blow', 100, 110]]],
    ['d', 'frenzy', 'Frenzy', 2, 'Below 50% HP you attack 12% faster.', () => [['Attack speed below 50% HP', 100, 112]]],
    ['f2a', 'blood_price', 'Blood Price', 2, 'You deal +10% damage, but flasks restore 15% less.', () => [['Damage', 100, 110], ['Flask heal', 100, 85]]],
    ['f2b', 'crimson_veil', 'Crimson Veil', 2, 'Below 30% HP you take 20% less damage.', () => [['Damage taken below 30% HP', 100, 80]]],
    ['e', 'leech', 'Leech', 2, 'Melee hits heal 0.8% of max HP (1.6% below 30% HP).', () => [['HP per hit', 0, dOr(() => +(D.maxHp * 0.008).toFixed(1))]]],
    ['k', 'crimson_pact', 'Crimson Pact', 4, 'KEYSTONE. Every bleed burst you cause heals 6% of your max HP, but you carry one fewer crimson flask.', () => [['Heal per bleed burst', 0, dOr(() => Math.round(D.maxHp * 0.06))], ['Crimson flasks', dOr(() => P.flasksR + (has('crimson_pact') ? 1 : 0), 4), dOr(() => P.flasksR - (has('crimson_pact') ? 0 : 1), 3)]]],
  ],
  flame: [
    ['a', 'ember_focus', 'Ember Focus', 1, 'Weapon arts deal +15% damage.', () => [['Art damage', 100, 115]]],
    ['s1', 'afterglow', 'Afterglow', 1, 'Using a weapon art restores 20 stamina.', () => [['Stamina per art', 0, 20]]],
    ['b', 'kindling', 'Kindling', 1, 'Weapon arts cost 20% less FP.', () => [['Art FP', dOr(() => ARTS[SAVE.art].fp, 12), dOr(() => Math.round(ARTS[SAVE.art].fp * 0.8), 10)]]],
    ['f1a', 'quick_charge', 'Quick Charge', 2, 'Weapon arts reach a full charge 40% sooner.', () => [['Charge time (s)', 0.6, 0.36]]],
    ['f1b', 'wildfire', 'Wildfire', 2, 'Uncharged weapon arts deal +12% damage.', () => [['Quick-release art', 100, 112]]],
    ['c', 'lingering_flame', 'Lingering Flame', 2, 'War Cry, Cinder Blade and other art buffs last 40% longer.', () => [['Cinder Blade (s)', 20, 28]]],
    ['s2', 'pyre_heart', 'Pyre Heart', 1, 'Melee hits restore 1 FP, or 2 while your weapon burns.', () => [['FP per hit', 0, 1]]],
    ['d', 'swift_arts', 'Swift Arts', 2, 'Weapon art cooldowns are 15% shorter.', () => [['Art cooldown', 100, 85]]],
    ['f2a', 'war_drums', 'War Drums', 2, 'Blows can’t interrupt your weapon arts, and you take 15% less damage while using one.', () => [['Damage during arts', 100, 85]]],
    ['f2b', 'ember_blood', 'Ember Blood', 2, 'After a weapon art, your next three melee hits deal +12%.', () => [['Next three hits', 100, 112]]],
    ['e', 'searing_arts', 'Searing Arts', 2, 'Weapon arts set the foes they strike burning for 3 s.', () => [['Burn per second', 0, dOr(() => Math.round(D.light * 0.35), 10)]]],
    ['k', 'kindled', 'Kindled', 4, 'KEYSTONE. Weapon arts leave a short trail of fire behind you, and every art cooldown is 20% shorter.', () => [['Art cooldown', 100, 80]]],
  ],
};
const SK_CLS_NAMES = { sword: 'Sword', dagger: 'Dagger', great: 'Great Weapon', spear: 'Spear', katana: 'Katana', staff: 'Staff', shield: 'Sword & Shield', twin: 'Twinblade', scythe: 'Scythe', whip: 'Whip' };
const SK_ARSENAL = [
  ['sword', 'Blade Discipline', 'Swords: every combo finisher looses a short arc of ash (60% of a light blow).'],
  ['dagger', 'Hollow Point', 'Daggers: critical hits deal +25% and burst the foe’s bleed at once.'],
  ['great', 'Earthshaker', 'Great weapons: heavy slams send a shockwave along the ground that hits foes beyond the blade.'],
  ['spear', 'Impaler', 'Spears: the heavy thrust lunges 30% further and breaks the stance of lesser foes.'],
  ['katana', 'Flash Step', 'Katanas: you are untouchable during the heavy draw-cut’s lunge.'],
  ['staff', 'Whirling Staff', 'Staves: the heavy spin costs 55% of your stamina instead of 80%, and knocks projectiles out of the air.'],
  ['shield', 'Thorned Bulwark', 'Shields: blows you block deal 35% of their damage back to the attacker.'],
  ['twin', 'Twin Rhythm', 'Twinblades: finishing the full five-hit combo quickens your blades by 15% for 4 s.'],
  ['scythe', 'Reaper', 'Scythes: reaping kills heal twice as much, and every scythe kill restores 10 FP.'],
  ['whip', 'Cracking Lash', 'Whips: the tip crack also staggers lesser foes.'],
];
const SK_WAY = [   // [id, name, cost, desc, needs item?, req]
  ['way_prosper', 'Prospector', 1, 'Foes drop 10% more cinders.', null, []],
  ['way_glint', 'Keen Eye', 1, 'Breakable walls glint when you are near them.', null, ['way_prosper']],
  ['way_remnant', 'Tight Purse', 2, 'When you die, you keep 30% of your cinders; only the rest is left behind.', null, ['way_glint']],
  ['way_hook', 'Long Root', 1, 'The Root Hook reaches 35% further.', 'hook', []],
  ['way_glide', 'Tailwind', 1, 'You glide 25% faster.', 'gale', []],
  ['way_dash', 'Second Ember', 1, 'A second Ember Dash in the air, once the first has finished.', 'emberdash', []],
  ['way_slam', 'Cinder Quake', 1, 'Cinder Slam sends a shockwave rolling along the ground both ways.', 'slam', []],
  ['way_wall', 'Talon Grip', 1, 'You slide down walls more slowly, and wall jumps carry you higher.', 'talon', []],
];
SKILLS.length = 0;
for (const [br, list] of Object.entries(SK_BRANCH_NODES)) {
  const th = SK_ANG[br] * Math.PI / 180, ids = {};
  for (const n of list) ids[n[0]] = n[1];
  for (const [slot, id, name, cost, desc, stat] of list) {
    const [d, l] = SK_SLOT[slot];
    const excl = slot === 'f1a' ? [ids.f1b] : slot === 'f1b' ? [ids.f1a] : slot === 'f2a' ? [ids.f2b] : slot === 'f2b' ? [ids.f2a] : [];
    SKILLS.push({ id, br, name, desc, cost, x: +(d * Math.cos(th) - l * Math.sin(th)).toFixed(2), y: +(d * Math.sin(th) + l * Math.cos(th)).toFixed(2),
      req: SK_REQ[slot].map(s => ids[s]), excl, key: slot === 'k' || undefined, icon: 'sk_' + id, stat, slot });
  }
}
SK_ARSENAL.forEach(([cls, name, desc], i) => SKILLS.push({ id: 'm_' + cls, br: 'arsenal', name, desc, cost: 2, x: (i % 5) * 2 - 4, y: i < 5 ? -1.1 : 1.1,
  req: [], excl: [], cls, icon: 'sk_m_' + cls, stat: () => [['Active with', SK_CLS_NAMES[cls], dOr(() => wcls() === cls ? 'in hand' : 'not in hand', '-')]] }));
SK_WAY.forEach(([id, name, cost, desc, item, req], i) => {
  const a = (-67.5 + i * 45) * Math.PI / 180;
  SKILLS.push({ id, br: 'way', name, desc, cost, x: +(9 * Math.cos(a)).toFixed(2), y: +(9 * Math.sin(a)).toFixed(2), req, excl: [], icon: 'sk_' + id, item });
});
const SKILL_BY = {}; for (const s of SKILLS) SKILL_BY[s.id] = s;
const SK_ITEM_NAME = { hook: 'the Root Hook', gale: 'the Gale Cloak', emberdash: 'the Ember Dash', slam: 'the Cinder Slam', talon: 'the Hound’s Talon' };

// ---- point economy: one point per two levels gained, plus every Memory Shard
function skillSpent(list = SAVE.skills) { return list.reduce((a, id) => a + (SKILL_BY[id] ? SKILL_BY[id].cost : 0), 0); }
function skillBudget() { return Math.floor((levelOf(SAVE.stats) - 1) / 2) + (SAVE.shards || 0); }
// arsenal masteries only work while their class is in hand (the mirror blade counts as the class it copies)
function skillOn(id) { if (!SAVE.skills.includes(id)) return false; const s = SKILL_BY[id]; return !s || !s.cls || wcls() === s.cls; }
function skillLearnable(id) {
  const s = SKILL_BY[id]; if (!s) return { ok: false, why: 'Unknown skill' };
  if (SAVE.skills.includes(id)) return { ok: false, why: 'Learned' };
  const lock = s.excl.find(x => SAVE.skills.includes(x));
  if (lock) return { ok: false, why: `Fork: you chose ${SKILL_BY[lock].name}` };
  const miss = s.req.filter(x => !SAVE.skills.includes(x));
  if (miss.length) return { ok: false, why: 'Requires ' + miss.map(x => SKILL_BY[x].name).join(' and ') };
  if (s.item && !SAVE.items[s.item]) return { ok: false, why: 'Requires ' + SK_ITEM_NAME[s.item] };
  const pts = skillPoints();
  if (pts < s.cost) return { ok: false, why: `Needs ${s.cost} point${s.cost === 1 ? '' : 's'} (you have ${pts})` };
  return { ok: true, why: `Learn for ${s.cost} point${s.cost === 1 ? '' : 's'}` };
}
function learnSkill(id) {
  const r = skillLearnable(id); if (!r.ok) { sfx.deny(); return r; }
  SAVE.skills.push(id); skOnLearn(id, true);
  sfx.levelup(); refreshDerived(); saveGame();
  return { ok: true, why: `${SKILL_BY[id].name} learned` };
}
// side effects that live in the save rather than in derive(): the extra flask and the extra spell slot
function skOnLearn(id, on) {
  if (id === 'iron_flask' && P) { if (on) P.flasksR++; else refillFlasks(); }
  if (id === 'memory_palace') {   // the slot rides in SAVE.spellSlots, so NG+ carries it with the skill
    if (on) SAVE.spellSlots++;
    else { SAVE.spellSlots = Math.max(1, SAVE.spellSlots - 1); SAVE.spellsEq = SAVE.spellsEq.slice(0, SAVE.spellSlots); if (SAVE.spell && !SAVE.spellsEq.includes(SAVE.spell)) SAVE.spell = SAVE.spellsEq[0] || null; }
  }
  if (id === 'crimson_pact' && P) { if (on) P.flasksR = Math.max(0, P.flasksR - 1); }
}
// what a build adds up to, in plain words, for the summary panel
const SK_SUM = {
  keen_edge: [['Melee damage', 12]], heavy_hand: [['Heavy damage', 15], ['Heavy stance damage', 25]], measured_cut: [['Opening blow damage', 30]],
  flowing_form: [['Follow-up stamina cost', -35]], charged_arts: [['Heavy charge time', -36]], sunder: [['Stance damage', 25]], executioner: [['Critical damage', 30]],
  blade_dancer: [['Light swing speed', 15]], crushing_weight: [['Charged heavy damage', 20]], tireless: [['Attack stamina cost', -20]],
  kindled_mind: [['Spell damage', 15]], deep_well: [['Max FP', 15]], azure_thrift: [['Spell FP cost', -30]], quick_recall: [['Spell cooldowns', -30], ['Spell FP cost', -10]],
  overcharge: [['Spell damage', 20], ['Spell cooldowns', 35]], swift_incant: [['Cast speed', 25]], steady_cast: [['Damage taken while casting', -20]], resonance: [['Melee after a spell hit', 30]],
  quickstep: [['Roll stamina cost', -30]], riposte_mastery: [['Critical damage', 50], ['Parry window', 41]], evasive_strike: [['Roll attack damage', 15]],
  steadfast: [['Damage taken', -10]], enduring: [['Max stamina', 10]], ironskin: [['First blow taken', -40]], light_feet: [['Stamina recovery', 15]],
  hemorrhage: [['Bleed burst damage', 35]], open_wounds: [['Bleed fade', -60]], last_stand: [['Damage below 30% HP', 25]], wrath: [['Damage after a blow', 10]],
  frenzy: [['Attack speed below 50% HP', 12]], blood_price: [['Damage', 10], ['Flask healing', -15]], crimson_veil: [['Damage taken below 30% HP', -20]],
  ember_focus: [['Weapon art damage', 15]], kindling: [['Art FP cost', -20]], quick_charge: [['Art charge time', -40]], wildfire: [['Quick-release art damage', 12]],
  lingering_flame: [['Art buff duration', 40]], swift_arts: [['Art cooldowns', -15]], war_drums: [['Damage taken during arts', -15]],
  ember_blood: [['Damage after an art (3 hits)', 12]], kindled: [['Art cooldowns', -20]], way_prosper: [['Cinders from foes', 10]], way_hook: [['Root Hook reach', 35]], way_glide: [['Glide speed', 25]],
};
const SK_SUM_TEXT = {
  fourth_strike: 'An extra combo strike', soul_siphon: 'Melee hits restore FP', mana_font: 'FP regenerates', memory_palace: '+1 spell slot', iron_flask: '+1 flask',
  deflect: 'Parries restore stamina and HP', second_wind: 'Perfect dodges restore stamina', featherfoot: 'Free follow-up rolls', bloodthirst: 'Every blow builds bleed',
  vein_burst: 'Bleed bursts spread', blood_drinker: 'Bleeding kills heal', leech: 'Melee lifesteal', afterglow: 'Arts restore stamina', pyre_heart: 'Melee hits restore FP', searing_arts: 'Arts set foes burning',
  way_glint: 'Breakable walls glint', way_remnant: 'Keep 30% of cinders on death', way_dash: 'Two Ember Dashes in the air', way_slam: 'Cinder Slam shockwaves', way_wall: 'Better wall grip',
};
function skillBuildSummary() {
  const tot = {}, out = [], order = [];
  for (const id of SAVE.skills) for (const [k, v] of SK_SUM[id] || []) { if (!(k in tot)) { tot[k] = 0; order.push(k); } tot[k] += v; }
  for (const k of order) if (tot[k]) out.push(`${k} ${tot[k] > 0 ? '+' : ''}${tot[k]}%`);
  for (const id of SAVE.skills) if (SK_SUM_TEXT[id]) out.push(SK_SUM_TEXT[id]);
  for (const id of SAVE.skills) { const s = SKILL_BY[id]; if (s && s.key) out.unshift('Keystone: ' + s.name); }
  for (const id of SAVE.skills) { const s = SKILL_BY[id]; if (s && s.cls) out.push(`${s.name} (${SK_CLS_NAMES[s.cls]}${wcls() === s.cls ? '' : ', inactive'})`); }
  return out;
}

// ================================================================== effects
// Most effects live here, on the shared hooks; the few that need a spot inside a hot function call the sk* helpers
// below from there (outgoing(), playerStrike(), hurtPlayer(), startArt(): see SHARED EDITS in the SK report).
const skL = () => SAVE.skills.length > 0;
const skFoes = () => targets().filter(t => !t.prop);
function skHeal(frac, x, y) { if (!P || P.state === 'dead') return 0; const n = Math.max(1, Math.round(D.maxHp * frac)); P.hp = Math.min(D.maxHp, P.hp + n); popup(x ?? P.x, (y ?? P.y) - 34, n, '#8fe08a'); return n; }
function skSpark(x, y, n, kind, sp = 70) { for (let i = 0; i < n; i++) particles.push({ x: x + rand(-4, 4), y: y + rand(-4, 4), vx: rand(-sp, sp), vy: -rand(10, sp), g: 200, life: rand(0.3, 0.6), kind }); }
// is this hit part of a weapon art? (projectiles remember whether an art loosed them)
function skArtCtx(pr) { return pr ? !!pr.skArt || (pr.skArt === undefined && P.state === 'art') : P.state === 'art'; }

// every skill-tree damage bonus, applied inside outgoing()
function skOutMul(kind, src) {
  if (!skL() || !P) return 1;
  const pr = src && src.owner === 'player' ? src : null, melee = kind !== 'spell';
  let m = 1;
  if (melee && has('keen_edge')) m *= 1.12;
  if (has('last_stand') && P.hp < D.maxHp * 0.3) m *= 1.25;
  if (has('blood_price')) m *= 1.1;
  if (has('wrath') && P.skWrathT > time) m *= 1.1;
  if (skArtCtx(pr)) {
    if (has('ember_focus')) m *= 1.15;
    if (has('wildfire') && !(pr && pr.skArt ? pr.skArt.ch : P.artCharged)) m *= 1.12;
    return m;
  }
  if (!melee || pr) return m;   // spells get theirs in derive(); a loose projectile carries no swing with it
  const A = ATK[P.state];
  if (A) {
    if (A.kind === 'heavy' && has('heavy_hand')) m *= 1.15;
    if (A.kind === 'heavy' && P.charged && has('crushing_weight')) m *= 1.2;
    if (has('measured_cut') && P.comboStep === 0) m *= 1.3;
    if (has('evasive_strike') && P.skRollAtk === P.hitSet) m *= 1.15;
  }
  if (P.state === 'riposte') { if (has('executioner')) m *= 1.3; if (skillOn('m_dagger')) m *= 1.25; }
  if (has('relentless')) m *= 1 + 0.05 * (P.skRel || 0);
  if (P.skResoT > time) m *= 1.3;
  if (P.skEmberN > 0) m *= 1.12;
  return m;
}
// stance (poise) damage of your melee blows, applied in playerStrike()
function skPoiseMul(A) { if (!skL()) return 1; return (has('sunder') ? 1.25 : 1) * (A.kind === 'heavy' && has('heavy_hand') ? 1.25 : 1); }
// blows that can't stagger you (hurtPlayer's armour check)
function skArmored() {
  if (!skL()) return false;
  if (P.state === 'cast' && has('steady_cast')) return true;
  if (P.state === 'art' && has('war_drums')) return true;
  const A = ATK[P.state]; if (A && A.kind === 'heavy' && (P.charged || P.charge > 0) && has('crushing_weight')) return true;
  return false;
}
function skArtCostMul() { return has('kindling') ? 0.8 : 1; }
function skCdMul(kind) {
  if (!skL()) return 1;
  if (kind === 'spell') return (has('quick_recall') ? 0.7 : 1) * (has('overcharge') ? 1.35 : 1);
  return (has('swift_arts') ? 0.85 : 1) * (has('kindled') ? 0.8 : 1);
}

HOOKS.derive.push(d => {
  if (!skL()) return;
  if (has('deep_well')) d.maxFp = Math.round(d.maxFp * 1.15);
  if (has('enduring')) d.maxSt = Math.round(d.maxSt * 1.1);
  if (has('kindled_mind')) d.spell *= 1.15;
  if (has('overcharge')) d.spell *= 1.2;
});
HOOKS.playerHurt.push((dmg, opt) => {
  if (!skL()) return dmg;
  let m = 1;
  if (has('ironskin') && time - (P.skHurtT ?? -99) > 6) { m *= 0.6; skSpark(P.x, P.y - 16, 6, 'spark'); }
  if (has('crimson_veil') && P.hp < D.maxHp * 0.3) m *= 0.8;
  if (has('steady_cast') && P.state === 'cast') m *= 0.8;
  if (has('war_drums') && P.state === 'art') m *= 0.85;
  P.skHurtT = time; P.skRel = 0;   // Relentless: a blow breaks the chain
  if (has('wrath')) P.skWrathT = time + 3;
  return dmg * m;
});
HOOKS.parry.push(() => {
  if (has('deflect')) { P.st = Math.min(D.maxSt, P.st + 30); skHeal(0.05); }
});
// dodges: Second Wind lives in hurtPlayer; Featherfoot and Shadowstep here
(HOOKS.negated = HOOKS.negated || []).push((dmg, dir, opt) => {
  if (!P || P.state !== 'roll') return;
  if (has('featherfoot')) P.skFreeRollT = time + 2;
  if (has('shadowstep') && P.anim.i <= 3 && !(P.skStepCd > time)) skShadowstep(dir, opt);
});
function skShadowstep(dir, opt) {
  let src = opt && opt.src && opt.src.hurtbox ? opt.src : null;
  if (!src) { let bd = 90; for (const t of skFoes()) { const hb = t.hurtbox && t.hurtbox(); if (!hb) continue; const cx = (hb.x0 + hb.x1) / 2, d = Math.abs(cx - P.x); if (d < bd && Math.sign(cx - P.x) === -dir && Math.abs(hb.y1 - P.y) < 60) { bd = d; src = t; } } }
  if (!src || src.alive === false) return false;
  const hb = src.hurtbox(); if (!hb) return false;
  const side = (hb.x0 + hb.x1) / 2 > P.x ? 1 : -1, nx = side > 0 ? hb.x1 + 9 : hb.x0 - 9;
  if (nx < 12 || nx > room.pw - 12 || [P.y - 4, P.y - 14, P.y - 24].some(y => solidAtPx(nx - 5, y) || solidAtPx(nx + 5, y))) return false;
  ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.35 });
  skSpark(P.x, P.y - 14, 10, 'ember', 60);
  P.x = nx; P.vx = 0; P.face = -side; P.inv = Math.max(P.inv, 0.25);
  setP('land', pHas('land') ? 'land' : 'idle', false);   // the roll ends where you land, a beat to find your feet, then a fresh combo at its back
  P.skStepCd = time + 0.8;
  skSpark(P.x, P.y - 14, 12, 'ember', 80); sfx.glint(); tone(300, 0.2, 0.06, 'sine', 3); hitstop = Math.max(hitstop, 0.05);
  return true;
}
// melee hits (playerStrike, plunge, spear dive)
HOOKS.strike.push((t, info, A) => {
  if (!skL() || !P) return;
  const once = P.skStrikeSet !== P.hitSet; P.skStrikeSet = P.hitSet;
  if (once && has('relentless')) { P.skRel = Math.min(5, (P.skRel || 0) + 1); P.skRelT = time; }
  if (P.skResoT > time) P.skResoT = 0;
  if (P.skEmberN > 0) P.skEmberN--;
  if (once && has('spellblade') && P.cds) { let any = false; for (const k in P.cds) if (k.startsWith('spell:') && P.cds[k] > time) { P.cds[k] -= 0.4; any = true; } if (any) particles.push({ x: P.x, y: P.y - 20, vx: 0, vy: -40, life: 0.4, kind: 'gold' }); }
  if (has('leech')) { const f = P.hp < D.maxHp * 0.3 ? 0.016 : 0.008; P.hp = Math.min(D.maxHp, P.hp + D.maxHp * f); }
  if (has('pyre_heart')) P.fp = Math.min(D.maxFp, P.fp + (P.fireT > 0 || D.W.fire ? 2 : 1));
  const lesser = t.alive !== false && !t.boss && !t.prop && t.breakStance && !(t.cfg && t.cfg.elite) && t.state !== 'stagger';
  if (skillOn('m_spear') && P.state === 'sp_heavy' && lesser) t.breakStance();
  if (skillOn('m_twin') && P.state === 'tw_5' && once) { P.skTwinT = time + 4; skSpark(P.x, P.y - 18, 8, 'gold'); }
  if (skillOn('m_scythe') && t.alive === false && !t.prop && !t.skReaped) { t.skReaped = true; P.fp = Math.min(D.maxFp, P.fp + 10); }
});
HOOKS.cast.push(() => { if (P) P.skCastT = time; });
// the doubled reap heal (scythe mastery)
{ const _reap = reapHeal; reapHeal = function (t) { _reap(t); if (skillOn('m_scythe')) _reap(t); }; }
// Whirling Staff: the spin is cheaper
{ const _ssc = staffSpinCost; staffSpinCost = function () { return _ssc() * (skillOn('m_staff') ? 55 / 80 : 1); }; }
// shorter / longer cooldowns (cdBase feeds both the timer and the HUD's cooldown pie)
{ const _cdb = cdBase; cdBase = function (kind, id) { return _cdb(kind, id) * skCdMul(kind); }; }
{ const _sc = spellCost; spellCost = function (id) { return Math.round(_sc(id) * (has('quick_recall') ? 0.9 : 1)); }; }
{ const _fm = flaskMul; flaskMul = function () { return _fm() * (has('blood_price') ? 0.85 : 1); }; }
// Crimson Pact: one fewer crimson flask
{ const _rf = refillFlasks; refillFlasks = function () { _rf(); if (P && has('crimson_pact')) P.flasksR = Math.max(0, P.flasksR - 1); }; }
{ const _wj = wallJump; wallJump = function () { _wj(); if (has('way_wall')) P.vy *= 1.14; }; }
{ const _gc = gainCinders; gainCinders = function (n, x, y) { return _gc(has('way_prosper') ? n * 1.1 : n, x, y); }; }
// Tight Purse: keep 30% of your cinders when you die
{ const _fd = finishDeath; finishDeath = function () { const keep = has('way_remnant') ? Math.floor(SAVE.cinders * 0.3) : 0; SAVE.cinders -= keep; _fd(); SAVE.cinders += keep; if (keep) { toast(`You kept ${keep} cinders`, 3); saveGame(); } }; }
// Thorned Bulwark (shield mastery): a blocked blow bites back
{ const _hurt = hurtPlayer; hurtPlayer = function (dmg, dir, id, opt = {}) {
  const guard = P && skillOn('m_shield') && isBlocking() && dir === -P.face && !iframes() && !(opt.parryable && P.state === 'parry' && P.parryWin > 0);
  const hp0 = P && P.hp, st0 = P && P.st, r = _hurt(dmg, dir, id, opt);
  if (guard && !r && P.hp === hp0 && P.st < st0 && opt.src && opt.src.hit && opt.src.alive !== false && !opt.src.prop) {
    const hb = opt.src.hurtbox && opt.src.hurtbox();
    if (hb && Math.abs((hb.x0 + hb.x1) / 2 - P.x) < 90) { opt.src.hit({ dmg: dmg * 0.35, poise: 12, dir: -dir, kind: 'light', x: clamp(P.x + P.face * 14, hb.x0 + 2, hb.x1 - 2), y: P.y - 18, melee: true }); skSpark(P.x + P.face * 12, P.y - 18, 8, 'spark', 90); }
  }
  return r;
}; }
// Cinder Quake: the slam rolls out as a pair of ground shockwaves
const SKW = { waves: [], trail: [] };
{ const _si = slamImpact; slamImpact = function () { _si(); if (has('way_slam') && P.state !== 'air') for (const d of [-1, 1]) SKW.waves.push({ x: P.x + d * 30, y: P.y, d, t: 0, hit: new Set(), dmg: outgoing(D.heavy, 0.9, 'melee', { owner: 'player', skArt: false }) }); }; }

// ---- per-frame: detect starts of attacks/rolls/arts, keep timers, poll foes for bleed bursts, burns and kills
const skSeen = new WeakMap();
function skNewAttack(A) {
  const cls = A.cls, first = P.comboStep === 0;
  let cost = A.staffSpin ? 0 : A.cost * D.W.stam * (A.kind === 'heavy' && charmOn('c_brand') ? 0.8 : 1), refund = 0;
  if (has('tireless') && (A.kind === 'light' || A.kind === 'heavy')) refund += 0.2;
  if (has('flowing_form') && P.comboStep > 0) refund += 0.35;
  if (has('evasive_strike') && P.skPrev === 'roll') { P.skRollAtk = P.hitSet; refund = 1; }
  if (refund) P.st = Math.min(D.maxSt, P.st + cost * Math.min(1, refund));
  // attack speed: Blade Dancer (lights), Frenzy (below half HP), Twin Rhythm
  let sp = 1;
  if (has('blade_dancer') && A.kind === 'light') sp *= 1.15;
  if (has('frenzy') && P.hp < D.maxHp * 0.5) sp *= 1.12;
  if (P.skTwinT > time && skillOn('m_twin')) sp *= 1.15;
  if (sp !== 1) P.anim.speed *= sp;
  P.skRelT = time;   // Relentless: swinging keeps the chain alive
}
HOOKS.update.push(dt => {
  if (!P || !D || P.state === 'dead') { if (P) P.skRel = 0; return; }
  const st = P.state, A = ATK[st], L = skL();
  // new swing / art / roll / cast
  if (A && P.hitSet !== P.skAtkSet) { P.skAtkSet = P.hitSet; if (L) skNewAttack(A); }
  if (st === 'roll' && P.skPrev !== 'roll' && L) {
    if (has('featherfoot') && P.skFreeRollT > time) { P.st = Math.min(D.maxSt, P.st + (has('quickstep') ? 14 : 20)); P.skFreeRollT = 0; skSpark(P.x, P.y - 8, 6, 'gold', 40); }
  }
  if (st === 'cast' && P.skPrev !== 'cast' && has('swift_incant')) P.anim.speed *= 1.25;
  if (st === 'art' && P.artCount !== P.skArtN) {
    P.skArtN = P.artCount; P.skArtT = time;
    if (has('afterglow')) P.st = Math.min(D.maxSt, P.st + 20);
    if (has('ember_blood')) P.skEmberN = 3;
  }
  if (st === 'art') P.skArtEnd = time;
  if (st === 'riposte' && P.skPrev !== 'riposte' && L) {
    if (has('executioner')) P.st = Math.min(D.maxSt, P.st + 30);
    if (has('blood_drinker') && P.crit && P.crit.bleed > 0) skHeal(0.05);
    P.skCritBleed = skillOn('m_dagger') ? P.crit : null;
  }
  if (st === 'riposte' && P.skCritBleed && P.anim.i >= 3) { const t = P.skCritBleed; P.skCritBleed = null; if (t.alive !== false) skBleedBurst(t); }
  // Quick Charge: art charge builds 40% sooner (0.36 s instead of 0.6 s to a full charge)
  if (st === 'art' && P.artHold && P.artChargeT > 0 && has('quick_charge')) P.artChargeT += dt * 0.667;
  // Lingering Flame: War Cry / Cinder Blade last 40% longer
  if (has('lingering_flame')) { if (P.cryT > (P.skCry || 0) + 0.05) P.cryT *= 1.4; if (P.fireT > (P.skFire || 0) + 0.05) P.fireT *= 1.4; }   // they only ever rise when an art sets them
  P.skCry = P.cryT; P.skFire = P.fireT;
  // Relentless: the chain falls apart if you stop swinging
  if (P.skRel && time - (P.skRelT || 0) > 1.2) P.skRel = 0;
  // regen: Mana Font, Light Feet
  if (has('mana_font')) P.fp = Math.min(D.maxFp, P.fp + 1.5 * dt);
  if (has('light_feet') && P.stDelay <= 0 && st !== 'roll' && !A && P.st < D.maxSt) P.st = Math.min(D.maxSt, P.st + (st === 'idle' ? 70 : 58) * 0.15 * dt * (st === 'guard' || st === 'block' ? 0.35 : 1));
  // arsenal: frame-exact bits of a swing
  if (A && P.skLunge === P.hitSet && !P.anim.changed) { P.vx *= 1.3; P.skLunge = null; }
  if (A && L) skArsenalFrame(A);
  // Second Ember (Wayfarer): a second air dash with the Ember Dash, like the Stormdrake Feather (they don't stack)
  if (has('way_dash') && SAVE.items.emberdash && !charmOn('c_feather')) { if (P.ground) P.skDash = 1; else if (!P.airDash && P.skDash && st !== 'roll') { P.airDash = true; P.skDash = 0; } }
  // mark projectiles an art loosed
  for (const pr of projectiles) if (pr.owner === 'player' && pr.skArt === undefined) pr.skArt = st === 'art' ? { ch: !!P.artCharged } : false;
  skPollFoes(dt);
  skUpdateKindled(dt); skUpdateWaves(dt);
  if (has('way_glint')) skGlint();
  P.skPrev = st;
});
function skArsenalFrame(A) {
  const an = P.anim, first = an.changed && an.i === A.active[0], cls = wcls();
  if (!first) return;
  if (cls === 'sword' && skillOn('m_sword') && A.kind === 'light' && !A.up && !A.down && isFinisher(P.state)) {   // Blade Discipline: a short arc of ash
    projectiles.push({ owner: 'player', kind: 'crescent', face: P.face, t: 0, hits: new Set(), x: P.x + P.face * 26, y: P.y - 16, vx: P.face * 260, vy: 0, dmg: D.light * 0.6, life: 0.32, r: 9, pierce: true, poise: 20, sh: 'fx_slash_air', skArt: false });
  }
  if (cls === 'great' && skillOn('m_great') && A.kind === 'heavy' && A.slam) {   // Earthshaker
    for (const d of [0.55, 1]) spawnFx('shockwave', P.x + P.face * (40 + 34 * d), P.y, 1, null, { speed: 1.3 });
    const r = rect(P.x + P.face * 30, P.y - 22, P.x + P.face * 100, P.y + 2), dmg = outgoing(D.heavy, 0.9, 'melee', { owner: 'player', skArt: false });
    for (const t of skFoes()) { const hb = hbOf(t); if (hb && overlap(r, hb) && !P.hitSet.has(t)) t.hit({ dmg, poise: 30, dir: P.face, kind: 'heavy', x: clamp(P.x + P.face * 60, hb.x0 + 2, hb.x1 - 2), y: P.y - 8, melee: true, big: true }); }
  }
  if (cls === 'spear' && skillOn('m_spear') && P.state === 'sp_heavy') P.skLunge = P.hitSet;   // Impaler: the lunge starts next frame; stretch it then
}
HOOKS.update.push(() => {   // untouchable / deflecting frames (run every frame of the swing)
  if (!P || !skL()) return;
  const A = ATK[P.state]; if (!A) return;
  if (P.state === 'kt_heavy' && skillOn('m_katana') && P.anim.i >= A.active[0] - 1 && P.anim.i <= A.active[1]) {   // the lunge, not the charge
    P.inv = Math.max(P.inv, 0.05); if (Math.random() < 0.5) ghosts.push({ f: P.anim.frame, x: P.x, y: P.y, face: P.face, life: 0.15 }); }
  if (A.staffSpin && skillOn('m_staff') && P.anim.i >= A.active[0] - 1 && P.anim.i <= A.active[1] + 1)
    for (const pr of projectiles) if (pr.owner !== 'player' && pr.life > 0 && Math.abs(pr.x - P.x) < 40 && Math.abs(pr.y - (P.y - 16)) < 30) { pr.life = 0; skSpark(pr.x, pr.y, 6, 'spark', 80); sfx.parry(); }
});
// bleed bursts, kills and burns: watch every foe's bleed meter and HP from frame to frame (works for every boss and foe class)
function skBleedBurst(t) {   // an instant burst (Hollow Point), same numbers as a natural one
  const bd = Math.round(t.boss ? t.maxHp * 0.06 + 40 : (t.maxHp || 100) * 0.15 + 20), hb = t.hurtbox && t.hurtbox();
  t.bleed = 0; const s = skSeen.get(t); if (s) s.bleed = 0; sfx.bleed(); spawnFx(fxOr('bleed', 'blood'), t.x, hb ? (hb.y0 + hb.y1) / 2 : t.y - 14, P.face);
  t.hit({ dmg: bd, poise: 0, dir: P.face, kind: 'spell', dot: true, x: t.x, y: hb ? hb.y0 : t.y - 20, quiet: true }); skOnBurst(t, bd);
}
function skOnBurst(t, bd) {
  if (has('hemorrhage') && t.alive !== false) t.hit({ dmg: bd * 0.35, poise: 0, dir: P.face, kind: 'spell', dot: true, x: t.x, y: t.y - 20, quiet: true });
  if (has('crimson_pact')) { skHeal(0.06); for (let i = 0; i < 10; i++) particles.push({ x: t.x + rand(-6, 6), y: t.y - rand(6, 26), vx: (P.x - t.x) * rand(1.5, 2.5), vy: (P.y - 16 - t.y) * rand(1, 2) - 30, life: 0.5, kind: 'blood' }); }
  if (has('vein_burst')) for (const o of skFoes()) if (o !== t && Math.hypot(o.x - t.x, o.y - t.y) < 70) { o.hit({ dmg: bd * 0.5, poise: 0, dir: sign(o.x - t.x), kind: 'spell', dot: true, x: o.x, y: o.y - 16, quiet: true }); spawnFx(fxOr('bleed', 'blood'), o.x, o.y - 14, 1); }
}
function skPollFoes(dt) {
  const list = [...enemies]; if (boss) { if (boss.parts) list.push(...boss.parts); else list.push(boss); }
  const art = P.state === 'art' || time - (P.skArtEnd ?? -9) < 0.8, sear = has('searing_arts') && art;
  const reso = has('resonance') && time - (P.skCastT ?? -9) < 2.5 && !art && !ATK[P.state] && !(P.skResoT > time);
  for (const t of list) {
    if (!t || t.prop) continue;
    let s = skSeen.get(t); if (!s) { s = { bleed: t.bleed || 0, hp: t.hp, alive: t.alive !== false }; skSeen.set(t, s); continue; }
    const alive = t.alive !== false, bleed = t.bleed || 0;
    // a burst drops the meter from a real build-up straight to zero
    if (skL() && s.bleed > 12 && bleed === 0 && t.hp < s.hp) skOnBurst(t, Math.round(t.boss ? t.maxHp * 0.06 + 40 : (t.maxHp || 100) * 0.15 + 20));
    if (s.alive && !alive && skL()) { if (has('blood_drinker') && (s.bleed > 0)) skHeal(0.05, t.x, t.y); }
    if (has('open_wounds') && alive && bleed > 0 && bleed < 100) t.bleed = Math.min(99, bleed + (t.boss ? 5 : 6) * 0.6 * dt);
    if (sear && alive && t.hp < s.hp && !t.skBurnT) t.skBurnT = 3;
    if (reso && s.alive && t.hp < s.hp) P.skResoT = time + 3;   // a killing blow counts too
    if (t.skBurnT > 0 && alive) {
      t.skBurnT -= dt; t.skBurnTick = (t.skBurnTick || 0) - dt;
      if (Math.random() < 0.4) particles.push({ x: t.x + rand(-8, 8), y: t.y - rand(4, 28), vx: 0, vy: -rand(20, 50), life: 0.4, kind: 'fire' });
      if (t.skBurnTick <= 0) { t.skBurnTick = 0.5; t.hit({ dmg: D.light * 0.175, poise: 0, dir: 1, kind: 'spell', dot: true, x: t.x, y: t.y - 16, fire: true, quiet: true }); }
      if (t.skBurnT <= 0) t.skBurnT = 0;
    }
    s.bleed = t.bleed || 0; s.hp = t.hp; s.alive = t.alive !== false;
  }
}
// Kindled: arts leave a trail of fire
function skUpdateKindled(dt) {
  if (has('kindled') && P.state === 'art' && P.ground) {
    const last = SKW.trail[SKW.trail.length - 1];
    if (!last || Math.abs(last.x - P.x) > 12 || time - last.born > 0.25) SKW.trail.push({ x: P.x, y: P.y, t: 0, born: time, life: 1.5 });
  }
  if (!SKW.trail.length) return;
  for (const f of SKW.trail) {
    f.t += dt;
    if (Math.random() < 0.5) particles.push({ x: f.x + rand(-7, 7), y: f.y - rand(0, 6), vx: rand(-6, 6), vy: -rand(20, 60), life: rand(0.3, 0.6), kind: 'fire' });
    addLight(f.x, f.y - 6, 22, '255,150,60', 0.55 * (1 - f.t / f.life));
    const r = rect(f.x - 9, f.y - 16, f.x + 9, f.y + 1);
    for (const t of skFoes()) {
      if ((t.skTrailT || 0) > time) continue;
      const hb = t.hurtbox && t.hurtbox(); if (!hb || !overlap(r, hb)) continue;
      t.skTrailT = time + 0.35;
      t.hit({ dmg: outgoing(D.light, 0.3, 'melee', { owner: 'player', skArt: false }), poise: 2, dir: sign(t.x - f.x), kind: 'fire', x: t.x, y: f.y - 8, fire: true, quiet: true });
    }
  }
  SKW.trail = SKW.trail.filter(f => f.t < f.life);
}
function skUpdateWaves(dt) {
  for (const w of SKW.waves) {
    w.t += dt; w.x += w.d * 240 * dt;
    if (Math.random() < 0.8) particles.push({ x: w.x + rand(-4, 4), y: w.y - 1, vx: w.d * rand(10, 40), vy: -rand(30, 100), g: 380, life: rand(0.3, 0.6), kind: Math.random() < 0.5 ? 'rock' : 'fire' });
    addLight(w.x, w.y - 8, 26, '255,160,80', 0.6);
    if (solidAtPx(w.x + w.d * 6, w.y - 6) || !solidAtPx(w.x, w.y + 4)) w.t = 99;   // walls and ledges stop it
    const r = rect(w.x - 10, w.y - 22, w.x + 10, w.y + 2);
    for (const t of skFoes()) { if (w.hit.has(t)) continue; const hb = hbOf(t); if (hb && overlap(r, hb)) { w.hit.add(t); t.hit({ dmg: w.dmg, poise: 50, dir: w.d, kind: 'heavy', x: w.x, y: w.y - 10, melee: true, big: true }); } }
    hitBreakables(r);
  }
  SKW.waves = SKW.waves.filter(w => w.t < 0.5);
}
// Keen Eye: breakable walls glint nearby (the Librarian's Lantern already does this)
function skGlint() {
  if (charmOn('c_lantern') || !room || !room.grid) return;
  const tx0 = Math.floor(P.x / TILE), ty0 = Math.floor((P.y - 12) / TILE);
  for (let ty = ty0 - 5; ty <= ty0 + 5; ty++) for (let tx = tx0 - 7; tx <= tx0 + 7; tx++) {
    if (tx < 0 || ty < 0 || tx >= room.w || ty >= room.h || room.grid[ty * room.w + tx] !== T_BREAK) continue;
    addLight(tx * TILE + 8, ty * TILE + 8, 20, '255,210,140', 0.25 + 0.15 * Math.sin(time * 3 + tx + ty));
    if (Math.random() < 0.012) particles.push({ x: tx * TILE + rand(2, 14), y: ty * TILE + rand(2, 14), vx: 0, vy: 0, life: 0.5, kind: 'gold' });
  }
}
HOOKS.enter.push(() => { SKW.waves = []; SKW.trail = []; });
HOOKS.death.push(() => { if (P) { P.skRel = 0; P.skEmberN = 0; } });
HOOKS.hud.push(() => {
  if (!P || !skL()) return;
  if (P.skRel > 0 && has('relentless')) { text(`Relentless +${P.skRel * 5}%`, 10, 42, 5.5, '#ffd070', 'left', { alpha: clamp(1.2 - (time - P.skRelT), 0.4, 1) }); }
  if (P.skEmberN > 0) text('Ember Blood ×' + P.skEmberN, 10, 50, 5.5, '#ff9d4a');
  if (P.skResoT > time) text('Resonance', 10, 58, 5.5, '#7fb0ff');
});

// ---- spells leave the tree: Ash Bolt is known from the start; the Scribe teaches Sunspear and Emberburst
for (const id of ['ash_bolt', 'sunspear', 'emberburst']) ITEMS['sp:' + id] = { name: SPELL_DEFS[id].name, icon: SPELL_DEFS[id].icon, sheet: SPELL_DEFS[id].sheet, desc: SPELL_DEFS[id].desc, spell: id };
if (SHOPS.scribe && !SHOPS.scribe.some(e => e.item === 'sp:sunspear')) SHOPS.scribe.unshift({ item: 'sp:sunspear', price: 1200, stock: 1 }, { item: 'sp:emberburst', price: 1800, stock: 1 });
{ const _ns = newSave; newSave = function () { const s = _ns(); s.spellsOwned = ['ash_bolt']; s.spellsEq = ['ash_bolt']; s.spell = 'ash_bolt'; s.skillv = 2; s.freeRespec = 1; return s; }; }

// ---- respec: the Pale Tear at a shrine (Rebirth), or once per journey for free at the Ashwright
function skillRespec(how) {
  if (!SAVE.skills.length) { toast('You have learned nothing to unlearn'); sfx.deny(); return false; }
  if (how === 'tear') { if (!(SAVE.inv.tear > 0)) { toast('Rebirth needs a Pale Tear'); sfx.deny(); return false; } SAVE.inv.tear--; }
  else if (how === 'free') { if (!(SAVE.freeRespec > 0)) { toast('The Ashwright can only do that once a journey'); sfx.deny(); return false; } SAVE.freeRespec--; }
  const had = [...SAVE.skills]; SAVE.skills = [];
  for (const id of had) skOnLearn(id, false);
  SAVE.spellsEq = SAVE.spellsEq.filter(s => spellKnown(s)); if (!SAVE.spellsEq.includes(SAVE.spell)) SAVE.spell = SAVE.spellsEq[0] || null;
  refreshDerived(); if (P) refillFlasks(); sfx.levelup(); flashScreen = 0.4; toast(`Reborn · ${skillPoints()} skill points to spend anew`); saveGame();
  return true;
}
{ const _npc = npcScript; npcScript = function (id) {
  const steps = _npc(id);
  if (id !== 'ashwright') return steps;
  const ch = steps.find(s => s.choice);
  if (ch && SAVE.freeRespec > 0 && SAVE.skills.length) ch.choice.splice(ch.choice.length - 1, 0, ['Reforge me (unlearn all skills, once)', [
    { w: 'ashwright', t: 'Hah. Hold still. Old habits come out like slag — hot, and all at once. Only doing this the once, mind.' },
    { do() { skillRespec('free'); } }]]);
  return steps;
}; }

// ---- save migration (skill tree v1 -> v2)
function skMigrate(o) {
  const old = [...(o.skills || [])];
  o.spellsOwned = o.spellsOwned || [];
  for (const id of ['ash_bolt', 'sunspear', 'emberburst']) if ((old.includes(id) || id === 'ash_bolt') && !o.spellsOwned.includes(id)) o.spellsOwned.push(id);
  if (!o.spellsEq.length && o.spellsOwned.includes('ash_bolt')) { o.spellsEq.push('ash_bolt'); o.spell = o.spell || 'ash_bolt'; }
  let keep = old.filter(id => SKILL_BY[id]);
  // drop what the new shape no longer supports: missing prerequisites, fork partners, and anything over budget
  for (let changed = true; changed;) { changed = false; for (const id of [...keep]) { const s = SKILL_BY[id]; if (s.req.some(r => !keep.includes(r)) || s.excl.some(x => keep.indexOf(x) > -1 && keep.indexOf(x) < keep.indexOf(id))) { keep = keep.filter(k => k !== id); changed = true; } } }
  const budget = Math.floor((levelOf(o.stats) - 1) / 2) + (o.shards || 0);
  while (keep.length && skillSpent(keep) > budget) keep.pop();
  o.skills = keep; o.skillv = 2; if (o.freeRespec === undefined) o.freeRespec = 1;
  return old.length > 0;
}
let skMigrateToast = false;
{ const _lg = loadGame; loadGame = function () {
  const o = _lg(); if (!o) return o;
  let raw = null; try { raw = JSON.parse(localStorage.getItem(SAVE_KEY)); } catch (e) {}
  if (!raw || !(raw.skillv >= 2)) { if (skMigrate(o)) skMigrateToast = true; }
  return o;
}; }
HOOKS.update.push(() => { if (skMigrateToast && state === 'play') { skMigrateToast = false; toast('The skill tree has changed: your points are refunded.', 5); saveGame(); } });

// headless tests (tools/shots/sk/): ev() evaluates inside the game scope
if (typeof window !== 'undefined' && window.__game) window.__game.sk = { SKILLS, SKILL_BY, skillLearnable, learnSkill, skillBuildSummary, skillOn, skillPoints: () => skillPoints(), ev: s => eval(s) };

// ------------------------------------------------------------------ gear: weapons, arts, charms, spells, items, shops
// scaling letters -> coefficient (bonus = coef * (stat - 10) / 35)
const GRADE = { S: 1.1, A: 0.9, B: 0.7, C: 0.5, D: 0.3, E: 0.15, '-': 0 };
const WEAPONS = {
  longsword: { name: 'Ashen Longsword', base: 30, sc: { str: 'D', dex: 'C', fth: '-' }, speed: 1.0, reach: 1.0, stam: 1.0, poise: 1.0, art: 'crescent',
    desc: 'The blade you woke holding. Balanced, dependable, dull with old ash.' },
  dagger: { name: 'Hollow Fang', base: 21, sc: { str: 'E', dex: 'A', fth: '-' }, speed: 1.4, reach: 0.72, stam: 0.65, poise: 0.6, bleed: 26, art: 'bloodstep',
    desc: 'A grave-robber’s curved knife. Quick cuts that open old wounds.' },
  greatsword: { name: 'Gravecleaver', base: 46, sc: { str: 'A', dex: 'D', fth: '-' }, speed: 0.76, reach: 1.25, stam: 1.45, poise: 1.9, armor: true, art: 'stormleap',
    desc: 'A slab of iron carved with runes of the ramparts’ dead. Carries the weight of a hundred oaths.' },
  spear: { name: 'Rootspear', base: 29, sc: { str: 'D', dex: 'B', fth: '-' }, speed: 1.05, reach: 1.45, stam: 0.95, poise: 0.9, art: 'warcry',
    desc: 'Its haft is a living root of the Pale Tree. It still reaches for the light.' },
  katana: { name: 'Duskveil', base: 29, sc: { str: 'E', dex: 'A', fth: 'E' }, speed: 1.15, reach: 1.1, stam: 0.9, poise: 0.9, bleed: 18, art: 'moonwave',
    desc: 'A blade forged under a dying moon. Its edge is pale and cold.' },
  maul: { name: 'Cinder Maul', base: 50, sc: { str: 'S', dex: '-', fth: '-' }, speed: 0.74, reach: 1.05, stam: 1.5, poise: 2.1, fire: 0.25, armor: true, art: 'cinderblade',
    desc: 'The head is a lump of the Root’s heartwood, still smouldering after the fall.' },
  oathbrand: { name: 'Oathbrand', base: 27, sc: { str: 'D', dex: 'D', fth: 'A' }, speed: 1.0, reach: 1.0, stam: 1.0, poise: 1.0, holy: 0.15, art: 'crescent',
    desc: 'A cathedral sword that remembers every prayer said over it. Spells cast by its bearer burn 15% brighter.' },
  kalden: { name: 'Oath of Kalden', base: 44, sc: { str: 'B', dex: 'B', fth: '-' }, speed: 0.9, reach: 1.2, stam: 1.2, poise: 1.5, armor: true, art: 'moonwave',
    desc: 'Ser Kalden swore on this blade to guard the Ashen Bell. He kept that oath past death, and past himself.' },
  gravetusk: { name: 'Gravetusk', base: 48, sc: { str: 'A', dex: 'D', fth: '-' }, speed: 0.78, reach: 1.25, stam: 1.4, poise: 1.9, armor: true, art: 'stormleap', boss: true,
    desc: 'The Hound\u2019s own tusk, still bound in golden root. Its finishing blows call roots up from the earth.' },
  omen: { name: 'Morvain\u2019s Eclipse', base: 36, sc: { str: 'C', dex: 'C', fth: 'C' }, speed: 1.0, reach: 1.1, stam: 1.05, poise: 1.2, art: 'crescent', boss: true,
    desc: 'The Omen\u2019s blade drinks the light it cuts through. Its swings leave golden arcs; heavy blows loose spears of light.' },
  rotmaw: { name: 'Rotmaw Cleaver', base: 50, sc: { str: 'S', dex: '-', fth: '-' }, speed: 0.74, reach: 1.05, stam: 1.5, poise: 2.0, armor: true, art: 'warcry', rot: true, boss: true,
    desc: 'Hacked from the Vessel\u2019s many bones. Every wound it opens festers, and heavy blows leave pools of rot.' },
  scepter: { name: 'Sovereign\u2019s Rootspear', base: 34, sc: { str: 'D', dex: 'C', fth: 'B' }, speed: 1.05, reach: 1.45, stam: 0.95, poise: 0.9, holy: 0.15, art: 'moonwave', boss: true,
    desc: 'The queen\u2019s own scepter. Its finishing thrusts loose lances of light; heavy blows call down pillars from the sky.' },
};
const ARTS = {
  crescent: { name: 'Ashen Crescent', fp: 12, desc: 'Loose a crescent of ash from the blade.' },
  bloodstep: { name: 'Bloodstep', fp: 8, desc: 'Dash through foes, invulnerable, cutting everything you pass. Builds bleed.' },
  stormleap: { name: 'Storm Leap', fp: 16, desc: 'Leap and crash down, the shockwave hurling foes on both sides.' },
  warcry: { name: 'War Cry', fp: 10, desc: 'A rallying roar. For 12 seconds, attacks deal +20% damage and you resist staggering.' },
  moonwave: { name: 'Moonwave', fp: 14, desc: 'A pale wave of moonlight that passes through every foe in its path.' },
  cinderblade: { name: 'Cinder Blade', fp: 14, desc: 'Set your weapon alight for 20 seconds: +25% damage, and every hit burns.' },
};
const CHARMS = {
  c_crimson: { name: 'Crimson Amber', desc: 'Maximum HP +15%.' },
  c_azure: { name: 'Azure Amber', desc: 'Maximum FP +25%.' },
  c_horn: { name: 'Stalwart Horn', desc: 'Attacks can’t be interrupted by weaker blows.' },
  c_fang: { name: 'Fang of the Vessel', desc: 'Bleed builds 50% faster.' },
  c_ember: { name: 'Ember Heart', desc: 'Fire and spell damage +15%.' },
  c_heel: { name: 'Quickened Heel', desc: 'Rolls travel further and stay invulnerable longer.' },
  c_crest: { name: 'Kalden’s Crest', desc: 'Melee damage +10%.' },
  c_scholar: { name: 'Scholar’s Ring', desc: 'Spells deal 15% more and cost 10% less.' },
  c_greed: { name: 'Greed Sigil', desc: 'Foes drop 25% more cinders. You take 10% more damage.' },
  c_grace: { name: 'Shard of Grace', desc: 'Flasks restore 25% more.' },
  c_thorn: { name: 'Thorned Crest', desc: 'Parry window +50%. Thorns hurt you half as much.' },
  c_veil: { name: 'Ashen Veil', desc: 'Foes notice you from shorter distances.' },
};
const SPELL_DEFS = {
  ash_bolt: { name: 'Ash Bolt', fp: 10, icon: 'ash_bolt', sheet: 'ui_icons', desc: 'A bolt of golden ash.' },
  sunspear: { name: 'Sunspear', fp: 18, icon: 'sunspear', sheet: 'ui_icons', desc: 'Hurl a spear of light that pierces every foe.' },
  emberburst: { name: 'Emberburst', fp: 26, icon: 'emberburst', sheet: 'ui_icons', desc: 'A ring of fire erupts around you.' },
  shards: { name: 'Grave Shards', fp: 12, icon: 's_shards', sheet: 'ui_icons2', desc: 'Three crystal shards that seek the nearest foe.' },
  lance: { name: 'Frost Lance', fp: 14, icon: 's_lance', sheet: 'ui_icons2', desc: 'A fast lance of ice. Shatters stance.' },
  warmth: { name: 'Warm Embers', fp: 22, icon: 's_warmth', sheet: 'ui_icons2', desc: 'Restore 35% HP over four seconds.' },
  rotmist: { name: 'Rot Mist', fp: 18, icon: 's_rotmist', sheet: 'ui_icons2', desc: 'Exhale a cloud of rot that eats at whatever stands in it.' },
};
Object.assign(SPELLS, SPELL_DEFS);
Object.assign(ITEMS, {
  emberstone: { name: 'Emberstone', icon: 'i_emberstone', sheet: 'ui_icons2', desc: 'A shard of the Root’s heartwood. Ashwright can temper a weapon with it.' },
  tear: { name: 'Pale Tear', icon: 'i_tear', sheet: 'ui_icons2', desc: 'Shed by the Root as it fell. Lets you unlearn your skills at a shrine (Rebirth).' },
  herb: { name: 'Golden Herb', icon: 'i_herb', sheet: 'ui_icons2', desc: 'Steeped into your flasks, it makes each draught 10% stronger.' },
  rotseed: { name: 'Rotseed', icon: 'i_rotseed', sheet: 'ui_icons2', desc: 'A seed that grew in the Mire’s filth, yet still carries grace. +1 flask charge.' },
  bell: { name: 'Ashen Bell', icon: 'i_bell', sheet: 'ui_icons2', desc: 'A small bell of blackened gold. Its peal opens the way to the Crown.' },
  letter: { name: 'Kalden’s Letter', icon: 'i_letter', sheet: 'ui_icons2', desc: '“If you read this, I have become what I swore to destroy. Take the bell. Ring it for me.”' },
  slot: { name: 'Memory Stone', icon: 'shard', sheet: 'ui_icons', desc: 'Your mind grows wide enough for another spell. +1 spell slot.' },
  charmslot: { name: 'Charm Notch', icon: 'c_veil', sheet: 'ui_icons2', desc: 'A notch worn into your gauntlet. +1 charm slot.' },
});
// item icons that live in ui_icons2
for (const id of Object.keys(WEAPONS)) ITEMS['w:' + id] = { name: WEAPONS[id].name, icon: 'w_' + id, sheet: 'ui_icons2', desc: WEAPONS[id].desc, weapon: id };
for (const id of Object.keys(CHARMS)) ITEMS[id] = { name: CHARMS[id].name, icon: id, sheet: 'ui_icons2', desc: CHARMS[id].desc, charm: true };
for (const id of Object.keys(SPELL_DEFS)) if (!['ash_bolt', 'sunspear', 'emberburst'].includes(id)) ITEMS['sp:' + id] = { name: SPELL_DEFS[id].name, icon: SPELL_DEFS[id].icon, sheet: 'ui_icons2', desc: SPELL_DEFS[id].desc, spell: id };
for (const id of Object.keys(ARTS)) ITEMS['art:' + id] = { name: 'Ash of ' + ARTS[id].name, icon: 'a_' + id, sheet: 'ui_icons2', desc: ARTS[id].desc, art: id };

// later files add gear through this so ITEMS entries (w:/sp:/art:/charm) stay in sync; icon sheet defaults to ui_icons3
function registerGear({ weapons = {}, arts = {}, charms = {}, spells = {}, items = {} } = {}, iconSheet = 'ui_icons3') {
  Object.assign(WEAPONS, weapons); Object.assign(ARTS, arts); Object.assign(CHARMS, charms); Object.assign(SPELL_DEFS, spells); Object.assign(SPELLS, spells); Object.assign(ITEMS, items);
  for (const id of Object.keys(weapons)) ITEMS['w:' + id] = { name: weapons[id].name, icon: 'w_' + id, sheet: weapons[id].iconSheet || iconSheet, desc: weapons[id].desc, weapon: id };
  for (const id of Object.keys(charms)) ITEMS[id] = { name: charms[id].name, icon: id, sheet: charms[id].iconSheet || iconSheet, desc: charms[id].desc, charm: true };
  for (const id of Object.keys(spells)) ITEMS['sp:' + id] = { name: spells[id].name, icon: spells[id].icon || 's_' + id, sheet: spells[id].sheet || iconSheet, desc: spells[id].desc, spell: id };
  for (const id of Object.keys(arts)) ITEMS['art:' + id] = { name: 'Ash of ' + arts[id].name, icon: 'a_' + id, sheet: arts[id].iconSheet || iconSheet, desc: arts[id].desc, art: id };
}

const SHOPS = {
  ashwright: [
    { item: 'emberstone', price: 450, stock: 8 }, { item: 'w:spear', price: 2400, stock: 1 }, { item: 'c_crimson', price: 1800, stock: 1 },
    { item: 'c_greed', price: 1200, stock: 1 }, { item: 'herb', price: 1500, stock: 1 },
  ],
  scribe: [
    { item: 'sp:shards', price: 1600, stock: 1 }, { item: 'sp:lance', price: 2200, stock: 1 }, { item: 'sp:warmth', price: 3000, stock: 1 },
    { item: 'c_scholar', price: 2600, stock: 1 }, { item: 'tear', price: 2000, stock: 2 }, { item: 'slot', price: 3500, stock: 1 },
  ],
};
function upgradeCost(lv) { return { stones: lv + 1, cinders: 250 * (lv + 1) }; }

// weapon attack rating for a stat block
function weaponAR(st, id, lv) {
  const w = WEAPONS[id], L = lv || 0;
  const k = s => GRADE[w.sc[s]] * (1 + 0.06 * L) * (softcap(st[s]) - 10) / 35;
  return w.base * (1 + 0.1 * L) * (1 + Math.max(-0.2, k('str') + k('dex') + k('fth')));
}
function gradeWithLv(g, lv) {   // for display: upgrades nudge the letter
  const order = ['-', 'E', 'D', 'C', 'B', 'A', 'S'];
  if (g === '-') return '-';
  return order[Math.min(6, order.indexOf(g) + (lv >= 5 ? 1 : 0))];
}

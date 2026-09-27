// ------------------------------------------------------------------ v9 Expansion 2 weapons (agent W)
// 21 weapons (classes in WEAPON_CLASS: new scythe + whip movesets in 04_player.js), boss signatures (★) in 04b_sigs.js.
// Tiers: Thornveil early · Barrows / Crimson mid · Necropolis mid-late · Dunes / Starfall late · NEO / Venn endgame.
registerGear({ weapons: {
  // ---- Thornveil Wood
  antler_scythe: { name: 'Antler of the Warden', base: 36, sc: { str: 'C', dex: 'C', fth: 'D' }, speed: 0.95, reach: 1.3, stam: 1.2, poise: 1.3, art: 'harvest_moon', boss: true,
    desc: 'The Warden grew this blade from its own crown and gave it only when the wood had no more need of it. Its sweeps wake the thorns under the soil.' },
  briar_scythe: { name: 'Briar Scythe', base: 32, sc: { str: 'C', dex: 'D', fth: '-' }, speed: 0.95, reach: 1.25, stam: 1.15, poise: 1.2, bleed: 16, art: 'reap',
    desc: 'A reaper’s scythe the bramble took back. Every sweep drags the harvest a little closer.' },
  thornwood_staff: { name: 'Thornwood Staff', base: 27, sc: { str: 'D', dex: 'C', fth: 'D' }, speed: 1.2, reach: 1.25, stam: 0.9, poise: 1.0, bleed: 10, art: 'whirlwind',
    desc: 'Cut green from Thornveil and never allowed to die. It still buds in spring, and still bites.' },
  // ---- The Drowned Barrows
  choir_harpoon: { name: 'Harpoon of the Drowned Choir', base: 36, sc: { str: 'D', dex: 'B', fth: 'D' }, speed: 1.05, reach: 1.45, stam: 0.95, poise: 1.0, art: 'tidal_surge', boss: true,
    desc: 'Bone of the leviathan that sang the barrows under. Its finishing thrusts loose lances of black water that drag their catch home.' },
  tidecleaver: { name: 'Tidecleaver', base: 50, sc: { str: 'A', dex: '-', fth: '-' }, speed: 0.75, reach: 1.25, stam: 1.45, poise: 1.9, armor: true, art: 'stormleap',
    desc: 'A drowned headsman’s cleaver, crusted with barnacle and coral. The sea did not blunt it; the sea never blunts anything.' },
  barnacle_fang: { name: 'Barnacle Fang', base: 23, sc: { str: 'E', dex: 'A', fth: '-' }, speed: 1.4, reach: 0.72, stam: 0.65, poise: 0.6, bleed: 24, art: 'bloodstep',
    desc: 'The Ferryman’s knife, a fang of shell. He took his fare in blood; so will you.' },
  // ---- The Crimson Manor
  sanguine_rapier: { name: 'Sanguine Rapier', base: 32, sc: { str: 'E', dex: 'A', fth: 'D' }, speed: 1.15, reach: 1.1, stam: 0.9, poise: 0.9, bleed: 18, art: 'blood_frenzy', boss: true,
    desc: 'The Countess never drew it for anything but a duel. Finishing thrusts loose needles of blood, and every critical blow drinks deep.' },
  carving_knife: { name: 'Carving Knife', base: 24, sc: { str: 'D', dex: 'A', fth: '-' }, speed: 1.4, reach: 0.74, stam: 0.65, poise: 0.65, bleed: 20, crit: 1.2, art: 'bloodstep',
    desc: 'The Butler carved for the Countess’s table for two hundred years. Backstabs and ripostes cut 20% deeper.' },
  crimson_scythe: { name: 'Crimson Scythe', base: 37, sc: { str: 'C', dex: 'C', fth: '-' }, speed: 0.95, reach: 1.3, stam: 1.2, poise: 1.25, bleed: 20, art: 'reap',
    desc: 'A dancing blade of the Crimson court, black-lacquered and ringed in gold. Its guests were reaped between courses.' },
  // ---- Necropolis of Vael
  vael_greatsword: { name: 'Greatsword of King Vael', base: 56, sc: { str: 'A', dex: 'D', fth: 'D' }, speed: 0.74, reach: 1.3, stam: 1.5, poise: 2.0, armor: true, art: 'moonwave', boss: true,
    desc: 'Fused from the bones of the king’s first court. Its blows leave ghost-fire in the wound; its heavies call spectral chains up from the grave.' },
  headsman_chain: { name: 'Headsman’s Chain', base: 32, sc: { str: 'B', dex: 'D', fth: '-' }, speed: 1.1, reach: 1.6, stam: 0.9, poise: 0.9, art: 'chain_drag',
    desc: 'The executioners of Vael hooked the condemned and drew them to the block. The chain still knows the way.' },
  gravechain: { name: 'Gravechain', base: 30, sc: { str: 'D', dex: 'B', fth: '-' }, speed: 1.15, reach: 1.6, stam: 0.85, poise: 0.8, bleed: 10, art: 'lash',
    desc: 'Rusted links and a knot of old bone. It cracks hardest at its very tip, like a mourner’s last word.' },
  // ---- The Sunscorched Dunes
  pharaoh_khopesh: { name: 'Khopesh of the Veiled Pharaoh', base: 35, sc: { str: 'C', dex: 'C', fth: 'C' }, speed: 1.0, reach: 1.1, stam: 1.05, poise: 1.2, fire: 0.15, art: 'solar_flare', boss: true,
    desc: 'The sun-king’s sickle-sword. Its finishers hurl a spinning disc of sunlight that returns to the hand; its heavies raise the sand.' },
  sun_sceptre: { name: 'Sun Sceptre', base: 34, sc: { str: 'D', dex: 'D', fth: 'A' }, speed: 1.15, reach: 1.25, stam: 0.9, poise: 1.0, holy: 0.2, art: 'cinderblade',
    desc: 'Gold ringed in lapis, crowned with the sun. The priests who carried it are dust; the sun is not. Spells cast by its bearer burn 20% brighter.' },
  scarab_spear: { name: 'Scarab Spear', base: 37, sc: { str: 'C', dex: 'B', fth: '-' }, speed: 1.05, reach: 1.45, stam: 0.95, poise: 1.0, art: 'warcry',
    desc: 'The Scarab Knights forged their blades from the shells of their sacred beetles, and their oaths from the sun’s path.' },
  // ---- The Starfall Crater
  starblade: { name: 'Starblade', base: 42, sc: { str: 'E', dex: 'A', fth: 'D' }, speed: 1.15, reach: 1.15, stam: 0.9, poise: 1.0, art: 'starfall', boss: true,
    desc: 'Astrel fell with this blade in her hand and it never stopped falling. Its finishers call shards of the sky down on your foes.' },
  meteor_maul: { name: 'Meteor Maul', base: 60, sc: { str: 'S', dex: '-', fth: 'E' }, speed: 0.7, reach: 1.1, stam: 1.55, poise: 2.3, armor: true, art: 'stormleap',
    desc: 'A fist of fallen star on an iron haft. It lands the way it arrived: all at once.' },
  orrery_whip: { name: 'Orrery Lash', base: 36, sc: { str: 'D', dex: 'B', fth: 'D' }, speed: 1.15, reach: 1.6, stam: 0.85, poise: 0.85, art: 'lash',
    desc: 'The Orrery Sentinel measured the heavens with this chain of brass and star-glass. It measures other things now.' },
  // ---- NEO-HALLOW
  saint_lance: { name: 'SAINT-0 Lance', base: 44, sc: { str: 'D', dex: 'B', fth: 'C' }, speed: 1.05, reach: 1.5, stam: 0.95, poise: 1.0, art: 'thunder_lunge', boss: true,
    desc: 'ERR: RELIC NOT FOUND. A lance of hard light from a city that should not exist. Its finishers draw neon lines through the world; its wounds glitch and strike again.' },
  plasma_katana: { name: 'Plasma Katana', base: 40, sc: { str: 'E', dex: 'A', fth: '-' }, speed: 1.2, reach: 1.1, stam: 0.9, poise: 0.9, bleed: 10, art: 'overclock',
    desc: 'A blade of magenta light from NEO-HALLOW. It hums a song no one in Cinderhollow has heard.' },
  // ---- Sister Venn
  last_kindling: { name: 'The Last Kindling', base: 43, sc: { str: 'C', dex: 'C', fth: 'B' }, speed: 1.0, reach: 1.35, stam: 1.2, poise: 1.35, fire: 0.2, holy: 0.1, art: 'pale_pyre', boss: true,
    desc: 'Venn’s scythe of root and pale flame. She kept the last ember alive for you; now it is yours to tend. Its blows leave pyres of white fire where foes stood.' },
} });

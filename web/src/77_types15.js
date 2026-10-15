// ------------------------------------------------------------------ v15: five new weapon types (platform agent, docs/v15/platform.md)
// Registers the Switch Axe, Close-range Bow, Martial Arts, Scythe and Warbell additively on top of the nine
// (74_arsenal9.js owns the type system; this file only extends its tables). Design spec: docs/WEAPON_REVAMP.md Part C.
//   type     prefix  weapon id            weapon                  art (default, locked)   spec
//   saxe     sx_     gravegrinder         Gravegrinder            magma_quake             C1
//   bow      bw_     ashstring            Ashstring Recurve       backstep_slash          C2
//   fist     ft_     penitent_knuckles    Penitent's Knuckles     bloodstep               C3
//   scythe   sc_     requiem_scythe       Requiem                 reap                    C4
//   bell     wb_     dirge_bell           Dirgebell               warcry                  C5
// Each type's moves live in its own web/src/78_mech_<type>.js (one mvRegister(type, T, moves), owned by its moveset agent).
// Weapon overlays wpn_<id> come from art/gen_player.py (art/player_v15_weapons.py); icons w_<id> from art/gen_ui15.py.
// Saves: nothing new. SAVE.weapons gains the five ids at +0 (74_arsenal9.js's loadGame fills any missing type), mastery
// is keyed by type id as for the nine; old saves (any wv) load unchanged.

const WTYPES15 = ['saxe', 'bow', 'fist', 'scythe', 'bell'];
registerGear({ weapons: {
  gravegrinder: { name: 'Gravegrinder', base: 42, sc: { str: 'B', dex: 'C', fth: '-' }, speed: 0.86, reach: 1.2, stam: 1.3, poise: 1.6, armor: true, art: 'magma_quake',
    desc: 'A gravedigger’s blade that folds out into a toothed axe. Its phial drinks the heat of every cut, and when it is full the teeth begin to turn.' },
  ashstring: { name: 'Ashstring Recurve', base: 42, sc: { str: 'E', dex: 'A', fth: '-' }, speed: 1.15, reach: 1.3, stam: 0.85, poise: 0.8, art: 'backstep_slash',
    desc: 'A horn-tipped recurve strung with braided ash. The hunters of the Hollow drew it at arm’s length, close enough to see the light go out.' },
  penitent_knuckles: { name: 'Penitent’s Knuckles', base: 42, sc: { str: 'C', dex: 'B', fth: '-' }, speed: 1.35, reach: 0.7, stam: 0.75, poise: 0.9, art: 'bloodstep',
    desc: 'Iron knuckles over wrappings that are never quite dry. The penitents of the cathedral fought bare of blade, as their vow allowed.' },
  requiem_scythe: { name: 'Requiem', base: 42, sc: { str: 'C', dex: 'C', fth: 'E' }, speed: 0.95, reach: 1.35, stam: 1.05, poise: 1.1, bleed: 10, art: 'reap',
    desc: 'A black-hafted scythe whose edge burns violet with what it has gathered. It is said to sing the dead their last verse as it cuts.' },
  dirge_bell: { name: 'Dirgebell', base: 42, sc: { str: 'A', dex: '-', fth: 'D' }, speed: 0.8, reach: 1.1, stam: 1.35, poise: 1.8, armor: true, art: 'warcry',
    desc: 'A funeral bell of black iron on a chained haft. Each blow rings a note; the old tolls still remember how to steel a congregation.' },
} }, 'ui_icons15');
if (typeof ICON_SHEETS !== 'undefined' && !ICON_SHEETS.includes('ui_icons15')) ICON_SHEETS.push('ui_icons15');

Object.assign(WTYPE_INFO, {
  saxe: { weapon: 'gravegrinder', name: 'Switch Axe', short: 'S. Axe', art: 'magma_quake', prefix: 'sx_', first: 'sx_1', alt: 'gs_1', diff: 5, mech: 'The Switch Gauge and the morph',
    desc: 'A blade that earns its fury: build the Switch Gauge the hard way, then morph into a chainsaw axe until it runs dry.',
    str: 'The highest burst in the game once morphed, an armoured morph slash, a Full Release that empties the gauge.',
    weak: 'The gauge fills slowly and drains when you’re hit or whiff; the axe is slow and vents you when it runs dry.' },
  bow: { weapon: 'ashstring', name: 'Bow', short: 'Bow', art: 'backstep_slash', prefix: 'bw_', first: 'bw_1', alt: 'sp_1', diff: 3, mech: 'Charge levels and the sweet spot',
    desc: 'A hunter’s bow fought up close: chain shots to climb charge levels and loose them from the point-blank sweet spot.',
    str: 'Safe mid-close range, charge levels that climb through a chain, a limb deflect with a counter shot.',
    weak: 'Weak far away and too close alike, light poise, and every big shot asks you to stand and draw.' },
  fist: { weapon: 'penitent_knuckles', name: 'Martial Arts', short: 'Fists', art: 'bloodstep', prefix: 'ft_', first: 'ft_1', alt: 'dg_1', diff: 4, mech: 'Swift and Iron styles',
    desc: 'Two styles, one body: switch between quick Swift strikes and slow Iron blows, even in the middle of a combo.',
    str: 'The most moves of any weapon, the fastest strikes, armoured Iron blows, combos that cross styles.',
    weak: 'The shortest reach, low damage per hit in Swift, and the style dance is a lot to learn.' },
  scythe: { weapon: 'requiem_scythe', name: 'Scythe', short: 'Scythe', art: 'reap', prefix: 'sc_', first: 'sc_1', alt: 'gs_1', diff: 3, mech: 'Souls and the hook step',
    desc: 'Wide reaping arcs that cut front and back; harvest souls with the far edge and spend them on the Reap.',
    str: 'Hits both sides, pulls small foes in, a hook step behind the foe, a soul-fed burst.',
    weak: 'Slow to recover, weak right up close, and the Reap is only as strong as the souls you gathered.' },
  bell: { weapon: 'dirge_bell', name: 'Warbell', short: 'Warbell', art: 'warcry', prefix: 'wb_', first: 'wb_1', alt: 'ml_1', diff: 3, mech: 'Notes and tolls',
    desc: 'A war-bell that rings a note with each blow; strike the right sequence and perform it as a toll that steels you.',
    str: 'Blunt stance damage, buffs you choose by how you fight, a ringing area blow.',
    weak: 'Slow swings and a heavy roll; the buffs ask you to plan your notes before you need them.' },
});
for (const t of WTYPES15) {
  if (!WTYPES.includes(t)) WTYPES.push(t);
  if (typeof MOVESETS_TYPES !== 'undefined' && !MOVESETS_TYPES.includes(t)) MOVESETS_TYPES.push(t);
  const I = WTYPE_INFO[t]; I.icon = 'w_' + I.weapon;
  WEAPON_TYPE[I.weapon] = t; WEAPON_CLASS[I.weapon] = t;
  if (WEAPONS[I.weapon]) WEAPONS[I.weapon].art = I.art;
}
// the short labels the New Game strip shows (14 cells don't fit full names); the nine get theirs here too
Object.entries({ longsword: 'Longsword', katana: 'Katana', greatsword: 'G. Sword', maul: 'Maul', sns: 'Shield', dual: 'Dual', spear: 'Spear', staff: 'Staff', whip: 'Whip' })
  .forEach(([t, s]) => { if (WTYPE_INFO[t] && !WTYPE_INFO[t].short) WTYPE_INFO[t].short = s; });

// ---- the per-type tables other systems key by type id (each keeps its own default for anything missing)
Object.assign(ART_CLS, { saxe: 'gs', bow: 'sw', fist: 'tw', scythe: 'gs', bell: 'gs' });        // 04_player: art pose language
Object.assign(FEEL_CLS_W, { saxe: 0.82, bow: 0.3, fist: 0.1, scythe: 0.62, bell: 0.88 });     // 61_feel: hit weight 0..1
Object.assign(WB_CLS_LABEL, { saxe: 'switch axe', bow: 'bow', fist: 'martial arts', scythe: 'scythe', bell: 'warbell' });   // 60_wbal
Object.assign(WS_CLS, {                                                                        // 62_wsfx: the whoosh per type
  saxe: { ...WS_CLS.great, f: 720, d: 0.22, v: 0.28 },
  bow: { f: 2400, q: 1.3, d: 0.08, v: 0.17, sl: 0.6 },
  fist: { f: 1700, q: 0.7, d: 0.06, v: 0.18, sl: 0.5 },
  scythe: WS_CLS.scythe,
  bell: { ...WS_CLS.great, f: 600, d: 0.26, v: 0.3 },
});

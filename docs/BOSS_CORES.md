# Cinderhollow — Boss Cores

Every boss drops its **Core** on the first kill — 32 in all. Socket one into a weapon at the **Ashwright**
("Enchant a weapon", **400 cinders**; removing it is free and gives the Core back). Each of the 14 weapon types keeps
its own Core, and a Core sits in one weapon at a time.

**What an enchant touches:** only **finishers, heavy attacks, counters and charged releases** — never light attacks,
weapon arts or plunges. Those "enchanted moves" glow in the Core's colour on every weapon. The bonus is modest by
design: +3–14% on the enchanted moves themselves, about +5% of your total damage at most (boss weapons used to be
far stronger). Control effects are weaker on bosses (40% strength for half the time, less with each repeat), and no
effect stacks with itself.

**Rekindle:** a cleared arena keeps an ember effigy that revives its boss for a rematch, as often as you like (not
Sister Venn). A rematch win gives +150 Weapon Mastery and 10% of the boss's cinders; dying in one costs
nothing. New Game+ keeps your Cores and enchants and never drops a duplicate.

*Generated from the game's own Core table (`web/src/77_cores.js`) by `tools/cores_doc.py`; reasoning, budget gates
and tests: `docs/v15/cores.md`.*

## Contents
1. [At a glance](#at-a-glance)
2. [Every Core, in journey order](#every-core-in-journey-order)
3. [Picking a Core](#picking-a-core)

## At a glance

- **Bonus strikes:** Gravetusk’s Core (*Rend*), Omen Core (*Omen Line*), Librarian’s Core (*Overdue*), Bell Core (*Toll*), Drake Core (*Stormcall*), Pharaoh’s Core (*Dusk Count*), Star Core (*Starfall*), Gilded Core (*Twin Oath*), First Ember Core (*Kindling*)
- **Damage over time:** Coven Core (*Thornbind*), Vessel Core (*Rot Sap*), Twinned Core (*Flame and Frost*), Overseer’s Core (*Forgefire*)
- **Raw power and stance:** Antlered Core (*Antler’s Weight*), Choir Core (*Resonance*), Champion’s Core (*Unyielding*), Headsman’s Core (*Verdict*), Colossus Core (*Molten Crack*), Orrery Core (*Orbit*), Sovereign Core (*Kneel*), Last Kindling Core (*Last Flame*)
- **Control:** Glacial Core (*Chill*), Enforcer Core (*Curfew*), Unwritten Core (*Redaction*)
- **Defence:** Oathless Core (*Unbroken Oath*), Scarab Core (*Sun Shell*), Null Core (*Nullify*)
- **Sustain and tempo:** Pilgrim’s Core (*Wayfarer’s Wind*), Ferryman’s Core (*Toll of Breath*), Vesper’s Core (*Attentive*), Sanguine Core (*Blood Tithe*), Hollow Crown Core (*Grief’s Due*)

| Boss | Core | Trait | Colour | Gain on enchanted moves |
|---|---|---|---|---|
| Gravetusk | Gravetusk’s Core | Rend | blood red `#c8342c` | 10% |
| Thorn Coven | Coven Core | Thornbind | thorn green `#7ab04c` | 8.9% |
| Oswin | Pilgrim’s Core | Wayfarer’s Wind | ash white `#d6dccc` | 4% + rolls |
| Antlered Warden | Antlered Core | Antler’s Weight | moss gold `#b8b070` | 3% + stance |
| Morvain | Omen Core | Omen Line | gold `#ffd27a` | 14% |
| Vessel of Rot | Vessel Core | Rot Sap | rot green `#9ab040` | 9.7% |
| Ser Kalden | Oathless Core | Unbroken Oath | oath ember `#e8a858` | utility |
| Head Librarian | Librarian’s Core | Overdue | violet ink `#a080e0` | 12.5% |
| The Ferryman | Ferryman’s Core | Toll of Breath | spectral teal `#60d0c0` | 48 st / 12 moves |
| The Unwritten | Unwritten Core | Redaction | deep ink `#6a4ab4` | 4% + defence |
| Hollow Champion | Champion’s Core | Unyielding | tarnished gold `#d8b878` | 12% (4% hit) |
| Drowned Choir | Choir Core | Resonance | sea glow `#70e8d8` | 8% |
| Ice Golem Warden | Glacial Core | Chill | ice blue `#a8dcff` | 5% + slow |
| Vesper | Vesper’s Core | Attentive | silver `#c8ccdc` | haste |
| Frostbound Twins | Twinned Core | Flame and Frost | flame / frost `#ff9a50 / #a8dcff` | 6.9% + slow |
| Twin Executioners | Headsman’s Core | Verdict | iron red `#b04838` | 3% (28% low) |
| Countess Sanguine | Sanguine Core | Blood Tithe | crimson `#c0182c` | 31 HP / 12 moves |
| The Bell-Ringer | Bell Core | Toll | bronze `#d89848` | 10% |
| King Vael | Hollow Crown Core | Grief’s Due | pale void `#90a8e8` | 18 FP / 12 moves |
| Cindervane | Drake Core | Stormcall | storm blue `#9ac8ff` | 7.9% (alone) |
| Forge Overseer | Overseer’s Core | Forgefire | molten orange `#ff9038` | 10.1% |
| Molten Colossus | Colossus Core | Molten Crack | magma `#ff5a20` | 12.9% |
| Scarab Knight | Scarab Core | Sun Shell | sun gold `#e8c060` | 3% + shell |
| Orrery Sentinel | Orrery Core | Orbit | star white `#d8e0ff` | 5% + pull |
| Veiled Pharaoh | Pharaoh’s Core | Dusk Count | dusk violet `#c890e8` | 12.5% |
| Astrel | Star Core | Starfall | starlight `#eef4ff` | 10% |
| Enforcer Mech | Enforcer Core | Curfew | neon red `#ff4858` | 5% + control |
| SAINT-0 | Null Core | Nullify | null cyan `#a8f4ff` | 4% + defence |
| Gilded Sentinels | Gilded Core | Twin Oath | gilded `#ffd870` | 12% |
| Pale Sovereign | Sovereign Core | Kneel | pale gold `#fff0c8` | 4% (12% staggered) |
| The First Ember | First Ember Core | Kindling | ember red `#ff6a24` | 6.7% |
| Venn | Last Kindling Core | Last Flame | pale flame `#f4eedc` | 4% (16% low) |

## Every Core, in journey order

### Gravetusk’s Core — *Rend*
**Boss:** Gravetusk · **Colour:** blood red (`#c8342c`) · **Type:** Bonus strikes

Enchanted blows mark the foe. The third mark within 6 s tears it open for 30% of that blow.

*The hound worries a wound; needs three committed moves.*

### Coven Core — *Thornbind*
**Boss:** Thorn Coven · **Colour:** thorn green (`#7ab04c`) · **Type:** Damage over time

Thorns take root: 9% of each enchanted blow as damage over 3 s. Fresh thorns refresh the old, never stack past twice.

*Thorns take root; pool capped so spam can't stack it.*

### Pilgrim’s Core — *Wayfarer’s Wind*
**Boss:** Oswin · **Colour:** ash white (`#d6dccc`) · **Type:** Sustain and tempo

+4% damage, and the roll you take within 2 s of an enchanted blow costs no stamina.

*The pilgrim's road: commit, then slip out for free.*

### Antlered Core — *Antler’s Weight*
**Boss:** Antlered Warden · **Colour:** moss gold (`#b8b070`) · **Type:** Raw power and stance

+25% stance damage and +3% damage: great foes break sooner under your heavier blows.

*A charging stag breaks guards, not health bars.*

### Omen Core — *Omen Line*
**Boss:** Morvain · **Colour:** gold (`#ffd27a`) · **Type:** Bonus strikes

A golden line flares under the foe and erupts 0.45 s later for 14% of the move’s damage (once every 1.5 s).

*His floor lines; ICD keeps it to one per exchange.*

### Vessel Core — *Rot Sap*
**Boss:** Vessel of Rot · **Colour:** rot green (`#9ab040`) · **Type:** Damage over time

Each enchanted move seeds rot: 10% of its damage over 5 s. Up to three rots run at once.

*Many mouths; never the old rot (0.6% max HP/s, far too strong).*

### Oathless Core — *Unbroken Oath*
**Boss:** Ser Kalden · **Colour:** oath ember (`#e8a858`) · **Type:** Defence

Enchanted moves can’t be flinched by blows under 20% of your max HP, and you take 10% less damage while they play.

*The knight who would not yield: hyper armour only while committed.*

### Librarian’s Core — *Overdue*
**Boss:** Head Librarian · **Colour:** violet ink (`#a080e0`) · **Type:** Bonus strikes

An enchanted move slips a page into the foe. Your next ordinary blow on it within 4 s tears the page for 15% of that move.

*Rewards weaving lights after a finisher (the only Core that pays off light hits, and only once).*

### Ferryman’s Core — *Toll of Breath*
**Boss:** The Ferryman · **Colour:** spectral teal (`#60d0c0`) · **Type:** Sustain and tempo

Enchanted blows return 8 stamina (at most every 0.6 s).

*"one breath for the crossing".*

### Unwritten Core — *Redaction*
**Boss:** The Unwritten · **Colour:** deep ink (`#6a4ab4`) · **Type:** Control

+4% damage, and the foe is blotted for 3 s: its blows land 12% softer (8% for great foes).

*Ink blind; works on the attacker's `src`, bosses' projectiles count when the boss is inked.*

### Champion’s Core — *Unyielding*
**Boss:** Hollow Champion · **Colour:** tarnished gold (`#d8b878`) · **Type:** Raw power and stance

+12% damage while you haven’t been hit for 6 s; +4% otherwise.

*Undefeated: rewards clean play.*

### Choir Core — *Resonance*
**Boss:** Drowned Choir · **Colour:** sea glow (`#70e8d8`) · **Type:** Raw power and stance

Each enchanted move within 4 s of the last rings 4% harder than the one before, up to +12%. Pause and the chord fades.

*A chord that builds and fades; additive, capped.*

### Glacial Core — *Chill*
**Boss:** Ice Golem Warden · **Colour:** ice blue (`#a8dcff`) · **Type:** Control

+5% damage; the foe is chilled, 15% slower for 2 s. Great foes resist: 6% for under a second, less each time.

*Frost slow, the resisted form on bosses.*

### Vesper’s Core — *Attentive*
**Boss:** Vesper · **Colour:** silver (`#c8ccdc`) · **Type:** Sustain and tempo

An enchanted move hastens the move after it by 12% (if it starts within 1.5 s).

*Impeccable service: tempo, not damage.*

### Twinned Core — *Flame and Frost*
**Boss:** Frostbound Twins · **Colour:** flame / frost (`#ff9a50` / `#a8dcff`) · **Type:** Damage over time

Enchanted moves alternate: flame burns for 8% of the blow over 3 s, frost chills the foe (10% slower). +3% damage.

*The only two-colour Core: the slash alternates orange and ice.*

### Headsman’s Core — *Verdict*
**Boss:** Twin Executioners · **Colour:** iron red (`#b04838`) · **Type:** Raw power and stance

+3% damage, and +25% against foes below 30% of their health.

*The headsman finishes; a closer, not an opener.*

### Sanguine Core — *Blood Tithe*
**Boss:** Countess Sanguine · **Colour:** crimson (`#c0182c`) · **Type:** Sustain and tempo

Heal 5% of the damage your enchanted blows deal, at most 2% of your max HP per move.

*Lifesteal sliver; per-move cap so multi-hit moves can't farm it.*

### Bell Core — *Toll*
**Boss:** The Bell-Ringer · **Colour:** bronze (`#d89848`) · **Type:** Bonus strikes

Every third enchanted move tolls: a ring of 56 px strikes every foe in it for 30% of the move and 40 stance.

*Every toll a name; strong in crowds by design.*

### Hollow Crown Core — *Grief’s Due*
**Boss:** King Vael · **Colour:** pale void (`#90a8e8`) · **Type:** Sustain and tempo

Enchanted blows restore 3 FP (at most every 0.8 s).

*The grief his court carries; fuels arts and spells.*

### Drake Core — *Stormcall*
**Boss:** Cindervane · **Colour:** storm blue (`#9ac8ff`) · **Type:** Bonus strikes

+4% damage; lightning arcs to the nearest other foe within 90 px for 35% of the blow (every 0.5 s). Alone, it grounds into the foe for 4%.

*The lightning arc to a second foe.*

### Overseer’s Core — *Forgefire*
**Boss:** Forge Overseer · **Colour:** molten orange (`#ff9038`) · **Type:** Damage over time

Enchanted blows set the foe alight: 10% of the blow as fire over 3 s. Fresh fire refreshes the old, never stacks past twice.

*The burn.*

### Colossus Core — *Molten Crack*
**Boss:** Molten Colossus · **Colour:** magma (`#ff5a20`) · **Type:** Raw power and stance

An enchanted move cracks the foe’s shell: for 4 s it takes 6% more from every blow you land (refreshes, never stacks).

*Plates come off (Ashwright's advice); a debuff, not a bigger finisher.*

### Scarab Core — *Sun Shell*
**Boss:** Scarab Knight · **Colour:** sun gold (`#e8c060`) · **Type:** Defence

+3% damage; an enchanted move raises a sun-shell that soaks 8% of your max HP from the next blow within 3 s (every 6 s).

*Carapace.*

### Orrery Core — *Orbit*
**Boss:** Orrery Sentinel · **Colour:** star white (`#d8e0ff`) · **Type:** Raw power and stance

+5% damage, +10% stance; enchanted moves draw small foes within 72 px in toward the blow.

*Gravity pull; bosses are never moved.*

### Pharaoh’s Core — *Dusk Count*
**Boss:** Veiled Pharaoh · **Colour:** dusk violet (`#c890e8`) · **Type:** Bonus strikes

An enchanted move marks the foe with dusk; 3 s later the mark falls for 25% of that move. One mark per foe at a time.

*He counted every grain; delayed, readable.*

### Star Core — *Starfall*
**Boss:** Astrel · **Colour:** starlight (`#eef4ff`) · **Type:** Bonus strikes

Every third enchanted move calls a falling star onto its foe for 30% of the move.

*She fell so nothing else would.*

### Enforcer Core — *Curfew*
**Boss:** Enforcer Mech · **Colour:** neon red (`#ff4858`) · **Type:** Control

+5% damage; enchanted moves jolt foes: small foes stagger (once per 4 s each), great foes only slow 10% for a moment.

*Compliance shock; the control is the resisted kind on bosses.*

### Null Core — *Nullify*
**Boss:** SAINT-0 · **Colour:** null cyan (`#a8f4ff`) · **Type:** Defence

+4% damage; an enchanted move erases enemy projectiles within 64 px of the blow (every 2 s).

*"be archived".*

### Gilded Core — *Twin Oath*
**Boss:** Gilded Sentinels · **Colour:** gilded (`#ffd870`) · **Type:** Bonus strikes

A gilded echo strikes 0.3 s after each enchanted move for 12% of its damage.

*Two oaths, one gate: the second blow.*

### Sovereign Core — *Kneel*
**Boss:** Pale Sovereign · **Colour:** pale gold (`#fff0c8`) · **Type:** Raw power and stance

+15% stance damage and +4% damage; a staggered foe takes 8% more from enchanted moves.

*Makes great foes kneel, then punishes the kneel.*

### First Ember Core — *Kindling*
**Boss:** The First Ember · **Colour:** ember red (`#ff6a24`) · **Type:** Bonus strikes

Enchanted moves build kindling. After three, the next enchanted move burns it all for +40% damage.

*The first fire, banked then loosed.*

### Last Kindling Core — *Last Flame*
**Boss:** Venn · **Colour:** pale flame (`#f4eedc`) · **Type:** Raw power and stance · *cannot be rekindled*

+16% damage while you are below 40% health; +4% otherwise.

*The last flame burns brightest when you're nearly out.*

## Picking a Core

- **Combo weapons with many finishers** (Longsword, Dual Blades, Martial Arts, Sword & Shield) get the most from
  per-move procs: *Rend*, *Twin Oath*, *Resonance*, *Starfall*.
- **Big single hits** (Greatsword, Maul, Katana Iai, Switch Axe) suit flat and delayed bonuses: *Omen Line*,
  *Dusk Count*, *Kindling*, *Molten Crack*, *Antler's Weight* for stance.
- **Crowds:** *Toll*, *Stormcall*, *Orbit*. **Bosses:** *Molten Crack*, *Verdict*, *Kneel*, *Unyielding*.
- **Surviving:** *Unbroken Oath*, *Sun Shell*, *Blood Tithe*, *Redaction*, *Nullify* (projectile-heavy fights).
- **Stamina and FP:** *Toll of Breath*, *Wayfarer's Wind*, *Grief's Due* (weapon arts), *Attentive* for tempo.
- Bow arrows carry the procs and the colour but not the flat damage bonuses, so procs suit the Bow best.

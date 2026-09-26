// agent G (Expansion 2): new gear in the pause menu (icons from ui_icons5)
await boot(); try { G.giveArmory(); } catch (e) {}
const SP = ['bramble_snare','drowning_hymn','blood_lance','crimson_rite','soul_chains','sunbeam','sandstorm','comet','pulse_shot','null_field'];
const AR = ['reap','harvest_moon','lash','chain_drag','blood_frenzy','tidal_surge','solar_flare','starfall','overclock','pale_pyre'];
const CH = ['c_antler','c_moss','c_gill','c_pearl','c_bloodvial','c_countess','c_crown','c_court','c_scarab','c_sun','c_star','c_orrery','c_hack','c_neon','c_lastflame'];
G.give({ spellsOwned: SP, spellsEq: SP.slice(0, 3), spellSlots: 3, arts: AR, art: 'harvest_moon', charms: CH, charmsEq: ['c_star', 'c_court', 'c_lastflame'], charmSlots: 3, spell: 'comet', items: { tidebreath: 1, moonstep: 1 } });
G.tp('R2', 5, 10); G.step(30);
G.step(1, [], ['pause']); G.step(5); await snap('m_equip');
G.step(1, [], ['map']); G.step(5);
const miss = [];
for (let i = 0; i < 140; i++) { G.step(1, [], ['down']); if (i % 17 === 16) await snap('m_inv_' + String(i).padStart(3, '0')); }
return G.state;

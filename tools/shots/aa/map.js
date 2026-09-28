await boot(); const E = G.sk.ev;
return E(`Object.keys(WEAPONS).map(id => [id, WEAPON_CLASS[id], WEAPONS[id].art, !!(typeof SIGS!=='undefined' && SIGS[id])].join(' '))`);

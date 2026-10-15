const out = {};
for (const t of E('MOVESETS_TYPES')) out[t] = { name: E(`WTYPE_INFO.${t}.name`), weapon: E(`WEAPONS[WTYPE_INFO.${t}.weapon].name`), art: E(`ARTS[WTYPE_INFO.${t}.art] && ARTS[WTYPE_INFO.${t}.art].name`), mech: E(`WTYPE_INFO.${t}.mech`), combos: E(`MV.types.${t}.combos`) };
return out;

await boot(); G.giveArmory();
const ev = G.sk.ev; const o = {};
o.enemy = ev("Object.keys(ENEMY)").join(' ');
o.bossInfo = ev("Object.keys(BOSS_INFO)").join(' ');
o.weapons = ev(`Object.keys(WEAPONS).map(k => k + ":" + (WEAPON_CLASS[k]||"?") + (SIGS[k] ? "*" : "") + (WEAPONS[k].fire?"F":"") + (WEAPONS[k].frost?"I":"") + (WEAPONS[k].holy?"H":"") + (WEAPONS[k].rot?"R":"") + (WEAPONS[k].bleed?"B":"")).join(" ")`);
o.room = G.room; o.pcol = ev("Object.keys(PCOL).join(\" \")"); o.smooth = ev("g.imageSmoothingEnabled"); o.WH = ev("[W,H]");
return o;

await boot(); G.giveArmory(); const o = [];
G.P.fp = 999; G.step(10);
const sp = G.SAVE.spell, art = G.SAVE.art; o.push('spell ' + sp + ' art ' + art);
G.step(1, [], ['cast']); G.step(3); const s1 = G.P.state; G.step(90);
const fp0 = G.P.fp; G.step(1, [], ['cast']); G.step(3); o.push('first cast state ' + s1 + '; recast after 1.5s state ' + G.P.state + ' fp spent ' + Math.round(fp0 - G.P.fp));
G.step(60 * 8); G.P.fp = 999; G.step(1, [], ['art']); G.step(3); const a1 = G.P.state; G.step(80); G.step(1, [], ['art']); G.step(3); o.push('art first ' + a1 + ', again after 1.3s ' + G.P.state);
await snap('cd_hud');
return o;

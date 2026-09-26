await boot(); G.give({ stats: { vig: 60 } });
for (const k of ['boss:vael']) delete G.SAVE.flags[k]; G.SAVE.flags['cut:vael'] = 1; G.SAVE.flags['cutp2:vael'] = 1; G.SAVE.flags['cutp3:vael'] = 1;
G.tp('NV7', 30, 12); const b = G.boss; b.activate(); G.step(5);
b.hp = b.maxHp * 0.6;
for (let i = 0; i < 900; i++) { G.step(1, Math.abs(b.x - G.P.x) > 120 ? [b.x < G.P.x ? 'left' : 'right'] : []); G.P.hp = 9999; if (i % 150 === 149) await snap('vl_p2_' + i); }
b.hp = b.maxHp * 0.25;
for (let i = 0; i < 900; i++) { G.step(1, Math.abs(b.x - G.P.x) > 120 ? [b.x < G.P.x ? 'left' : 'right'] : []); G.P.hp = 9999; if (i % 150 === 149) await snap('vl_p3_' + i); }
return b.phase;

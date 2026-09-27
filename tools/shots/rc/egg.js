await boot(); G.SETTINGS.god = 1; G.SAVE.seenAreas = { lastfield: 1 };
G.tp('LF1', 97, 16); G.step(250); await snap('egg_a'); G.tp('LF1', 100, 17); G.step(30); G.xrc.hatch(); G.step(100); await snap('egg_b'); G.step(400);
for (let i = 0; i < 5 && G.state !== 'play'; i++) { G.step(1, [], ['interact']); G.step(10); }
await snap('egg_c'); return [G.SAVE.spellsOwned.join(','), G.state];

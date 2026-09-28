await boot(); G.give({ shards: 40 });
const E = G.sk.ev;
E("openShrineMenu({ name: 'Test' })"); E("menuInput('down')"); E("menuInput('confirm')"); G.step(10);
const scr = E('menu && menu.screen');
for (const a of ['right', 'confirm', 'confirm', 'down', 'confirm', 'confirm']) { E(`menuInput('${a}')`); G.step(3); }
await snap('tree');
return { scr, skills: G.SAVE.skills, pts: G.sk.skillPoints() };

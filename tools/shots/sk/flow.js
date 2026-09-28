// economy, spells out of the tree, respec (tear + free), migration, NG+
await boot();
const E = G.sk.ev, R = {}, fail = [];
const ok = (k, v, cond) => { R[k] = v; if (!cond) fail.push(k); };
// fresh journey: Ash Bolt known and equipped, one free respec, v2
ok('newgame', E('[SAVE.spellsOwned.join(), SAVE.spellsEq.join(), SAVE.spell, SAVE.skillv, SAVE.freeRespec]'), E("SAVE.spellsOwned.includes('ash_bolt') && SAVE.spell === 'ash_bolt' && SAVE.skillv === 2 && SAVE.freeRespec === 1"));
// points: floor((level - 1) / 2) + shards - spent
G.give({ stats: { vig: 20, mnd: 10, end: 12, str: 13, dex: 12, fth: 9 }, shards: 3 });   // level 1 + 10 + 2 + 2 + 2 + 1 = 18
ok('points', `level ${E('levelOf(SAVE.stats)')} shards 3 -> ${G.sk.skillPoints()}`, G.sk.skillPoints() === Math.floor((E('levelOf(SAVE.stats)') - 1) / 2) + 3);
G.sk.learnSkill('keen_edge'); ok('points.spent', G.sk.skillPoints(), G.sk.skillPoints() === Math.floor((E('levelOf(SAVE.stats)') - 1) / 2) + 3 - 1);
// the Scribe sells Sunspear and Emberburst
const scribe = E("SHOPS.scribe.slice(0, 3).map(e => e.item + ':' + e.price).join(' ')"); ok('scribe', scribe, /sp:sunspear:1200 sp:emberburst:1800/.test(scribe));
E("SAVE.cinders = 5000; menu = { screen: 'shop', shop: 'scribe', sel: 0 }; state = 'menu'"); E("shopInput('confirm')");
ok('buy.sunspear', E('SAVE.spellsOwned.join() + " cinders " + SAVE.cinders'), E("SAVE.spellsOwned.includes('sunspear') && SAVE.cinders === 3800"));
E("menu = null; state = 'play'");
// Pale Tear rebirth (shrine) and the Ashwright's free respec
G.give({ shards: 20 }); ['keen_edge', 'fourth_strike', 'kindled_mind', 'azure_thrift', 'soul_siphon', 'memory_palace'].forEach(id => G.sk.learnSkill(id));
const slots = E('SAVE.spellSlots'), pts0 = G.sk.skillPoints();
E("SAVE.inv.tear = 0"); E("skillRespec('tear')"); ok('rebirth.noTear', E('SAVE.skills.length'), E('SAVE.skills.length') > 0);
E("SAVE.inv.tear = 1"); E("skillRespec('tear')"); ok('rebirth.tear', `skills ${E('SAVE.skills.length')} tears ${E('SAVE.inv.tear')} slots ${slots} -> ${E('SAVE.spellSlots')}`, E('SAVE.skills.length') === 0 && E('SAVE.inv.tear') === 0 && E('SAVE.spellSlots') === slots - 1);
G.sk.learnSkill('keen_edge');
const steps = E("npcScript('ashwright')"), ch = steps.find(s => s.choice), opt = ch && ch.choice.find(c => /Reforge/.test(c[0]));
ok('ashwright.offer', ch ? ch.choice.map(c => c[0]).join(' | ') : 'none', !!opt);
opt[1].find(s => s.do).do(); ok('ashwright.free', `skills ${E('SAVE.skills.length')} freeRespec ${E('SAVE.freeRespec')}`, E('SAVE.skills.length') === 0 && E('SAVE.freeRespec') === 0);
G.sk.learnSkill('keen_edge'); const steps2 = E("npcScript('ashwright')"); ok('ashwright.once', steps2.find(s => s.choice).choice.map(c => c[0]).join(' | '), !steps2.find(s => s.choice).choice.some(c => /Reforge/.test(c[0])));
// NG+: skills and shards stay, the free respec comes back
const sh = E('SAVE.shards'); E('startNGPlus()'); ok('ngplus', `skills ${E('SAVE.skills.join()')} shards ${E('SAVE.shards')} free ${E('SAVE.freeRespec')} v ${E('SAVE.skillv')}`, E("SAVE.skills.includes('keen_edge')") && E('SAVE.shards') === sh && E('SAVE.freeRespec') === 1);
// migration: a v1 save with the old tree
const old = E(`(() => { const o = newSave(); delete o.skillv; delete o.freeRespec; o.spellsOwned = []; o.spellsEq = []; o.spell = null;
  o.stats = { vig: 30, mnd: 20, end: 20, str: 20, dex: 20, fth: 20 }; o.shards = 10;
  o.skills = ['keen_edge','fourth_strike','charged_arts','riposte_mastery','bloodthirst','ash_bolt','sunspear','azure_thrift','emberburst','soul_siphon','quickstep','iron_flask','steadfast','last_stand','second_wind'];
  localStorage.setItem(SAVE_KEY, JSON.stringify(o)); return o.skills.length; })()`);
E('continueGame()'); G.step(5);
ok('migrate', `kept ${E('SAVE.skills.join()')} | spells ${E('SAVE.spellsOwned.join()')} | eq ${E('SAVE.spellsEq.join()')} | v ${E('SAVE.skillv')} | pts ${G.sk.skillPoints()}`,
  E("SAVE.skillv === 2 && ['ash_bolt','sunspear','emberburst'].every(s => SAVE.spellsOwned.includes(s)) && !SAVE.skills.includes('ash_bolt') && SAVE.skills.every(id => SKILL_BY[id])") && G.sk.skillPoints() >= 0);
ok('migrate.valid', E("SAVE.skills.filter(id => SKILL_BY[id].req.some(r => !SAVE.skills.includes(r))).join() || 'all prerequisites met'"), E("SAVE.skills.every(id => SKILL_BY[id].req.every(r => SAVE.skills.includes(r)))"));
ok('migrate.toast', E("toasts.map(t => t.msg).join(' / ')"), /skill tree has changed/.test(E("toasts.map(t => t.msg).join(' / ')")));
// loading again does not migrate twice
E('saveGame()'); const k = E('SAVE.skills.join()'); E('toasts.length = 0'); E('continueGame()'); G.step(5); ok('migrate.once', E('SAVE.skills.join()') === k, E('SAVE.skills.join()') === k && !/skill tree has changed/.test(E("toasts.map(t => t.msg).join(' / ')")));
// a save with nothing learned migrates quietly
E(`(() => { const o = newSave(); delete o.skillv; o.skills = []; localStorage.setItem(SAVE_KEY, JSON.stringify(o)); })()`); E("toasts.length = 0"); E('continueGame()'); G.step(5);
ok('migrate.quiet', E("toasts.map(t => t.msg).join(' / ') || 'no toast'"), !/skill tree has changed/.test(E("toasts.map(t => t.msg).join(' / ')")));
// summary
G.give({ shards: 99 }); ['keen_edge', 'fourth_strike', 'measured_cut', 'bloodthirst', 'm_whip', 'way_prosper'].forEach(id => G.sk.learnSkill(id));
ok('summary', G.sk.skillBuildSummary().join(' · '), G.sk.skillBuildSummary().length > 3);
return { fail, R };

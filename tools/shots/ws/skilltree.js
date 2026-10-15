// the skill tree: the Arsenal page is now the Weapon Mastery page (9 types, rank, XP, unlocks); no m_<cls> nodes
await boot();
const E = G.sk.ev, out = [], fail = [];
const ok = (c, m) => { out.push((c ? 'OK   ' : 'FAIL ') + m); if (!c) fail.push(m); };
ok(!G.st.SKILLS.some(s => /^m_/.test(s.id) || s.br === 'arsenal'), 'no Arsenal nodes in SKILLS');
G.SAVE.mastery = { longsword: 950, greatsword: 2100, whip: 4000, katana: 120 };
G.st.open(0); G.step(2);
const pages = G.st.layout().map(p => p.id + ':' + p.name); out.push('pages ' + pages.join(', '));
ok(pages.includes('mastery:Mastery') && !pages.some(p => p.startsWith('arsenal')), 'a Mastery page, no Arsenal page');
const mi = G.st.layout().findIndex(p => p.id === 'mastery'); G.st.page(mi); G.step(20);
ok(E('ST.sel') === 'wm:' + G.ws.wtype(), 'the cursor starts on the weapon in hand: ' + E('ST.sel'));
await snap('tree_mastery');
G.st.input('right'); G.step(2); ok(E('ST.sel') === 'wm:katana', 'right -> Katana');
G.st.input('down'); G.step(2); out.push('down -> ' + E('ST.sel'));
G.st.input('confirm'); G.step(2); ok(G.st.pts === E('stPts()') && G.SAVE.skills.length === 0, 'confirm on a type learns nothing');
E("ST.sel = 'wm:whip'"); G.step(10); await snap('tree_mastery_whip');
G.st.input('map'); G.step(2); ok(G.st.layout()[E('ST.page')].id !== 'mastery', 'Tab moves on');
G.st.input('back'); G.step(2);
// a skill learned under the old tree's m_ ids can't be learned any more
ok(E("skillLearnable('m_sword').ok") === false, 'm_sword is unknown');
out.push(fail.length ? `${fail.length} FAILED` : 'ALL PASS');
return out;

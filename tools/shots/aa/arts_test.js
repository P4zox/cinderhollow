// AA: every weapon -> its locked art plays the right animation (class-true variant art_<id>__<cls> when one exists, else art_<id>),
// the art's effect fires (damage / buff / guard / echo), no errors. Snaps each weapon's art mid-release (cropped by snaps_sheet.py).
// SHOT_HTML=web/dist/aa.html node tools/shots/shot.js tools/shots/aa/arts_test.js tools/shots/aa/out_arts
await boot(); G.giveArmory(); G.grantTechniques(); G.SETTINGS.god = 1; G.SETTINGS.nocd = 1;
const E = G.sk.ev;
const X = E('({ Enemy, refreshDerived, setP, get enemies() { return enemies; }, get cam() { return cam; }, get D() { return D; }, WEAPON_CLASS, WEAPONS })');
const PRE = { sword: 'sw', dagger: 'dg', great: 'gs', spear: 'sp', katana: 'kt', staff: 'st', shield: 'sh', twin: 'tw', scythe: 'sc', whip: 'wh' };
const VAR = { moonwave: ['sw', 'sp', 'gs'], bloodstep: ['kt'], warcry: ['sp'], cinderblade: ['gs', 'st'], backstep_slash: ['dg'],
  ink_mark: ['dg'], tidal_surge: ['gs'], solar_flare: ['st'], overclock: ['sp'] };
const BUFF = { warcry: p => p.cryT > 0, cinderblade: p => p.fireT > 0 };
const GUARD = new Set(['aegis', 'frost_aegis']);
const expectTag = (art, cls) => (VAR[art] || []).includes(PRE[cls]) ? `art_${art}__${PRE[cls]}` : `art_${art}`;
const clear = () => { for (const e of X.enemies) e.state = 'dead'; X.enemies.length = 0; };
const foe = (dx, dy = 0) => { const e = new X.Enemy('hollow_soldier', G.P.x + dx, G.P.y + dy, 'aa' + Math.random()); e.hp = e.maxHp = 99999;
  e.update = function (dt) { this.flash = Math.max(0, this.flash - dt * 6); }; X.enemies.push(e); return e; };
const pos = {}, rows = [], bad = [];
const shot = async n => { await snap(n); pos[n] = [Math.round((G.P.x - X.cam.x) * 3), Math.round((G.P.y - X.cam.y) * 3), G.P.anim.tag + ':' + G.P.anim.i]; };
async function run(id, opts = {}) {
  E(`applyEquip({ k: 'weapon' }, ${JSON.stringify(id)})`); X.refreshDerived();
  await E("sheet('wpn_' + SAVE.weapon).img.decode()").catch(() => {});
  G.tp('R1', 38, 10); G.step(30); G.P.face = 1; clear();
  if (opts.pre) opts.pre();
  const art = G.SAVE.art, cls = E('wcls()');
  const want = expectTag(art, cls);
  const e1 = foe(26), e2 = foe(52), e3 = foe(-24);
  G.P.fp = X.D.maxFp; G.P.hp = X.D.maxHp;
  G.step(1, [], ['art']);
  const first = G.P.anim.tag, tags = [first];
  let rel = false, artI = false, snapped = false, echoSnap = false, maxCry = 0, maxFire = 0;
  for (let i = 0; i < 360; i++) {
    G.step(1);
    const t = G.P.anim.tag; if (tags[tags.length - 1] !== t) tags.push(t);
    if ((G.P.g2 && G.P.g2.rel) || G.P.artFired) rel = true;
    if (G.P.state === 'art' && G.P.artI) artI = true;
    maxCry = Math.max(maxCry, G.P.cryT || 0); maxFire = Math.max(maxFire, G.P.fireT || 0);
    const relI = G.P.artRel ?? 3;
    if (!snapped && G.P.state === 'art' && t.startsWith('art_') && t !== 'art_echo' && G.P.anim.i >= relI) { snapped = true; await shot(opts.name || id); }
    if (!echoSnap && t === 'art_echo' && G.P.anim.i >= 2) { echoSnap = true; await shot((opts.name || id) + '_stance'); }
    if (G.P.state !== 'art' && i > 20) break;
  }
  G.step(30);
  const dmg = [e1, e2, e3].reduce((a, e) => a + (e.maxHp - e.hp), 0);
  let effect; const fa = opts.effectArt || art;
  if (BUFF[fa]) effect = BUFF[fa]({ cryT: maxCry, fireT: maxFire });
  else if (GUARD.has(fa)) effect = artI && rel;
  else effect = dmg > 0;
  const ok = first === (opts.first || want) && tags.includes(opts.play || want) && rel && effect;
  const r = { id, cls, art, want: opts.play || want, first, tags: tags.join('>'), rel, dmg: Math.round(dmg), buff: BUFF[fa] ? Math.round(maxCry || maxFire) : undefined, guard: GUARD.has(art) ? artI : undefined, ok };
  rows.push(r); if (!ok) bad.push(r);
  clear(); G.step(20);
}
for (const id of Object.keys(X.WEAPONS)) {
  if (X.WEAPON_CLASS[id] === 'mirror') continue;
  await run(id);
}
// the First Ember's Echo: its own golden stance, then the art of the last weapon, in that weapon's class pose (Vael's great moonwave)
await run('vael_greatsword');
await run('first_ember', { pre: () => { G.SAVE.lastCls = 'great'; E("GEAR2.S.lastArt = 'moonwave'"); }, first: 'art_echo', play: 'art_moonwave__gs', name: 'first_ember_great' });
await run('first_ember', { pre: () => { G.SAVE.lastCls = 'spear'; E("GEAR2.S.lastArt = 'warcry'"); }, first: 'art_echo', play: 'art_warcry__sp', name: 'first_ember_spear', effectArt: 'warcry' });
return { bad, rows, pos };

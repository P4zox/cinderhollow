await boot(); G.give({ items: { talon: 1 } }); G.SAVE.flags['cut:warden'] = 1; G.SAVE.flags['cutp2:warden'] = 1;
G.tp('TV8', 12, 10); G.step(5);
for (let i = 0; i < 200 && !(G.boss && G.boss.active); i++) G.step(2, ['right']);
const b = G.boss; G.step(200);
const out = {};
async function trial(m, dist, action, stag, tagFor) {
  G.TVR.pillars = []; G.TVR.rootLines = []; G.TVR.orbs = []; G.TVR.thorns = []; G.TVR.sflames = [];
  b.x = 22 * 16; b.state = 'idle'; b.cool = 99; b.hidden = false; b.y = b.floor; b.air = null; b.q = [];
  G.P.x = b.x + dist; G.P.y = 176; G.P.vx = 0; G.P.hp = 999; G.P.st = 999; G.step(3);
  b.face = 1; b.stormT = 99; b.pilT = 99; stag ? b.beginStag(m) : b.begin(m); b.chain = 9; let hit = false, did = 0, last = 999, moveDone = 0;
  const tt = tagFor || { gallop: 'cprep', bound: 'leap' }[m] || (stag ? m : ({ pillars: 'summon', wave: 'erupt' }[m] || m));
  for (let i = 0; i < 320; i++) {
    const tel = b.sh.meta.telegraph[b.anim.tag];
    let hold = [], tap = [];
    const atTel = tel && b.anim.tag === tt && b.anim.i >= tel.frame && (b.anim.i > tel.frame || b.anim.t > 90);
    if (!did && atTel) { did = 1; if (action === 'rollin') { tap = ['roll']; hold = ['left']; } if (action === 'rollout') { tap = ['roll']; hold = ['right']; } if (action === 'jump') { tap = ['jump']; hold = ['jump']; } }
    if (did && action === 'runback') hold = ['right'];
    if (did && action === 'runin') hold = ['left'];
    if (action === 'jumpwaves') { for (const w of G.TVR.rootLines) if (Math.abs(w.x - G.P.x) < 34 && G.P.ground) { tap = ['jump']; } hold = hold.concat(['jump']); if (did) hold.push('right'); }
    if (action === 'rollchain' && b.state === 'attack') { const w = (b.sh.meta.attacks[b.anim.tag] || {}); const wins = w.windows || (w.active ? [w] : []); for (const x of wins) if (b.anim.i === x.active[0] - 1 && b.anim.t > b.anim.ms() * 0.55 && !G.P.inv) { tap = ['roll']; hold = ['left']; } }
    if (action === 'rollgallop' && b.state === 'gallop' && Math.abs(b.x - G.P.x) < 165 && did < 2) { did = 2; tap = ['roll']; hold = ['left']; }
    if (action !== 'none') {   // a sensible player: jump the root waves, step out of pillar streaks
      for (const w of G.TVR.rootLines) if (Math.abs(w.x - G.P.x) < 34 && Math.sign(G.P.x - w.x) === w.dir && G.P.ground) { tap = ['jump']; hold = hold.concat(['jump']); }
      for (const pl of G.TVR.pillars) if (pl.t < 0.1) { const lx = pl.bx + (pl.tx - pl.bx) * 0.08; if (Math.abs(lx - G.P.x) < 20) { hold = [G.P.x < lx ? 'left' : 'right']; } }
    }
    if (action === 'rollland' && b.air && b.y > b.floor - 30 && !G.P.inv && G.P.state !== 'roll') { tap = ['roll']; hold = ['left']; }
    G.P.st = 999; b.stormT = 99; b.pilT = 99; if (b.state === 'idle') { b.cool = 99; if (!moveDone) moveDone = i; }
    G.step(1, hold, tap);
    if (G.P.hp < last && !hit) { hit = `${b.state}:${b.anim.tag}:${b.anim.i} px${Math.round(G.P.x)} bx${Math.round(b.x)} py${Math.round(G.P.y)} ${G.P.state} pil${G.TVR.pillars.length} w${G.TVR.rootLines.length} th${G.TVR.thorns.length}`; } G.P.hp = 999; last = 999;
    if (moveDone && i > moveDone + 10 && !G.TVR.pillars.length && !G.TVR.rootLines.length && !G.TVR.thorns.length) break;
  }
  out[`${stag ? 'S' : 'M'} ${m}@${dist}:${action}`] = hit ? 'HIT ' + hit : 'safe';
}
for (const [m, d, a] of [['combo', 70, 'none'], ['combo', 70, 'rollchain'], ['combo', 70, 'runback'], ['gore', 60, 'rollchain'], ['leap', 150, 'none'], ['leap', 150, 'runback'], ['gore', 60, 'none'], ['gore', 60, 'rollout'],
                         ['nova', 80, 'none'], ['nova', 80, 'runback'], ['wave', 140, 'none'], ['wave', 140, 'jumpwaves'], ['pillars', 140, 'none'], ['pillars', 140, 'avoid'], ['leap', 150, 'rollland']]) await trial(m, d, a, false);
b.hit({ dmg: b.hp - b.maxHp * 0.45, poise: 0, dir: -1, kind: 'light', x: b.x, y: b.y - 50 }); b.state = 'idle';
for (let i = 0; i < 400 && b.form !== 'stag'; i++) { G.step(1); if (G.state === 'cut') G.step(1, [], ['pause']); G.P.hp = 999; }
for (let i = 0; i < 60; i++) { G.step(1); if (G.state === 'cut') G.step(1, [], ['pause']); }
out.form = b.form;
for (const [m, d, a] of [['gallop', 200, 'none'], ['gallop', 200, 'rollgallop'], ['toss', 80, 'rollchain'], ['rear', 90, 'none'], ['rear', 90, 'runback'], ['toss', 80, 'none'], ['toss', 80, 'rollout'],
                         ['bound', 160, 'none'], ['bound', 160, 'rollland'], ['rear', 90, 'avoid']]) await trial(m, d, a, true);
return out;

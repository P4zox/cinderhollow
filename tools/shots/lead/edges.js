await boot(); G.grantTechniques(); G.giveArmory(); G.SAVE.items.tidebreath = 1; G.SAVE.items.moonstep = 1; G.SETTINGS.god = 1;
// a finished world: every boss down, a rest after it (hidden passages open), so only real layout problems remain
for (const b of ['hound','omen','kalden','vessel','sovereign','librarian','unwritten','ice_warden','twins','bellringer','cindervane','overseer','colossus','oswin','sentinels','first_ember','coven','warden','ferryman','choir','butler','sanguine','executioners','vael','scarab','pharaoh','orrery','astrel','enforcer','saint0','venn']) G.SAVE.flags['boss:' + b] = 1;
G.SAVE.x3 = G.SAVE.x3 || {}; G.SAVE.x3.t = G.SAVE.x3.t || {}; for (const k of Object.keys(G.SAVE.flags)) if (k.startsWith('boss:')) G.SAVE.x3.t[k] = -1e6; G.SAVE.x3.restAt = 1;
const T = TESTS, fails = []; let ok = 0;
for (const t of T) {
  try {
    G.tp(t.from, t.x, t.y);
    for (const e of G.enemies) e.alive = false; G.enemies.length = 0;
    let got = false, lastX = G.P.x, still = 0;
    for (let f = 0; f < 240 && !got; f += 3) {
      let hold = [], tap = [];
      if (t.kind === 'walk') { hold = [t.dir]; if (still > 6) tap = f % 12 < 3 ? ['jump'] : f % 12 < 6 ? ['attack'] : []; }
      else { hold = ['down']; if (G.P.ground) tap = f % 12 < 6 ? ['jump'] : ['attack']; }
      G.step(3, hold, tap);
      if (G.state !== 'play') G.step(1, [], ['pause']);
      still = Math.abs(G.P.x - lastX) < 1 ? still + 1 : 0; lastX = G.P.x;
      if (G.room === t.to) got = true; else if (G.room !== t.from) { got = 'other:' + G.room; break; }
    }
    if (got === true) ok++; else fails.push(`${t.kind} ${t.from}->${t.to} @${t.x},${t.y} ${got || 'stuck at ' + Math.round(G.P.x) + ',' + Math.round(G.P.y) + ' in ' + G.room}`);
  } catch (e) { fails.push(`${t.from}->${t.to} EXC ${e}`); }
}
return { ok, fail: fails.length, fails };

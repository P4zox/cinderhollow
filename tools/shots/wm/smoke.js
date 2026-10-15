// every type: mash every input for a while; no exceptions, never stuck in a state
const errs = []; window.addEventListener('error', e => errs.push(String(e.message)));
const ce = console.error; console.error = (...a) => { errs.push(String(a[0] && a[0].stack || a[0]).slice(0, 300)); ce(...a); };
G.tp('C5', 6, 10); W().frame(30);
const out = {};
for (const t of ['longsword', 'katana', 'greatsword', 'maul', 'sns', 'dual', 'spear', 'staff', 'whip']) {
  for (const rank of [1, 5]) {
    W().reset(t, rank); G.tp('C4', 17, 10); W().frame(10); W().dummy(30);
    const states = new Set(); let stuck = 0, last = '', same = 0;
    const acts = ['attack', 'heavy', 'parry', 'roll', 'jump', 'left', 'right', 'up', 'down'];
    let seed = 1; const r = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 1500; i++) {
      const a = acts[Math.floor(r() * acts.length)];
      if (r() < 0.3) W().down(a); else if (r() < 0.5) W().up(a);
      if (r() < 0.15) W().tap(acts[Math.floor(r() * 4)]);
      W().frame(1); G.P.hp = Math.max(G.P.hp, 100); if (G.P.st < 5 && r() < 0.05) G.P.st = 100;
      states.add(G.P.state);
      if (G.P.state === last) { if (++same > 600 && !['idle', 'run', 'guard', 'air'].includes(last)) stuck++; } else { same = 0; last = G.P.state; }
    }
    for (const a of acts) W().up(a); W().frame(240);
    out[t + rank] = { n: states.size, stuck, end: G.P.state, states: [...states].filter(s => !['idle', 'run', 'air', 'land'].includes(s)).join(' ') };
  }
}
return { out, errs: [...new Set(errs)].slice(0, 12) };

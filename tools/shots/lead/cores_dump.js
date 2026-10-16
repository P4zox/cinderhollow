const o = {}; for (const [k, c] of Object.entries(E('CORES'))) o[k] = { name: c.name, trait: c.trait, desc: c.desc, col: c.col, col2: c.col2 || null, stage: E(`BOSS_STAGE['${k}']`), rematch: !E(`CR_NO_REMATCH.has('${k}')`) };
o._cost = E('CR_COST'); o._cin = E('CR_REMATCH_CINDERS'); o._xp = E('CR_REMATCH_XP'); return o;

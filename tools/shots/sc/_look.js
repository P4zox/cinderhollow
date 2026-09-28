const SPOTS = [['SF10',12,11,'i_SF10a'],['SF10',48,11,'i_SF10b'],['SF16',20,14,'i_SF16'],['SF13',4,6,'i_SF13a'],['SF13',45,16,'i_SF13b'],['SF14',8,4,'i_SF14a'],['SF14',28,17,'i_SF14b'],['SF17',8,11,'i_SF17'],['SF11',108,28,'i_SF11a'],['SF11',80,26,'i_SF11b'],['SF11',6,14,'i_SF11c'],['W6',11,40,'i_W6'],];
await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.moonstep = 1; G.SAVE.items.wings = 1; G.SAVE.items.talon = 1; G.SAVE.items.tidebreath = 1;
const spots = window.__spots || [];
const out = [];
for (const [r, x, y, tag] of SPOTS) {
  try { G.tp(r, x, y); G.step(90); G.xs.clean(); G.step(2); await snap((tag || r)); out.push(r + ' ok lights=' + G.xs.lights); }
  catch (e) { out.push(r + ' ERR ' + e.message); }
}
return out;

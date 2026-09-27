await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.moonstep=1;
for (const [r,x,y] of [['SF2',32,9],['SF4',14,48],['SF6',14,40],['NH2',28,10],['NH4',18,24],['NH1',18,12],['H1',20,10],['E2',41,10],['E1',12,22]]) { G.tp(r,x,y); G.step(40); await snap('old_'+r); }
return 'ok';

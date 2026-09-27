await boot(); G.SETTINGS.god = 1; G.grantTechniques(); G.SAVE.items.tidebreath=1;
for (const [r,x,y] of [['TV3',24,10],['TV6',20,9],['TV2',24,10],['DB4',10,24],['DB2',3,9],['DB7',8,23],['CM4',27,10],['CM2',12,37],['CM5',27,7],['CM3',12,9]]) { G.tp(r,x,y); G.step(40); await snap('ref_'+r); }
return 'ok';

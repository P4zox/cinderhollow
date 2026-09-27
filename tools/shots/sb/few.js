const spots = [['NV10',14,7],['NV15',46,12],['DU9',36,9]];
for (const [r,x,y] of spots) await shot(r,x,y,'few_'+r,{noenemy:1});
return 'ok';

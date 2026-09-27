const spots=[['NV2',17,10],['NV3',10,41],['NV4',30,16],['NV4',60,16],['NV6',18,14],['NV1',12,21],['DU1',3,10],['DU2',20,15],['DU3',30,14],['DU4',12,35],['DU5',36,8],['DU7',13,17]];
for (const [r,x,y] of spots) await shot(r,x,y,null,{noenemy:1});
return 'ok';

await boot(); G.SETTINGS.god = 1;
G.tp('T2', 9, 26); G.step(30);
await snap('s01_t2_start');
const out = { room: G.room, props: G.props.filter(p => p.type && p.type.startsWith('sys_')).map(p => p.type + ':' + (p.s.id || p.s.page || p.s.trial || '')) };
G.tp('T2', 45, 17); G.step(20); await snap('s02_t2_mid');
G.tp('T2', 80, 26); G.step(20); await snap('s03_t2_arena');
G.tp('T2b', 12, 10); G.step(20); await snap('s04_t2b');
return out;

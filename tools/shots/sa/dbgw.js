G.tp('DB13', 17, 21); wait(20); for (let i = 0; i < 6 && G.room === 'DB13'; i++) { step(['down'], ['attack']); wait(25); } for (let i = 0; i < 200 && G.room === 'DB13'; i++) step(['down']); here('bell');
swim(5, 3, { maxF: 400 }); here('under well'); for (let i = 0; i < 200 && G.room === 'DB17'; i++) step(['up', 'jump'], i % 30 === 0 ? ['jump'] : []); here('out?'); wait(30); here('ts');

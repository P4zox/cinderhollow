for (const k of ['gale','hook','emberdash','slam','wings','moonstep','tidebreath']) delete G.SAVE.items[k];
G.tp('D16', 7, 61); G.step(30); G.step(1, [], ['interact']); G.step(3); log.push('trial on ' + !!S.SYS.trial);

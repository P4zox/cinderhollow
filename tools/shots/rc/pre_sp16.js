for (const k of ['hook','emberdash','slam','wings','moonstep','tidebreath']) delete G.SAVE.items[k]; G.SAVE.items.gale = 1;
G.tp('SP16', 5, 33); G.step(30); G.step(1, [], ['interact']); G.step(3); log.push('trial on ' + !!S.SYS.trial);

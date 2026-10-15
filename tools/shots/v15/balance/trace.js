const r = E(`window.__bb.fight('${ARGS.k}', '${ARGS.t}', ${JSON.stringify({ ...(ARGS.o || {}), trace: ARGS.every || 30, secs: ARGS.secs || 60 })})`);
return [r, ...window.__bb.log];

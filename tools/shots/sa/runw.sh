#!/bin/sh
# usage: runw.sh walk_xx.js  -> builds _run.js and prints the log
cd /Users/halstonchen/Claude/cinderhollow
cat tools/shots/sa/pilot.js tools/shots/sa/$1 > tools/shots/sa/_run.js; echo 'return LOG.concat(["ROOMS " + ROOMSEQ.join(" ")]);' >> tools/shots/sa/_run.js
SHOT_HTML=web/dist/sa.html node tools/shots/shot.js tools/shots/sa/_run.js tools/shots/sa/out_w 2>&1 | head -${2:-80}

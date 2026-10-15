#!/usr/bin/env python3
# count OK/PASS and BAD/FAIL lines in a route-suite output file
import re, sys
t = open(sys.argv[1]).read()
ok = len(re.findall(r'"(?:OK |PASS )', t)); bad = re.findall(r'"((?:BAD|FAIL) [^"]*)', t)
print(ok, 'OK', len(bad), 'BAD', 'PAGE-ERRORS' if 'ERRORS' in t else '')
for b in bad: print('   ', b[:220])

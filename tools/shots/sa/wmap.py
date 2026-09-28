import sys,io,contextlib,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
src=open('rooms.py').read().split("if __name__ == '__main__':")[0]
g={'__file__':os.path.abspath('rooms.py'),'__name__':'x'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,'rooms.py','exec'),g)
X0,X1,Y0,Y1,S=[int(a) for a in sys.argv[1:6]]
R=g['ROOMS']
for r in R:
    if r.gx<X1 and r.gx+r.w>X0 and r.gy<Y1 and r.gy+r.h>Y0: print(f'{r.id:6s} {r.gx:5d}..{r.gx+r.w-1:5d}  y {r.gy:5d}..{r.gy+r.h-1:5d}  {r.biome}')
print('     '+''.join(str((X0+i*S)//10%10) if (X0+i*S)%10<S else ' ' for i in range((X1-X0)//S)))
for y in range(Y0,Y1,S):
    line=''
    for x in range(X0,X1,S):
        c='.'
        for r in R:
            if r.gx<=x<r.gx+r.w and r.gy<=y<r.gy+r.h: c=r.id[-1] if r.id[:2] in ('TV','DB','CM') else r.id[0].lower(); break
        line+=c
    print(f'{y:5d} '+line)

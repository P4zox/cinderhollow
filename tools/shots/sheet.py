import sys,glob
from PIL import Image
pat,out=sys.argv[1],sys.argv[2]; cols=int(sys.argv[3]) if len(sys.argv)>3 else 4
fs=sorted(glob.glob(pat)); ims=[Image.open(f).convert('RGB') for f in fs]
w,h=ims[0].size; s=0.5; tw,th=int(w*s),int(h*s)
rows=(len(ims)+cols-1)//cols; S=Image.new('RGB',(tw*cols,th*rows))
for i,im in enumerate(ims): S.paste(im.resize((tw,th)),((i%cols)*tw,(i//cols)*th))
S.save(out); print(len(fs),S.size)

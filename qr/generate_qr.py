import segno, random, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
URL="https://sinai-seeds.mo2868417.workers.dev"
F="/usr/share/fonts/truetype/noto/"
def font(n,s): return ImageFont.truetype(F+n,s)
# logo
og=Image.open('og_source_for_logo_cut.png').convert('RGB').crop((515,158,675,278))
import numpy as np
a=np.asarray(og).astype(float); r,g,b=a[...,0],a[...,1],a[...,2]
al=np.clip((g-b-25)/60,0,1)*np.clip((g-40)/50,0,1)
al=np.asarray(Image.fromarray((al*255).astype('uint8')).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8)))
logo=og.convert('RGBA'); logo.putalpha(Image.fromarray(al)); logo=logo.crop(logo.getchannel('A').point(lambda v:255 if v>30 else 0).getbbox())
logo.save('logo_cut.png')
qr=segno.make(URL,error='h',boost_error=False)
M=qr.matrix; N=len(M); print('modules',N,'version',qr.version)
def lerp(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))
def make_qr(px, c1, c2, logo_bg=(250,243,214), ring=(176,138,40), clear=0.22):
    SS=2; P=px*SS; m=P/N; 
    mask=Image.new('L',(P,P),0); d=ImageDraw.Draw(mask)
    cx=cy=N/2; cr=clear*N/2+0.8
    def finder(x0,y0):
        d.rounded_rectangle([x0*m,y0*m,(x0+7)*m,(y0+7)*m],radius=m*.45,fill=255)
        d.rounded_rectangle([(x0+1)*m,(y0+1)*m,(x0+6)*m,(y0+6)*m],radius=m*.2,fill=0)
        d.rounded_rectangle([(x0+2)*m,(y0+2)*m,(x0+5)*m,(y0+5)*m],radius=m*.2,fill=255)
    for fx,fy in((0,0),(N-7,0),(0,N-7)): finder(fx,fy)
    for y in range(N):
        for x in range(N):
            if not M[y][x]: continue
            if (x<8 and y<8) or (x>=N-8 and y<8) or (x<8 and y>=N-8): continue
            if math.hypot(x+.5-cx,y+.5-cy)<cr: continue
            d.rounded_rectangle([x*m-m*.05,y*m-m*.05,(x+1)*m+m*.05,(y+1)*m+m*.05],radius=m*.3,fill=255)
    grad=Image.new('RGB',(P,P)); gd=ImageDraw.Draw(grad)
    for i in range(P): gd.line([(0,i),(P,i)],fill=lerp(c1,c2,i/P))
    out=Image.new('RGBA',(P,P),(0,0,0,0)); out.paste(grad,(0,0),mask)
    # logo medallion
    R=int(clear*P/2); dd=ImageDraw.Draw(out)
    dd.ellipse([P/2-R,P/2-R,P/2+R,P/2+R],fill=logo_bg+(255,))
    dd.ellipse([P/2-R,P/2-R,P/2+R,P/2+R],outline=ring+(255,),width=max(2,P//150))
    # leaf on dark disc inside
    r2=int(R*0.82); dd.ellipse([P/2-r2,P/2-r2,P/2+r2,P/2+r2],fill=(22,30,12,255))
    lw=int(r2*1.45); lh=int(logo.height*lw/logo.width); l=logo.resize((lw,lh),Image.LANCZOS)
    out.alpha_composite(l,(int(P/2-lw/2),int(P/2-lh/2)+int(R*0.02)))
    return out.resize((px,px),Image.LANCZOS)
def spaced(d,xy,t,f,fill,sp,anchor='m'):
    w=sum(d.textlength(c,font=f) for c in t)+sp*(len(t)-1)
    x=xy[0]-w/2 if anchor=='m' else xy[0]; 
    for c in t:
        d.text((x,xy[1]),c,font=f,fill=fill); x+=d.textlength(c,font=f)+sp
def ctext(d,cx,y,t,f,fill): 
    d.text((cx,y),t,font=f,fill=fill,anchor='mt')
GOLD=(226,196,110); CREAM=(250,243,214)
# ---------- A poster
W,H=2400,3600
A=Image.new('RGB',(W,H)); ad=ImageDraw.Draw(A)
stops=[(0,(14,9,4)),(.25,(46,24,8)),(.42,(150,78,20)),(.5,(214,128,40)),(.56,(60,34,10)),(1,(14,10,4))]
for y in range(H):
    t=y/H
    for i in range(len(stops)-1):
        if stops[i][0]<=t<=stops[i+1][0]:
            u=(t-stops[i][0])/(stops[i+1][0]-stops[i][0]); c=lerp(stops[i][1],stops[i+1][1],u);break
    ad.line([(0,y),(W,y)],fill=c)
glow=Image.new('RGB',(W,H),(0,0,0)); gd=ImageDraw.Draw(glow)
gd.ellipse([W/2-520,H*.47-520,W/2+520,H*.47+520],fill=(255,170,60))
glow=glow.filter(ImageFilter.GaussianBlur(220)); A=ImageChops.add(A,glow.point(lambda v:int(v*.55)))
ad=ImageDraw.Draw(A)
random.seed(7)
for i in range(1100):
    x=random.uniform(-20,W+20); base=H+20; top=random.uniform(H*.60,H*.80); lean=random.uniform(-60,60)
    col=lerp((18,12,4),(70,44,10),random.random()*.7)
    pts=[(x+lean*(k/12)**2,base+(top-base)*k/12) for k in range(13)]
    ad.line(pts,fill=col,width=random.randint(4,8))
    ex,ey=pts[-1]
    for k in range(7):
        yy=ey+k*26; ad.ellipse([ex-9+(k%2)*10-5,yy,ex+9+(k%2)*10-5,yy+34],fill=lerp(col,(150,100,25),.35))
A=A.filter(ImageFilter.GaussianBlur(1.2)); ad=ImageDraw.Draw(A)
# panel
pw=1700; ph=1700; px0=(W-pw)//2; py0=1000
sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([px0,py0+30,px0+pw,py0+ph+30],radius=110,fill=(0,0,0,170))
A=Image.alpha_composite(A.convert('RGBA'),sh.filter(ImageFilter.GaussianBlur(50))); ad=ImageDraw.Draw(A)
ad.rounded_rectangle([px0-14,py0-14,px0+pw+14,py0+ph+14],radius=124,fill=GOLD)
ad.rounded_rectangle([px0,py0,px0+pw,py0+ph],radius=110,fill=CREAM)
q=make_qr(1420,(24,52,14),(56,34,8)); A.alpha_composite(q,(px0+(pw-1420)//2,py0+(ph-1420)//2))
# headline
ctext(ad,W/2,230,"SINAI SEEDS",font("NotoSerif-Bold.ttf",50),GOLD) if False else spaced(ad,(W/2,230),"SINAI SEEDS",font("NotoSerif-Bold.ttf",130),GOLD,34)
spaced(ad,(W/2,430),"GROW  HARVEST",font("NotoSans-Bold.ttf",46),(200,170,95),22)
ad.line([(W/2-260,560),(W/2+260,560)],fill=(176,138,40),width=4)
ctext(ad,W/2,650,"Scan to open the digital card",font("NotoSans-Bold.ttf",84),CREAM)
ctext(ad,W/2,790,"امسح الكود لفتح كارت التواصل",font("NotoSansArabic-Bold.ttf",88),(197,225,165))
ctext(ad,W/2,py0+ph+110,"Ali Fayed",font("NotoSerif-Bold.ttf",110),GOLD)
spaced(ad,(W/2,py0+ph+260),"COMPANY OWNER  ·  SINAI SEEDS",font("NotoSans-Bold.ttf",46),(200,170,95),12)
ctext(ad,W/2,py0+ph+350,"Sadat City, 11th District, Monufia, Egypt",font("NotoSans-Bold.ttf",44),(150,190,110))
A.convert('RGB').save('./sinai-qr-A-poster.png',dpi=(300,300))
# ---------- B clean
S=3000; B=Image.new('RGB',(S,S),CREAM); bd=ImageDraw.Draw(B)
q=make_qr(2150,(28,58,16),(70,42,8)); B.paste(q,((S-2150)//2,(S-2150)//2-150),q)
bd.rounded_rectangle([110,110,S-110,S-110],radius=120,outline=(176,138,40),width=10)
spaced(bd,(S/2,S-580),"SINAI SEEDS",font("NotoSerif-Bold.ttf",120),(80,52,10),30)
ctext(bd,S/2,S-390,"Scan to open the digital card",font("NotoSans-Bold.ttf",64),(70,100,40))
ctext(bd,S/2,S-285,"امسح لفتح كارت التواصل",font("NotoSansArabic-Bold.ttf",68),(70,100,40))
B.save('./sinai-qr-B-clean.png',dpi=(300,300))
# ---------- C round dark sticker (transparent corners)
S=3000; C=Image.new('RGBA',(S,S),(0,0,0,0)); cd=ImageDraw.Draw(C)
cd.ellipse([0,0,S,S],fill=(176,138,40)); cd.ellipse([40,40,S-40,S-40],fill=(16,22,10))
rg=Image.new('RGB',(S,S),(0,0,0)); ImageDraw.Draw(rg).ellipse([S/2-1100,S/2-1100,S/2+1100,S/2+1100],fill=(60,90,20))
rg=rg.filter(ImageFilter.GaussianBlur(260)); m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([60,60,S-60,S-60],fill=255)
C.paste(ImageChops.add(Image.new('RGB',(S,S),(16,22,10)),rg.point(lambda v:int(v*.5))),(0,0),m)
cd=ImageDraw.Draw(C); cd.ellipse([90,90,S-90,S-90],outline=(226,196,110),width=8)
pw=1700; cd.rounded_rectangle([(S-pw)//2,(S-pw)//2+20,(S+pw)//2,(S+pw)//2+20],radius=140,fill=CREAM)
q=make_qr(1450,(24,52,14),(56,34,8)); C.alpha_composite(q,((S-1450)//2,(S-1450)//2+20))
spaced(cd,(S/2,230),"SINAI SEEDS",font("NotoSerif-Bold.ttf",150),GOLD,36)
spaced(cd,(S/2,440),"GROW  HARVEST",font("NotoSans-Bold.ttf",56),(200,170,95),24)
ctext(cd,S/2,S-500,"Scan to open the digital card",font("NotoSans-Bold.ttf",96),CREAM)
ctext(cd,S/2,S-370,"امسح الكود لفتح كارت التواصل",font("NotoSansArabic-Bold.ttf",96),(197,225,165))
C.save('./sinai-qr-C-sticker-round.png',dpi=(300,300))

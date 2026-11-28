"""Build the printable QR cards (poster, clean square, round sticker).

Usage:  python3 generate_qr.py [URL] [OUTPUT-PREFIX]
  URL            the link the QR opens (default: the live card)
  OUTPUT-PREFIX  file name stem, written in this folder (default: sinai-qr)
  MARK           leaf (default), lockup (dark badge) or free (logo on the
                 background, no badge): what sits in the middle of the QR

The design is the same for every URL; only the encoded link changes.
Needs: pip install segno pillow numpy
"""
import segno, random, math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
URL = sys.argv[1] if len(sys.argv) > 1 else "https://sinai-seeds.mo2868417.workers.dev"
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "sinai-qr"
MARK = sys.argv[3] if len(sys.argv) > 3 else "leaf"      # "leaf" or "lockup"

# the real client logo (three leaves over the sign plate), used when MARK="lockup"
LOCKUP_W, LOCKUP_H = 363, 414
LOCKUP = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "site", "img", "logo-lockup.png")).convert("RGBA")
# same logo with the white sign plate tinted to the card cream, so it can sit
# straight on the cream background with no visible plate edge
_CREAM = (250, 243, 214)
_tint = Image.new("RGB", LOCKUP.size, _CREAM)
LOGO_CREAM = ImageChops.multiply(LOCKUP.convert("RGB"), _tint).convert("RGBA")
LOGO_CREAM.putalpha(LOCKUP.getchannel("A"))

# same again, but the sign plate is dropped altogether: only the leaves and the
# sign's lettering are kept, with a soft alpha edge, so nothing rectangular is
# drawn behind the mark at all
_PLATE_TOP = int(round(LOCKUP_H * 252 / 414))
LOGO_FREE = Image.new("RGBA", LOCKUP.size, (0, 0, 0, 0))
_src = np.asarray(LOCKUP.crop((0, _PLATE_TOP, LOCKUP_W, LOCKUP_H)).convert("RGB")).astype("float32")
_lum = _src.mean(axis=2)
_green = (_src[..., 1] - np.maximum(_src[..., 0], _src[..., 2])) > 18
# alpha is how much ink covers each pixel, measured against the plate colour and
# the ink colour, so thin strokes keep their weight instead of being cut away
_bg = np.median(_src[_lum > 200], axis=0)
_dark = _src[_lum < 90]
_ink_col = np.median(_dark, axis=0) if len(_dark) else np.array([60, 40, 30], dtype="float32")
_cov = np.clip((_bg[None, None, :] - _src) /
               np.maximum(_bg[None, None, :] - _ink_col[None, None, :], 1.0), 0, 1)
_a = np.clip((_cov.max(axis=2) - 0.04) / 0.96, 0, 1)
# drop the plate's own border line and shadow: they run along the crop's edges
_a[:18, :] = 0; _a[146:, :] = 0; _a[:, :14] = 0; _a[:, 346:] = 0
_a[_green] = 1.0                                 # leaf pixels keep full weight
# recover the true ink colour from the blend, so antialiased edges stay smooth
_rgb = (_src - (1 - _a[..., None]) * _bg[None, None, :]) / np.maximum(_a[..., None], 1e-3)
_rgb = np.clip(_rgb, 0, 255)
_rgb[_a < 0.05] = _ink_col
_rgb[_green] = _src[_green]
_ink_img = Image.fromarray(_rgb.astype("uint8")).convert("RGBA")
_ink_img.putalpha(Image.fromarray((_a * 255).astype("uint8")))
LOGO_FREE.alpha_composite(_ink_img, (0, _PLATE_TOP))
# the leaves above the plate, unchanged
LOGO_FREE.alpha_composite(LOCKUP.crop((0, 0, LOCKUP_W, _PLATE_TOP)), (0, 0))
# the leaves are cut flat where the sign plate used to cover them: soften the
# last two rows a little so the cut is not a hairline (not a fade, just a feather)
_la = np.asarray(LOGO_FREE.getchannel("A")).astype("float32")
for _i, _k in enumerate((0.35, 0.65, 0.88)):
    _la[_PLATE_TOP - 3 + _i, :] *= _k
LOGO_FREE.putalpha(Image.fromarray(_la.astype("uint8")))
LOGO_FREE.save('logo-free-preview.png')
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
def make_qr(px, c1, c2, mark="leaf", logo_bg=(250,243,214), ring=(176,138,40), clear=0.22, badge_h=0.24, badge_fill=(20,28,11)):
    """Draw the QR with a mark in the middle.

    mark="leaf"    the old green leaf on a dark disc (the first card's set)
    mark="lockup"  the real Sinai Seeds logo, leaves over the sign plate, on a
                   dark badge with a gold ring
    mark="free"    the same logo straight on the background, no badge, plate
                   tinted to the card cream so it has no visible edge
    """
    SS=2; P=px*SS; m=P/N
    mask=Image.new('L',(P,P),0); d=ImageDraw.Draw(mask)
    cx=cy=N/2
    if mark=="leaf":
        cr=clear*N/2+0.8; hw=hh=cr
        def covered(x,y): return math.hypot(x+.5-cx,y+.5-cy)<cr
    elif mark=="free":
        logo_h=0.30*N                       # logo height in modules
        hw=logo_h*LOCKUP_W/LOCKUP_H/2+1.0   # one module of margin all round
        hh=logo_h/2+1.0
        def covered(x,y): return abs(x+.5-cx)<hw and abs(y+.5-cy)<hh
    else:
        hh=badge_h*N/2+0.8
        hw=hh*LOCKUP_W/LOCKUP_H*1.06
        def covered(x,y): return abs(x+.5-cx)<hw and abs(y+.5-cy)<hh
    def finder(x0,y0):
        d.rounded_rectangle([x0*m,y0*m,(x0+7)*m,(y0+7)*m],radius=m*.45,fill=255)
        d.rounded_rectangle([(x0+1)*m,(y0+1)*m,(x0+6)*m,(y0+6)*m],radius=m*.2,fill=0)
        d.rounded_rectangle([(x0+2)*m,(y0+2)*m,(x0+5)*m,(y0+5)*m],radius=m*.2,fill=255)
    for fx,fy in((0,0),(N-7,0),(0,N-7)): finder(fx,fy)
    for y in range(N):
        for x in range(N):
            if not M[y][x]: continue
            if (x<8 and y<8) or (x>=N-8 and y<8) or (x<8 and y>=N-8): continue
            if covered(x,y): continue
            d.rounded_rectangle([x*m-m*.05,y*m-m*.05,(x+1)*m+m*.05,(y+1)*m+m*.05],radius=m*.3,fill=255)
    grad=Image.new('RGB',(P,P)); gd=ImageDraw.Draw(grad)
    for i in range(P): gd.line([(0,i),(P,i)],fill=lerp(c1,c2,i/P))
    out=Image.new('RGBA',(P,P),(0,0,0,0)); out.paste(grad,(0,0),mask)
    dd=ImageDraw.Draw(out)
    if mark=="leaf":
        R=int(clear*P/2)
        dd.ellipse([P/2-R,P/2-R,P/2+R,P/2+R],fill=logo_bg+(255,))
        dd.ellipse([P/2-R,P/2-R,P/2+R,P/2+R],outline=ring+(255,),width=max(2,P//150))
        r2=int(R*0.82); dd.ellipse([P/2-r2,P/2-r2,P/2+r2,P/2+r2],fill=(22,30,12,255))
        lw=int(r2*1.45); lh=int(logo.height*lw/logo.width); l=logo.resize((lw,lh),Image.LANCZOS)
        out.alpha_composite(l,(int(P/2-lw/2),int(P/2-lh/2)+int(R*0.02)))
    elif mark=="free":
        lw=int(2*(hw-1.0)*m); lh=int(2*(hh-1.0)*m)
        _lo = LOGO_FREE.convert("RGBa").resize((lw,lh),Image.LANCZOS).convert("RGBA")  # premultiplied: no halo from the transparent edge
        out.alpha_composite(_lo,(int(P/2-lw/2),int(P/2-lh/2)))
    else:
        bw=int(2*hw*m); bh=int(2*hh*m)
        dd.rounded_rectangle([P/2-bw/2,P/2-bh/2,P/2+bw/2,P/2+bh/2],radius=int(bh*.10),
                             fill=badge_fill+(255,),outline=ring+(255,),width=max(3,int(P/260)))
        pad=int(bh*.07)
        lh=bh-2*pad; lw=int(lh*LOCKUP_W/LOCKUP_H)
        out.alpha_composite(LOCKUP.resize((lw,lh),Image.LANCZOS),(int(P/2-lw/2),int(P/2-lh/2)))
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
q=make_qr(1420,(24,52,14),(56,34,8),mark=MARK); A.alpha_composite(q,(px0+(pw-1420)//2,py0+(ph-1420)//2))
# headline
ctext(ad,W/2,230,"SINAI SEEDS",font("NotoSerif-Bold.ttf",50),GOLD) if False else spaced(ad,(W/2,230),"SINAI SEEDS",font("NotoSerif-Bold.ttf",130),GOLD,34)
spaced(ad,(W/2,430),"GROW  HARVEST",font("NotoSans-Bold.ttf",46),(200,170,95),22)
ad.line([(W/2-260,560),(W/2+260,560)],fill=(176,138,40),width=4)
ctext(ad,W/2,650,"Scan to open the digital card",font("NotoSans-Bold.ttf",84),CREAM)
ctext(ad,W/2,790,"امسح الكود لفتح كارت التواصل",font("NotoSansArabic-Bold.ttf",88),(197,225,165))
ctext(ad,W/2,py0+ph+110,"Ali Fayed",font("NotoSerif-Bold.ttf",110),GOLD)
spaced(ad,(W/2,py0+ph+260),"COMPANY OWNER  ·  SINAI SEEDS",font("NotoSans-Bold.ttf",46),(200,170,95),12)
ctext(ad,W/2,py0+ph+350,"Sadat City, 11th District, Monufia, Egypt",font("NotoSans-Bold.ttf",44),(150,190,110))
ad.line([(W/2-200,py0+ph+455),(W/2+200,py0+ph+455)],fill=(120,96,32),width=3)
spaced(ad,(W/2,py0+ph+500),URL.replace("https://",""),font("NotoSans-Bold.ttf",40),(170,150,105),5)
A.convert('RGB').save(f'./{PREFIX}-A-poster.png',dpi=(300,300))
# ---------- B clean
S=3000; B=Image.new('RGB',(S,S),CREAM); bd=ImageDraw.Draw(B)
QS=2000; q=make_qr(QS,(28,58,16),(70,42,8),mark=MARK); B.paste(q,((S-QS)//2,360),q)
bd.rounded_rectangle([110,110,S-110,S-110],radius=120,outline=(176,138,40),width=10)
spaced(bd,(S/2,2470),"SINAI SEEDS",font("NotoSerif-Bold.ttf",110),(80,52,10),28)
ctext(bd,S/2,2640,"Scan to open the digital card",font("NotoSans-Bold.ttf",60),(70,100,40))
ctext(bd,S/2,2740,"امسح لفتح كارت التواصل",font("NotoSansArabic-Bold.ttf",64),(70,100,40))
B.save(f'./{PREFIX}-B-clean.png',dpi=(300,300))
# ---------- C round dark sticker (transparent corners)
S=3000; C=Image.new('RGBA',(S,S),(0,0,0,0)); cd=ImageDraw.Draw(C)
cd.ellipse([0,0,S,S],fill=(176,138,40)); cd.ellipse([40,40,S-40,S-40],fill=(16,22,10))
rg=Image.new('RGB',(S,S),(0,0,0)); ImageDraw.Draw(rg).ellipse([S/2-1100,S/2-1100,S/2+1100,S/2+1100],fill=(60,90,20))
rg=rg.filter(ImageFilter.GaussianBlur(260)); m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse([60,60,S-60,S-60],fill=255)
C.paste(ImageChops.add(Image.new('RGB',(S,S),(16,22,10)),rg.point(lambda v:int(v*.5))),(0,0),m)
cd=ImageDraw.Draw(C); cd.ellipse([90,90,S-90,S-90],outline=(226,196,110),width=8)
pw=1700; cd.rounded_rectangle([(S-pw)//2,(S-pw)//2+20,(S+pw)//2,(S+pw)//2+20],radius=140,fill=CREAM)
q=make_qr(1450,(24,52,14),(56,34,8),mark=MARK); C.alpha_composite(q,((S-1450)//2,(S-1450)//2+20))
spaced(cd,(S/2,230),"SINAI SEEDS",font("NotoSerif-Bold.ttf",150),GOLD,36)
spaced(cd,(S/2,440),"GROW  HARVEST",font("NotoSans-Bold.ttf",56),(200,170,95),24)
ctext(cd,S/2,S-500,"Scan to open the digital card",font("NotoSans-Bold.ttf",96),CREAM)
ctext(cd,S/2,S-370,"امسح الكود لفتح كارت التواصل",font("NotoSansArabic-Bold.ttf",96),(197,225,165))
C.save(f'./{PREFIX}-C-sticker-round.png',dpi=(300,300))

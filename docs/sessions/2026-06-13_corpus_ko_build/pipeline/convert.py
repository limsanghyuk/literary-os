import os,glob,subprocess,re,json,sys
SC="/sessions/upbeat-focused-bohr/mnt/literary/scripts"
ROOT="/sessions/upbeat-focused-bohr/mnt/literary/corpus_ko"
TXT=ROOT+"/txt"; os.makedirs(TXT,exist_ok=True)
def hwpver(p):
    b=open(p,'rb').read(48)
    if b.startswith(b'HWP Document File V3.00'): return "HWP3"
    if b[:8]==b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': return "HWP5"
    return "UNK"
def wid(fn):
    n=os.path.splitext(os.path.basename(fn))[0]
    n=re.sub(r'_\d+$','',n)              # 감시자들_1 -> 감시자들
    n=re.sub(r'\.part\d+$','',n)
    return n.strip()
srcs=[]
for media,sub in [("film","한국 영화"),("drama_sgc","한국 드라마/신사의 품격"),("drama_dots","한국 드라마/새 폴더")]:
    for p in glob.glob(f"{SC}/{sub}/*"):
        if os.path.isdir(p): continue
        ext=os.path.splitext(p)[1].lower()
        t={'.hwp':hwpver(p),'.pdf':'PDF','.doc':'DOC','.docx':'DOCX','.rar':'RAR'}.get(ext,'UNK')
        srcs.append((media,wid(p),p,ext,t))
json.dump([{"media":m,"id":i,"src":os.path.basename(p),"type":t} for m,i,p,e,t in srcs],
          open(ROOT+"/sources.json","w"),ensure_ascii=False,indent=1)
from collections import Counter
print("TOTAL",len(srcs),dict(Counter(t for *_,t in srcs)))
# HWP5 -> hwp5txt ; PDF -> pdftotext
import time;START=time.time();TIME_BUDGET=33
done=0;fail=[]
for m,i,p,e,t in srcs:
    if time.time()-START>TIME_BUDGET: print('time budget hit',flush=True); break
    out=f"{TXT}/{i}.txt"
    if os.path.exists(out) and os.path.getsize(out)>200: continue
    try:
        if t=="HWP5":
            r=subprocess.run(["hwp5txt",p],capture_output=True,timeout=60)
            txt=r.stdout.decode('utf-8','ignore')
        elif t=="PDF":
            r=subprocess.run(["pdftotext","-layout",p,"-"],capture_output=True,timeout=60)
            txt=r.stdout.decode('utf-8','ignore')
        else:
            continue
        if len(txt.strip())>200:
            open(out,"w").write(txt); done+=1
        else: fail.append((i,t,"empty"))
    except Exception as ex: fail.append((i,t,str(ex)[:40]))
rem=sum(1 for m,i,p,e,t in srcs if t in("HWP5","PDF") and not(os.path.exists(f"{TXT}/{i}.txt") and os.path.getsize(f"{TXT}/{i}.txt")>200))
print("converted(hwp5+pdf) this run:",done,"remaining:",rem,"fail:",fail[:6],flush=True)

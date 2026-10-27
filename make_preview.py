"""dist içinden tek dosyalık önizlemeler üretir (görseller gömülü)."""
import re,base64
from pathlib import Path
R=Path(__file__).parent; D=R/'dist'
def emb(path):
    b=(D/path).read_bytes(); t='image/webp' if path.endswith('.webp') else 'image/png'
    return f'data:{t};base64,'+base64.b64encode(b).decode()
pages=sorted(x.name for x in D.glob('*.html') if x.name!='index.html')
for src,dst in [('index.html','ONIZLEME-MICE-Xperience-Global.html')]+[(x,'ONIZLEME-'+x) for x in pages]:
    s=(D/src).read_text(encoding='utf-8')
    s=re.sub(r'\s(srcset|sizes)="[^"]*"','',s)
    s=re.sub(r'<link rel="preload" as="image"[^>]*>','',s)
    s=re.sub(r'(?<=["\'(])img/[A-Za-z0-9_\-/]+\.(webp|png)(?=["\')])',lambda m:emb(m.group(0)),s)
    for x in pages: s=s.replace(f'href="{x}"',f'href="ONIZLEME-{x}"')
    s=s.replace('href="index.html','href="ONIZLEME-MICE-Xperience-Global.html')
    s=s.replace('if(target&&grid&&grid.getAttribute("data-month-feat")!==target){','if(false){').replace('if(kick&&target) kick','if(false) kick')
    (R/dst).write_text(s,encoding='utf-8'); print(dst, round((R/dst).stat().st_size/1e6,1),'MB')

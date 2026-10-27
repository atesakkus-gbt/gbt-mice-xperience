"""MICE Xperience Türkiye (inbound, TR + EN) derleyici.

Kullanım:
  python3 build_tr.py [SHA] [--canli]
Çıktılar:
  dist-tr/img/                       webp görseller (depo main/img/ klasörüne kopyalanır)
  tek/mice-xperience-turkiye.html    panel dosyası (görseller jsDelivr @SHA)
  ONIZLEME-MICE-Xperience-Turkiye.html  görselleri gömülü önizleme (ekip kontrolü)
Kaynaklar: tr/programlar.json, tr/detaylar.json, tr/template*.html, tr/full/<anahtar>.(webp|jpg|png)
Görsel yoksa geçici yer tutucu üretilir (sayısı derleme sonunda yazılır).
Dil: sayfada TR/EN düğmesi; ?lang=en ile İngilizce açılır. Seçim tarayıcıda hatırlanır.
"""
import json, re, sys, html, base64, shutil
from urllib.parse import quote
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from build import fit
from build_tek import scope

ROOT = Path(__file__).parent
TR = ROOT / "tr"
DIST = ROOT / "dist-tr"
IMG = DIST / "img"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
CANLI = "--canli" in sys.argv
SURUM = ARGS[0] if ARGS else "v1"
CDN = f"https://cdn.jsdelivr.net/gh/atesakkus-gbt/gbt-mice-xperience@{SURUM}/img/"
SAYFA_URL = "https://kurumsal.goldenbaytour.com/experience/mice-xperience-turkiye"
AY = {"tr": ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"],
      "en": ["January","February","March","April","May","June","July","August","September","October","November","December"]}
AILE = {"sehir": ("Şehir & Kongre", "City & Congress"), "kiyi": ("Kıyı & Resort", "Coast & Resort"),
        "miras": ("Kültür & Doğa", "Heritage & Nature"), "mavi": ("Yat & Mavi Yolculuk", "Yacht & Blue Voyage")}
e = html.escape

def L(tr, en, raw=False):
    f = (lambda x: x) if raw else e
    return f'<span data-l="tr">{f(tr)}</span><span data-l="en">{f(en)}</span>'

def A(attr, tr, en):
    return f'{attr}="{e(tr)}" data-{attr}-tr="{e(tr)}" data-{attr}-en="{e(en)}"'

def markers(s):
    s = re.sub(r"\{\{A:([a-z-]+):(.*?)\|\|(.*?)\}\}", lambda m: A(m.group(1), m.group(2), m.group(3)), s)
    return re.sub(r"\[\[(.*?)\|\|(.*?)\]\]", lambda m: L(m.group(1), m.group(2), raw=True), s, flags=re.S)

def ym(m, lang):
    y, mo = m.split("-"); return f"{AY[lang][int(mo)-1]} {y}"

# ---------- görseller ----------
yer_tutucu = []
dusuk = []
def placeholder(key, ratio):
    w = 1200; h = round(w / ratio)
    im = Image.new("RGB", (w, h), "#14213D"); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h; d.line([(0, y), (w, y)], fill=(int(20 + 154*t*.5), int(33 + 102*t*.5), int(61 - 4*t)))
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
    except OSError: f = ImageFont.load_default()
    d.text((w/2, h/2), key, fill="#E7D6AA", font=f, anchor="mm")
    return im

done = set()
def make_image(key, ratio=1.6):
    if (key, ratio) in done: return
    done.add((key, ratio))
    src = next((p for p in (TR / "full" / f"{key}.{x}" for x in ("webp", "jpg", "jpeg", "png")) if p.exists()), None)
    if src is None and (TR / "canva_thumbs" / f"{key}.png").exists():
        src = TR / "canva_thumbs" / f"{key}.png"; dusuk.append(key)  # geçici düşük çözünürlük (Canva önizlemesi)
    if src is None:
        g = next((p for p in [ROOT / "src/full" / f"{key}.{x}" for x in ("webp", "jpg", "png")] + [ROOT / "src/canva_thumbs" / f"{key}.jpg"] if p.exists()), None)
        if g is not None: im = Image.open(g)  # global sayfadaki ortak görseller (ör. toplantı)
        else: im = placeholder(key, ratio); yer_tutucu.append(key)
    else:
        im = Image.open(src)
    fit(im, 1200, ratio).save(IMG / f"{key}.webp", "WEBP", quality=76, method=6)
    fit(im, 640, ratio).save(IMG / f"{key}-sm.webp", "WEBP", quality=74, method=6)

def pic(key, alt_tr, alt_en, sizes, w=640, h=400, eager=False):
    lz = "" if eager else ' loading="lazy"'
    return (f'<img src="img/{key}-sm.webp" srcset="img/{key}-sm.webp 640w, img/{key}.webp 1200w" sizes="{sizes}" '
            f'width="{w}" height="{h}"{lz} {A("alt", alt_tr, alt_en)}>')

# ---------- ana sayfa ----------
def build_master(P):
    progs = sorted(P["programlar"], key=lambda p: p["ay"])
    months = list(dict.fromkeys(p["ay"] for p in progs))
    for p in progs: make_image(p["gorsel"])
    for y in P["yilbasi"]: make_image(y["gorsel"], ratio=4/3)
    make_image("toplanti", ratio=640/704)
    Image.open(ROOT / "src/logo-koyu-crop.png").save(IMG / "logo-gbt-mice.png", optimize=True)

    strip = "".join(f'<a href="#ay-{m}" data-month="{m}">{L(AY["tr"][int(m[5:])-1], AY["en"][int(m[5:])-1])}<small>{m[:4]}</small></a>' for m in months)

    def btn(p):
        if p.get("hazir"): return f'<a class="more" href="{p["sayfa"]}.html">{L("Programı İncele →", "View Programme →")}</a>'
        return f'<a class="more ask" href="#teklif">{L("Teklif İste →", "Request a Quote →")}</a>'

    cal = []
    for i, m in enumerate(months):
        cards = []
        for p in [x for x in progs if x["ay"] == m]:
            t, n = p["tr"], p["en"]
            cards.append(f'<article class="route" data-family="{p["aile"]}"><figure class="img">'
                         f'{pic(p["gorsel"], t["alt"], n["alt"], "(max-width:760px) 92vw, (max-width:980px) 46vw, 440px")}</figure>'
                         f'<div class="route-body"><div class="fam">{L(*AILE[p["aile"]])}</div><h3>{L(t["baslik"], n["baslik"])}</h3><p>{L(t["slogan"], n["slogan"])}</p>'
                         f'<div class="route-foot"><span class="tag">{L(t["etiket"], n["etiket"])}</span>{btn(p)}</div></div></article>')
        mo = int(m[5:]) - 1
        cal.append(f'<section class="month" id="ay-{m}" data-month="{m}"><div class="month-label"><span class="m">{L(AY["tr"][mo], AY["en"][mo])}</span>'
                   f'<span class="y">{m[:4]}</span></div><div class="routes">{"".join(cards)}</div></section>')
        if i % 3 == 2 and i < len(months) - 1:
            cal.append(f'<div class="mid-cta" data-month="{m}"><strong>{L("Bu dönem için grubunuzu Türkiye’de mi ağırlamak istiyorsunuz?", "Planning to bring your group to Türkiye in this period?")}</strong>'
                       f'<a class="btn btn-gold" href="#teklif">{L("Teklif İste", "Request a Quote")}</a></div>')

    hedef = {"inbound": ("Yurtdışından gelen gruplar", "Groups from abroad"), "ikisi": None, "yerel": None}
    ny = []
    for y in P["yilbasi"]:
        t, n = y["tr"], y["en"]
        ny.append(f'<article class="nyc"><figure class="img">{pic(y["gorsel"], t["alt"], n["alt"], "(max-width:560px) 92vw, (max-width:980px) 46vw, 280px", 640, 480)}</figure>'
                  f'<div class="nyc-body"><span class="who">{L(t["kim"], n["kim"])}</span><h3>{L(t["baslik"], n["baslik"])}</h3><p>{L(t["metin"], n["metin"])}</p>'
                  f'<a class="more" href="{y["sayfa"]}.html">{L("Programı İncele →", "View Programme →")}</a></div></article>')

    feat_m = months[0]
    feat = []
    for p in [x for x in progs if x["ay"] == feat_m]:
        t, n = p["tr"], p["en"]
        acts = (f'<a class="btn btn-navy" href="{p["sayfa"]}.html">{L("Programı İncele", "View Programme")}</a><a class="btn btn-line" href="#teklif">{L("Teklif İste", "Request a Quote")}</a>'
                if p.get("hazir") else f'<a class="btn btn-navy" href="#teklif">{L("Bu Rota İçin Teklif İste", "Request a Quote for This Route")}</a>')
        feat.append(f'<article class="feat"><div class="img"><img src="img/{p["gorsel"]}.webp" width="1200" height="750" loading="lazy" {A("alt", t["alt"], n["alt"])}></div>'
                    f'<div class="feat-body"><div class="fam">{L(*AILE[p["aile"]])}</div><h3>{L(t["baslik"], n["baslik"])}</h3><p>{L(t["ozet"], n["ozet"])}</p><div class="feat-actions">{acts}</div></div></article>')

    gcss = re.search(r"<style>(.*?)</style>", (ROOT / "src/template.html").read_text(encoding="utf-8"), re.S).group(1)
    tpl = (TR / "template.html").read_text(encoding="utf-8").replace("{{GLOBAL_CSS}}", gcss)
    data = {"programlar": [{k: p[k] for k in ("ay", "aile", "gorsel", "sayfa", "hazir", "tr", "en")} for p in progs]}
    body = (markers(tpl).replace("{{STRIP}}", strip).replace("{{CALENDAR}}", "".join(cal)).replace("{{YILBASI}}", "".join(ny))
            .replace("{{FEATURED}}", "".join(feat)).replace("{{FEAT_KICKER}}", L(ym(feat_m, "tr") + " · öne çıkanlar", ym(feat_m, "en") + " · featured"))
            .replace("{{STAT_MONTHS}}", str(len(months))).replace("{{STAT_PROGRAMS}}", str(len(progs)))
            .replace("{{DATA}}", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    body = body.replace('id="feat-grid">', f'id="feat-grid" data-month-feat="{feat_m}">')
    return body, progs

# ---------- detay sayfaları ----------
def build_details(P, progs):
    det = json.loads((TR / "detaylar.json").read_text(encoding="utf-8"))["sayfalar"]
    gcss = re.search(r"<style>(.*?)</style>", (ROOT / "src/template_detay.html").read_text(encoding="utf-8"), re.S).group(1)
    tpl = markers((TR / "template_detay.html").read_text(encoding="utf-8").replace("{{GLOBAL_CSS}}", gcss))
    lw, lh = Image.open(IMG / "logo-gbt-mice.png").size
    by = {}
    for p in progs: by.setdefault(p["sayfa"], p)
    for y in P["yilbasi"]:
        by.setdefault(y["sayfa"], {"sayfa": y["sayfa"], "gorsel": y["gorsel"], "tr": {**y["tr"], "slogan": y["tr"]["kim"]}, "en": {**y["en"], "slogan": y["en"]["kim"]}, "ay": "yilbasi", "hazir": True})
    out = {}
    for d in det:
        p = by[d["sayfa"]]; t, n = d["tr"], d["en"]
        bt, bn = p["tr"]["baslik"], p["en"]["baslik"]
        make_image(d["kapak"])
        dt = t.get("donem") or ym(p["ay"], "tr"); dn = n.get("donem") or ym(p["ay"], "en")
        gun = []
        for i, g in enumerate(d["gunler"], 1):
            make_image(g["gorsel"], ratio=1.5)
            gt, gn = g["tr"], g["en"]
            gun.append(f'<article class="day"><div class="day-no"><b>{i:02d}</b><span>{L(f"{i}. {t["birim"].lower()}", f"{n["birim"]} {i}")}</span></div>'
                       f'<figure class="day-img">{pic(g["gorsel"], gt["alt"], gn["alt"], "(max-width:760px) 92vw, 520px", 640, 427)}</figure>'
                       f'<div class="day-body"><h3>{L(gt["baslik"], gn["baslik"])}</h3><p>{L(gt["metin"], gn["metin"])}</p><span class="tag">{L(gt["etiket"], gn["etiket"])}</span></div></article>')
        others, seen = [], {d["sayfa"]}
        for o in sorted(by.values(), key=lambda x: (not x.get("hazir"), x["ay"] == "yilbasi", x["ay"])):
            if o["sayfa"] in seen or not o.get("hazir"): continue
            seen.add(o["sayfa"]); others.append(o)
            if len(others) == 3: break
        rel = []
        for o in others:
            m = L("Yılbaşı", "New Year") if o["ay"] == "yilbasi" else L(ym(o["ay"], "tr"), ym(o["ay"], "en"))
            rel.append(f'<a class="rel" href="{o["sayfa"]}.html"><figure class="img"><img src="img/{o["gorsel"]}-sm.webp" width="640" height="400" loading="lazy" {A("alt", o["tr"]["alt"], o["en"]["alt"])}></figure>'
                       f'<div class="rel-body"><span class="m">{m}</span><h3>{L(o["tr"]["baslik"], o["en"]["baslik"])}</h3><p>{L(o["tr"]["slogan"], o["en"]["slogan"])}</p></div></a>')
        ny = d["sayfa"].startswith("yilbasi")
        crumb_href = "index.html#yilbasi" if ny else f'index.html#ay-{p["ay"]}'
        crumb = L("Yılbaşı", "New Year") if ny else L(ym(p["ay"], "tr"), ym(p["ay"], "en"))
        h1 = lambda s: e(s).replace(" · ", ' <span class="amp">·</span><br>').replace(" &amp; ", ' <span class="amp">&amp;</span><br>')
        konu = quote(f"MICE Xperience Türkiye – {bt} ({dt})")
        body = (tpl.replace("{{KAPAK}}", d["kapak"]).replace("{{KAPAK_ALT}}", A("alt", t["kapak_alt"], n["kapak_alt"]))
                .replace("{{CRUMB_HREF}}", crumb_href).replace("{{CRUMB}}", crumb).replace("{{BASLIK}}", L(bt, bn))
                .replace("{{BASLIK_H1}}", L(h1(bt), h1(bn), raw=True)).replace("{{DONEM}}", L(dt, dn))
                .replace("{{ALT_BASLIK}}", L(t["alt_baslik"], n["alt_baslik"])).replace("{{GIRIS}}", L(t["giris"], n["giris"]))
                .replace("{{SURE}}", L(t["sure"], n["sure"])).replace("{{AILE}}", L(*AILE[d["aile"]]))
                .replace("{{AKIS_NOTU}}", L(t["akis_notu"], n["akis_notu"])).replace("{{GUNLER}}", "".join(gun))
                .replace("{{CTA_H2}}", L(f"{bt} programınızı birlikte tasarlayalım.", f"Let's design your {bn} programme together."))
                .replace("{{DIGER}}", "".join(rel)).replace("{{MAIL_KONU}}", konu)
                .replace("{{LOGO_W}}", str(lw)).replace("{{LOGO_H}}", str(lh)))
        out[d["sayfa"]] = (body, {"tr": f"{bt} | MICE Xperience Türkiye | Golden Bay Tour", "en": f"{bn} | MICE Xperience Türkiye | Golden Bay Tour"})
    return out

# ---------- tek dosya ----------
LANG_CSS = ('[data-l]{font:inherit!important;color:inherit!important;letter-spacing:inherit!important;text-transform:inherit!important;background:none!important;padding:0!important;margin:0!important;border:0!important}\n'
            'html:not([data-lang="en"]) [data-l="en"]{display:none!important}\n'
            'html[data-lang="en"] [data-l="tr"]{display:none!important}')
LANG_HEAD = """<script>(function(){var l=null;try{l=new URLSearchParams(location.search).get("lang");}catch(e){}
if(l!=="tr"&&l!=="en"){try{l=localStorage.getItem("mx-lang");}catch(e){}}
if(l!=="tr"&&l!=="en"){l=((navigator.languages&&navigator.languages[0])||navigator.language||"").toLowerCase().indexOf("tr")===0?"tr":"en";}
var d=document.documentElement;d.setAttribute("data-lang",l);d.lang=l;})();</script>"""

def split(doc):
    css = "\n".join(re.findall(r"<style>(.*?)</style>", doc, re.S))
    body = re.sub(r"<style>.*?</style>", "", doc, flags=re.S)
    body = re.sub(r"<link [^>]*>", "", body).replace("{{HEAD}}", "").replace("{{BODY_OPEN}}", "").replace("{{BODY_CLOSE}}", "")
    return css, body.strip()

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    IMG.mkdir(parents=True)
    P = json.loads((TR / "programlar.json").read_text(encoding="utf-8"))
    master, progs = build_master(P)
    details = build_details(P, progs)
    slugs = set(details)

    def link_fix(s):
        s = re.sub(r'href="([a-z0-9-]+)\.html"', lambda m: f'href="#{m.group(1)}"' if m.group(1) in slugs else m.group(0), s)
        return s.replace('href="index.html#', 'href="#').replace('href="index.html"', 'href="#top"')

    mcss, mb = split(master)
    mb = link_fix(mb).replace('var href=p.hazir?p.sayfa:"#teklif"', 'var href=p.hazir?"#"+p.sayfa:"#teklif"')
    mb = f'<div id="mv">{mb}</div>'
    dviews, titles, dcss = [], {}, ""
    for slug, (doc, tt) in details.items():
        css, b = split(doc); dcss = dcss or css; titles[slug] = tt
        b = link_fix(b)
        for i in set(re.findall(r'\bid="([^"]+)"', b)):
            b = b.replace(f'id="{i}"', f'id="{slug}--{i}"').replace(f'href="#{i}"', f'href="#{slug}--{i}"')
        b = re.sub(r'<iframe([^>]*?)\ssrc="', r'<iframe\1 data-src="', b)
        dviews.append(f'<div class="dv" id="dv-{slug}" data-slug="{slug}" hidden>{b}</div>')

    ortak = re.search(r"/\* Türkiye sürümü ekleri \*/(.*?)/\* yılbaşı bölümü \*/", mcss, re.S).group(1)  # dil düğmesi vb.
    css = scope(mcss, "#mv") + "\n" + scope(dcss + ortak, ".dv") + "\n" + LANG_CSS + "\n[hidden]{display:none!important}\nbody{margin:0;background:#FCFAF6}"

    MT = {"tr": "MICE Xperience Türkiye | Türkiye'de Incentive, Kongre ve Yılbaşı | Golden Bay Tour",
          "en": "MICE Xperience Türkiye | Incentives, Congresses & New Year in Türkiye | Golden Bay Tour"}
    desc = ("Golden Bay Tour MICE Xperience Türkiye: yurtdışından Türkiye'ye gelen kurumsal gruplar için incentive, kongre, kick-off ve yılbaşı programları. "
            "Incentive, congress and New Year programmes in Türkiye for international corporate groups.")
    router = """<script>
(function(){
  var MT=%s, TITLES=%s, mv=document.getElementById("mv");
  var views=[].slice.call(document.querySelectorAll(".dv")), cur=null;
  function lang(){return document.documentElement.getAttribute("data-lang")==="en"?"en":"tr";}
  function setTitle(){var s=cur&&cur.getAttribute("data-slug");document.title=(s&&TITLES[s]?TITLES[s]:MT)[lang()];}
  function apply(){
    var l=lang();
    document.querySelectorAll("[data-set-lang]").forEach(function(b){b.setAttribute("aria-pressed",String(b.getAttribute("data-set-lang")===l));});
    ["alt","aria-label","title"].forEach(function(a){document.querySelectorAll("[data-"+a+"-"+l+"]").forEach(function(x){x.setAttribute(a,x.getAttribute("data-"+a+"-"+l));});});
    setTitle();
  }
  window.mxLang={apply:apply,set:function(l){var d=document.documentElement;d.setAttribute("data-lang",l);d.lang=l;try{localStorage.setItem("mx-lang",l);}catch(e){}apply();}};
  document.addEventListener("click",function(ev){var b=ev.target.closest&&ev.target.closest("[data-set-lang]");if(b){window.mxLang.set(b.getAttribute("data-set-lang"));}});
  function find(h){for(var i=0;i<views.length;i++){var s=views[i].getAttribute("data-slug");if(h===s||h.indexOf(s+"--")===0)return views[i];}return null;}
  function route(){
    var h=decodeURIComponent((location.hash||"").slice(1)), v=find(h);
    if(v){
      mv.hidden=true; views.forEach(function(x){x.hidden=(x!==v);});
      v.querySelectorAll("iframe[data-src]").forEach(function(f){f.src=f.getAttribute("data-src");f.removeAttribute("data-src");});
      var t=h!==v.getAttribute("data-slug")?document.getElementById(h):null;
      if(t){t.scrollIntoView();}else if(cur!==v){window.scrollTo(0,0);}
      cur=v;
    }else{
      var was=cur; views.forEach(function(x){x.hidden=true;}); mv.hidden=false; cur=null;
      var t=(h&&h!=="top")?document.getElementById(h):null;
      if(h==="top"){window.scrollTo(0,0);}else if(t){setTimeout(function(){t.scrollIntoView();},0);}else if(was){window.scrollTo(0,0);}
    }
    setTitle();
  }
  window.addEventListener("hashchange",route); route(); apply();
})();
</script>""" % (json.dumps(MT, ensure_ascii=False), json.dumps(titles, ensure_ascii=False))

    robots = "index, follow, max-image-preview:large" if CANLI else "noindex, nofollow"
    seo = ""
    if CANLI:
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "TravelAgency", "@id": "https://kurumsal.goldenbaytour.com/#org", "name": "Golden Bay Tour", "url": "https://kurumsal.goldenbaytour.com/",
             "telephone": "+90 850 202 3901", "email": "event@goldenbaytour.com.tr", "slogan": "Kurumsal Seyahatin Gücü"},
            {"@type": "WebPage", "@id": SAYFA_URL, "url": SAYFA_URL, "name": MT["en"], "description": desc, "inLanguage": ["tr-TR", "en"],
             "isPartOf": {"@id": "https://kurumsal.goldenbaytour.com/#org"}}]}
        seo = (f'<link rel="canonical" href="{SAYFA_URL}">\n<meta property="og:type" content="website">\n<meta property="og:site_name" content="Golden Bay Tour">\n'
               '<meta property="og:locale" content="tr_TR">\n<meta property="og:locale:alternate" content="en_GB">\n<meta name="twitter:card" content="summary_large_image">\n'
               '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&display=swap">')
    doc = f"""<!DOCTYPE html>
<html lang="tr" data-lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{LANG_HEAD}
<title>{e(MT["tr"])}</title>
<meta name="robots" content="{robots}">
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="MICE Xperience Türkiye | Golden Bay Tour">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="img/tr-istanbul-yilbasi.webp">
<meta property="og:url" content="{SAYFA_URL}">
<meta name="theme-color" content="#FCFAF6">
{seo}{fonts}
<style>
{css}
</style>
</head>
<body>
{mb}
{"".join(dviews)}
{router}
</body>
</html>
"""
    # panel dosyası (görseller CDN'den)
    (ROOT / "tek").mkdir(exist_ok=True)
    panel = re.sub(r'(["\s,])img/', lambda m: m.group(1) + CDN, doc)
    panel = panel.replace("'<img src=\"img/'+p.gorsel", "'<img src=\"" + CDN + "'+p.gorsel")
    (ROOT / "tek/mice-xperience-turkiye.html").write_text(panel, encoding="utf-8")
    # önizleme (görseller gömülü)
    def emb(m):
        p = DIST / m.group(0); t = "image/webp" if p.suffix == ".webp" else "image/png"
        return f"data:{t};base64," + base64.b64encode(p.read_bytes()).decode()
    prev = re.sub(r'\s(srcset|sizes)="[^"]*"', "", doc)
    prev = re.sub(r'(?<=["\'(])img/[A-Za-z0-9_\-/]+\.(webp|png)(?=["\')])', emb, prev)
    prev = prev.replace('if(next&&grid&&grid.getAttribute("data-month-feat")!==next){', 'if(false){')
    (ROOT / "ONIZLEME-MICE-Xperience-Turkiye.html").write_text(prev, encoding="utf-8")
    (DIST / "index.html").write_text(doc, encoding="utf-8")
    print(f"program: {len(progs)} | detay: {len(details)} | panel: {round(len(panel.encode())/1024)} KB | önizleme: {round(len(prev.encode())/1e6,1)} MB | yer tutucu: {len(yer_tutucu)} | geçici düşük çözünürlük: {len(set(dusuk))} | sürüm: {SURUM}")
    if yer_tutucu: print("eksik:", " ".join(sorted(set(yer_tutucu))))

if __name__ == "__main__":
    main()

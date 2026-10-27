"""Tek HTML (panel landing sayfası) üretici.
Önce:  python3 build.py   (dist/ oluşur)
Sonra: python3 build_tek.py [sürüm]   ->  tek/mice-xperience-global.html
Görseller: https://cdn.jsdelivr.net/gh/atesakkus-gbt/gbt-mice-xperience@<sürüm>/img/
Ana sayfa + tüm detay sayfaları tek dosyada; detaylar #<slug> ile açılır.
"""
import re, sys, json, html
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
OUT = ROOT / "tek"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
CANLI = "--canli" in sys.argv   # canlı yayın: Google'a açık + SEO etiketleri
SURUM = ARGS[0] if ARGS else "v1"
IMG = f"https://cdn.jsdelivr.net/gh/atesakkus-gbt/gbt-mice-xperience@{SURUM}/img/"
SAYFA_URL = "https://kurumsal.goldenbaytour.com/experience/mice-xperience-global"

SEO_TITLE = "Yurtdışı MICE ve Incentive Programları | MICE Xperience Global"
OG_TITLE = "MICE Xperience Global | Golden Bay Tour"
SEO_DESC = ("Bayi motivasyonu, ödüllendirme ve kick-off için her ay yenilenen yurtdışı MICE programları. "
            "Gemi turları, gala ve ekip etkinlikleriyle Golden Bay Tour güvencesi.")
AYLAR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]

def seo_block(desc):
    P = json.loads((ROOT / "src/programlar.json").read_text(encoding="utf-8"))
    D = {d["sayfa"]: d for d in json.loads((ROOT / "src/detaylar.json").read_text(encoding="utf-8"))["sayfalar"]}
    items = []
    for i, x in enumerate(sorted((x for x in P["programlar"] if x.get("hazir") and x["sayfa"] in D), key=lambda x: x["ay"]), 1):
        y, m = x["ay"].split("-")
        items.append({"@type": "ListItem", "position": i, "item": {
            "@type": "TouristTrip",
            "name": f'{x["baslik"]} – {AYLAR[int(m)-1]} {y}',
            "description": x.get("ozet") or x.get("slogan", ""),
            "url": SAYFA_URL + "#" + x["sayfa"][:-5],
            "image": IMG + x["gorsel"] + ".webp",
            "touristType": "Kurumsal gruplar, bayi ve çalışan ödül seyahatleri",
            "provider": {"@id": "https://kurumsal.goldenbaytour.com/#org"}}})
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "TravelAgency", "@id": "https://kurumsal.goldenbaytour.com/#org", "name": "Golden Bay Tour",
         "url": "https://kurumsal.goldenbaytour.com/", "telephone": "+90 850 202 3901", "slogan": "Kurumsal Seyahatin Gücü"},
        {"@type": "WebPage", "@id": SAYFA_URL, "url": SAYFA_URL, "name": SEO_TITLE, "description": desc,
         "inLanguage": "tr-TR", "isPartOf": {"@id": "https://kurumsal.goldenbaytour.com/#org"},
         "primaryImageOfPage": IMG + "og-mice-xperience-global.jpg",
         "mainEntity": {"@type": "ItemList", "name": "MICE Xperience Global program takvimi", "numberOfItems": len(items), "itemListElement": items}}]}
    return (f'<link rel="canonical" href="{SAYFA_URL}">\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:site_name" content="Golden Bay Tour">\n'
            '<meta property="og:locale" content="tr_TR">\n'
            '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            '<meta property="og:image:alt" content="MICE Xperience Global – Golden Bay Tour yurtdışı incentive programları">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="twitter:title" content="{OG_TITLE}">\n<meta name="twitter:description" content="{html.escape(desc)}">\n'
            f'<meta name="twitter:image" content="{IMG}og-mice-xperience-global.jpg">\n'
            '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + '</script>\n')

def split_rules(css):
    """Üst düzey kuralları (seçici, gövde) olarak böl; @media iç içe."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0: break
        sel = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{": depth += 1
            elif css[k] == "}": depth -= 1
            k += 1
        out.append((sel, css[j + 1:k - 1]))
        i = k
    return out

def scope_sel(s, sc):
    s = s.strip()
    if not s: return s
    if s.startswith(":root"): return s
    m = re.match(r"^(html|body)\b(.*)$", s)
    if m: return (sc + m.group(2)).strip()
    return f"{sc} {s}"

def scope(css, sc):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    res = []
    for sel, body in split_rules(css):
        if sel.startswith("@media") or sel.startswith("@supports"):
            res.append(f"{sel}{{{scope(body, sc)}}}")
        elif sel.startswith("@"):
            res.append(f"{sel}{{{body}}}")
        else:
            if re.fullmatch(r"\s*html\s*", sel):  # html kuralı: genel kalır
                res.append(f"html{{{body}}}")
                continue
            res.append(",".join(scope_sel(x, sc) for x in sel.split(",")) + "{" + body + "}")
    return "\n".join(res)

def parts(path):
    s = path.read_text(encoding="utf-8")
    head, body = s.split("<body>", 1)
    body = body.rsplit("</body>", 1)[0]
    css = "\n".join(re.findall(r"<style>(.*?)</style>", head, re.S))
    title = re.search(r"<title>(.*?)</title>", head, re.S).group(1)
    return css, body, title

def fix_img(s):
    return re.sub(r'(["\s,])img/', lambda m: m.group(1) + IMG, s)

def main():
    master_css, master_body, master_title = parts(DIST / "index.html")
    det_files = sorted(p for p in DIST.glob("*.html") if p.name != "index.html")
    slugs = [p.stem for p in det_files]
    slugset = set(slugs)

    def link_fix(s):
        # detay sayfası bağlantıları -> #slug
        s = re.sub(r'href="([a-z0-9-]+)\.html"', lambda m: f'href="#{m.group(1)}"' if m.group(1) in slugset else m.group(0), s)
        s = s.replace('href="index.html#', 'href="#').replace('href="index.html"', 'href="#top"')
        return s

    mb = link_fix(fix_img(master_body))
    # JS içindeki bağlantı ve görsel yolu
    mb = mb.replace("var href=p.hazir?p.sayfa:\"#teklif\"", "var href=p.hazir?\"#\"+p.sayfa.replace(/\\.html$/,\"\"):\"#teklif\"")
    mb = mb.replace("'<img src=\"img/'+p.gorsel", "'<img src=\"" + IMG + "'+p.gorsel")
    assert IMG + "'+p.gorsel" in mb, "öne çıkanlar görsel yolu bulunamadı"
    assert '"#"+p.sayfa' in mb, "öne çıkanlar bağlantısı bulunamadı"
    mb = f'<div id="mv">{mb}</div>'

    det_css = None
    dviews, titles = [], {}
    for p, slug in zip(det_files, slugs):
        css, body, title = parts(p)
        det_css = det_css or css
        titles[slug] = html.unescape(title)
        b = link_fix(fix_img(body))
        # sayfa içi kimlikleri benzersizleştir
        ids = set(re.findall(r'\bid="([^"]+)"', b))
        for i in ids:
            b = b.replace(f'id="{i}"', f'id="{slug}--{i}"').replace(f'href="#{i}"', f'href="#{slug}--{i}"')
            b = b.replace(f'aria-labelledby="{i}"', f'aria-labelledby="{slug}--{i}"')
        # form iframe'i görünür olunca yüklensin
        b = re.sub(r'<iframe([^>]*?)\ssrc="', r'<iframe\1 data-src="', b)
        dviews.append(f'<div class="dv" id="dv-{slug}" data-slug="{slug}" hidden>{b}</div>')

    css = scope(master_css, "#mv") + "\n" + scope(det_css, ".dv")
    css += "\n[hidden]{display:none!important}\nbody{margin:0;background:#FCFAF6}"

    fonts = re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', (DIST / "index.html").read_text(encoding="utf-8").split("<body>")[0])
    desc = "Golden Bay Tour MICE Xperience Global: bayi motivasyonu, ödüllendirme, kick-off ve kurumsal incentive seyahatleri için her ay yenilenen yurtdışı program takvimi."
    seo = ""
    robots = "noindex, nofollow"
    if CANLI:
        robots = "index, follow, max-image-preview:large"
        master_title = SEO_TITLE
        desc = SEO_DESC
        seo = seo_block(desc)

    router = """<script>
(function(){
  var MT=%s, TITLES=%s, mv=document.getElementById("mv");
  var views=[].slice.call(document.querySelectorAll(".dv"));
  function find(h){for(var i=0;i<views.length;i++){var s=views[i].getAttribute("data-slug");if(h===s||h.indexOf(s+"--")===0)return views[i];}return null;}
  var cur=null;
  function route(){
    var h=decodeURIComponent((location.hash||"").slice(1)), v=find(h);
    if(v){
      mv.hidden=true; views.forEach(function(x){x.hidden=(x!==v);});
      v.querySelectorAll("iframe[data-src]").forEach(function(f){f.src=f.getAttribute("data-src");f.removeAttribute("data-src");});
      document.title=TITLES[v.getAttribute("data-slug")]||MT;
      var t=h!==v.getAttribute("data-slug")?document.getElementById(h):null;
      if(t){t.scrollIntoView();}else if(cur!==v){window.scrollTo(0,0);}
      cur=v;
    }else{
      var was=cur; views.forEach(function(x){x.hidden=true;}); mv.hidden=false; document.title=MT; cur=null;
      var t=(h&&h!=="top")?document.getElementById(h):null;
      if(h==="top"){window.scrollTo(0,0);}else if(t){setTimeout(function(){t.scrollIntoView();},0);}else if(was){window.scrollTo(0,0);}
    }
  }
  window.addEventListener("hashchange",route); route();
})();
</script>""" % (json.dumps(html.unescape(master_title), ensure_ascii=False), json.dumps(titles, ensure_ascii=False))

    doc = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{master_title}</title>
<meta name="robots" content="{robots}">
<meta name="description" content="{desc}">
<meta property="og:title" content="{OG_TITLE}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{IMG}{'og-mice-xperience-global.jpg' if CANLI else 'kuala-lumpur.webp'}">
<meta property="og:url" content="{SAYFA_URL}">
<meta name="theme-color" content="#FCFAF6">
{seo}{chr(10).join(fonts)}
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
    OUT.mkdir(exist_ok=True)
    out = OUT / "mice-xperience-global.html"
    out.write_text(doc, encoding="utf-8")
    left = re.findall(r'(?:src|href|srcset)="img/', doc)
    print("detay:", len(slugs), "| boyut:", round(len(doc.encode()) / 1024), "KB | yerel img kalan:", len(left), "| sürüm:", SURUM)

if __name__ == "__main__":
    main()

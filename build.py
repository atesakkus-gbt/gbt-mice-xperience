"""MICE Xperience master sayfa derleyici.
Kullanım: python3 build.py  ->  dist/ (yayın klasörü) + dist-artifact.html (önizleme)
Görseller: src/full/<anahtar>.(png|jpg|webp) varsa onu kullanır; yoksa src/canva_thumbs/<anahtar>.jpg (düşük çözünürlüklü geçici önizleme).
"""
import json, re, base64, html, os, shutil
from urllib.parse import quote
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"
IMG = DIST / "img"
AYLAR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
AILE = {"yakin":"Yakın & Dinamik","prestij":"Prestij & Keşif","premium":"Premium & VIP","cruise":"Cruise Xperience"}
e = html.escape

def fit(im, w, ratio):
    """Merkezden ratio (en/boy) oranında kırp, w genişliğe ölçekle."""
    im = im.convert("RGB")
    W, H = im.size
    if W / H > ratio:
        nw = int(H * ratio); x = (W - nw) // 2; im = im.crop((x, 0, x + nw, H))
    else:
        nh = int(W / ratio); y = (H - nh) // 2; im = im.crop((0, y, W, y + nh))
    up = im.width < w
    im = im.resize((w, round(w / ratio)), Image.LANCZOS)
    if up:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    return im

lowres = []
def make_image(key, ratio=1.6):
    src = None
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = SRC / "full" / f"{key}.{ext}"
        if p.exists(): src = p; break
    if src is None:
        src = SRC / "canva_thumbs" / f"{key}.jpg"; lowres.append(key)
    im = Image.open(src)
    fit(im, 1200, ratio).save(IMG / f"{key}.webp", "WEBP", quality=76, method=6)
    fit(im, 640, ratio).save(IMG / f"{key}-sm.webp", "WEBP", quality=74, method=6)

def label(ym):
    y, m = ym.split("-"); return AYLAR[int(m) - 1], y

def picture(key, alt, sizes, eager=False):
    lz = '' if eager else ' loading="lazy"'
    return (f'<img src="img/{key}-sm.webp" srcset="img/{key}-sm.webp 640w, img/{key}.webp 1200w" '
            f'sizes="{sizes}" width="640" height="400"{lz} alt="{e(alt)}">')

def btn(p):
    if p.get("hazir"):
        return f'<a class="more" href="{e(p["sayfa"])}">Programı İncele →</a>'
    return '<a class="more ask" href="#teklif">Teklif İste →</a>'

def build():
    data = json.loads((SRC / "programlar.json").read_text(encoding="utf-8"))
    progs, ozel = sorted(data["programlar"], key=lambda p: p["ay"]), data["ozel"]  # aylar her zaman kronolojik
    if DIST.exists(): shutil.rmtree(DIST)
    IMG.mkdir(parents=True)

    keys = sorted({p["gorsel"] for p in progs + ozel})
    for k in keys: make_image(k)
    make_image("toplanti", ratio=640/704)
    # logo
    lg = Image.open(SRC / "logo-koyu-crop.png"); lg.save(IMG / "logo-gbt-mice.png", optimize=True)

    months = []
    for p in progs:
        if p["ay"] not in months: months.append(p["ay"])

    strip = "".join(f'<a href="#ay-{m}" data-month="{m}">{label(m)[0]}<small>{label(m)[1]}</small></a>' for m in months)

    cal = []
    for i, m in enumerate(months):
        ad, yil = label(m)
        cards = []
        for p in [x for x in progs if x["ay"] == m]:
            cards.append(
                f'<article class="route" data-family="{p["aile"]}">'
                f'<figure class="img">{picture(p["gorsel"], p["alt"], "(max-width:760px) 92vw, (max-width:980px) 46vw, 440px")}</figure>'
                f'<div class="route-body"><div class="fam">{e(AILE[p["aile"]])}</div><h3>{e(p["baslik"])}</h3><p>{e(p["slogan"])}</p>'
                f'<div class="route-foot"><span class="tag">{e(p["etiket"])}</span>{btn(p)}</div></div></article>')
        cal.append(f'<section class="month" id="ay-{m}" data-month="{m}" aria-label="{ad} {yil}">'
                   f'<div class="month-label"><span class="m">{ad}</span><span class="y">{yil}</span></div>'
                   f'<div class="routes">{"".join(cards)}</div></section>')
        if i % 3 == 2 and i < len(months) - 1:
            cal.append(f'<div class="mid-cta" data-month="{m}"><strong>Bu dönem için bayi programınızı planlıyor musunuz?</strong>'
                       f'<a class="btn btn-gold" href="#teklif">Kuruma Özel Teklif İste</a></div>')

    sp = []
    for p in ozel:
        ad, yil = label(p["ay"])
        link = (f'<a class="more" href="{e(p["sayfa"])}">Programı İncele →</a>' if p.get("hazir")
                else '<a class="more" href="#teklif">Teklif İste →</a>')
        sp.append(f'<article class="sp" data-month="{p["ay"]}"><figure class="img">{picture(p["gorsel"], p["alt"], "(max-width:560px) 92vw, 260px")}</figure>'
                  f'<div class="sp-body"><div class="sp-date">{ad} {yil}</div><h3>{e(p["baslik"])}</h3><p><b>{e(p["slogan"])}</b><br>{e(p["not"])}</p>{link}</div></article>')

    # Statik öne çıkanlar: Kasım 2026 (JS tarihe göre günceller)
    feat_m = "2026-11"
    feat = []
    for p in [x for x in progs if x["ay"] == feat_m]:
        acts = (f'<a class="btn btn-navy" href="{e(p["sayfa"])}">Programı İncele</a><a class="btn btn-line" href="#teklif">Teklif İste</a>'
                if p.get("hazir") else '<a class="btn btn-navy" href="#teklif">Bu Rota İçin Teklif İste</a>')
        feat.append(f'<article class="feat"><div class="img"><img src="img/{p["gorsel"]}.webp" width="1200" height="750" loading="lazy" alt="{e(p["alt"])}"></div>'
                    f'<div class="feat-body"><div class="fam">{e(AILE[p["aile"]])}</div><h3>{e(p["baslik"])}</h3><p>{e(p.get("ozet") or p["slogan"])}</p><div class="feat-actions">{acts}</div></div></article>')

    tpl = (SRC / "template.html").read_text(encoding="utf-8")
    body = (tpl.replace("{{STRIP}}", strip).replace("{{CALENDAR}}", "".join(cal)).replace("{{SPECIAL}}", "".join(sp))
               .replace("{{FEATURED}}", "".join(feat)).replace("{{FEAT_KICKER}}", "Kasım 2026 · gelecek ayın rotaları")
               .replace("{{STAT_MONTHS}}", str(len(months))).replace("{{STAT_PROGRAMS}}", str(len(progs) + len(ozel)))
               .replace("{{DATA}}", json.dumps({"programlar": progs, "ozel": ozel}, ensure_ascii=False).replace("</", "<\\/")))
    body = body.replace('id="feat-grid">', f'id="feat-grid" data-month-feat="{feat_m}">')

    desc = "Golden Bay Tour MICE Xperience Global: bayi motivasyonu, ödüllendirme, kick-off ve kurumsal incentive seyahatleri için her ay yenilenen yurtdışı program takvimi."
    prod_head = f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MICE Xperience Global | Yurtdışı MICE Programları | Golden Bay Tour</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="MICE Xperience Global | Golden Bay Tour">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="img/kuala-lumpur.webp">
<meta name="theme-color" content="#FCFAF6">'''
    prod = body.replace("{{HEAD}}", prod_head).replace("{{BODY_OPEN}}", "</head>\n<body>").replace("{{BODY_CLOSE}}", "</body>\n</html>")
    (DIST / "index.html").write_text(prod, encoding="utf-8")

    art_head = '<title>MICE Xperience Global</title>\n<meta name="claude:viewport-fit-sides" content="cover">'
    art = body.replace("{{HEAD}}", art_head).replace("{{BODY_OPEN}}", "").replace("{{BODY_CLOSE}}", "")
    (ROOT / "dist-artifact.html").write_text(art, encoding="utf-8")

    build_details(progs)
    print("ay:", len(months), "program:", len(progs), "+", len(ozel), "| geçici düşük çözünürlük:", len(lowres))

def ekler(g):
    """Bir güne ait ek görseller (küçük galeri)."""
    if not g.get("ek"): return ""
    out = []
    for x in g["ek"]:
        make_image(x["gorsel"], ratio=4/3)
        out.append(f'<figure><img src="img/{x["gorsel"]}-sm.webp" srcset="img/{x["gorsel"]}-sm.webp 640w, img/{x["gorsel"]}.webp 1200w" sizes="(max-width:760px) 30vw, 170px" width="640" height="480" loading="lazy" alt="{e(x["alt"])}"></figure>')
    return '<div class="day-extra">' + "".join(out) + '</div>'

def build_details(progs):
    """src/detaylar.json'daki her kayıt için açık tasarımlı detay sayfası üretir."""
    det = json.loads((SRC / "detaylar.json").read_text(encoding="utf-8"))["sayfalar"]
    tpl = (SRC / "template_detay.html").read_text(encoding="utf-8")
    lw, lh = Image.open(IMG / "logo-gbt-mice.png").size
    by_page = {p["sayfa"]: p for p in progs}
    for d in [x for x in det if not x.get("taslak")]:
        p = by_page[d["sayfa"]]
        ad, yil = label(p["ay"])
        make_image(d["kapak"]) if not (IMG / f'{d["kapak"]}.webp').exists() else None
        gun = []
        for i, g in enumerate(d["gunler"], 1):
            make_image(g["gorsel"], ratio=1.5)
            gun.append(f'<article class="day"><div class="day-no"><b>{i:02d}</b><span>{i}. {d.get("birim","gün").lower()}</span></div>'
                       f'<figure class="day-img"><img src="img/{g["gorsel"]}-sm.webp" srcset="img/{g["gorsel"]}-sm.webp 640w, img/{g["gorsel"]}.webp 1200w" '
                       f'sizes="(max-width:760px) 92vw, 520px" width="640" height="427" loading="lazy" alt="{e(g["alt"])}"></figure>'
                       f'<div class="day-body"><h3>{e(g["baslik"])}</h3><p>{e(g["metin"])}</p><span class="tag">{e(g["etiket"])}</span>{ekler(g)}</div></article>')
        # diğer rotalar: sonraki aylardan, farklı başlıklı 3 program (önce hazır olanlar)
        others = [x for x in progs if x["sayfa"] != p["sayfa"] and x["ay"] >= p["ay"]]
        others = sorted(others, key=lambda x: (not x.get("hazir"), x["ay"]))[:3]
        rel = []
        for o in others:
            oad, oyil = label(o["ay"])
            href = o["sayfa"] if o.get("hazir") else f'index.html#ay-{o["ay"]}'
            rel.append(f'<a class="rel" href="{e(href)}"><figure class="img"><img src="img/{o["gorsel"]}-sm.webp" width="640" height="400" loading="lazy" alt="{e(o["alt"])}"></figure>'
                       f'<div class="rel-body"><span class="m">{oad} {oyil}</span><h3>{e(o["baslik"])}</h3><p>{e(o["slogan"])}</p></div></a>')
        h1 = e(p["baslik"]).replace(" &amp; ", ' <span class="amp">&amp;</span><br>')
        body = (tpl.replace("{{KAPAK}}", d["kapak"]).replace("{{KAPAK_ALT}}", e(d["kapak_alt"]))
                   .replace("{{AY}}", p["ay"]).replace("{{AY_AD}}", f"{ad} {yil}")
                   .replace("{{BASLIK_DUZ}}", e(p["baslik"])).replace("{{MAIL_KONU}}", quote(f"MICE Xperience Global – {p['baslik']} ({ad} {yil})")).replace("{{BASLIK_H1}}", h1)
                   .replace("{{ALT_BASLIK}}", e(d["alt_baslik"])).replace("{{GIRIS}}", e(d["giris"]))
                   .replace("{{SURE}}", e(d["sure"])).replace("{{AILE}}", e(AILE[p["aile"]]))
                   .replace("{{AKIS_NOTU}}", e(d["akis_notu"])).replace("{{NOT_EK}}", (" " + e(d["esnek_not"])) if d.get("esnek_not") else "").replace("{{GUNLER}}", "".join(gun))
                   .replace("{{DIGER}}", "".join(rel)).replace("{{LOGO_W}}", str(lw)).replace("{{LOGO_H}}", str(lh)))
        title = f'{p["baslik"]} | MICE Xperience Global | Golden Bay Tour'
        head = f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(d["giris"])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:image" content="img/{d["kapak"]}.webp">
<meta name="theme-color" content="#FCFAF6">'''
        out = body.replace("{{HEAD}}", head).replace("{{BODY_OPEN}}", "</head>\n<body>").replace("{{BODY_CLOSE}}", "</body>\n</html>")
        (DIST / d["sayfa"]).write_text(out, encoding="utf-8")
    print("detay sayfası:", len(det))

def build_kl_detail_eski():
    """Kuala Lumpur detay sayfası: gömülü PNG'leri WebP dosyalarına çıkar."""
    src = Path("/mnt/user-data/uploads/kasim-2026-kuala-lumpur-langkawi.html")
    kayit = SRC / "detay"
    if not src.exists():
        # Daha önce optimize edilmiş detay sayfaları src/detay içinde saklanır
        if kayit.exists():
            shutil.copytree(kayit, DIST, dirs_exist_ok=True)
        return
    s = src.read_text(encoding="utf-8")
    out = IMG / "kl-detay"; out.mkdir(exist_ok=True)
    n = [0]
    def rep(m):
        i = n[0]; n[0] += 1
        raw = base64.b64decode(m.group(1))
        tmp = out / f"_{i}.png"; tmp.write_bytes(raw)
        im = Image.open(tmp)
        if im.width <= 600:  # logo
            name = f"logo-{i}.png"; im.save(out / name, optimize=True)
        else:
            name = f"g{i:02d}.webp"
            im.convert("RGB").thumbnail((1600, 1600))
            rgb = im.convert("RGB"); rgb.thumbnail((1600, 1600), Image.LANCZOS)
            rgb.save(out / name, "WEBP", quality=74, method=6)
        tmp.unlink()
        return f"img/kl-detay/{name}"
    s = re.sub(r"data:image/png;base64,([A-Za-z0-9+/=]+)", rep, s)
    # alt görsellere tembel yükleme
    s = s.replace('<iframe allow="clipboard-write" class="bigin-iframe" height="690px" loading="eager"', '<iframe allow="clipboard-write" class="bigin-iframe" height="690px" loading="lazy"')
    s = s.replace('<meta charset="utf-8"/>', '<meta charset="utf-8"/><link rel="preload" as="image" href="img/kl-detay/g00.webp" type="image/webp"/>', 1)
    (DIST / src.name).write_text(s, encoding="utf-8")
    (kayit / "img").mkdir(parents=True, exist_ok=True)
    shutil.copy(DIST / src.name, kayit / src.name)
    shutil.copytree(out, kayit / "img" / "kl-detay", dirs_exist_ok=True)

if __name__ == "__main__":
    build()

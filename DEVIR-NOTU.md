# MICE Xperience – Devir Notu (yeni sohbet için)

Bu notu okuyan Claude: Bu dosya, "MICE Xperience Global" sayfasını oluşturan sohbetin özetidir. Kaynak dosyaların tamamı GitHub'da
`atesakkus-gbt/gbt-mice-xperience` deposunun **`kaynak`** dalındadır. İşe başlarken depoyu bu dalla klonla:
`git clone -b kaynak https://github.com/atesakkus-gbt/gbt-mice-xperience.git mice`
(Depo oturuma ekli değilse önce add_repo ile `push` erişimiyle ekle.)

Son güncelleme: 27.10.2026

---

## 1. Ne yapıldı

- **MICE Xperience Global** = yurtdışı MICE/incentive programları sayfası (Türk kurumların bayi/çalışan ödül gezileri).
- Kasım 2026 – Kasım 2027 arası **13 ay, her ay 2 program = 26 program**, her birinin gün gün detay sayfası var.
- Takvim kendini her ay kaydırır (geçen ay kalkar; tarih İstanbul saatine göre okunur; `#tarih-test-2027-03` ile test edilir).
- Canlı adres: **https://kurumsal.goldenbaytour.com/experience/mice-xperience-global**
- Sıradaki iş: **MICE Xperience Türkiye** = yurtdışından Türkiye'ye gelen misafirler (inbound) için aynı tasarım dilinde sayfa, **Türkçe + İngilizce**.

## 2. Yayın yöntemi (önemli)

- Sirius (site ajansı) 15.000 TL + KDV istedi; bu yüzden **Ateş Bey'in kendi admin panelindeki "Landing Sayfası Oluştur"** kullanılıyor.
  - Alanlar: Sayfa adı, **Slug** (adres `/experience/<slug>` olur), **HTML İçeriği** (tam HTML olduğu gibi servis edilir), **Yayında** kutusu (işaretsizse 404).
  - Menüde link yok; sayfa sadece linkle erişilir (Google'a açık).
- Panel tek HTML kabul ettiği için **tek dosya SPA** üretiliyor: ana sayfa + 26 detay aynı HTML'de, detaylar `#<slug>` ile açılır (hash router).
- **Görseller HTML'de değil**: GitHub deposunun `main` dalındaki `img/` klasöründe, jsDelivr ile commit SHA'ya sabitlenmiş adresten gelir:
  `https://cdn.jsdelivr.net/gh/atesakkus-gbt/gbt-mice-xperience@<SHA>/img/<ad>.webp`
  - Şu an canlıdaki SHA: **5104e9f703c045a2cd771c2dc651ad1eea55ff0a**
  - jsDelivr GitHub sınırı ~50 MB/sürüm: `main` dalına yalnızca webp'ler konur (şu an ~30 MB). Büyük kaynaklar `kaynak` dalında.
  - Yeni görsel yüklenince ilk açılışta birkaç dakika gecikme olabilir.
  - Claude uygulamasındaki dosya önizlemesi dış görselleri engeller; "resim görünmüyor" derse önizleme olabilir, panelde/tarayıcıda açılınca görünür.
- Bu ortamdan jsDelivr / raw.githubusercontent'e erişilemiyor (proxy). Test: Playwright ile dış istekleri kapatıp router/sıra kontrolü.

## 3. Dosyalar (`kaynak` dalı)

| Dosya | Görev |
|---|---|
| `build.py` | `src/` → `dist/` (index.html + 26 detay + `img/` webp 1200w ve `-sm` 640w). Aylar **tarihe göre sıralanır** (bir kez sıra hatası yaşandı, düzeltildi). ~100 sn sürer, arka planda çalıştır. |
| `build_tek.py` | `dist/` → `tek/mice-xperience-global.html` (panel dosyası). `python3 build_tek.py <SHA> --canli` (canlı: index,follow + canonical + OG + JSON-LD). `--canli` olmadan `noindex` test sürümü. CSS `#mv` / `.dv` ile kapsamlanır, detay id'leri `<slug>--id` olur, iframe'ler görününce yüklenir. |
| `make_preview.py` | Görselleri base64 gömülü tek dosya önizlemeler (ekip kontrolü için). |
| `src/programlar.json` | Takvim: `ay, baslik, slogan, aile (yakin/prestij/premium/cruise), etiket, gorsel, alt, sayfa, hazir, ozet`. `ozel` = özel tarih programları (ABD). |
| `src/detaylar.json` | Detay sayfaları: `sayfa, sure, kapak, kapak_alt, giris, alt_baslik, akis_notu (sonunda "Vize: …"), esnek_not (gemilerde), gunler[{baslik, metin, etiket, gorsel, alt, ek?}]`. `ek` = tekne/yat günlerinde 3'lü galeri. |
| `src/template.html`, `src/template_detay.html` | Tasarım. Telefon/e-posta/web tıklanabilir (`tel:+908502023901`, `mailto:` konu satırı program adıyla dolu). |
| `src/full/<anahtar>.webp` | Tam çözünürlüklü görseller (Canva'dan). Yoksa `src/canva_thumbs/<anahtar>.jpg` (düşük çözünürlüklü geçici) kullanılır. |
| `ekip-notlari.md` | Ekip geri bildirim kaydı (vize, gemi, MICE). |
| `OKUBENI.txt` | Kısa yayın/çalışma notu. |

OG paylaşım görseli: `img/og-mice-xperience-global.jpg` (1200×630, gala görseli + lacivert geçiş + logo).

## 4. Aylık / değişiklik akışı

1. `src/*.json` güncelle (yeni ay: 2 program + detay sayfası).
2. Yeni görselleri Canva'da üret → Ateş Bey klasörü zip olarak indirir → zip'teki görselleri küçük önizlemelerle (48×27, MSE < 200) eşleştirip `src/full/<anahtar>.webp` (q90) kaydet.
3. `python3 build.py` → yeni webp'leri depo `main/img/`'e kopyala → commit + push → yeni SHA.
4. `python3 build_tek.py <yeni SHA> --canli` → Playwright ile kontrol (ay sırası, `#slug` rotaları, hata yok).
5. HTML'i gönder; Ateş Bey paneldeki HTML İçeriği alanına yapıştırır.

## 5. Kurallar (Ateş Bey'in tercihleri)

- Telefon: **+90 850 202 3901**; MICE e-posta: **event@goldenbaytour.com.tr**; site: kurumsal.goldenbaytour.com. Motto: "Kurumsal Seyahatin Gücü"; sayfa üst bandı "Siz hayal edin, biz yapalım."
- Marka: Newsreader (başlık) + Figtree (gövde); lacivert #14213D, altın #AE8739, krem #FCFAF6, marka #C29A69.
- **Gemi turları gerçek seferler** olmalı; ifade her zaman **"örnek sefer / bu tur veya benzeri"**: gemi, güzergâh ve tarih müsaitlik, katılımcı sayısı ve talep zamanına göre değişebilir.
- **Görseller**: Türk görünümlü, farklı yaş ve görünüşte insanlar (birbirine benzeyen "ikiz" yüzler yok); tekne/yat günlerine dalış/mercan/yat galerisi. Her görsel partisi Canva'da **ayrı numaralı klasöre** konur (üst klasör "Aylara Göre Programlar", id `FAHYYTnj7J8`; son kullanılan numara **33**). Gün görselleri 3:2, kapak/kart 16:9.
- Ekiple paylaşırken sadece **önizleme zip**'i gönderilir (diğer paketler istenirse).
- Ekip notları "not al" diye gelir; `ekip-notlari.md`'ye işlenir, sonra uygulanır.
- Rehber/açıklama metinleri **sade ve kısa** olsun.
- Teklif formu: Bigin (Zoho) `https://eu.bigin.online/org20113131990/forms/mice-xperience` (iframe; panelde çalışıyor).

## 6. Ekip kararları (kesinleşti)

- **Vize** (vize müdürü teyitli, her detayda "Vize: …" cümlesi): Schengen gerekli; Tanzanya, Vietnam, BAE, Bahreyn e-vize; Mısır kapıda vize (İskenderiye/Nil 25 USD; Şarm'da 15 günlük turist vizesi); Kamboçya e-vize veya sınır kapısında; Karadağ şu an vizesiz (01.11.2026'dan itibaren kurallar güncellenecek); Japonya vizesiz + giriş formu; Malezya girişte ücretsiz vize + 3 gün önce form; Tayland vizesiz + 3 gün önce Dijital Varış Kartı; Singapur, Brezilya, Sırbistan, Bosna, Katar, Fas, Maldivler, Gürcistan, Tunus, K. Makedonya, Arnavutluk, Özbekistan, Umman, Azerbaycan vizesiz; ABD vize gerekli.
- **Gemi** (gemi ekibi): Şubat AROYA 27.02–06.03.2027; Haziran **VIVA ENJOY 2–9 Haziran 2027** Budapeşte çıkışlı; Temmuz MSC Lirica; Eylül Navigator of the Seas **12–16 Eylül 2027**; Ekim Sonesta St. George I 18–22 Ekim; Kasım **Victoria Mekong Ho Chi Minh – Siem Reap** (3–10 veya 17–24 Kasım 2027; Hanoi programının yerine).
- **MICE**: Tokyo & Kyoto **Kasım 2027**'ye (sonbahar renkleri, erken rezervasyon notu), Maskat & Umman **Ekim 2027**'ye (Ekim son haftası, geziler sabah/gün batımı). Gemi turlarına dokunulmadı.

## 7. MICE Xperience Türkiye için başlangıç fikirleri (henüz karar yok)

- Hedef: yurtdışındaki kurumların Türkiye'ye gelen grupları (inbound incentive, kongre, kick-off). **TR + EN** iki dil.
- Aynı tasarım ve aynı panel yöntemi; ayrı slug(lar) (ör. `mice-xperience-turkiye` ve `mice-xperience-turkey` ya da tek sayfada dil düğmesi — karar verilecek).
- Görseller aynı depoya, ayrı önek ile (ör. `tr-…`); Canva klasör numarası 34'ten devam.
- Vize bilgisi bu sayfada yabancı misafir bakış açısıyla olacağından ayrıca ele alınmalı.

---

## 8. MICE Xperience Türkiye (inbound, TR + EN) – 27.10.2026'da başladı

- **Karar**: tek sayfa + TR/EN düğmesi (slug önerisi `mice-xperience-turkiye`); `?lang=en` İngilizce açar, seçim tarayıcıda hatırlanır, yoksa tarayıcı diline göre.
- **Takvim**: Aralık 2026 – Aralık 2027, 13 ay × 2 = 26 program. Kategoriler: `sehir` Şehir & Kongre, `kiyi` Kıyı & Resort, `miras` Kültür & Doğa, `mavi` Yat & Mavi Yolculuk.
- **Yılbaşı bölümü** (Aralık önceliği; lacivert bant, geri sayım, Eylül–Aralık arası görünür, diğer aylarda kendiliğinden gizlenir): 4 konsept — Boğaz'da Yılbaşı Galası (yurtdışı gruplar), Özel Yatta Geri Sayım, Kapadokya'da Beyaz Yılbaşı, Kurumsal Yılbaşı Partisi (Türkiye'deki şirketler, Aralık boyunca). Hedef: hem yabancı hem Türk firmalar. Farklılaştırıcılar: 3 iş gününde teklif, mekân opsiyonu hemen, tek ekip.
- **Detayı hazır 6 sayfa**: yilbasi-istanbul-bogaz, yilbasi-kapadokya, yilbasi-bogaz-yat, yilbasi-kurumsal-parti, ocak-2027-istanbul-kickoff, ocak-2027-uludag-bursa. Diğerleri "Teklif İste".
- **Vize** (yabancı misafir): "Türkiye'ye giriş uyruğa göre değişir; birçok ülke vizesiz ya da e-Vize; katılımcı listesine göre kontrol ederiz."
- **Dosyalar**: `tr/programlar.json`, `tr/detaylar.json` (her metin `tr`/`en`), `tr/template.html`, `tr/template_detay.html` (`[[TR||EN]]` ve `{{A:alt:TR||EN}}` işaretleri), `build_tr.py`.
- **Derleme**: `python3 build_tr.py <SHA> [--canli]` → `tek/mice-xperience-turkiye.html` (panel) + `ONIZLEME-MICE-Xperience-Turkiye.html` (gömülü görselli) + `dist-tr/img/` (main/img'e kopyalanacak webp'ler).
- **Görseller**: Canva klasör **34** (`FAHZO59kyXY`), 50 görsel, anahtar→Canva id eşlemesi `tr/canva_ids.json`. Şu an `tr/canva_thumbs/` (200 px, geçici). Tam çözünürlük için Ateş Bey klasör 34'ü zip indirir → `tr/full/<anahtar>.webp`. Son kullanılan Canva klasör numarası: **34**.
- **Yayın için kalan**: zip → tam görseller → `dist-tr/img/tr-*.webp` main/img'e → push → SHA → `build_tr.py <SHA> --canli` → panelde yeni landing sayfası (slug `mice-xperience-turkiye`).

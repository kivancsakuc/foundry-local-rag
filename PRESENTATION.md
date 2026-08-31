# Bitirme Sunumu — Konuşma Metni

**Kıvanç Sakuçoğlu · Rüya Ödül Sakuçoğlu**
Microsoft Summer School 2026 — *Building Your First Local RAG Application with Foundry Local*
Kod: <https://github.com/kivancsakuc/foundry-local-rag>

---

## Nasıl kullanılır

- Ekranda baştan sona **tek pencere**: `http://127.0.0.1:8501`. Slayt yok.
- **KIVANÇ** / **RÜYA** satırları ağızdan çıkacak metin. Olduğu gibi okuyabilirsiniz.
- `▶` satırları ekranda yapılacak hareket, söylenmiyor.
- Yapı, plan dokümanının *Final Presentation Prep* bölümünün istediği dört başlık.
- **Sorular İngilizce.** Anlatım Türkçe. Sebebi en altta.

---

## 1 · Problem Statement — 0:40

▶ *Uygulama açık, henüz soru sorulmamış.*

> **KIVANÇ:** "Merhaba, ben Kıvanç, yanımdaki Rüya. Bu yaz Foundry Local ile bir RAG
> asistanı yaptık — şu an ekranda gördüğünüz şey o.
>
> Şöyle bir problemden yola çıktık. Bir dil modeline kendi ders notlarınızı
> soramıyorsunuz. Çünkü o notları hiç görmedi. Ama size 'bilmiyorum' da demiyor, gayet
> emin bir tonda uyduruyor. Asıl sıkıntı da bu zaten: cevabın yanlış olması değil,
> yanlış olduğunu anlayamamanız.
>
> RAG bunu üçe bölüyor: soruyla ilgili pasajı belgelerden **buluyorsun**, modele
> **veriyorsun**, model de kendi hafızasından değil senin verdiğin metinden **cevap
> üretiyor**.
>
> Bizim buna eklediğimiz bir şart daha vardı: her şey bilgisayarda çalışsın. Bulut yok,
> API anahtarı yok. Modeller bir kere indikten sonra internete hiç çıkmıyor."

---

## 2 · Key Features / Components — 1:00

▶ *Üstteki gri satırı göster: `Offline · embeddings via qwen3-embedding-0.6b · chat via qwen2.5-0.5b · vectors in SQLite`*

> **KIVANÇ:** "Şuradaki tek satır aslında sistemin tamamı. Dört parça var.
>
> Birincisi **embedding modeli**. Metni, anlamını taşıyan sayılara çeviriyor. Benzer
> anlamdaki cümleler benzer sayılar üretiyor. Arama da tam olarak bunun üzerinden
> çalışıyor — kelime eşleştirmiyoruz, anlam eşleştiriyoruz.
>
> İkincisi **sohbet modeli**, `qwen2.5-0.5b`. Yarım milyar parametre, yani epey küçük.
> Bunu bilerek seçtik, sebebini sonda anlatacağım.
>
> Üçüncüsü **SQLite**. Vektörleri orada saklıyoruz ki her açılışta baştan
> hesaplamayalım."

▶ *Kenar çubuğunu göster: Indexed chunks 27, Source documents 14.*

> **KIVANÇ:** "Dördüncüsü de **belgeler**. Solda görüyorsunuz: 14 doküman, 27 parça.
> İçlerinde kurulum anlatımları, kavram açıklamaları, sorun giderme rehberi var. Yani
> asistan kendi kursu hakkındaki soruları cevaplıyor.
>
> Bir de şunu söyleyeyim: biz bunu üç ayrı şekilde yaptık. Biri kelime frekansıyla
> arıyor, biri embedding'li ama hiçbir şey saklamıyor, üçüncüsü de bu. Üçü de repoda,
> aynı belgelerle. Neden üç tane yaptığımızı Rüya anlatacak.
>
> Rüya, sana bırakıyorum."

---

## 3 · Live Demo — 2:20

### 3a. Cevaplayabildiği bir soru — 0:50

▶ *Yaz ve gönder:* `How do I install Foundry Local?`

> **RÜYA:** "Soruları İngilizce soracağım, çünkü belgelerimiz de sistem talimatımız da
> İngilizce.
>
> Cevap gelene kadar arka planda ne olduğunu anlatayım. Sorum önce sayılara çevriliyor,
> sonra 27 parçanın hepsiyle tek tek karşılaştırılıyor, en yakın üç tanesi seçilip
> modele veriliyor."

▶ *Cevap gelince "Retrieved 3 chunks" expander'ını aç.*

> **RÜYA:** "İşte asıl önemli kısım burası. Cevabın altında, o cevabı hangi pasajlardan
> ürettiğini gösteriyoruz — belge adı ve benzerlik puanıyla birlikte. Puanlar 0.45 ile
> 0.78 arasında.
>
> Bunu bilerek koyduk. Çünkü cevap yanlış çıktığında ilk sorulması gereken şey şu:
> doğru pasaj zaten getirilmiş miydi? Getirilmediyse arama bozuk demektir. Getirildiği
> halde cevap saçmaysa model bozuk demektir. İkisinin çözümü bambaşka."

### 3b. Cevaplayamadığı bir soru — 0:50

▶ *Yaz ve gönder:* `How many students fit in the lab and what is the tuition fee?`

> **RÜYA:** "Şimdi de belgelerimizde kesinlikle olmayan bir şey soruyorum: laboratuvar
> kaç kişilik, öğrenim ücreti ne kadar. Böyle bir bilgi hiçbir dokümanımızda yok."

▶ *Cevap gelince expander'ı aç, düşük puanları göster.*

> **RÜYA:** "İki şeye bakın. Puanlar 0.30'un altında kaldı — az önce 0.45 ile 0.78
> arasındaydı. Yani sistem bu sorunun kapsam dışı olduğunu sayı olarak biliyor.
>
> Ve model uydurmuyor. Bilginin elinde olmadığını söylüyor.
>
> Bizim için en kritik test buydu. Çünkü 'bilmiyorum' diyemeyen bir asistan, doğru
> sorulara ne kadar güzel cevap verirse versin işe yaramaz. Hangisine güveneceğinizi
> bilemezsiniz."

### 3c. topK ve offline — 0:40

▶ *topK kaydırıcısını 3'ten 1'e çek, aynı soruyu tekrar sor.*

> **RÜYA:** "Soldaki şu ayar, modele kaç pasaj verdiğimizi belirliyor. Üçten bire
> çekiyorum ve aynı soruyu tekrar soruyorum. Cevabın zayıfladığını göreceksiniz.
> Bağlamı kısınca cevap da kısılıyor."

▶ *Wi-Fi'yi kapat, görev çubuğunda görünsün. Bir soru daha sor.*

> **RÜYA:** "Son olarak Wi-Fi'yi kapatıyorum. Ve soru sormaya devam ediyorum.
>
> Projenin bütün iddiası buydu zaten. Kanıtlaması da on saniye sürüyor."

---

## 4 · Lessons Learned — 1:00

> **RÜYA:** "İki şey öğrendik. Biri ölçümden çıktı, biri süreçten.
>
> Kıvanç üç mimariden bahsetmişti. Sebebi şu: hangisi daha iyi diye tahmin etmek
> yerine ölçmek istedik. Altı soruluk bir test yaptık. Embedding'li sürüm altıda
> altısını buldu, kelime frekanslı sürüm altıda ikisini.
>
> Ama asıl bulgumuz bu değil. Az önce sorduğum o kapsam dışı soruyu kelime frekanslı
> sürüme de sorduk. O sürüm bu soruya **0.520** puan verdi. Cevaplayabildiği en iyi
> soruya verdiği puansa **0.300**.
>
> Yani cevaplayamadığı soruya, cevaplayabildiği her sorudan yüksek puan verdi. Bunun
> anlamı şu: o mimaride 'puan şunun altındaysa bilmiyorum de' diyebileceğiniz bir eşik
> yok. Hangi sayıyı seçerseniz seçin yanlış yerden kesiyor.
>
> Bu bir ayar meselesi değil, mimarinin sınırı. Embedding'lere geçmemizin asıl sebebi
> de doğruluk farkı değil, buydu."

> **KIVANÇ:** "İkinci ders süreçten. Resmî kaynakları takip ederken hiçbir yerde
> yazmayan dört tane hata bulduk. Hepsini repoda `RESULTS.md`'ye yazdık.
>
> En kötüsü şuydu: örnek projenin kullandığı SDK sürümü, güncel çalışma zamanıyla
> sessizce donuyor. Ne hata veriyor ne uyarı, sadece bekliyor. Yeni başlayan biri için
> bundan kötü hata olmaz. Bizim de saatlerimizi aldı.
>
> Küçük modeli de bu yüzden seçtik. Büyük modelle cevap başına altmış saniye
> bekliyorduk, küçükle beş. Bir ayda kaç kere deneyebildiğiniz, öğrenmenin kendisi
> oluyor.
>
> Kodun ve ölçümlerin hepsi GitHub'da. Teşekkür ederiz."

---

## Soru gelirse

**"Neden üç mimari, biri yetmez miydi?"**
Yeterdi ama o zaman 0.520'yi göremezdik. Kelime frekanslı sürümün eşiklenemez olduğunu,
ancak embedding'li sürümle yan yana koyunca fark ettik.

**"Bu sayıları nasıl doğrularız?"**
Repoda iki script var: `retrieval_check.js` ve `retrieval_check.py`. Aynı soru setini
bilerek paylaşıyorlar. İkisini çalıştırıp çıktıları yan yana koyabilirsiniz, model
yüklemedikleri için saniyeler sürüyor.

**"Neden bu kadar küçük model?"**
Ölçtük: büyükle cevap başına ~60 saniye, küçükle 4-7 saniye. Bir aylık programda kaç
kere deneyebildiğiniz her şeyi belirliyor.

**"Türkçe soru sorulabiliyor mu?"**
Arama katmanı Türkçede de doğru çalışıyor, kapsam dışı soruya Türkçe de düşük puan
veriyor. Ama sistem talimatımız İngilizce ve bu boyuttaki bir model o talimatı Türkçe
soruda uygulayamıyor — reddetmesi gerekirken cevap uyduruyor. Yani sorun aramada değil,
üretimde. Biliyoruz, sınırlarımızdan biri.

**"macOS'ta denediniz mi?"**
Hayır, bütün ölçümler Windows 11'de. `requirements.txt` platforma göre doğru paketi
seçiyor ama macOS'u doğrulamadık.

**"Kaç kişi çalıştınız?"**
İkimiz. Commit geçmişi ve README ikimizi de gösteriyor.

---

## Sunum öncesi kontrol listesi

1. **Uygulamayı önceden başlatın:**
   ```powershell
   cd C:\Users\kivan\foundry-local-rag
   .venv\Scripts\Activate.ps1
   cd path-c-sqlite
   streamlit run app.py
   ```
2. **Isıtın** — rastgele bir soru sorup cevabı alın, sonra sayfayı yenileyin. Model
   bellekte kalır, sunumda ilk soruda beklemezsiniz.
3. **topK'yı 3'e geri alın** (3c'de 1'e çekiyorsunuz).
4. Tarayıcıyı tam ekran yapın, yer imleri çubuğunu gizleyin.
5. Windows bildirimlerini kapatın (Focus Assist).
6. **Wi-Fi kapatmayı prova edin.** Uzaktan sunuyorsanız bu kendi bağlantınızı da keser —
   o durumda 3c'nin son kısmını önceden kaydedip kaydı oynatın.
7. **İkiniz birlikte, kronometreyle bir tam prova.** Devir teslim anları (bölüm 2 sonu,
   bölüm 4 ortası) prova edilmezse orada duraklama olur.
8. Uzarsa kesilecek ilk yer bölüm 2'nin son paragrafı. **3b ve 4'teki 0.520 asla
   kesilmez.**

# Kurumsal ve Medikal RAG Bilgi Asistanı: Uçtan Uca Proje Rehberi
Bu doküman; binlerce sayfalık medikal cihaz kılavuzu, vaka arşivi veya akademik ders notunu **kalıcı bir kurumsal bilgi bankasına** dönüştüren ve son kullanıcının yalnızca soru sorarak saniyeler içinde doğrulanmış, kaynak referanslı yanıtlar aldığı **RAG (Retrieval-Augmented Generation)** sisteminin tüm mimarisini, teknik gereksinimlerini ve uygulama adımlarını kapsar.
---
## 1. Proje Özeti ve Temel Çalışma Mantığı
### ⚠️ Kritik Prensip (Kalıcı Bilgi Bankası)
Kullanıcı sisteme her girdiğinde PDF yüklemez. Tüm doküman havuzu sistemin kurulum aşamasında **bir kez kalıcı olarak indekslenir**. Kullanıcı web arayüzünü açtığında doğrudan sorusunu sorar ve arka planda hazır bekleyen kütüphaneden anında yanıt alır.
### Mimari Akış Şeması
[1. AŞAMA: KALICI İNDEKSEME (Yönetici Tarafı - 1 Kez Yapılır)] Dokümanlar (PDF) ➡️ Metin Ayıklama ➡️ Akıllı Parçalama ➡️ Vektörleştirme ➡️ KALICI VEKTÖR DB (Disk)

[2. AŞAMA: KULLANICI SORU-CEVAP (Canlı Sistem)] Kullanıcı Sorusu ➡️ Vektör Arama (DB) ➡️ En İlgili 3-5 Sayfa ➡️ LLM (Yapay Zeka) ➡️ Cevap + Sayfa Referansı



---
## 2. Proje İçin Gerekli Yetkinlikler ve Beceriler (Skills)
Bu projeyi tek başına veya bir ekiple hayata geçirmek için gereken temel yetenekler 6 ana başlıkta toplanır:
### 1. Doküman İşleme & Veri Mühendisliği (Data Parsing)
* **Metin & Tablo Çıkarma:** Dijital PDF'leri metin, tablo ve başlık hiyerarşisini bozmadan okuyabilme (`PyMuPDF`, `pdfplumber`).
* **OCR (Optik Karakter Tanıma):** Taranmış fotokopi veya görsel ağırlıklı slaytlar için görüntüden metin okuma (`Tesseract OCR` veya multimodal modeller).
* **Veri Temizliği & Anonimleştirme:** Geçmiş hasta kayıtlarındaki T.C. Kimlik, isim, telefon gibi hassas verileri Regex/script ile temizleyip anonim vaka formatına getirme.
### 2. Parçalama (Chunking) & Vektör Arama (Retrieval)
* **Akıllı Parçalama:** Metinleri rastgele kesmek yerine anlam bütünlüğünü (paragraf, tablo, slayt sayfası) koruyarak 500–1000 kelimelik bloklara bölme.
* **Vektör Veritabanı Yönetimi:** Vektör benzerlik aramaları (Cosine Similarity), mesafe metrikleri ve metadata (etiket) filtreleme yapabilme.
### 3. Prompt Mühendisliği & Halüsinasyon Kontrolü (Guardrails)
* **Sert Kısıtlama Promptları:** Modelin kendi kafasından bilgi uydurmasını engelleyip, *"Sadece sağlanan doküman parçalarını referans al, emin değilsen 'Belgelerde bu bilgi yer almamaktadır' de"* kuralını uygulama.
* **Kaynak Doğrulama (Grounding):** Cevabın sonuna hangi belgeden ve hangi sayfadan alındığını (`Örn: Ventilatör_X_Kilavuz.pdf, Sayfa 42`) otomatik iliştirme.
### 4. Arka Yüz (Backend API) Geliştirme
* **Python ile Servis Yazma:** Kullanıcıdan gelen soruları alıp vektör araması yaptıran ve yapay zeka yanıtını frontend'e ileten REST API mimarisi kurma (`FastAPI`).
* **Oturum ve Yetkilendirme:** Müşteri personeli veya öğrenciler için kullanıcı girişi ve rol yönetimi (JWT / Auth).
### 5. Ön Yüz (Frontend / UI) Geliştirme
* **Sade ve Hızlı Chat Ekranı:** WhatsApp/ChatGPT benzeri bir sohbet penceresi, yanıt akışı (streaming), kaynakları gösteren kartlar ve kategori filtreleme butonları (`Streamlit` veya `Next.js / React`).
### 6. Medikal Güvenlik & Regülasyon Bilgisi
* **KVKK / GDPR Standartları:** Hasta verilerinin internete sızmasını önleyen kapalı havuz prensibi.
* **Yasal Sorumluluk Reddi (Disclaimer):** Sistemin tıbbi reçete/kesin tanı koymadığını, klinik karar destek aracı olduğunu belirten yasal çerçeve.
---
## 3. Önerilen Teknoloji Yığını (Tech Stack)
| Katman | Teknoloji | Neden Bu Seçim? |
| :--- | :--- | :--- |
| **Ana Dil** | **Python 3.10+** | Yapay zeka, veri işleme ve API kütüphanelerinin dünya standardı. |
| **Backend API** | **FastAPI** | Asenkron, çok hızlı ve otomatik Swagger dokümantasyonu üretir. |
| **Kalıcı Vektör DB** | **ChromaDB** *(Yerel/Başlangıç)*<br>**Qdrant** *(Büyük Kurumsal)* | ChromaDB tek klasörde diske yazar, kurulumu sıfır maliyetlidir. Qdrant ise milyonlarca sayfada yüksek ölçeklenme sağlar. |
| **Embedding Modeli** | **text-embedding-3-small** (OpenAI) veya **text-embedding-004** (Google) | Çok ucuz, yüksek Türkçe anlamsal kavrama başarısı. |
| **Büyük Dil Modeli (LLM)** | **Google Gemini 1.5 / 2.0 Flash** veya **GPT-4o-mini** | Geniş bağlam (context) penceresi, yüksek hız ve soru başı kuruş seviyesinde maliyet. |
| **PDF Okuyucu** | **PyMuPDF (`fitz`) & pdfplumber** | PDF'leri hızlı ve tabloları bozmadan metne dönüştürür. |
| **Frontend Arayüzü** | **Streamlit** *(Hızlı Demo İçin)*<br>**Next.js + Tailwind** *(Canlı Kurumsal Ürün)* | Streamlit ile 1 günde çalışan web arayüzü çıkarılır. Next.js ile müşteriye özel SaaS paneli yapılır. |
---
## 4. Adım Adım Uygulama Yol Haritası
### 🔹 1. Faz: Klasörleme ve Veri Hazırlığı (Offline)
1. PDF'ler kategorilerine göre klasörlenir:
   * `dokumanlar/cihazlar/` (Kullanım kılavuzları)
   * `dokumanlar/vakalar/` (Anonim hasta süreçleri)
   * veya `dokumanlar/dersler/` (Diş hekimliği slaytları)
2. Vaka dokümanlarında isim/kimlik taraması yapılıp maskelenir.
### 🔹 2. Faz: Kalıcı İndeksleme Scripti (`ingest.py`)
1. Bir Python scripti yazılır:
   * Klasördeki tüm PDF'leri sırayla açar.
   * Sayfa sayfa okur.
   * Her sayfaya dosya adı, sayfa no, konu etiketi (metadata) ekler.
   * Embedding modeline gönderip vektörünü alır.
   * Diskteki kalıcı veritabanına (`./chroma_db/`) kaydeder.
2. **Bu işlem bir kez çalıştırılır ve biter.** Yeni PDF geldikçe bu script tetiklenir.
### 🔹 3. Faz: Arama ve Yanıt Motoru (`rag_engine.py`)
1. Kullanıcıdan gelen soru vektöre dönüştürülür.
2. Vektör DB'de `cosine similarity` ile en alakalı 3-5 sayfa çekilir.
3. Çekilen sayfalar LLM'e şu sistem promptu ile verilir:
   > *"Sen bir medikal asistansın. Yalnızca aşağıda sağlanan doküman parçalarındaki bilgilere sadık kalarak soruyu yanıtla. Dokümanda yer almayan hiçbir bilgiyi tahmin etme. Yanıtının sonuna mutlaka (Doküman Adı, Sayfa X) referansını ekle."*
### 🔹 4. Faz: Web Arayüzü (`app.py`)
1. Kullanıcının gireceği web sitesi ayağa kaldırılır.
2. Sadece bir chat kutusu ve isteğe bağlı "Kategori Seçimi" (Örn: *Ders Seçimi* veya *Cihaz Seçimi*) yer alır.
3. Kullanıcı sorusunu yazar, saniyeler içinde sayfa referanslı cevabını alır.
### 🔹 5. Faz: Test ve Güvenlik Doğrulaması
1. Dokümanda cevabı **olmayan** tuzak sorular sorulur (Modelin *"Dokümanlarda bu bilgi bulunmamaktadır"* dediği doğrulanır).
2. Sayfa numaraları manuel olarak orijinal PDF ile karşılaştırılır.
---
## 5. Maliyet ve Performans Analizi
* **Tek Seferlik İndeksleme (10.000 Sayfa):**
  * Toplam ~3-4 milyon token.
  * Modern embedding modelleriyle tüm arşivi bir kez vektörleştirme maliyeti: **~0.05$ - 0.10$ (yaklaşık 2-4 TL)**.
* **Soru Başına İşletme Maliyeti:**
  * Her soruda sadece bulunan 3-5 sayfa (~1.500 kelime) LLM'e gönderilir.
  * 1.000 adet soru sormanın toplam maliyeti: **~0.20$ - 0.50$ (10-20 TL)**.
* **Yanıt Hızı:**
  * Vektör DB'den ilgili sayfaları bulma: **100 - 300 ms**.
  * Yapay zekanın cevabı üretip ekrana basması: **1 - 2 saniye**.
---
## 6. Müşteri (Medikal Şirket) vs. Öğrenci (Diş Hekimliği) Karşılaştırması
| Özellik | Medikal Cihaz Müşterisi | Diş Hekimliği Ders Notları |
| :--- | :--- | :--- |
| **Doküman Türü** | Teknik servis kitapları, hasta formları, klinik kılavuzlar | PowerPoint'ten çevrilmiş ders slaytları, sınav notları |
| **Kritik İhtiyaç** | Hata payının sıfır olması, sayfa referansı, KVKK gizliliği | Sınav quiz modu, slayt referansı, hızlı konu özetleri |
| **Chunking Yapısı** | Paragraf ve teknik parametre tabloları | Slayt bazlı (her slayt = 1 bağımsız parça) |
| **Arayüz Odak Noktası** | Cihaz modeline ve hata koduna göre filtreleme | Ders adına göre filtreleme (Endodonti, Pedodonti vb.) |
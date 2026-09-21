---
name: rag-chunking-retrieval
description: Slayt ve doküman bazlı akıllı parçalama (chunking), embedding oluşturma ve ChromaDB kalıcı vektör veritabanı yönetimi ve benzerlik araması becerisi.
---

# RAG Parçalama, Embedding ve Vektör Arama Becerisi

Bu beceri; ayrıştırılmış medikal ve akademik metinlerin anlamsal bütünlüklerini koruyarak vektörleştirilmesini, ChromaDB'de kalıcı olarak saklanmasını ve soru anında en alakalı içeriklerin getirilmesini yönetir.

## 1. Parçalama (Chunking) Stratejileri

- **Slayt Bazlı İndeksleme (Diş Hekimliği Slaytları İçin Öncelikli):**
  - Her bir slayt bağımsız bir anlamsal birimdir.
  - Slayt başlığı + içerik tek parça olarak chunk yapılır (yaklaşık 100-300 kelime).
  - Parça boyutu sınırı: 500-1000 karakter. Eğer bir slayt çok uzunsa `RecursiveCharacterTextSplitter` ile `chunk_size=800`, `overlap=100` kullanılır.
- **Kitap & Kılavuz İndeksleme:**
  - Bölüm ve başlık bütünlüğü korunur.
  - Paragraflar anlamsal olarak bölünür.

## 2. Embedding Modelleri

- **Birincil Öneri:** Google `text-embedding-004` (yüksek Türkçe kavrama, ekonomik) veya OpenAI `text-embedding-3-small`.
- **Boyut (Dimension):** Modelin çıktı boyutuna uygun ChromaDB koleksiyonu oluşturulur (`cosine` mesafesi tercih edilir).

## 3. ChromaDB Kalıcı Depolama Yapısı

- Veritabanı diske `./chroma_db` dizininde kalıcı olarak yazılır.
- Koleksiyon adı: `dis_hekimligi_rag`
- Metadata alanları mutlaka şunları içermelidir:
  - `source`: Dosya adı
  - `page`: Sayfa / Slayt numarası
  - `category`: Ders veya doküman tipi
  - `chunk_id`: Tekil tanımlayıcı

## 4. Geri Çağırma (Retrieval) Parametreleri

- Benzerlik metriği: `cosine`
- Top-K: Kullanıcı sorusu için en benzer 3 ila 5 doküman parçası getirilir.
- Skor Eşiği (Score Threshold): Benzerlik skoru 0.40 altında olan alakasız parçalar LLM bağlamına dahil edilmemelidir.

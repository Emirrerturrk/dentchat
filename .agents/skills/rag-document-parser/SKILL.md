---
name: rag-document-parser
description: Doküman (PDF ve PPTX) işleme, metin/tablo çıkarma, slayt ayrıştırma ve medikal veri temizliği için standart yönergeler ve kod şablonları.
---

# RAG Doküman İşleme ve Veri Ayrıştırma (Data Parsing) Becerisi

Bu beceri; PDF kılavuzları, taranmış dokümanları ve PowerPoint (`.pptx`) ders slaytlarını yapısal hiyerarşiyi ve sayfa/slayt bütünlüğünü bozmadan metne dönüştürmek için kullanılır.

## 1. Desteklenen Formatlar ve Kütüphaneler

- **Dijital PDF'ler:** `PyMuPDF` (`fitz`) - Hızlı, sayfa bazlı metin ve blok çıkarma.
- **Tablo Ağırlıklı PDF'ler:** `pdfplumber` - Karmaşık medikal parametre tablolarını yapısal okuma.
- **PowerPoint Slaytları (`.pptx`):** `python-pptx` - Her slaytın başlık, gövde metni ve konuşmacı notlarını sırayla okuma.
- **Görsel/Taranmış Slaytlar:** `pytesseract` veya multimodal LLM (Gemini Vision) ile görselden metin çıkarma.

## 2. Çıktı Standardı (Parsed Document Schema)

Her ayrıştırılan sayfa veya slayt şu metadata yapısına sahip olmalıdır:

```python
{
    "content": "Slayt veya sayfa metni...",
    "metadata": {
        "source_file": "10Curugun operatif tedavisi.pdf",
        "file_type": "pdf", # veya "pptx"
        "page_or_slide": 14,
        "category": "Restoratif Diş Tedavisi", # Klasör veya dosya adından
        "title": "Çürük Lezyonlarının Sınıflandırılması"
    }
}
```

## 3. Veri Temizliği & KVKK/Anonimleştirme Kuralları

Eğer hasta verisi veya klinik vaka dokümanı işleniyorsa:
1. T.C. Kimlik Numaraları: `r"\b[1-9][0-9]{10}\b"` maskelenmelidir (`[TC KİMLİK SİLİNDİ]`).
2. Telefon Numaraları: `r"(0?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2})"` maskelenmelidir.
3. Hasta İsimleri: Başlık formatında tekil geçen şahıs isimleri anonimleştirilmelidir.

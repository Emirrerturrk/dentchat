---
name: rag-service-ui
description: RAG sistemi için FastAPI REST API arka yüzü ve Streamlit / Next.js kullanıcı arayüzü mimarisi, streaming yanıtlar ve kategori filtreleme becerisi.
---

# RAG Servis & Ön Yüz (Backend & UI) Becerisi

Bu beceri; FastAPI ile asenkron soru-cevap REST API uç noktalarının oluşturulmasını ve Streamlit / modern web teknolojileri ile son kullanıcı sohbet arayüzünün geliştirilmesini kapsar.

## 1. FastAPI Uç Noktası Standardı

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    category: str | None = None # İsteğe bağlı ders/cihaz filtresi

class SourceItem(BaseModel):
    source_file: str
    page: int
    content_snippet: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
```

## 2. Arayüz Tasarım Prensipleri (Streamlit / Next.js)

1. **Sade ve Hızlı Chat:** ChatGPT/WhatsApp tarzı akıcı sohbet balonları.
2. **Kategori Seçici:** Kullanıcının isterse "Tüm Dokümanlar" veya belirli bir dersi (Örn: *Endodonti*, *Periodontoloji*, *Protez*) filtreleyebileceği seçim kutusu.
3. **Açılır Kaynak Kartları:** Yanıtın altındaki referans sayfaların tıklandığında alıntı yapılan metin parçacığını göstermesi.
4. **Yanıt Akışı (Streaming):** Token token gerçek zamanlı yanıt hissi.

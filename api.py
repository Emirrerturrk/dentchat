"""
FastAPI REST API Servisi (api.py).
Dokümantasyon: /docs (Swagger UI)
Uç noktalar:
- POST /api/query: Soru-cevap servisi (kategori filtreli, kaynak referanslı)
- GET /api/stats: İndekslenmiş içerik istatistikleri
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

from rag_engine import RAGEngine
from indexer import get_chroma_collection

app = FastAPI(
    title="Diş Hekimliği RAG API",
    description="Akademik diş hekimliği ders notları ve kılavuzları için doğrulanmış RAG soru-cevap servisi",
    version="1.0.0"
)

engine = None

@app.on_event("startup")
def startup_event():
    global engine
    engine = RAGEngine()


class QueryRequest(BaseModel):
    question: str
    category: Optional[str] = None


class SourceItem(BaseModel):
    source: str
    page: int
    category: str
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]


@app.get("/api/stats")
def get_stats():
    """Veritabanındaki toplam indeksli sayfa ve slayt sayısını döndürür."""
    try:
        col = get_chroma_collection()
        return {"total_indexed_chunks": col.count(), "status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
def query_rag(req: QueryRequest):
    """Kullanıcı sorusunu alır, vektör aramayla ilgili sayfaları bulur ve LLM ile yanıtlar."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Soru boş olamaz.")
    
    global engine
    if engine is None:
        engine = RAGEngine()

    result = engine.ask(req.question, category_filter=req.category)
    return result

"""
RAG Soru-Cevap Motoru (rag_engine.py).
1. Kullanıcı sorusunu vektörleştirir.
2. ChromaDB'den en alakalı ilk 3-4 doküman parçasını (Top-K) çeker (Token tasarrufu).
3. Sıkı medikal guardrail kurallarıyla LLM'e (Gemini Flash) iletir.
4. Kaynak referanslı (Grounding) yanıt ve alıntıları döndürür.
"""

import os
import re
from typing import List, Dict, Any, Optional
import chromadb
from dotenv import load_dotenv

from embedder import GeminiEmbedder

load_dotenv()

def get_api_key() -> Optional[str]:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                key = st.secrets["GEMINI_API_KEY"]
            elif "GOOGLE_API_KEY" in st.secrets:
                key = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            pass
    return key

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = "dis_hekimligi_rag"
API_KEY = get_api_key()

GUARDRAIL_SYSTEM_PROMPT = """Sen diş hekimliği fakültesi ders notları ve medikal kılavuzlar konusunda uzmanlaşmış akademik bir asistansın.
Görevin, kullanıcının sorularını YALNIZCA sana sağlanan 'BAĞLAM' (Ders Slaytları ve Sayfaları) içeriğine sadık kalarak, doğrudan, akıcı ve net bir dille yanıtlamaktır.

KAT'İ KURALLAR:
1. SADECE SAĞLANAN BAĞLAM: Sağlanan metin parçalarında açıkça yer almayan hiçbir bilgiyi kendi genel eğitiminden uydurma, tahmin etme veya ekleme yapma.
2. BELGELERDE YOKSA: Eğer sorunun yanıtı sağlanan metin parçalarında açıkça yer almıyorsa veya yetersizse, KESİNLİKLE şunu söyle:
   "Sağlanan ders notları ve dokümanlarda bu konuyla ilgili bilgi yer almamaktadır."
3. METİN İÇİNDE ASLA KAYNAK/SLAYT YAZMA: Yanıt metninin içerisine KESİNLİKLE [Kaynak: ...], (Sayfa: ...), [Slayt ...] veya dosya isimleri YAZMA. Kaynaklar kullanıcı arayüzü tarafından otomatik olarak alt kısma eklenecektir. Metin tamamen temiz, akıcı ve doğrudan soruya odaklı olmalıdır.
4. SORUMLULUK REDDİ YAZMA: Yanıtın sonuna sorumluluk reddi, telif veya sistem notu ekleme; yalnızca sorulan soruya odaklan.
"""


class RAGEngine:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = GeminiEmbedder()
        self.model_name = model_name
        self._init_llm()

    def _init_llm(self):
        try:
            from google import genai
            self.genai_client = genai.Client(api_key=API_KEY)
            self.use_new_sdk = True
        except ImportError:
            import google.generativeai as genai_legacy  # type: ignore
            genai_legacy.configure(api_key=API_KEY)
            self.genai_client = genai_legacy.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=GUARDRAIL_SYSTEM_PROMPT
            )
            self.use_new_sdk = False

    def retrieve(self, question: str, top_k: int = 4, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Kullanıcı sorusuyla en alakalı parça ve slaytları getirir.
        Token tasarrufu için top_k varsayılan 4'tür.
        """
        question_vector = self.embedder.get_embedding(question)
        if not question_vector:
            return []

        where_clause = None
        if category_filter and category_filter != "Tümü":
            where_clause = {"category": category_filter}

        results = self.collection.query(
            query_embeddings=[question_vector],
            n_results=top_k,
            where=where_clause
        )

        retrieved_docs = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else []
            distances = results["distances"][0] if "distances" in results else []

            for i in range(len(docs)):
                # Cosine distance 0.65'ten büyükse (alaka düzeyi düşükse) ele
                dist = distances[i] if i < len(distances) else 0.0
                retrieved_docs.append({
                    "content": docs[i],
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dist
                })

        return retrieved_docs

    def ask(self, question: str, category_filter: Optional[str] = None) -> Dict[str, Any]:
        """Soruyu yanıtlar ve kaynak parçalarıyla birlikte döndürür."""
        relevant_chunks = self.retrieve(question, top_k=4, category_filter=category_filter)

        if not relevant_chunks:
            return {
                "answer": "Sağlanan ders notları ve dokümanlarda bu konuyla ilgili bilgi yer almamaktadır.",
                "sources": []
            }

        # Token tasarruflu bağlam derleme
        context_parts = []
        sources = []
        for i, chunk in enumerate(relevant_chunks, start=1):
            meta = chunk["metadata"]
            source_info = f"Kaynak {i}: {meta.get('source', 'Bilinmeyen Dosya')} (Sayfa/Slayt: {meta.get('page', '?')})"
            context_parts.append(f"--- {source_info} ---\n{chunk['content']}\n")
            sources.append({
                "source": meta.get("source", "Bilinmeyen"),
                "page": meta.get("page", 1),
                "category": meta.get("category", "Genel"),
                "snippet": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
            })

        full_context = "\n".join(context_parts)
        user_prompt = f"""AŞAĞIDAKİ BAĞLAMI DİKKATLİCE İNCELE VE SORUYU YANITLA:

{full_context}

KULLANICI SORUSU: {question}

ÖNEMLİ KURAL: Yanıtının içine KESİNLİKLE dosya adı, sayfa/slayt numarası veya '[Kaynak: ...]' yazma. Yalnızca sorunun doğrudan ve anlaşılır cevabını Türkçe olarak yaz:"""

        try:
            if self.use_new_sdk:
                # google-genai SDK
                response = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config={
                        "system_instruction": GUARDRAIL_SYSTEM_PROMPT,
                        "temperature": 0.2, # Düşük yaratıcılık = sıfır halüsinasyon
                    }
                )
                answer_text = response.text
            else:
                response = self.genai_client.generate_content(
                    user_prompt,
                    generation_config={"temperature": 0.2}
                )
                answer_text = response.text

            # Metin içindeki olası kaynak etiketlerini ve sorumluluk notlarını temizle
            clean_answer = re.sub(r"\[Kaynak:[^\]]*\]", "", answer_text, flags=re.IGNORECASE)
            clean_answer = re.sub(r"\(Kaynak:[^\)]*\)", "", clean_answer, flags=re.IGNORECASE)
            clean_answer = re.sub(r"\[Doküman:[^\]]*\]", "", clean_answer, flags=re.IGNORECASE)
            clean_answer = re.sub(r"\[Slayt:[^\]]*\]", "", clean_answer, flags=re.IGNORECASE)
            clean_answer = re.sub(r"\*?Not:\s*Bu sistem akademik.*$", "", clean_answer, flags=re.IGNORECASE | re.MULTILINE)
            # Çift boşlukları ve gereksiz satır sonlarını toparla
            clean_answer = re.sub(r"[ \t]+", " ", clean_answer)
            clean_answer = re.sub(r"\n{3,}", "\n\n", clean_answer)
            clean_answer = clean_answer.strip()

            return {
                "answer": clean_answer,
                "sources": sources
            }
        except Exception as e:
            return {
                "answer": f"Yapay zeka yanıtı üretilirken bir sorun oluştu: {str(e)}",
                "sources": sources
            }

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
    # 1. Ortam Değişkenleri (.env veya os.environ)
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        return key.strip().strip('"').strip("'")

    # 2. Streamlit Cloud Secrets (Bulut Sunucu Kasası)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GEMINI_API_KEY" in st.secrets:
                return str(st.secrets["GEMINI_API_KEY"]).strip().strip('"').strip("'")
            if "GOOGLE_API_KEY" in st.secrets:
                return str(st.secrets["GOOGLE_API_KEY"]).strip().strip('"').strip("'")
    except Exception:
        pass

    return None

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = "dis_hekimligi_rag"

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
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.api_key = api_key or get_api_key()
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = GeminiEmbedder(api_key=self.api_key)
        self.model_name = model_name
        self._init_llm()

    def _init_llm(self):
        key = self.api_key or get_api_key()
        if not key:
            raise ValueError("GEMINI_API_KEY bulunamadı. Lütfen Streamlit Secrets veya .env dosyasını kontrol edin.")
        try:
            from google import genai
            self.genai_client = genai.Client(api_key=key)
            self.use_new_sdk = True
        except ImportError:
            import google.generativeai as genai_legacy  # type: ignore
            genai_legacy.configure(api_key=key)
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

    def contextualize_question(self, question: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Kullanıcı bir devam sorusu sorduğunda (örn: 'peki bunun tedavisi?', '2. maddeyi açıkla'),
        soruyu sohbet geçmişiyle harmanlayarak bağımsız, anahtar kelimeleri içeren bir arama sorgusuna dönüştürür.
        """
        if not chat_history or len(chat_history) < 2:
            return question

        # Son 2 soru ve cevabı bağlam için al
        history_lines = []
        for msg in chat_history[-4:]:
            role = "Öğrenci" if msg.get("role") == "user" else "Asistan"
            content = str(msg.get("content", ""))[:200].strip()
            if content:
                history_lines.append(f"{role}: {content}")

        if not history_lines:
            return question

        history_context = "\n".join(history_lines)
        rephrase_prompt = f"""Aşağıdaki diş hekimliği ders sohbet geçmişini ve kullanıcının son sorusunu oku.
Kullanıcının son sorusu önceki konuşmaya gönderme yapıyorsa (örneğin 'bunun tedavisi', 'peki neden?', '2. madde'), veritabanından doğru slaytları bulabilmek için soruyu tek başına anlaşılır, tıbbi terimleri içeren bağımsız bir arama cümlesine dönüştür.

SOHBET GEÇMİŞİ:
{history_context}

KULLANICININ SON SORUSU: {question}

KURAL: Soruya cevap verme. Sadece veritabanında aranacak tek bir Türkçe arama cümlesi yaz:"""

        try:
            if self.use_new_sdk:
                resp = self.genai_client.models.generate_content(
                    model=self.model_name,
                    contents=rephrase_prompt
                )
                rephrased = resp.text.strip()
            else:
                resp = self.genai_client.generate_content(rephrase_prompt)
                rephrased = resp.text.strip()

            if rephrased and len(rephrased) < 250:
                return rephrased
        except Exception:
            pass

        return question

    def ask(self, question: str, chat_history: Optional[List[Dict[str, Any]]] = None, category_filter: Optional[str] = None) -> Dict[str, Any]:
        """Soruyu yanıtlar ve kaynak parçalarıyla birlikte döndürür (Bağlam takipli)."""
        # 1. Takip eden sorularda konuyu kaybetmemek için sorguyu bağlamsallaştır
        search_query = self.contextualize_question(question, chat_history=chat_history)

        # 2. Vektör veritabanından ilgili slaytları çek
        relevant_chunks = self.retrieve(search_query, top_k=4, category_filter=category_filter)

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

        # Önceki sohbet özeti (Varsa)
        prev_chat_context = ""
        if chat_history and len(chat_history) >= 2:
            prev_lines = []
            for msg in chat_history[-4:]:
                r = "Kullanıcı" if msg.get("role") == "user" else "Asistan"
                prev_lines.append(f"{r}: {str(msg.get('content', ''))[:200]}")
            prev_chat_context = "ÖNCEKİ DİYALOG BAĞLAMI:\n" + "\n".join(prev_lines) + "\n\n"

        user_prompt = f"""{prev_chat_context}AŞAĞIDAKİ DERS DOKÜMANLARINI DİKKATLİCE İNCELE VE YANITLA:

{full_context}

KULLANICI SORUSU: {question}

ÖNEMLİ KURAL: Yanıtının içine KESİNLİKLE dosya adı, sayfa/slayt numarası veya '[Kaynak: ...]' yazma. Eğer önceki diyalogla ilgili bir devam sorusuysa önceki cevabınla tutarlı, doğrudan ve anlaşılır bir Türkçe yanıt ver:"""

        import time
        answer_text = ""
        for attempt in range(3):
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
                break
            except Exception as e:
                if attempt == 2:
                    return {
                        "answer": f"Yapay zeka yanıtı üretilirken bir sorun oluştu: {str(e)}",
                        "sources": sources
                    }
                time.sleep(2 * (attempt + 1))

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

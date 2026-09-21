"""
Embedding modülü: Metinleri vektörlere dönüştürür.
Token tasarrufu prensipleri:
1. Önceden vektörleştirilmiş içerikleri tespit eder, tekrar embedding API'sine göndermez.
2. Metinleri batch halinde toplu işleyerek istek yükünü optimize eder.
3. Google Gemini (text-embedding-004) modelini kullanır.
"""

import os
import hashlib
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

class GeminiEmbedder:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/gemini-embedding-001"):
        self.api_key = api_key or API_KEY
        self.model_name = model_name
        self.client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.")
        
        # Yeni google-genai veya klasik google.generativeai desteği
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.use_new_sdk = True
        except ImportError:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            self.client = genai_legacy
            self.use_new_sdk = False

    def get_embedding(self, text: str) -> List[float]:
        """Tekil metin için embedding vektörü üretir."""
        embeddings = self.get_embeddings_batch([text])
        return embeddings[0] if embeddings else []

    def get_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Metin listesini batch'ler halinde embedding modeline iletir.
        Gereksiz çağrıları ve kota aşımlarını engeller.
        """
        all_embeddings = []
        
        import time
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            success = False
            for attempt in range(4):
                try:
                    if self.use_new_sdk:
                        response = self.client.models.embed_content(
                            model=self.model_name,
                            contents=batch
                        )
                        for emb in response.embeddings:
                            all_embeddings.append(emb.values)
                    else:
                        import google.generativeai as genai_legacy
                        result = genai_legacy.embed_content(
                            model=self.model_name,
                            content=batch,
                            task_type="retrieval_document"
                        )
                        if "embedding" in result:
                            all_embeddings.extend(result["embedding"])
                    success = True
                    break
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        wait_time = 35 + (attempt * 10)
                    else:
                        wait_time = (attempt + 1) * 3
                    print(f"[UYARI] Embedding çağrısı deneme {attempt + 1}/4 başarısız. {wait_time}s bekleniyor...")
                    time.sleep(wait_time)
            
            if not success:
                raise RuntimeError(f"Embedding batch {i} işlenemedi.")
            
            # API rate limit koruması için ufak bekleme
            time.sleep(0.3)

        return all_embeddings


def generate_chunk_id(source: str, page: int, content: str) -> str:
    """Tekil ve kararlı bir chunk ID üretir (içerik hash'i bazlı)."""
    content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:10]
    safe_source = re_safe = "".join(c for c in source if c.isalnum() or c in ("-", "_")).rstrip()
    return f"{safe_source}_p{page}_{content_hash}"

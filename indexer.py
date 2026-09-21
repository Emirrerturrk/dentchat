"""
Kalıcı İndeksleme Scripti (ingest.py / indexer.py).
Tüm PDF ve PPTX dokümanlarını ayrıştırır, yeni parçaları vektörleştirir ve ChromaDB'ye kalıcı yazar.
Token Tasarrufu:
- Halihazırda veritabanında var olan hiçbir parça tekrar embedding modeline GÖNDERİLMEZ.
"""

import os
import sys
import glob
from typing import List, Dict, Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import chromadb
from dotenv import load_dotenv

from parser import parse_document
from embedder import GeminiEmbedder, generate_chunk_id

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
DATA_DIR = os.getenv("DATA_DIR", "./pdfler")
COLLECTION_NAME = "dis_hekimligi_rag"


def get_chroma_collection():
    """Kalıcı ChromaDB istemcisini ve koleksiyonunu başlatır."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def categorize_filename(filename: str) -> str:
    """Dosya isminden ana diş hekimliği ders/konu kategorisini tahmin eder."""
    fn = filename.lower()
    if "kanal" in fn or "endodonti" in fn:
        return "Endodonti"
    elif "çürük" in fn or "curuk" in fn or "dentin" in fn or "dolgu" in fn or "restoratif" in fn:
        return "Restoratif Diş Tedavisi"
    elif "protez" in fn or "oklzyon" in fn or "kaide" in fn:
        return "Protetik Diş Tedavisi"
    elif "biyopsi" in fn or "klinik" in fn or "oral diagnoz" in fn or "dagnoz" in fn or "muayene" in fn:
        return "Ağız, Diş ve Çene Radyolojisi & Cerrahisi"
    elif "anomali" in fn or "iskeletsel" in fn:
        return "Ortodonti"
    elif "davranıs" in fn or "davrans" in fn:
        return "Pedodonti / Davranış Yönetimi"
    return "Genel Diş Hekimliği"


def index_documents():
    """Tüm doküman havuzunu tarar ve ChromaDB'ye kalıcı indeksler."""
    print("=" * 60)
    print("🦷 DİŞ HEKİMLİĞİ RAG KALICI İNDEKSLEME BAŞLATIYOR...")
    print("=" * 60)

    collection = get_chroma_collection()
    embedder = GeminiEmbedder()

    # Mevcut tüm ID'leri çekerek mükerrer token harcamasını önle
    existing_items = collection.get()
    existing_ids = set(existing_items["ids"]) if existing_items and "ids" in existing_items else set()
    print(f"📌 Veritabanında halihazırda bulunan parça sayısı: {len(existing_ids)}")

    # Desteklenen dosyaları bul
    supported_extensions = ["*.pdf", "*.pptx"]
    all_files = []
    for ext in supported_extensions:
        all_files.extend(glob.glob(os.path.join(DATA_DIR, ext)))

    print(f"📁 Bulunan toplam doküman: {len(all_files)}")

    total_new_chunks = 0
    total_skipped_chunks = 0

    for idx, file_path in enumerate(all_files, start=1):
        file_name = os.path.basename(file_path)
        category = categorize_filename(file_name)
        print(f"\n[{idx}/{len(all_files)}] Ayrıştırılıyor: {file_name} (Ders: {category})")

        try:
            raw_chunks = parse_document(file_path)
        except Exception as e:
            print(f"  ❌ Dosya okunamadı: {e}")
            continue

        if not raw_chunks:
            print("  ⚠️ Metin çıkarılamadı veya boş.")
            continue

        new_chunks = []
        new_ids = []
        new_metadatas = []
        new_documents = []

        for chunk in raw_chunks:
            chunk_id = generate_chunk_id(
                source=chunk["metadata"]["source"],
                page=chunk["metadata"]["page"],
                content=chunk["content"]
            )

            # TOKEN KORUMA: Eğer bu ID zaten veritabanında varsa atla
            if chunk_id in existing_ids:
                total_skipped_chunks += 1
                continue

            metadata = chunk["metadata"]
            metadata["category"] = category
            
            new_ids.append(chunk_id)
            new_documents.append(chunk["content"])
            new_metadatas.append(metadata)

        if not new_ids:
            print(f"  ✅ Tüm slaytlar/sayfalar zaten indeksli (Atlandı: {len(raw_chunks)} parça).")
            continue

        print(f"  ⚡ {len(new_ids)} yeni parça için embedding alınıyor...")
        try:
            embeddings = embedder.get_embeddings_batch(new_documents, batch_size=25)
            collection.add(
                ids=new_ids,
                documents=new_documents,
                embeddings=embeddings,
                metadatas=new_metadatas
            )
            total_new_chunks += len(new_ids)
            print(f"  💾 {len(new_ids)} parça kalıcı olarak ChromaDB'ye yazıldı.")
        except Exception as e:
            print(f"  ❌ Vektörleştirme hatası: {e}")

    print("\n" + "=" * 60)
    print("🎉 İNDEKSLEME TAMAMLANDI!")
    print(f"Yeni Eklenen Parça: {total_new_chunks}")
    print(f"Önceden Kayıtlı (Token Tasarrufu): {total_skipped_chunks}")
    print(f"Veritabanındaki Güncel Toplam Parça: {collection.count()}")
    print("=" * 60)


if __name__ == "__main__":
    index_documents()

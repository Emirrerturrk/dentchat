"""
Doküman ve slayt ayrıştırma modülü (PDF & PPTX).
Akıllı Hibrit Mimari:
1. Vektörel (Dijital) Sayfalar: PyMuPDF (fitz) ile milisaniyeler içinde doğrudan ve ücretsiz okunur.
2. Taranmış / Fotoğraflı Sayfalar: Sayfada metin yoksa veya bozuksa, Gemini Vision OCR ile taranıp temiz Markdown'a dönüştürülür.
3. Önbellekleme (.ocr_cache): Bir kez OCR yapılan sayfa diske kaydedilir, tekrar çalıştığında API harcaması yapılmaz.
"""

import os
import re
from typing import List, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

try:
    from pptx import Presentation
except ImportError:
    Presentation = None

# OCR sonuçlarının saklanacağı yerel önbellek dizini
OCR_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".ocr_cache")
_genai_client = None


def clean_text(text: str) -> str:
    """Metindeki gereksiz boşlukları, satır sonlarını ve fazlalıkları temizler."""
    if not text:
        return ""
    # Birden fazla ardışık boşluğu ve tab'ları teke indir
    text = re.sub(r"[ \t]+", " ", text)
    # 2'den fazla ardışık satır başlarını ikiye indir (paragraf yapısını koru)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Satır başı ve sonundaki boşlukları kırp
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


def is_vector_text(text: str) -> bool:
    """
    Sayfadan çekilen metnin gerçek ve okunabilir vektörel metin olup olmadığını denetler.
    Kısa metinleri veya bozuk OCR katmanlarını eler.
    """
    if not text:
        return False
    cleaned = clean_text(text)
    if len(cleaned) < 40:
        return False
    # Harf ve rakam oranını kontrol et (bozuk karakter / glif yığınlarını engelle)
    alnum_count = sum(c.isalnum() for c in cleaned)
    ratio = alnum_count / len(cleaned)
    return ratio >= 0.45


def get_genai_client():
    """Gemini API istemcisini tekil (singleton) olarak başlatır."""
    global _genai_client
    if _genai_client is not None:
        return _genai_client
    try:
        from embedder import get_api_key
        api_key = get_api_key()
        if not api_key:
            return None
        from google import genai
        _genai_client = genai.Client(api_key=api_key)
        return _genai_client
    except Exception as e:
        print(f"  [UYARI] Gemini Vision başlatılamadı: {e}")
        return None


def ocr_page_with_gemini(page, file_name: str, page_index: int) -> str:
    """
    Taranmış veya fotoğraflanmış PDF sayfasını yüksek çözünürlüklü görsele çevirir
    ve Gemini Vision ile kusursuz Türkçe medikal Markdown metne dönüştürür.
    Yerel disk önbelleği (.ocr_cache) kullanarak mükerrer harcamayı önler.
    """
    os.makedirs(OCR_CACHE_DIR, exist_ok=True)
    
    # Güvenli önbellek dosya adı oluştur
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', file_name)
    cache_path = os.path.join(OCR_CACHE_DIR, f"{safe_name}_p{page_index + 1}.txt")

    # 1. Önbellekte varsa doğrudan diskten oku
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = f.read().strip()
            if cached and cached != "BOŞ_SAYFA":
                return cached
            elif cached == "BOŞ_SAYFA":
                return ""
        except Exception:
            pass

    client = get_genai_client()
    if not client:
        return ""

    try:
        from google.genai import types
        # 150 DPI medikal ders slaytları için ideal denge sağlar
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")

        prompt = (
            "Sen bir tıp ve diş hekimliği doküman ayrıştırıcısısın. "
            "Bu slayt veya ders notu sayfasında yer alan tüm metinleri, başlıkları, "
            "madde işaretlerini ve tabloları yapısını koruyarak eksiksiz biçimde Türkçe Markdown olarak çıkar. "
            "Yorum, özet veya ekstra açıklama ekleme, yalnızca görseldeki içeriği aktar. "
            "Eğer sayfada hiç okunabilir metin yoksa sadece 'BOŞ_SAYFA' yaz."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt
            ]
        )

        ocr_text = response.text.strip() if response and response.text else ""

        # Sonucu önbelleğe kaydet
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(ocr_text)

        if ocr_text == "BOŞ_SAYFA" or len(ocr_text) < 20:
            return ""

        return clean_text(ocr_text)
    except Exception as e:
        print(f"  [UYARI] Gemini OCR hatası ({file_name} Sayfa {page_index + 1}): {e}")
        return ""


def parse_pdf(file_path: str, enable_ocr: bool = True) -> List[Dict[str, Any]]:
    """
    PDF dosyasını sayfa sayfa okur.
    Akıllı Hibrit Kontrol:
    - Sayfada vektörel metin varsa doğrudan alır.
    - Metin yoksa veya fotoğraf/taranmış ise Gemini Vision OCR devreye girer.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) kütüphanesi yüklü değil.")

    chunks = []
    file_name = os.path.basename(file_path)
    
    doc = fitz.open(file_path)
    total_pages = len(doc)
    
    for page_index in range(total_pages):
        page = doc[page_index]
        raw_text = page.get_text("text")
        
        # 1. Öncelik: Vektörel Metin Kontrolü (Hızlı, Ücretsiz)
        if is_vector_text(raw_text):
            cleaned = clean_text(raw_text)
            chunks.append({
                "content": cleaned,
                "metadata": {
                    "source": file_name,
                    "file_type": "pdf",
                    "page": page_index + 1,
                    "total_pages": total_pages,
                    "is_ocr": False,
                }
            })
            continue

        # 2. Öncelik: Taranmış / Fotoğraflı Sayfa için OCR Fallback
        if enable_ocr:
            ocr_text = ocr_page_with_gemini(page, file_name, page_index)
            if ocr_text and len(ocr_text) >= 20:
                chunks.append({
                    "content": ocr_text,
                    "metadata": {
                        "source": file_name,
                        "file_type": "pdf",
                        "page": page_index + 1,
                        "total_pages": total_pages,
                        "is_ocr": True,
                    }
                })
                
    doc.close()
    return chunks


def parse_pptx(file_path: str) -> List[Dict[str, Any]]:
    """
    PowerPoint (.pptx) sunumunu slayt slayt okur.
    Başlık ve metin kutularını sırayla birleştirir.
    """
    if Presentation is None:
        raise ImportError("python-pptx kütüphanesi yüklü değil.")

    chunks = []
    file_name = os.path.basename(file_path)
    
    prs = Presentation(file_path)
    total_slides = len(prs.slides)
    
    for slide_index, slide in enumerate(prs.slides):
        slide_texts = []
        
        # Slayttaki tüm şekilleri (şekil, metin kutusu, tablo) tara
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    line = paragraph.text.strip()
                    if line:
                        slide_texts.append(line)
            elif shape.has_table:
                # Tablo hücrelerini oku
                for row in shape.table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        slide_texts.append(" | ".join(row_texts))

        raw_text = "\n".join(slide_texts)
        cleaned = clean_text(raw_text)

        if len(cleaned) < 25:
            continue

        chunks.append({
            "content": cleaned,
            "metadata": {
                "source": file_name,
                "file_type": "pptx",
                "page": slide_index + 1,  # Slayt numarası
                "total_pages": total_slides,
                "is_ocr": False,
            }
        })
        
    return chunks


def parse_document(file_path: str, enable_ocr: bool = True) -> List[Dict[str, Any]]:
    """Dosya uzantısına göre uygun ayrıştırıcıyı çağırır."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return parse_pdf(file_path, enable_ocr=enable_ocr)
    elif ext == ".pptx":
        return parse_pptx(file_path)
    else:
        print(f"[UYARI] Desteklenmeyen dosya türü: {file_path}")
        return []

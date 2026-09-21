"""
Diş Hekimliği RAG Asistanı - Yüksek Okunabilirlik & Ferah Arayüz.
Tasarım Prensipleri:
- Sıfır çakışma (No layout collision): Yerel Streamlit bileşenleriyle kusursuz uyum
- Yüksek kontrast, yormayan tipografi (1.7 satır aralığı, net metinler)
- Tıbbi bülten ve akademik referans sadeliği
- Mobil ve masaüstünde mükemmel okuma konforu
"""

import streamlit as st
import os
from dotenv import load_dotenv

from rag_engine import RAGEngine
from indexer import get_chroma_collection

load_dotenv()

# Sayfa Ayarları
st.set_page_config(
    page_title="Diş Hekimliği Asistanı",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Temiz & Ferah Tipografi (Bozucu !important kuralları kaldırıldı)
st.markdown("""
<style>
    /* Tipografi ve Rahat Okuma */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Rahat okuma için satır aralıkları */
    .stMarkdown p {
        font-size: 1.02rem;
        line-height: 1.75;
        color: #1E293B;
        margin-bottom: 0.8rem;
    }
    .stMarkdown li {
        font-size: 1.02rem;
        line-height: 1.7;
        color: #1E293B;
        margin-bottom: 0.4rem;
    }
    .stMarkdown h3, .stMarkdown h4 {
        color: #0F172A;
        font-weight: 700;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
    }

    /* Başlık Alanı */
    .hero-container {
        text-align: center;
        padding: 1.5rem 0 1.2rem 0;
        border-bottom: 1px solid #F1F5F9;
        margin-bottom: 1.5rem;
    }
    .hero-pill {
        display: inline-block;
        background-color: #E0F2FE;
        color: #0369A1;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 9999px;
        margin-bottom: 0.6rem;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin: 0.2rem 0 0.4rem 0;
    }
    .hero-desc {
        color: #64748B;
        font-size: 0.98rem;
        margin: 0;
    }

    /* Kaynak Kartları */
    .citation-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .citation-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .citation-title {
        font-weight: 600;
        color: #0F172A;
        font-size: 0.88rem;
    }
    .citation-tag {
        background-color: #F1F5F9;
        color: #334155;
        font-weight: 600;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .citation-text {
        font-size: 0.84rem;
        color: #475569;
        line-height: 1.55;
        border-left: 2px solid #0284C7;
        padding-left: 10px;
        margin-top: 4px;
        font-style: italic;
    }

    /* Menü Fazlalıklarını Gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_engine():
    return RAGEngine()


def main():
    # Toplam doküman sayısı
    try:
        col = get_chroma_collection()
        total_chunks = col.count()
    except Exception:
        total_chunks = 870

    # Yan Menü (Minimalist & Net)
    with st.sidebar:
        st.subheader("📚 Filtre ve Ayarlar")
        categories = [
            "Tümü",
            "Endodonti",
            "Restoratif Diş Tedavisi",
            "Protetik Diş Tedavisi",
            "Ortodonti",
            "Pedodonti / Davranış Yönetimi",
            "Ağız, Diş ve Çene Radyolojisi & Cerrahisi",
            "Genel Diş Hekimliği"
        ]
        selected_category = st.selectbox(
            "Ders / Alan",
            categories,
            help="Sadece seçtiğiniz derse ait slaytların taranmasını sağlar."
        )

        st.divider()
        if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.caption(f"Veritabanı: {total_chunks} slayt hazır")

    # Üst Başlık Alanı
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-pill">● {total_chunks} Slayt İndeksli &bull; {selected_category}</div>
        <div class="hero-title">🦷 Diş Hekimliği Asistanı</div>
        <div class="hero-desc">Ders notları, slaytlar ve klinik arşivden doğrulanmış kaynaklı yanıtlar.</div>
    </div>
    """, unsafe_allow_html=True)

    # Sohbet Geçmişi
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # İlk Açılış Örnek Sorular (Sohbet başlayınca otomatik gizlenir)
    quick_prompt = None
    if len(st.session_state.messages) == 0:
        st.markdown("<p style='text-align:center; color:#64748B; font-size:0.9rem; margin-bottom:12px;'>Örnek Konular:</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔬 Biyopsi endikasyonları nelerdir?", use_container_width=True):
                quick_prompt = "Oral lezyonlarda biyopsi endikasyonları ve cerrahi yaklaşım nedir?"
            if st.button("🦷 Kök kanal patları ve özellikleri?", use_container_width=True):
                quick_prompt = "Kök kanal dolgu maddeleri, kanal patları ve özellikleri nelerdir?"
        with col2:
            if st.button("⚡ Dentin hassasiyeti ve mekanizması?", use_container_width=True):
                quick_prompt = "Dentin hassasiyetinin oluşum mekanizmaları ve hidrodinamik teori nedir?"
            if st.button("📋 Tam protezlerin teslimi ve bakımı?", use_container_width=True):
                quick_prompt = "Tam protezlerin teslimi ve bakımı nasıl yapılır?"

    # Mesaj Akışı
    for msg in st.session_state.messages:
        avatar = "🧑‍⚕️" if msg["role"] == "user" else "🦷"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
            # Kaynak Referansları
            if "sources" in msg and msg["sources"]:
                with st.expander(f"📚 Kaynak Referansları ({len(msg['sources'])} Slayt)"):
                    for s in msg["sources"]:
                        st.markdown(f"""
                        <div class="citation-card">
                            <div class="citation-header">
                                <span class="citation-title">📄 {s['source']}</span>
                                <span class="citation-tag">Slayt / Sayfa {s['page']} &bull; {s['category']}</span>
                            </div>
                            <div class="citation-text">
                                "{s['snippet']}"
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # Soru Giriş Alanı
    user_input = st.chat_input("Ders notları hakkında sorunuzu yazın...")
    prompt_to_use = quick_prompt or user_input

    if prompt_to_use:
        # Kullanıcı mesajını ekle
        st.session_state.messages.append({"role": "user", "content": prompt_to_use})
        with st.chat_message("user", avatar="🧑‍⚕️"):
            st.markdown(prompt_to_use)

        # Asistan yanıtını üret
        with st.chat_message("assistant", avatar="🦷"):
            with st.spinner("İlgili slaytlar taranıyor ve doğrulanmış yanıt hazırlanıyor..."):
                engine = load_engine()
                result = engine.ask(prompt_to_use, category_filter=selected_category)
                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)

                if sources:
                    with st.expander(f"📚 Kaynak Referansları ({len(sources)} Slayt)"):
                        for s in sources:
                            st.markdown(f"""
                            <div class="citation-card">
                                <div class="citation-header">
                                    <span class="citation-title">📄 {s['source']}</span>
                                    <span class="citation-tag">Slayt / Sayfa {s['page']} &bull; {s['category']}</span>
                                </div>
                                <div class="citation-text">
                                    "{s['snippet']}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
        st.rerun()


if __name__ == "__main__":
    main()

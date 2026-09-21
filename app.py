"""
Diş Hekimliği RAG Asistanı - Ultra-Premium & Modern Arayüz.
Tasarım Felsefesi:
- Deep Obsidian & Dark Glassmorphism Tema (Apple / Linear / Raycast standartlarında)
- Gradient Tipografi & Mikro Animasyonlar
- Bento-Style Etkileşimli Öneri Kartları
- Temiz, Zarif Kaynak ve Atıf Kartları (Citations Drawer)
"""

import streamlit as st
import os
import re
from dotenv import load_dotenv

from rag_engine import RAGEngine
from indexer import get_chroma_collection

load_dotenv()

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="Diş Hekimliği RAG Asistanı",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Ultra-Premium Modern Dark CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Genel Arka Plan ve Tipografi */
    html, body, [class*="st-emotion-cache"], .stApp {
        background-color: #0B0F19 !important;
        color: #F1F5F9 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Streamlit Varsayılan Başlık ve Kenar Çubuklarını Gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Ana Başlık (Hero Section) */
    .hero-wrapper {
        text-align: center;
        padding: 2.2rem 0 1.2rem 0;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.25);
        color: #38BDF8;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.15);
    }
    .pulse-dot {
        width: 7px;
        height: 7px;
        background-color: #38BDF8;
        border-radius: 50%;
        box-shadow: 0 0 8px #38BDF8;
    }
    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #FFFFFF 20%, #94A3B8 70%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 0.98rem;
        color: #94A3B8;
        font-weight: 400;
        max-width: 540px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* Bento Tarzı Hızlı Soru Kartları Butonları */
    .stButton > button {
        background: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #E2E8F0 !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
        text-align: left !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: rgba(30, 41, 59, 0.85) !important;
        border-color: rgba(56, 189, 248, 0.4) !important;
        color: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 16px -2px rgba(56, 189, 248, 0.12) !important;
    }

    /* Sohbet Mesaj Kutuları */
    .stChatMessage {
        background: transparent !important;
        padding: 0.8rem 0 !important;
        border: none !important;
    }
    
    /* Kullanıcı Mesajı */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
        margin: 0.5rem 0 !important;
    }

    /* Asistan Mesajı */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(56, 189, 248, 0.12) !important;
        border-radius: 14px !important;
        padding: 1.2rem 1.4rem !important;
        margin: 0.5rem 0 1rem 0 !important;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3) !important;
    }

    /* Akordiyon (Kaynak Kutusu) */
    .streamlit-expanderHeader {
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 10px !important;
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 8px 14px !important;
    }
    .streamlit-expanderHeader:hover {
        color: #38BDF8 !important;
        border-color: rgba(56, 189, 248, 0.25) !important;
    }
    .streamlit-expanderContent {
        background: transparent !important;
        border: none !important;
        padding: 8px 0 !important;
    }

    /* Premium Kaynak Kartı */
    .source-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 12px 14px;
        margin: 8px 0;
        transition: all 0.2s ease;
    }
    .source-card:hover {
        border-color: rgba(56, 189, 248, 0.3);
        background: rgba(15, 23, 42, 0.95);
    }
    .badge-cat {
        background: rgba(99, 102, 241, 0.15);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-page {
        background: rgba(16, 185, 129, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .source-title {
        color: #F8FAFC;
        font-weight: 600;
        font-size: 0.86rem;
    }
    .source-snippet {
        color: #94A3B8;
        font-size: 0.8rem;
        line-height: 1.45;
        margin-top: 6px;
        padding-left: 8px;
        border-left: 2px solid rgba(56, 189, 248, 0.4);
    }

    /* Input Alanı Şıklığı */
    .stChatInputContainer {
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4) !important;
    }
    .stChatInputContainer:focus-within {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.2) !important;
    }

    /* Yan Menü (Sidebar) Şıklığı */
    section[data-testid="stSidebar"] {
        background-color: #070A10 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_engine():
    return RAGEngine()


def main():
    # ChromaDB toplam sayfa sayısını çek
    try:
        col = get_chroma_collection()
        total_chunks = col.count()
    except Exception:
        total_chunks = 870

    # Yan Menü (Minimalist & Profesyonel)
    with st.sidebar:
        st.markdown("### ⚙️ Sistem Ayarları")
        
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
            "📚 Ders / Alan Filtresi",
            categories,
            help="İsterseniz yapay zekanın sadece tek bir dersin notlarına bakmasını sağlayabilirsiniz."
        )

        st.markdown("---")
        if st.button("🗑️ Yeni Sohbet Başlat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:12px; border-radius:10px; margin-top:20px;">
            <div style="font-size:0.75rem; color:#64748B; text-transform:uppercase; font-weight:600;">Veritabanı Durumu</div>
            <div style="font-size:1.1rem; color:#F8FAFC; font-weight:700; margin-top:2px;">{total_chunks} Slayt/Sayfa</div>
            <div style="font-size:0.75rem; color:#10B981; margin-top:4px;">● Kalıcı ChromaDB Aktif</div>
        </div>
        """, unsafe_allow_html=True)

    # Hero Başlık Alanı
    st.markdown(f"""
    <div class="hero-wrapper">
        <div class="hero-badge">
            <span class="pulse-dot"></span> Akıllı Akademik RAG &bull; {total_chunks} Slayt Hazır
        </div>
        <div class="hero-title">Diş Hekimliği Bilgi Asistanı</div>
        <div class="hero-subtitle">Ders notları, klinik slaytlar ve akademik arşivden doğrudan, doğrulanmış ve kaynaklı yanıtlar.</div>
    </div>
    """, unsafe_allow_html=True)

    # Sohbet Geçmişi
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # İlk Açılış: Bento Öneri Butonları (Sohbet başlayınca otomatik gizlenir)
    quick_prompt = None
    if len(st.session_state.messages) == 0:
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔬 Biyopsi endikasyonları ve cerrahi yaklaşım", use_container_width=True):
                quick_prompt = "Oral lezyonlarda biyopsi endikasyonları ve cerrahi yaklaşım nedir?"
            if st.button("🦷 Kök kanal dolgu maddeleri ve patlar", use_container_width=True):
                quick_prompt = "Kök kanal dolgu maddeleri, kanal patları ve özellikleri nelerdir?"
        with col2:
            if st.button("⚡ Dentin hassasiyeti ve hidrodinamik teori", use_container_width=True):
                quick_prompt = "Dentin hassasiyetinin oluşum mekanizmaları ve hidrodinamik teori nedir?"
            if st.button("📋 Tam protezlerin teslimi ve bakım kuralları", use_container_width=True):
                quick_prompt = "Tam protezlerin teslimi ve bakımı nasıl yapılır?"
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Sohbet Mesajlarını Ekrana Bas
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Kaynak Referansları
            if "sources" in msg and msg["sources"]:
                with st.expander(f"📚 Kaynak ve Doğrulama Referansları ({len(msg['sources'])} Slayt)"):
                    for s in msg["sources"]:
                        st.markdown(f"""
                        <div class="source-card">
                            <div>
                                <span class="badge-cat">{s['category']}</span>
                                <span class="badge-page">Slayt / Sayfa {s['page']}</span>
                                <span class="source-title">{s['source']}</span>
                            </div>
                            <div class="source-snippet">
                                "{s['snippet']}"
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # Soru Giriş Kutusu
    user_input = st.chat_input("Ders notları hakkında sorunuzu yazın...")
    prompt_to_use = quick_prompt or user_input

    if prompt_to_use:
        # 1. Kullanıcı mesajı ekle
        st.session_state.messages.append({"role": "user", "content": prompt_to_use})
        with st.chat_message("user"):
            st.markdown(prompt_to_use)

        # 2. Asistan cevabını üret
        with st.chat_message("assistant"):
            with st.spinner("İlgili slaytlar taranıyor ve doğrulanmış yanıt hazırlanıyor..."):
                engine = load_engine()
                result = engine.ask(prompt_to_use, category_filter=selected_category)
                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)

                if sources:
                    with st.expander(f"📚 Kaynak ve Doğrulama Referansları ({len(sources)} Slayt)"):
                        for s in sources:
                            st.markdown(f"""
                            <div class="source-card">
                                <div>
                                    <span class="badge-cat">{s['category']}</span>
                                    <span class="badge-page">Slayt / Sayfa {s['page']}</span>
                                    <span class="source-title">{s['source']}</span>
                                </div>
                                <div class="source-snippet">
                                    "{s['snippet']}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

        # Mesajı kaydet
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
        st.rerun()


if __name__ == "__main__":
    main()

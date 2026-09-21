"""
Diş Hekimliği RAG Asistanı - Göz Yormayan Sade Arayüz.
Özellikler:
- Göz yormayan yumuşak koyu tema (Soft Slate / Dark Charcoal)
- Doğrudan cevabı panoya kopyalama butonu (Tek tıkla kopyalama)
- Sade, ferah ve okunması kolay tipografi
- Kaynak referansları için temiz kartlar
"""

import streamlit as st
import streamlit.components.v1 as components
import json
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

# Göz Yormayan, Sade ve Ferah Stil
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Uzun okumalar için göz yormayan yumuşak metin ve ferah satır aralığı */
    .stMarkdown p {
        font-size: 1.02rem !important;
        line-height: 1.8 !important;
        color: #E2E8F0 !important;
        margin-bottom: 0.8rem !important;
    }
    .stMarkdown li {
        font-size: 1.02rem !important;
        line-height: 1.75 !important;
        color: #E2E8F0 !important;
        margin-bottom: 0.4rem !important;
    }
    .stMarkdown strong {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* Sade Başlık Alanı */
    .hero-box {
        text-align: center;
        padding: 1.8rem 0 1rem 0;
        margin-bottom: 1.2rem;
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #F8FAFC;
        letter-spacing: -0.02em;
        margin-bottom: 0.3rem;
    }
    .hero-desc {
        color: #94A3B8;
        font-size: 0.95rem;
        font-weight: 400;
        margin: 0;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(56, 189, 248, 0.12);
        color: #38BDF8;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        margin-bottom: 0.5rem;
    }

    /* Sade Kaynak Kartı */
    .source-item {
        background: #182032;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .source-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .source-name {
        font-size: 0.86rem;
        font-weight: 600;
        color: #F1F5F9;
    }
    .source-pill {
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 4px;
    }
    .source-quote {
        font-size: 0.82rem;
        color: #94A3B8;
        line-height: 1.5;
        border-left: 2px solid #38BDF8;
        padding-left: 8px;
        margin-top: 5px;
        font-style: italic;
    }

    /* Menü Fazlalıklarını Gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def render_copy_button(text_to_copy: str, btn_id: str):
    """Tek tıkla panoya kopyalama butonu (Sayfa yenilenmez)."""
    escaped = json.dumps(text_to_copy)
    html_code = f"""
    <div style="display:flex; justify-content:flex-end; margin: 4px 0 8px 0;">
        <button id="copy_{btn_id}" onclick="copyToClipboard_{btn_id}()" 
            style="background: #182032; color: #94A3B8; border: 1px solid rgba(255,255,255,0.12); padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; font-family: sans-serif; transition: all 0.2s;">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span id="label_{btn_id}">Cevabı Kopyala</span>
        </button>
    </div>
    <script>
    function copyToClipboard_{btn_id}() {{
        const text = {escaped};
        navigator.clipboard.writeText(text).then(function() {{
            const btn = document.getElementById('copy_{btn_id}');
            const label = document.getElementById('label_{btn_id}');
            label.innerText = '✓ Kopyalandı!';
            btn.style.color = '#34D399';
            btn.style.borderColor = '#10B981';
            setTimeout(function() {{
                label.innerText = 'Cevabı Kopyala';
                btn.style.color = '#94A3B8';
                btn.style.borderColor = 'rgba(255,255,255,0.12)';
            }}, 2000);
        }}).catch(function(err) {{
            console.error('Kopyalama hatası:', err);
        }});
    }}
    </script>
    """
    components.html(html_code, height=38)


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

    # Sade Yan Menü
    with st.sidebar:
        st.subheader("📚 Ayarlar")
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
            "Ders / Alan Filtresi",
            categories,
            help="İsteğe bağlı olarak aramayı tek bir derse daraltabilirsiniz."
        )

        st.divider()
        if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.caption(f"Veritabanı: {total_chunks} slayt hazır")

    # Sade Başlık
    st.markdown(f"""
    <div class="hero-box">
        <div class="hero-badge">● {total_chunks} Slayt Hazır &bull; {selected_category}</div>
        <div class="hero-title">🦷 Diş Hekimliği Asistanı</div>
        <div class="hero-desc">Ders notları, sunum slaytları ve klinik arşivden doğrulanmış yanıtlar.</div>
    </div>
    """, unsafe_allow_html=True)

    # Sohbet Geçmişi
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # İlk Açılış: Örnek Sorular (Sohbet başlayınca kaybolur)
    quick_prompt = None
    if len(st.session_state.messages) == 0:
        st.markdown("<p style='text-align:center; color:#94A3B8; font-size:0.88rem; margin-bottom:12px;'>Hızlı Başlangıç Konuları:</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔬 Biyopsi endikasyonları nelerdir?", use_container_width=True):
                quick_prompt = "Oral lezyonlarda biyopsi endikasyonları ve cerrahi yaklaşım nedir?"
            if st.button("🦷 Kök kanal dolgu patları?", use_container_width=True):
                quick_prompt = "Kök kanal dolgu maddeleri, kanal patları ve özellikleri nelerdir?"
        with col2:
            if st.button("⚡ Dentin hassasiyeti teorileri?", use_container_width=True):
                quick_prompt = "Dentin hassasiyetinin oluşum mekanizmaları ve hidrodinamik teori nedir?"
            if st.button("📋 Tam protezlerin teslimi ve bakımı?", use_container_width=True):
                quick_prompt = "Tam protezlerin teslimi ve bakımı nasıl yapılır?"

    # Mesaj Akışı
    for idx, msg in enumerate(st.session_state.messages):
        avatar = "🧑‍⚕️" if msg["role"] == "user" else "🦷"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
            # Asistan mesajlarında Kopyalama Butonu ve Kaynaklar
            if msg["role"] == "assistant":
                render_copy_button(msg["content"], f"msg_{idx}")

                if "sources" in msg and msg["sources"]:
                    with st.expander(f"📚 Kaynak Referansları ({len(msg['sources'])} Slayt)"):
                        for s in msg["sources"]:
                            st.markdown(f"""
                            <div class="source-item">
                                <div class="source-header">
                                    <span class="source-name">📄 {s['source']}</span>
                                    <span class="source-pill">Slayt {s['page']} &bull; {s['category']}</span>
                                </div>
                                <div class="source-quote">
                                    "{s['snippet']}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

    # Soru Giriş Kutusu
    user_input = st.chat_input("Ders notları veya slaytlar hakkında sorunuzu yazın...")
    prompt_to_use = quick_prompt or user_input

    if prompt_to_use:
        # 1. Kullanıcı mesajını ekle
        st.session_state.messages.append({"role": "user", "content": prompt_to_use})
        with st.chat_message("user", avatar="🧑‍⚕️"):
            st.markdown(prompt_to_use)

        # 2. Asistan cevabını üret
        with st.chat_message("assistant", avatar="🦷"):
            with st.spinner("İlgili slaytlar taranıyor ve doğrulanmış yanıt hazırlanıyor..."):
                engine = load_engine()
                # Önceki mesajları bağlam olarak ilet
                history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
                result = engine.ask(prompt_to_use, chat_history=history, category_filter=selected_category)
                answer = result["answer"]
                sources = result["sources"]

                st.markdown(answer)
                render_copy_button(answer, f"new_{len(st.session_state.messages)}")

                if sources:
                    with st.expander(f"📚 Kaynak Referansları ({len(sources)} Slayt)"):
                        for s in sources:
                            st.markdown(f"""
                            <div class="source-item">
                                <div class="source-header">
                                    <span class="source-name">📄 {s['source']}</span>
                                    <span class="source-pill">Slayt {s['page']} &bull; {s['category']}</span>
                                </div>
                                <div class="source-quote">
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

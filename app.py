import os

import streamlit as st
from dotenv import load_dotenv

from rag_chatbot import (
    KNOWLEDGE_DIR,
    SYSTEM_PROMPT_PATH,
    TOP_K,
    buat_model,
    muat_dokumen,
    bangun_vectorstore,
    muat_system_prompt,
    buat_rag_chain,
)


# ============================================================
# 1. PENGATURAN HALAMAN
# ============================================================
# Wajib jadi perintah Streamlit pertama: judul tab browser dan ikonnya.

st.set_page_config(
    page_title="WhoAmAI",
    page_icon=":material/gavel:",
)

# ============================================================
# 2. CEK API KEY
# ============================================================
# Di laptop, GROQ_API_KEY dibaca dari file .env.
# Di Streamlit Cloud, GROQ_API_KEY diisi lewat menu Secrets, dan Streamlit
# otomatis menjadikannya environment variable. Jadi kode yang sama ini
# jalan di dua tempat tanpa perlu diubah.

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    st.error(
        "GROQ_API_KEY belum diisi. Cek file .env (di laptop) "
        "atau menu Secrets (di Streamlit Cloud)."
    )
    st.stop()

    # ============================================================
# 3. SIAPKAN MESIN CHATBOT (sekali saja, lalu disimpan)
# ============================================================
# Streamlit menjalankan ulang SELURUH file ini dari atas setiap kali
# pengguna berinteraksi (misalnya mengirim pertanyaan).
# @st.cache_resource membuat fungsi di bawah ini cukup dijalankan SEKALI.
# Hasilnya disimpan, lalu dipakai ulang, sehingga dokumen tidak dimuat
# ulang dan vector store tidak dibangun ulang di setiap pertanyaan.

@st.cache_resource(show_spinner="Menyiapkan chatbot, mohon tunggu sebentar...")
def siapkan_chatbot():
    model = buat_model()
    dokumen = muat_dokumen(KNOWLEDGE_DIR)
    vectorstore = bangun_vectorstore(dokumen)
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    system_prompt = muat_system_prompt(SYSTEM_PROMPT_PATH)
    return buat_rag_chain(retriever, model, system_prompt)


rag_chain = siapkan_chatbot()


# ============================================================
# 4. BUKU CATATAN PERCAKAPAN
# ============================================================
# st.session_state adalah tempat menyimpan data yang tidak ikut hilang
# saat file ini dijalankan ulang. Di sini dipakai untuk mencatat riwayat
# percakapan: siapa yang bicara ("user" atau "assistant") dan isinya.
# Sama saja dengan menjaga percakapan terus muncul di atas chat baru

if "riwayat" not in st.session_state:
    st.session_state.riwayat = []

# ============================================================
# 5. TAMPILAN
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="margin-bottom: 0.8rem; color: #f1f5f9; font-size: 1.25rem;
                    font-weight: 700;">
            Tentang chatbot ini
        </div>
        <div style="color: #d5dbe3; font-size: 0.92rem; line-height: 1.6;">
            Chatbot ini menjawab pertanyaan tentang siapa itu
            <strong style="color: #ffffff;">Ralief Langga Rivansyah</strong>.
        </div>
        <div style="margin-top: 0.65rem; margin-bottom: 0.65rem; color: #9da7b3; font-size: 0.8rem;
                    line-height: 1.5;">
            Jawaban hanya diambil dari dokumen sumber, bukan dari internet.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Mulai percakapan baru"):
        st.session_state.riwayat = []

st.markdown(
    """
    <h1 style="margin: 0; text-align: center; font-weight: 800;
               letter-spacing: -0.035em;
               background: linear-gradient(180deg, #FFFDF8, #FCD34D, #F59E0B);
               -webkit-background-clip: text; background-clip: text;
               -webkit-text-fill-color: transparent;">
        WhoAmAI
    </h1>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div style="margin: 0.25rem 0 1.25rem; color: #9da7b3;
                font-size: 1rem; text-align: center;">
        Tanyakan apa saja seputar Ralief Langga Rivansyah.
    </div>
    """,
    unsafe_allow_html=True,
)

# Salam pembuka, selalu tampil paling atas.
st.markdown(
    """
    <div style="margin: 1.25rem 0 1.5rem; padding: 1rem 1.15rem;
                border: 1px solid rgba(245, 158, 11, 0.28);
                border-radius: 0.9rem; color: #fef3c7;
                background-color: rgba(120, 74, 24, 0.38);
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
                line-height: 1.55;">
        Silakan ajukan pertanyaan. Contoh:
        <em>Siapa itu Ralief Langga Rivansyah?</em>
    </div>
    """,
    unsafe_allow_html=True,
)

# Tampilkan ulang seluruh riwayat percakapan dari buku catatan.
for pesan in st.session_state.riwayat:
    with st.chat_message(pesan["role"]):
        st.markdown(pesan["isi"])


# ============================================================
# 6. TANYA JAWAB
# ============================================================

pertanyaan = st.chat_input("Tulis pertanyaan Anda di sini...")

if pertanyaan:
    # Tampilkan pertanyaan, lalu catat ke buku catatan.
    with st.chat_message("user"):
        st.markdown(pertanyaan)
    st.session_state.riwayat.append({"role": "user", "isi": pertanyaan})

    # Minta jawaban ke mesin RAG. .stream() + st.write_stream() membuat
    # jawaban muncul bertahap, kata demi kata, seperti sedang diketik.
    with st.chat_message("assistant"):
        with st.spinner("Mencari jawaban di dokumen..."):
            jawaban = st.write_stream(rag_chain.stream(pertanyaan))
    st.session_state.riwayat.append({"role": "assistant", "isi": jawaban})
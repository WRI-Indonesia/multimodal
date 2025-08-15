import streamlit as st
from openai import OpenAI
import time
import math

# for evaluation
import sacrebleu
from bert_score import score

# ─────────────────────────────────────────────────────────────────────
# CONFIGURATION & UTILITIES
# ─────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def init_client(key_path: str, base_url: str):
    try:
        key = open(key_path, "r").read().strip()
    except Exception as e:
        st.error(f"Gagal membaca API key: {e}")
        st.stop()
    try:
        return OpenAI(api_key=key, base_url=base_url)
    except Exception as e:
        st.error(f"Gagal inisialisasi client: {e}")
        st.stop()

def type_writer(text: str, delay: float = 0.01):
    placeholder = st.empty()
    buf = ""
    for ch in text:
        buf += ch
        placeholder.markdown(
            "<div style='white-space: pre-wrap; font-size:16px; "
            "padding:1rem; background:#f4f4f4; border-radius:8px; "
            "line-height:1.5;'>"
            f"{buf}</div>",
            unsafe_allow_html=True
        )
        time.sleep(delay)

def show_text_block(text: str):
    # Fast renderer for long outputs (no typewriter)
    st.markdown(
        "<div style='white-space: pre-wrap; font-size:16px; "
        "padding:1rem; background:#f4f4f4; border-radius:8px; line-height:1.5;'>"
        f"{text}</div>",
        unsafe_allow_html=True
    )

def safe_usage(usage):
    # Normalize usage object; handle providers that omit fields
    try:
        pt = getattr(usage, "prompt_tokens", 0) or 0
        ct = getattr(usage, "completion_tokens", 0) or 0
        tt = getattr(usage, "total_tokens", pt + ct) or (pt + ct)
    except Exception:
        pt, ct, tt = 0, 0, 0
    return pt, ct, tt

# ─────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT (FULL, SINGLE STYLE) & FEW-SHOTS
# ─────────────────────────────────────────────────────────────────────

SYSTEM_MESSAGE_FULL = {
    "role": "system",
    "content": (
        "You are a Natural Resources Specialist with a cross-disciplinary background in ecology, "
        "environmental management, social and economic systems, remote sensing, and forestry. "
        "You bring integrative perspectives to landscape-level interventions and sustainability projects.\n\n"
        "Your task is to translate English into Indonesian as publication-ready, domain-accurate prose. "
        "Follow these guidelines:\n"
        "1) Preserve all original meaning, context, and nuance.\n"
        "2) Render environmental and technical terms precisely, using idiomatic Indonesian preferred in professional and academic publications.\n"
        "3) Use varied academic connectors for a smooth, natural flow between ideas.\n"
        "4) Maintain clarity, conciseness, and logical structure, even for complex sentences.\n"
        "5) Avoid overly literal, word-for-word phrasing that sounds unnatural."
    )
}

FEW_SHOT_EXAMPLES = [
    {"role": "user", "content": "Mangrove restoration reduces coastal erosion risk."},
    {"role": "assistant", "content": "Restorasi mangrove mengurangi risiko abrasi pantai."},

    {"role": "user", "content": "Water governance improves basin-wide allocation efficiency."},
    {"role": "assistant", "content": "Tata kelola sumber daya air meningkatkan efisiensi alokasi pada skala daerah aliran sungai."},

    {"role": "user", "content": "Results suggest that community forestry may enhance livelihood resilience."},
    {"role": "assistant", "content": "Hasil menunjukkan bahwa kehutanan berbasis masyarakat dapat meningkatkan ketangguhan mata pencaharian."},

    {"role": "user", "content": "REDD+ requires robust MRV to ensure emissions reductions are credible."},
    {"role": "assistant", "content": "REDD+ memerlukan MRV (Measurement, Reporting, and Verification) yang andal agar penurunan emisi kredibel."},

    {"role": "user", "content": "Peat subsidence averaged 3.1 ± 0.4 cm yr−1 between 2015–2020."},
    {"role": "assistant", "content": "Rata-rata penurunan permukaan gambut sebesar 3,1 ± 0,4 cm per tahun selama 2015–2020."},

    {"role": "user", "content": "Protected status alone does not guarantee biodiversity outcomes."},
    {"role": "assistant", "content": "Status kawasan lindung saja tidak menjamin capaian keanekaragaman hayati."},

    {"role": "user", "content": "Land-cover maps were derived from Sentinel-2 imagery and validated using 1,200 field points."},
    {"role": "assistant", "content": "Peta tutupan lahan diturunkan dari citra Sentinel-2 dan divalidasi menggunakan 1.200 titik lapangan."},

    {"role": "user", "content": "Nature-based solutions can lower flood risk while delivering co-benefits [23]."},
    {"role": "assistant", "content": "Solusi berbasis alam dapat menurunkan risiko banjir sekaligus memberikan ko-manfaat [23]."},

    {"role": "user", "content": "Key drivers include: (i) commodity prices, (ii) road expansion, and (iii) weak enforcement."},
    {"role": "assistant", "content": "Pendorong utama meliputi: (i) harga komoditas, (ii) perluasan jalan, dan (iii) lemahnya penegakan hukum."},

    {"role": "user", "content": "We sampled in the Kapuas Hulu Regency, West Kalimantan, Indonesia."},
    {"role": "assistant", "content": "Kami melakukan pengambilan sampel di Kabupaten Kapuas Hulu, Kalimantan Barat, Indonesia."}
]

# ─────────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="AI Translator + Metrics", layout="wide")
st.title("AI Translations Project")

client = init_client("keys/opdeepseek.txt", "https://openrouter.ai/api/v1")

# ─────────────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────────────────────────────

st.sidebar.header("Settings")
model_options = {
    "DeepSeek Chat V3":   "deepseek/deepseek-chat-v3-0324:free",
    "GPT-3.5 Turbo":      "openai/gpt-3.5-turbo",
    "GPT-4":              "openai/gpt-4",
    "GPT-4.1":            "openai/gpt-4.1",
    "GPT-4o-mini":        "openai/gpt-4o-mini",
    "Gemini Flash 2.0":   "google/gemini-2.0-flash-001",
}
selected_model = st.sidebar.selectbox("Model AI", list(model_options.keys()))
model_id = model_options[selected_model]

temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
top_p       = st.sidebar.slider("Top-p",       0.1, 1.0, 0.9, 0.05)
seed        = st.sidebar.number_input("Seed (for reproducibility)", min_value=0, value=42, step=1)
use_typewriter = st.sidebar.checkbox("Typewriter effect", value=True)

# cost rates for known models (USD per token)
# NOTE: providers report costs in different units; these are best-effort.
cost_rates = {
    "openai/gpt-4o-mini": (0.15/1e6, 0.60/1e6),  # per million tokens
    "openai/gpt-4":       (0.03/1e3, 0.06/1e3),  # per thousand tokens
    "openai/gpt-4.1":     (0.03/1e3, 0.06/1e3),  # per thousand tokens
}

# ─────────────────────────────────────────────────────────────────────
# TRANSLATION FUNCTION
# ─────────────────────────────────────────────────────────────────────

def translate_environmental(text: str, model: str, temp: float, p: float, seed: int):
    system_msg = SYSTEM_MESSAGE_FULL
    user_msg = {"role": "user", "content": text}
    messages = [system_msg, *FEW_SHOT_EXAMPLES, user_msg]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temp,
        top_p=p,
        seed=seed
    )
    fingerprint = getattr(resp, "system_fingerprint", None)
    return resp.choices[0].message.content, resp.usage, fingerprint

# ─────────────────────────────────────────────────────────────────────
# MAIN INTERFACE
# ─────────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["Translate & Evaluate", "Evaluate Only"])

with tab1:
    source = st.text_area("Enter English source text here:", height=200, key="source_text")
    reference = st.text_area("Enter reference Indonesian translation (optional):", height=200, key="ref_text")

    if st.button("Translate & Evaluate", type="primary"):
        if not source.strip():
            st.warning("Please enter source text.")
        else:
            with st.spinner(f"Translating via {selected_model}…"):
                start = time.monotonic()
                try:
                    result, usage, fingerprint = translate_environmental(
                        source, model_id, temperature, top_p, seed
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.stop()
                elapsed = time.monotonic() - start

                # Display translation
                st.subheader("Model Translation")
                if use_typewriter and len(source) <= 2000:
                    type_writer(result)
                else:
                    show_text_block(result)

                # Copy / Download helpers
                st.download_button(
                    "Download translation (.txt)",
                    data=result,
                    file_name="translation_id.txt",
                    mime="text/plain"
                )
                st.text_area("Quick copy buffer (Ctrl/Cmd+C):", value=result, height=150)

                # Token, cost & speed metrics
                prompt_tokens, completion_tokens, total_tokens = safe_usage(usage)
                in_rate, out_rate = cost_rates.get(model_id, (0.0, 0.0))
                prompt_cost     = prompt_tokens     * in_rate
                completion_cost = completion_tokens * out_rate
                total_cost      = prompt_cost + completion_cost

                with st.expander("Token, Cost & Speed Metrics", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Prompt Tokens",     prompt_tokens)
                    c2.metric("Completion Tokens", completion_tokens)
                    c3.metric("Total Tokens",      total_tokens)

                    c4, c5, c6 = st.columns(3)
                    c4.metric("Prompt Cost (USD)",     f"${prompt_cost:.6f}")
                    c5.metric("Completion Cost (USD)", f"${completion_cost:.6f}")
                    c6.metric("Total Cost (USD)",      f"${total_cost:.6f}")

                    # Speed metrics
                    speed_col, rate_col = st.columns(2)
                    elapsed = max(elapsed, 1e-6)
                    speed_col.metric("Elapsed time (s)", f"{elapsed:.2f}")
                    tps = total_tokens / elapsed if elapsed > 0 else 0.0
                    rate_col.metric("Tokens per second", f"{tps:.1f}")

                    if total_tokens > 0:
                        sec_per_1k = (elapsed / total_tokens) * 1000
                        st.metric("Time per 1,000 tokens (s)", f"{sec_per_1k:.2f}")

                    if fingerprint:
                        st.write(f"**Seed used:** {seed} | **System fingerprint:** {fingerprint}")

                # Automatic evaluation if reference provided
                if reference.strip():
                    bleu = sacrebleu.corpus_bleu([result], [[reference]]).score
                    chrf = sacrebleu.corpus_chrf([result], [[reference]]).score
                    _, _, bert_f1 = score([result], [reference], lang="id", verbose=False)
                    bert_f1 = bert_f1.mean().item()

                    st.subheader("Automatic Evaluation Metrics")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("BLEU Score",   f"{bleu:.2f}")
                    m2.metric("chrF Score",   f"{chrf:.2f}")
                    m3.metric("BERTScore F1", f"{bert_f1:.3f}")

                st.success("Done.")

with tab2:
    st.caption("Use this when you already have a model translation from elsewhere and just want to score it.")
    hypo = st.text_area("Candidate translation (Indonesian)", height=200, key="hypo_text")
    ref  = st.text_area("Reference translation (Indonesian)", height=200, key="ref_only_text")

    col_a, col_b = st.columns(2)
    with col_a:
        eval_do_bert = st.checkbox("Compute BERTScore (slower)", value=True)
    with col_b:
        bert_lang = st.text_input("BERTScore language code", value="id", help="e.g., 'id' for Indonesian")

    if st.button("Evaluate Only"):
        if not hypo.strip() or not ref.strip():
            st.warning("Please provide both candidate and reference texts.")
        else:
            bleu = sacrebleu.corpus_bleu([hypo], [[ref]]).score
            chrf = sacrebleu.corpus_chrf([hypo], [[ref]]).score

            if eval_do_bert:
                _, _, bert_f1 = score([hypo], [ref], lang=bert_lang, verbose=False)
                bert_f1 = bert_f1.mean().item()
            else:
                bert_f1 = None

            st.subheader("Evaluation Metrics")
            m1, m2, m3 = st.columns(3)
            m1.metric("BLEU Score", f"{bleu:.2f}")
            m2.metric("chrF Score", f"{chrf:.2f}")
            m3.metric("BERTScore F1", f"{bert_f1:.3f}" if bert_f1 is not None else "—")

            st.success("Scoring complete.")

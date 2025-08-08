import streamlit as st
from openai import OpenAI
import time

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
    buffer = ""
    for ch in text:
        buffer += ch
        placeholder.markdown(
            "<div style='white-space: pre-wrap; font-size:16px; "
            "padding:1rem; background:#f4f4f4; border-radius:8px; "
            "line-height:1.5;'>"
            f"{buffer}</div>",
            unsafe_allow_html=True
        )
        time.sleep(delay)

# ─────────────────────────────────────────────────────────────────────
# PROMPT & EXAMPLES (Option 1: Idiomatic Paraphrase Instruction)
# ─────────────────────────────────────────────────────────────────────

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a senior environmental-science translator. "
        "Translate English to Indonesian as publication-ready prose by:  "
        "1. Preserving all original meaning and context.  "
        "2. Rendering technical terms precisely and idiomatically, avoiding overly literal, single-word translations.  "
        "3. Using varied academic connectors for a smooth, natural flow.  "
        "4. Keeping sentences clear and easy to read."
    )
}

FEW_SHOT_EXAMPLES = [
    {"role": "user",      "content": "Mangrove restoration reduces coastal erosion risk."},
    {"role": "assistant", "content": "Restorasi mangrove mengurangi risiko abrasi pantai."},
    {"role": "user",      "content": "Tropical peatland carbon stocks are exceptionally high."},
    {"role": "assistant", "content": "Stok karbon di lahan gambut tropis sangat tinggi."},
    {"role": "user",      "content": "Water governance management optimizes resource allocation."},
    {"role": "assistant", "content": "Pengelolaan tata kelola air mengoptimalkan distribusi sumber daya."}
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

# cost rates for known models
cost_rates = {
    "openai/gpt-4o-mini": (0.15/1e6, 0.60/1e6),
    "openai/gpt-4":       (0.03/1e3, 0.06/1e3),
    "openai/gpt-4.1":     (0.03/1e3, 0.06/1e3),
}

# ─────────────────────────────────────────────────────────────────────
# TRANSLATION FUNCTION
# ─────────────────────────────────────────────────────────────────────

def translate_environmental(text: str, model: str, temp: float, p: float, seed: int):
    user_msg = {"role": "user", "content": text}
    messages = [SYSTEM_MESSAGE, *FEW_SHOT_EXAMPLES, user_msg]
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

source = st.text_area("Enter English source text here:", height=200)
reference = st.text_area("Enter reference Indonesian translation (optional):", height=200)

if st.button("Translate & Evaluate"):
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
            type_writer(result)

            # Token, cost & speed metrics
            in_rate, out_rate = cost_rates.get(model_id, (0.0, 0.0))
            prompt_cost     = usage.prompt_tokens     * in_rate
            completion_cost = usage.completion_tokens * out_rate
            total_cost      = prompt_cost + completion_cost

            with st.expander("Token, Cost & Speed Metrics", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Prompt Tokens",     usage.prompt_tokens)
                c2.metric("Completion Tokens", usage.completion_tokens)
                c3.metric("Total Tokens",      usage.prompt_tokens + usage.completion_tokens)

                c4, c5, c6 = st.columns(3)
                c4.metric("Prompt Cost (USD)",     f"${prompt_cost:.6f}")
                c5.metric("Completion Cost (USD)", f"${completion_cost:.6f}")
                c6.metric("Total Cost (USD)",      f"${total_cost:.6f}")

                # Speed metrics
                speed_col, rate_col = st.columns(2)
                speed_col.metric("Time per 1 000 tokens (s)", f"{elapsed:.2f}")
                tokens_per_sec = (usage.prompt_tokens + usage.completion_tokens) / elapsed
                rate_col.metric("Tokens per second", f"{tokens_per_sec:.1f}")

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

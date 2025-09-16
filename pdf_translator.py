#!/usr/bin/env python3
# pdf_translator.py — Translator, Metrics, Comparison, and PDF Translate
# - OpenAI models use OpenAI API directly
# - Other models are routed internally without UI provider names
# - Costs normalized to USD per 1,000,000 tokens
# - UI text is fully English; no stack/provider names are shown

import io
import re
import os
import csv
import zipfile
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import streamlit as st
import pandas as pd
from openai import OpenAI

# Evaluation
import sacrebleu
from bert_score import score

# Optional DOCX export (no UI mention)
try:
    import docx  # python-docx
    _HAS_DOCX = True
except Exception:
    _HAS_DOCX = False

# Preferred PDF text extraction (required internally)
try:
    from docling.document_converter import DocumentConverter
    _HAS_DOCLING = True
except Exception:
    _HAS_DOCLING = False


# ─────────────────────────────────────────────────────────────────────
# CONFIGURATION & UTILITIES
# ─────────────────────────────────────────────────────────────────────

OPENAI_KEY_FILE     = "keys/openai_api_key.txt"
OPENROUTER_KEY_FILE = "keys/openrouter_api_key.txt"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

@st.cache_resource(show_spinner=False)
def load_key(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except Exception as e:
        st.error(f"Failed reading API key at {path}: {e}")
        st.stop()

@st.cache_resource(show_spinner=False)
def get_openai_client() -> OpenAI:
    key = load_key(OPENAI_KEY_FILE)
    try:
        return OpenAI(api_key=key)  # OpenAI direct
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {e}")
        st.stop()

@st.cache_resource(show_spinner=False)
def get_proxy_client() -> OpenAI:
    """Client for non-OpenAI models (routed via your internal gateway)."""
    key = load_key(OPENROUTER_KEY_FILE)
    try:
        return OpenAI(
            api_key=key,
            base_url=OPENROUTER_BASE_URL,
            # Optional headers (kept generic; not shown in UI)
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "AI Translations Project",
            },
        )
    except Exception as e:
        st.error(f"Failed to initialize secondary model client: {e}")
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
    st.markdown(
        "<div style='white-space: pre-wrap; font-size:16px; "
        "padding:1rem; background:#f4f4f4; border-radius:8px; line-height:1.5;'>"
        f"{text}</div>",
        unsafe_allow_html=True
    )

def safe_usage(usage):
    """Handle OpenAI objects or plain dicts; never crash."""
    try:
        pt = getattr(usage, "prompt_tokens", None)
        ct = getattr(usage, "completion_tokens", None)
        tt = getattr(usage, "total_tokens", None)
        if pt is None and isinstance(usage, dict):
            pt = usage.get("prompt_tokens", 0)
            ct = usage.get("completion_tokens", 0)
            tt = usage.get("total_tokens", (pt or 0) + (ct or 0))
        pt = pt or 0
        ct = ct or 0
        tt = tt or (pt + ct)
    except Exception:
        pt = ct = tt = 0
    return pt, ct, tt

def _is_gpt5(model_id: str) -> bool:
    return isinstance(model_id, str) and model_id.lower().startswith("gpt-5")

def _chat_create(client, *, model, messages, temperature, top_p, seed, provider):
    """
    Send only parameters each provider/model supports.
    - OpenAI non-GPT-5: allow temperature/top_p/seed
    - OpenAI GPT-5: omit temperature/top_p/seed (avoid 400s)
    - Proxy (non-OpenAI): include temperature/top_p, omit seed
    """
    params = {"model": model, "messages": messages}
    if provider == "openai":
        if not _is_gpt5(model):
            params["temperature"] = float(temperature)
            params["top_p"] = float(top_p)
            params["seed"] = int(seed)
        # GPT-5: omit all sampling controls
    else:  # proxy client
        params["temperature"] = float(temperature)
        params["top_p"] = float(top_p)
        # no seed on proxy
    return client.chat.completions.create(**params)


# ─────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT & FEW-SHOTS
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
# MODEL CATALOG (UI labels are clean; no provider names)
# All costs are USD per 1,000,000 tokens: (input_rate, output_rate)
# ─────────────────────────────────────────────────────────────────────

MODEL_CATALOG = {
    # OpenAI (direct)
    "GPT-4o-mini": {
        "provider": "openai",
        "api_model": "gpt-4o-mini",
        "cost": (0.15, 0.60),
    },
    "GPT-4.1": {
        "provider": "openai",
        "api_model": "gpt-4.1",
        "cost": (3.00, 12.00),
    },
    "GPT-4": {
        "provider": "openai",
        "api_model": "gpt-4",
        "cost": (30.00, 60.00),
    },
    "GPT-5": {
        "provider": "openai",
        "api_model": "gpt-5",          # sampling params omitted automatically
        "cost": (1.25, 10.00),         # adjust if your pricing differs
    },

    # Routed via proxy client (internal, no UI naming)
    "Gemini 2.0 Flash": {
        "provider": "proxy",
        "api_model": "google/gemini-2.0-flash-001",
        "cost": (0.10, 0.40),
    },
    "DeepSeek Chat V3 (Free)": {
        "provider": "proxy",
        "api_model": "deepseek/deepseek-chat-v3-0324:free",
        "cost": (0.00, 0.00),
    },
}


# ─────────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="AI Translator + Metrics", layout="wide")
st.title("AI Translations Project")

# ─────────────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────────────────────────────

st.sidebar.header("Settings")

# Primary single-model run (Tab 1 / Tab 2)
selected_label = st.sidebar.selectbox("Model (single run)", list(MODEL_CATALOG.keys()))
selected_cfg = MODEL_CATALOG[selected_label]

# Multi-model comparison config (Tab 3)
compare_labels = st.sidebar.multiselect(
    "Models for comparison (Tab 3)",
    options=list(MODEL_CATALOG.keys()),
    default=[selected_label],
    help="Pick ≥1 models to compare in Tab 3."
)

temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
top_p       = st.sidebar.slider("Top-p",       0.1, 1.0, 0.9, 0.05)
seed        = st.sidebar.number_input("Seed (ignored for some models)", min_value=0, value=42, step=1)
use_typewriter = st.sidebar.checkbox("Typewriter effect", value=True)


# ─────────────────────────────────────────────────────────────────────
# TRANSLATION CORE
# ─────────────────────────────────────────────────────────────────────

def translate_environmental(text: str, cfg: dict, temp: float, p: float, seed: int):
    provider = cfg["provider"]
    model    = cfg["api_model"]

    client = get_openai_client() if provider == "openai" else get_proxy_client()

    system_msg = SYSTEM_MESSAGE_FULL
    user_msg = {"role": "user", "content": text}
    messages = [system_msg, *FEW_SHOT_EXAMPLES, user_msg]

    resp = _chat_create(
        client,
        model=model,
        messages=messages,
        temperature=temp,
        top_p=p,
        seed=seed,
        provider=provider,
    )

    fingerprint = getattr(resp, "system_fingerprint", None) or getattr(resp.choices[0], "system_fingerprint", None)
    return resp.choices[0].message.content, resp.usage, fingerprint


# ─────────────────────────────────────────────────────────────────────
# MARKDOWN → PARAGRAPHS & CHUNKING (for PDF)
# ─────────────────────────────────────────────────────────────────────

_MD_HEADER = re.compile(r"^\s{0,3}#{1,6}\s+", flags=re.MULTILINE)

def markdown_to_paragraphs(md: str) -> List[str]:
    """Convert markdown-ish text to paragraphs (remove headers, keep bullet text)."""
    md = _MD_HEADER.sub("", md)
    md = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", md)              # strip emphasis markers
    md = re.sub(r"^\s*[-•]\s+", "", md, flags=re.MULTILINE)            # bullets -> lines
    md = re.sub(r"\n{3,}", "\n\n", md)                                 # collapse blanks
    parts = [p.strip() for p in md.split("\n\n") if p.strip()]
    return parts

def chunk_paragraphs(paragraphs: List[str], max_chars: int = 1400) -> List[str]:
    """Group paragraphs into chunks ≤ max_chars to keep prompts manageable."""
    chunks, buf = [], []
    current = 0
    for p in paragraphs:
        if current + len(p) + 1 <= max_chars:
            buf.append(p)
            current += len(p) + 1
        else:
            if buf:
                chunks.append("\n\n".join(buf))
            buf = [p]
            current = len(p)
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


# ─────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "Translate & Evaluate",
    "Evaluate Only",
    "Model Comparison",
    "PDF Translate",
])

# ─────────────────────────────────────────────────────────────────────
# TAB 1 — Translate & Evaluate
# ─────────────────────────────────────────────────────────────────────

with tab1:
    source = st.text_area("Enter English source text:", height=200, key="source_text")
    reference = st.text_area("Enter Indonesian reference translation (optional):", height=200, key="ref_text")

    if st.button("Translate & Evaluate", type="primary"):
        if not source.strip():
            st.warning("Please enter source text.")
        else:
            with st.spinner(f"Translating via {selected_label}…"):
                start = time.monotonic()
                try:
                    result, usage, fingerprint = translate_environmental(
                        source, selected_cfg, temperature, top_p, seed
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
                in_rate_per_m, out_rate_per_m = selected_cfg["cost"]  # per 1M tokens

                prompt_cost     = (prompt_tokens     / 1_000_000) * in_rate_per_m
                completion_cost = (completion_tokens / 1_000_000) * out_rate_per_m
                total_cost      = prompt_cost + completion_cost

                with st.expander("Token, Cost & Speed Metrics", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Prompt Tokens",     f"{prompt_tokens:,}")
                    c2.metric("Completion Tokens", f"{completion_tokens:,}")
                    c3.metric("Total Tokens",      f"{total_tokens:,}")

                    c4, c5, c6 = st.columns(3)
                    c4.metric("Prompt Cost (USD)",     f"${prompt_cost:,.6f}")
                    c5.metric("Completion Cost (USD)", f"${completion_cost:,.6f}")
                    c6.metric("Total Cost (USD)",      f"${total_cost:,.6f}")

                    speed_col, rate_col = st.columns(2)
                    elapsed = max(elapsed, 1e-6)
                    speed_col.metric("Elapsed time (s)", f"{elapsed:.2f}")
                    tps = total_tokens / elapsed if elapsed > 0 else 0.0
                    rate_col.metric("Tokens per second", f"{tps:.1f}")

                    if total_tokens > 0:
                        sec_per_1k = (elapsed / total_tokens) * 1000
                        st.metric("Time per 1,000 tokens (s)", f"{sec_per_1k:.2f}")
                    else:
                        st.info("Provider did not return token usage. Costs shown as $0.00 may be under-reported.")

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

# ─────────────────────────────────────────────────────────────────────
# TAB 2 — Evaluate Only
# ─────────────────────────────────────────────────────────────────────

with tab2:
    st.caption("Use this when you already have a model translation and just want to score it.")
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

# ─────────────────────────────────────────────────────────────────────
# TAB 3 — Model Comparison (clean table + full translations)
# ─────────────────────────────────────────────────────────────────────

with tab3:
    st.subheader("Comparison Summary")
    st.caption("Compare tokens, costs, speed, and evaluation metrics on the same input. Full translations are available below.")

    src_cmp = st.text_area("Source text (English) for comparison", height=180, key="src_cmp")
    ref_cmp = st.text_area("Reference translation (optional, Indonesian)", height=180, key="ref_cmp")

    if st.button("Run Comparison (Tab 3)"):
        if not src_cmp.strip():
            st.warning("Please provide source text.")
        elif not compare_labels:
            st.warning("Pick at least one model in the sidebar.")
        else:
            rows: List[Dict[str, Any]] = []
            progress = st.progress(0.0)
            status = st.empty()
            n = len(compare_labels)

            for i, label in enumerate(compare_labels, start=1):
                cfg = MODEL_CATALOG[label]
                status.info(f"Running {label} ({i}/{n}) …")
                t0 = time.monotonic()
                try:
                    out, usage, fingerprint = translate_environmental(
                        src_cmp, cfg, temperature, top_p, seed
                    )
                    elapsed = time.monotonic() - t0
                except Exception as e:
                    out, usage, fingerprint, elapsed = f"[ERROR] {e}", None, None, 0.0

                pt, ct, tt = safe_usage(usage or {})
                in_rate, out_rate = cfg["cost"]
                cost_prompt = (pt / 1_000_000) * in_rate
                cost_comp   = (ct / 1_000_000) * out_rate
                cost_total  = cost_prompt + cost_comp
                tps = (tt / max(elapsed, 1e-6)) if tt > 0 else 0.0

                # Metrics if ref provided
                if ref_cmp.strip() and not (isinstance(out, str) and out.startswith("[ERROR]")):
                    try:
                        bleu = sacrebleu.corpus_bleu([out], [[ref_cmp]]).score
                        chrf = sacrebleu.corpus_chrf([out], [[ref_cmp]]).score
                        _, _, bert_f1 = score([out], [ref_cmp], lang="id", verbose=False)
                        bert_f1 = bert_f1.mean().item()
                    except Exception as e:
                        bleu = chrf = None
                        bert_f1 = None
                        st.warning(f"Evaluation failed for {label}: {e}")
                else:
                    bleu = chrf = bert_f1 = None

                rows.append({
                    "model_label": label,
                    "provider": cfg["provider"],
                    "model_id": cfg["api_model"],
                    "prompt_tokens": pt,
                    "completion_tokens": ct,
                    "total_tokens": tt,
                    "prompt_cost_usd": cost_prompt,
                    "completion_cost_usd": cost_comp,
                    "total_cost_usd": cost_total,
                    "elapsed_s": elapsed,
                    "tokens_per_s": tps,
                    "BLEU": bleu,
                    "chrF": chrf,
                    "BERTScore_F1": bert_f1,
                    "translation_len": len(out) if isinstance(out, str) else 0,
                    "translation_preview": (out[:120] + "…") if isinstance(out, str) and len(out) > 120 else out,
                    "translation_full": out if isinstance(out, str) else "",
                })

                progress.progress(i / n)

            status.empty()
            progress.empty()

            # Dataframe summary (no Provider column in UI)
            df = pd.DataFrame(rows)

            def _fmt_int(x):
                try: return f"{int(x):,}"
                except: return "—"

            def _fmt_usd(x):
                try: return f"${float(x):,.6f}"
                except: return "—"

            def _fmt_float(x, nd=2):
                try: return f"{float(x):.{nd}f}"
                except: return "—"

            def _preview(text, n=120):
                if not isinstance(text, str) or not text: return "—"
                text = text.replace("\n", " ")
                return text if len(text) <= n else (text[:n] + " …")

            display_df = pd.DataFrame({
                "Model": df["model_label"],
                "Model ID": df["model_id"],
                "Prompt Tokens": df["prompt_tokens"].map(_fmt_int),
                "Completion Tokens": df["completion_tokens"].map(_fmt_int),
                "Total Tokens": df["total_tokens"].map(_fmt_int),
                "Prompt $": df["prompt_cost_usd"].map(_fmt_usd),
                "Comp $": df["completion_cost_usd"].map(_fmt_usd),
                "Total $": df["total_cost_usd"].map(_fmt_usd),
                "Sec": df["elapsed_s"].map(lambda x: _fmt_float(x, 2)),
                "Tok/s": df["tokens_per_s"].map(lambda x: _fmt_float(x, 1)),
                "BLEU": df["BLEU"].map(lambda x: _fmt_float(x, 2)),
                "chrF": df["chrF"].map(lambda x: _fmt_float(x, 2)),
                "BERT-F1": df["BERTScore_F1"].map(lambda x: _fmt_float(x, 3)),
                "Len": df["translation_len"].map(_fmt_int),
                "Preview": df["translation_preview"].map(_preview),
            })

            st.markdown("### Summary Table")
            st.dataframe(display_df, hide_index=True, use_container_width=True)

            # Raw CSV download (keeps provider/internal fields for analysis if needed)
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
            st.download_button(
                "Download comparison CSV",
                data=buf.getvalue().encode("utf-8"),
                file_name="model_comparison_summary.csv",
                mime="text/csv",
            )

            # Full translations (expand/collapse + per-model download + ZIP)
            st.markdown("### Full Translations")
            expand_all = st.checkbox("Expand all", value=False, help="Show full text for every model")

            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in rows:
                    title = f"{r['model_label']} — {r['model_id']}"
                    full_text = r.get("translation_full") or r.get("translation_preview") or ""
                    with st.expander(title, expanded=expand_all):
                        show_text_block(full_text)
                        st.download_button(
                            f"Download ({r['model_label']}).txt",
                            data=full_text,
                            file_name=f"{r['model_label'].replace(' ','_')}.txt",
                            mime="text/plain",
                            key=f"dl_{r['model_label']}"
                        )
                    # add to zip
                    zf.writestr(f"{r['model_label'].replace(' ','_')}.txt", full_text)

            st.download_button(
                "Download all translations (.zip)",
                data=zip_buf.getvalue(),
                file_name="translations_all_models.zip",
                mime="application/zip",
            )

            st.success("Comparison complete.")

# ─────────────────────────────────────────────────────────────────────
# TAB 4 — PDF Translate (relies on your preferred extractor internally; no names shown in UI)
# ─────────────────────────────────────────────────────────────────────

with tab4:
    st.subheader("Translate PDF")
    st.caption("Upload a PDF, translate it to Indonesian, and download the results.")

    if not _HAS_DOCLING:
        st.error("PDF translation requires an additional component that is not installed in this environment.")
        st.stop()

    pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

    DEFAULT_CHUNK_CHARS = 1400  # balanced for latency + quality
    with st.expander("Advanced options", expanded=False):
        use_custom_chunk = st.checkbox("Use custom chunk size", value=False)
        if use_custom_chunk:
            chunk_chars = st.slider("Max characters per chunk", min_value=600, max_value=4000, value=1400, step=100)
        else:
            chunk_chars = DEFAULT_CHUNK_CHARS

    run_btn = st.button("Translate PDF", type="primary")

    if run_btn:
        if pdf_file is None:
            st.warning("Please upload a PDF first.")
        else:
            # Save uploaded bytes to a temp file for converter
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_file.read())
                    tmp_path = tmp.name

                converter = DocumentConverter()
                doc = converter.convert(tmp_path).document
                md = doc.export_to_markdown()
            except Exception as e:
                st.error(f"Failed to read the PDF: {e}")
                st.stop()
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

            paragraphs = markdown_to_paragraphs(md)
            if not paragraphs:
                st.warning("No readable text found in the PDF.")
                st.stop()
            chunks = chunk_paragraphs(paragraphs, max_chars=chunk_chars)

            st.write(f"Identified **{len(paragraphs)}** paragraphs → **{len(chunks)}** translation chunks.")

            progress = st.progress(0.0)
            status = st.empty()

            all_out: List[str] = []
            total_pt = total_ct = total_tt = 0
            start_all = time.monotonic()

            for i, ch in enumerate(chunks, start=1):
                status.info(f"Translating chunk {i}/{len(chunks)} via {selected_label}…")
                try:
                    out, usage, _ = translate_environmental(
                        ch, selected_cfg, temperature, top_p, seed
                    )
                except Exception as e:
                    out, usage = f"[ERROR] {e}", {}
                pt, ct, tt = safe_usage(usage or {})
                total_pt += pt
                total_ct += ct
                total_tt += tt
                all_out.append(out if isinstance(out, str) else "")
                progress.progress(i / len(chunks))

            status.empty()
            progress.empty()

            total_elapsed = time.monotonic() - start_all
            translated_text = "\n\n".join(all_out).strip()

            # Show sample and metrics
            st.subheader("Preview")
            show_text_block(translated_text[:1500] + ("…" if len(translated_text) > 1500 else ""))

            in_rate_per_m, out_rate_per_m = selected_cfg["cost"]
            prompt_cost     = (total_pt / 1_000_000) * in_rate_per_m
            completion_cost = (total_ct / 1_000_000) * out_rate_per_m
            total_cost      = prompt_cost + completion_cost

            with st.expander("Token, Cost & Speed (PDF run)", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Prompt Tokens",     f"{total_pt:,}")
                c2.metric("Completion Tokens", f"{total_ct:,}")
                c3.metric("Total Tokens",      f"{total_tt:,}")

                c4, c5, c6 = st.columns(3)
                c4.metric("Prompt Cost (USD)",     f"${prompt_cost:,.6f}")
                c5.metric("Completion Cost (USD)", f"${completion_cost:,.6f}")
                c6.metric("Total Cost (USD)",      f"${total_cost:,.6f}")

                c7, c8 = st.columns(2)
                c7.metric("Total time (s)", f"{total_elapsed:.2f}")
                tps = total_tt / max(total_elapsed, 1e-6) if total_tt > 0 else 0.0
                c8.metric("Tokens per second", f"{tps:.1f}")

                if total_tt == 0:
                    st.info("Provider did not return token usage. Costs shown as $0.00 may be under-reported.")

            # Downloads: TXT and DOCX
            st.download_button(
                "Download translation (.txt)",
                data=translated_text,
                file_name="translation_from_pdf_id.txt",
                mime="text/plain"
            )

            if _HAS_DOCX:
                try:
                    buf = io.BytesIO()
                    d = docx.Document()
                    for para in translated_text.split("\n\n"):
                        d.add_paragraph(para)
                        d.add_paragraph("")  # blank line between paragraphs
                    d.save(buf)
                    st.download_button(
                        "Download translation (.docx)",
                        data=buf.getvalue(),
                        file_name="translation_from_pdf_id.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                except Exception as e:
                    st.warning(f"Could not generate DOCX: {e}")

            st.success("PDF translation completed.")


import json
import re
import os
import base64
import requests
from pathlib import Path

import pandas as pd
import streamlit as st
from pypdf import PdfReader

try:
    import pymupdf
except ImportError:
    pymupdf = None

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(
    page_title="Consultant Quotation Database",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRO_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --bp-paper: #f4efe6;
  --bp-paper-2: #ebe4d8;
  --bp-white: #fffdf8;
  --bp-ink: #102033;
  --bp-navy: #10283f;
  --bp-navy-2: #173a59;
  --bp-blue: #2f6f9f;
  --bp-coral: #d96c4e;
  --bp-gold: #c69a4a;
  --bp-sage: #9dac9b;
  --bp-muted: #6d7277;
  --bp-line: rgba(16,32,51,.14);
  --bp-soft-line: rgba(16,32,51,.08);
  --bp-danger: #9d3c32;
}

html, body, [class*="css"], .stApp {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
  color-scheme: light !important;
}

.stApp {
  background:
    linear-gradient(rgba(16,40,63,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16,40,63,.035) 1px, transparent 1px),
    #d6d1c8 !important;
  background-size: 28px 28px !important;
  color: var(--bp-ink) !important;
}

[data-testid="stAppViewContainer"] > .main {
  background:
    linear-gradient(180deg, rgba(255,255,255,.45), rgba(255,255,255,0) 170px),
    var(--bp-paper) !important;
  margin: 20px 20px 20px 0;
  border-radius: 18px;
  min-height: calc(100vh - 40px);
  overflow: hidden;
  box-shadow: 0 22px 55px rgba(16,32,51,.16);
}

.block-container {
  max-width: 1500px;
  padding: 1.8rem 2.15rem 2.8rem 2.15rem;
  color: var(--bp-ink) !important;
}

/* Editorial typography */
h1, h2, h3, h4 { color: var(--bp-ink) !important; }
h1, h2, h3 { font-family: Georgia, 'Times New Roman', serif !important; letter-spacing: -.035em; }
.stMarkdown p, .stMarkdown li, [data-testid="stCaptionContainer"], .stCaption {
  color: var(--bp-muted) !important;
  line-height: 1.58 !important;
}
label, [data-testid="stWidgetLabel"] p {
  color: var(--bp-ink) !important;
  font-weight: 700 !important;
}

/* Editorial masthead */
.pro-header {
  padding: 4px 0 22px;
  margin-bottom: 22px;
  border-bottom: 2px solid var(--bp-ink);
  color: var(--bp-ink) !important;
}
.pro-header * { color: var(--bp-ink) !important; }
.pro-header h1 {
  margin: 0 0 9px 0;
  font-size: clamp(2.05rem, 3.4vw, 3.25rem);
  font-weight: 700;
  line-height: .96;
}
.pro-header p {
  margin: 0;
  color: var(--bp-muted) !important;
  font-size: .93rem;
  max-width: 78ch;
}
.pro-chip {
  display: inline-flex;
  align-items: center;
  margin-top: 13px;
  margin-right: 7px;
  padding: 6px 10px;
  border-radius: 7px;
  background: var(--bp-white);
  color: var(--bp-ink) !important;
  font-size: .69rem;
  font-weight: 800;
  letter-spacing: .055em;
  text-transform: uppercase;
  border: 1px solid var(--bp-line);
}
.pro-chip:first-of-type {
  background: var(--bp-paper-2);
  color: var(--bp-coral) !important;
  border-color: var(--bp-line);
}

/* Left rail / sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0d2033 0%, #142d45 100%) !important;
  border-right: 1px solid rgba(255,255,255,.08) !important;
  box-shadow: 0 18px 45px rgba(16,32,51,.16) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.35rem; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 { color: #ffffff !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: #d3e0e8 !important; }
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small { color: #a8bdca !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12) !important; }
[data-testid="stSidebar"] .pro-section { color: #efb49e !important; }

/* Light controls */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
  background: var(--bp-white) !important;
  color: var(--bp-ink) !important;
  -webkit-text-fill-color: var(--bp-ink) !important;
  border: 1px solid var(--bp-line) !important;
  border-radius: 8px !important;
  caret-color: var(--bp-coral) !important;
  box-shadow: none !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {
  border-color: rgba(217,108,78,.65) !important;
  box-shadow: 0 0 0 3px rgba(217,108,78,.10) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder { color: #8b8e90 !important; opacity: 1 !important; }

[data-baseweb="select"] > div {
  background: var(--bp-white) !important;
  color: var(--bp-ink) !important;
  border: 1px solid var(--bp-line) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
[data-baseweb="select"] span, [data-baseweb="select"] div { color: var(--bp-ink) !important; }
[data-baseweb="popover"], [data-baseweb="menu"] { background: var(--bp-white) !important; }
[data-baseweb="popover"] [role="option"], [data-baseweb="menu"] [role="option"] {
  background: var(--bp-white) !important;
  color: var(--bp-ink) !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"]:hover { background: #eef0ea !important; }

/* Sidebar controls remain navy-friendly */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="textarea"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: rgba(255,255,255,.07) !important;
  color: #f4f7f9 !important;
  -webkit-text-fill-color: #f4f7f9 !important;
  border-color: rgba(255,255,255,.15) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div { color: #f4f7f9 !important; }

textarea:disabled, input:disabled,
[data-baseweb="input"] input:disabled,
[data-baseweb="textarea"] textarea:disabled {
  background: #eef0ea !important;
  color: #62686d !important;
  -webkit-text-fill-color: #62686d !important;
  opacity: 1 !important;
}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
  background: var(--bp-white) !important;
  border: 1.5px dashed rgba(16,32,51,.26) !important;
  border-radius: 12px !important;
}
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] div {
    color: #334155 !important;
    -webkit-text-fill-color: #334155 !important;
    opacity: 1 !important;
}

[data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderDropzoneInstructions"] span {
    color: #102033 !important;
    -webkit-text-fill-color: #102033 !important;
    font-weight: 700 !important;
}

[data-testid="stFileUploaderDropzone"] small {
    color: #5F6872 !important;
    -webkit-text-fill-color: #5F6872 !important;
}
[data-testid="stFileUploaderDropzone"] button {
  background: var(--bp-navy) !important;
  color: #fff !important;
  border: 1px solid var(--bp-navy) !important;
  border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzone"] button * { color: #fff !important; }

/* KPI / metric cards mirror the blueprint paper tiles */
[data-testid="stMetric"] {
  position: relative;
  background: var(--bp-white) !important;
  border: 1px solid var(--bp-line) !important;
  padding: 16px 18px 16px 21px !important;
  border-radius: 12px !important;
  min-height: 124px;
  box-shadow: 0 7px 22px rgba(16,32,51,.045) !important;
  overflow: hidden;
}
[data-testid="stMetric"]::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 5px;
  background: var(--bp-blue);
}
div[data-testid="stHorizontalBlock"] > div:nth-child(4n+2) [data-testid="stMetric"]::before { background: var(--bp-coral); }
div[data-testid="stHorizontalBlock"] > div:nth-child(4n+3) [data-testid="stMetric"]::before { background: var(--bp-gold); }
div[data-testid="stHorizontalBlock"] > div:nth-child(4n+4) [data-testid="stMetric"]::before { background: var(--bp-sage); }
[data-testid="stMetricLabel"] * { color: #777b80 !important; font-weight: 750 !important; }
[data-testid="stMetricValue"] * {
  color: var(--bp-ink) !important;
  font-family: Georgia, 'Times New Roman', serif !important;
  font-size: 2rem !important;
  font-weight: 700 !important;
  letter-spacing: -.045em !important;
}
[data-testid="stMetricDelta"] * { color: var(--bp-muted) !important; }

/* Tabs */
[data-baseweb="tab-list"] {
  gap: 5px;
  background: #e8e4dc !important;
  padding: 5px;
  border-radius: 10px;
  border: 1px solid var(--bp-line);
}
[data-baseweb="tab"] {
  border-radius: 7px;
  color: #6f7478 !important;
  min-height: 44px;
}
[data-baseweb="tab"] * { color: #6f7478 !important; }
[data-baseweb="tab"][aria-selected="true"] {
  background: var(--bp-navy) !important;
  color: #fff !important;
}
[data-baseweb="tab"][aria-selected="true"] * { color: #fff !important; font-weight: 800 !important; }

/* Panels / expanders */
[data-testid="stExpander"] {
  background: var(--bp-white) !important;
  border: 1px solid var(--bp-line) !important;
  border-radius: 10px !important;
  overflow: hidden;
  box-shadow: 0 7px 22px rgba(16,32,51,.04) !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * { color: var(--bp-ink) !important; font-weight: 750 !important; }

/* Dataframe / data editor: light paper with navy header treatment */
[data-testid="stDataFrame"] {
  border: 1px solid var(--bp-line) !important;
  border-radius: 10px !important;
  overflow: hidden;
  background: var(--bp-white) !important;
  box-shadow: 0 7px 22px rgba(16,32,51,.04) !important;
}
[data-testid="stDataFrame"] * { font-family: 'Plus Jakarta Sans','Inter',sans-serif !important; }
[data-testid="stDataFrame"] [role="columnheader"] {
  background: var(--bp-navy) !important;
  color: #eef4f7 !important;
  font-weight: 750 !important;
}
[data-testid="stDataFrame"] [role="gridcell"] {
  color: var(--bp-ink) !important;
  background: var(--bp-white) !important;
}

/* Buttons */
.stButton > button, .stDownloadButton > button {
  min-height: 44px;
  border-radius: 9px !important;
  font-weight: 750 !important;
  border: 1px solid var(--bp-line) !important;
  background: var(--bp-white) !important;
  color: var(--bp-ink) !important;
  box-shadow: none !important;
}
.stButton > button *, .stDownloadButton > button * { color: var(--bp-ink) !important; }
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: rgba(47,111,159,.45) !important;
  background: #eef0ea !important;
  transform: translateY(-1px);
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--bp-navy) !important;
  color: #fff !important;
  border-color: var(--bp-navy) !important;
  box-shadow: inset 4px 0 0 var(--bp-coral) !important;
}
.stButton > button[kind="primary"] *,
.stButton > button[data-testid="stBaseButton-primary"] * { color: #fff !important; }
button:focus-visible, input:focus-visible, textarea:focus-visible, [role="tab"]:focus-visible {
  outline: 3px solid var(--bp-coral) !important;
  outline-offset: 2px !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stDownloadButton > button {
  background: rgba(255,255,255,.07) !important;
  color: #f4f7f9 !important;
  border-color: rgba(255,255,255,.14) !important;
}
[data-testid="stSidebar"] .stButton > button *,
[data-testid="stSidebar"] .stDownloadButton > button * { color: #f4f7f9 !important; }

/* Radio / checkbox */
input[type="radio"], input[type="checkbox"] { accent-color: var(--bp-coral) !important; }
[data-baseweb="radio"] div, [data-baseweb="checkbox"] div { color: var(--bp-ink) !important; }
[data-testid="stSidebar"] [data-baseweb="radio"] div,
[data-testid="stSidebar"] [data-baseweb="checkbox"] div { color: #e8f0f4 !important; }

/* Alerts */
[data-testid="stAlert"] {
  border-radius: 9px !important;
  border: 1px solid var(--bp-line) !important;
  color: var(--bp-ink) !important;
}
[data-testid="stAlert"] p, [data-testid="stAlert"] span { color: var(--bp-ink) !important; }

/* Small utility components */
.pro-section {
  color: var(--bp-coral) !important;
  font-size: .72rem;
  font-weight: 850;
  text-transform: uppercase;
  letter-spacing: .12em;
  margin: 5px 0 9px 0;
}
.pro-note {
  background: #eef0ea;
  border: 1px solid var(--bp-line);
  border-left: 4px solid var(--bp-coral);
  border-radius: 9px;
  padding: 12px 14px;
  color: var(--bp-ink) !important;
  font-size: .86rem;
}
.pro-note * { color: var(--bp-ink) !important; }
.field-meta { color: #777b80 !important; font-size: .74rem; margin-top: -6px; margin-bottom: 5px; }
.conf-high { color: #386c59 !important; font-weight: 800; }
.conf-med { color: #9b6a27 !important; font-weight: 800; }
.conf-low { color: var(--bp-danger) !important; font-weight: 800; }

/* Dividers / links / scrollbars */
hr { border-color: var(--bp-line) !important; }
a { color: var(--bp-blue) !important; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #e6e0d6; }
::-webkit-scrollbar-thumb { background: #8996a0; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #6f7d88; }

/* Streamlit status / toolbar surfaces */
[data-testid="stStatusWidget"], [data-testid="stToolbar"] { color: var(--bp-ink) !important; }

@media (max-width: 900px) {
  [data-testid="stAppViewContainer"] > .main { margin: 0; border-radius: 0; }
  .block-container { padding-left: 1rem; padding-right: 1rem; }
  .pro-header h1 { font-size: 2rem; }
}
</style>
"""
st.markdown(PRO_CSS, unsafe_allow_html=True)

DEFAULT_WEIGHTS = {
    "Land Valuation": {
        "Professional Fee": 35,
        "Scope & Methodology": 30,
        "Completion Time": 15,
        "Payment Terms": 10,
        "Deliverables / Commercial Terms": 10,
    },
    "Market Study": {
        "Professional Fee": 25,
        "Scope Depth": 30,
        "HBU / Strategic Usefulness": 20,
        "Completion Time": 15,
        "Payment & Deliverables": 10,
    },
}

DEFAULT_SCOPE_ITEMS = {
    "Land Valuation": [
        "Entire subject land / whole phase",
        "Market Value",
        "As-is / existing condition",
        "Physical inspection",
        "Title / legal search",
        "Planning check",
        "Comparable sales evidence",
        "Valuation methodology stated",
        "Full valuation report",
    ],
    "Market Study": [
        "Market overview",
        "Site assessment",
        "Competitor analysis",
        "Supply & demand",
        "Pricing analysis",
        "Planning considerations",
        "Highest & Best Use",
        "SWOT / risk analysis",
        "Financial / commercial viability",
        "Recommendations",
    ],
}

if "records" not in st.session_state:
    st.session_state.records = []

def extract_pdf_text(uploaded_file):
    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)
    parts = []
    for i, page in enumerate(reader.pages, 1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        parts.append(f"--- PAGE {i} ---\n{txt}")
    uploaded_file.seek(0)
    return "\n".join(parts)

def pdf_page_count(uploaded_file):
    uploaded_file.seek(0)
    try:
        count = len(PdfReader(uploaded_file).pages)
    except Exception:
        count = 0
    uploaded_file.seek(0)
    return count

def assess_text_quality(text, pages=1):
    """Heuristic check to decide whether the PDF text layer is usable."""
    body = re.sub(r"--- PAGE \d+ ---", " ", text or "")
    body = re.sub(r"\s+", " ", body).strip()
    chars = len(body)
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9%&/().,'+-]*", body)
    alpha = sum(ch.isalpha() for ch in body)
    alpha_ratio = alpha / max(1, chars)
    replacement_chars = body.count("\ufffd")

    min_chars = max(250, max(1, pages) * 120)
    min_words = max(35, max(1, pages) * 18)

    reasons = []
    if chars < min_chars:
        reasons.append(f"only {chars} text characters")
    if len(words) < min_words:
        reasons.append(f"only {len(words)} readable words")
    if chars and alpha_ratio < 0.35:
        reasons.append(f"low alphabetic-text ratio ({alpha_ratio:.0%})")
    if replacement_chars > max(5, chars * 0.02):
        reasons.append("many unreadable/replacement characters")

    poor = len(reasons) > 0
    score = 100
    if chars < min_chars:
        score -= 35
    if len(words) < min_words:
        score -= 35
    if chars and alpha_ratio < 0.35:
        score -= 20
    if replacement_chars > max(5, chars * 0.02):
        score -= 10

    return {
        "poor": poor,
        "score": max(0, score),
        "chars": chars,
        "words": len(words),
        "alpha_ratio": alpha_ratio,
        "reasons": reasons,
    }

def openrouter_pdf_scan(pdf_bytes, filename, api_key, model, engine="mistral-ocr"):
    """
    Send the original PDF to OpenRouter's PDF parser.
    For scanned/image PDFs, mistral-ocr is the recommended parser.
    Returns parsed text plus parser metadata.
    """
    if not api_key:
        raise RuntimeError("OpenRouter API key is required for PDF scanning.")

    data_url = "data:application/pdf;base64," + base64.b64encode(pdf_bytes).decode("utf-8")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Read this consultant quotation carefully. Preserve all readable wording, "
                            "headings, tables, fee figures, SST/disbursement statements, completion period, "
                            "payment terms, scope, methodology, deliverables, exclusions and validity. "
                            "Do not summarise yet. Return the document text as faithfully as possible."
                        ),
                    },
                    {
                        "type": "file",
                        "file": {
                            "filename": filename,
                            "file_data": data_url,
                        },
                    },
                ],
            }
        ],
        "plugins": [
            {
                "id": "file-parser",
                "pdf": {"engine": engine},
            }
        ],
        "temperature": 0,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "Quotation Comparison Dashboard",
        },
        json=payload,
        timeout=180,
    )

    try:
        data = response.json()
    except Exception:
        raise RuntimeError(f"OpenRouter PDF scan returned HTTP {response.status_code} with a non-JSON response.")

    if response.status_code >= 400:
        msg = data.get("error", {}).get("message") if isinstance(data, dict) else None
        raise RuntimeError(msg or f"OpenRouter PDF scan failed with HTTP {response.status_code}.")

    message = ((data.get("choices") or [{}])[0].get("message") or {})
    annotations = message.get("annotations") or []

    parsed_parts = []
    parsed_hash = None
    for annotation in annotations:
        if annotation.get("type") != "file":
            continue
        file_obj = annotation.get("file") or {}
        parsed_hash = parsed_hash or file_obj.get("hash")
        for part in file_obj.get("content") or []:
            if part.get("type") == "text" and part.get("text"):
                parsed_parts.append(part["text"])

    # The file parser annotations are preferred because they contain the parsed PDF content.
    scanned_text = "\n\n".join(parsed_parts).strip()
    if not scanned_text:
        scanned_text = (message.get("content") or "").strip()

    if not scanned_text:
        raise RuntimeError("OpenRouter completed the PDF request but returned no readable document text.")

    return scanned_text, {
        "engine": engine,
        "file_hash": parsed_hash,
        "model": data.get("model", model),
    }

def render_pdf_pages_as_images(pdf_bytes, max_pages=12, dpi=170):
    """Render image-only/scanned PDF pages to PNG data URLs for vision OCR."""
    if pymupdf is None:
        raise RuntimeError("PyMuPDF is not installed. Run: python -m pip install pymupdf")
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    if len(doc) == 0:
        raise RuntimeError("The PDF contains no pages.")
    if len(doc) > max_pages:
        raise RuntimeError(f"Scanned-PDF vision mode currently supports up to {max_pages} pages per quotation; this PDF has {len(doc)} pages.")

    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    images = []
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        png_bytes = pix.tobytes("png")
        images.append({
            "page": page_index + 1,
            "data_url": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
            "bytes": len(png_bytes),
            "width": pix.width,
            "height": pix.height,
        })
    doc.close()
    return images

def openrouter_vision_ocr(pdf_bytes, filename, api_key, model):
    """
    Render every PDF page locally and ask an OpenRouter vision-capable model to transcribe it.
    openrouter/free can route to a model that supports image understanding.
    """
    if not api_key:
        raise RuntimeError("OpenRouter API key is required for vision OCR.")

    pages = render_pdf_pages_as_images(pdf_bytes)
    content = [{
        "type": "text",
        "text": (
            "This is a consultant quotation rendered page-by-page from a scanned/image-only PDF. "
            "Perform OCR by reading every visible page carefully. Return a faithful transcription, "
            "not a summary. Preserve page boundaries and all commercially important details including "
            "consultant/company name, date, assignment/property, professional fee, SST/service tax, "
            "disbursements, deposits/payment terms, abortive/cancellation fees, time frame, deliverables, "
            "validity, scope/terms of reference, methodology, exclusions and contact details. "
            "Prefix each page with --- PAGE N ---. If a word is genuinely unreadable, write [unclear]."
        ),
    }]
    for p in pages:
        content.append({
            "type": "image_url",
            "image_url": {"url": p["data_url"]},
        })

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "Quotation Comparison Dashboard",
        },
        json=payload,
        timeout=240,
    )
    try:
        data = response.json()
    except Exception:
        raise RuntimeError(f"OpenRouter vision OCR returned HTTP {response.status_code} with a non-JSON response.")
    if response.status_code >= 400:
        error = data.get("error", {}) if isinstance(data, dict) else {}
        msg = error.get("message") if isinstance(error, dict) else None
        raise RuntimeError(msg or f"OpenRouter vision OCR failed with HTTP {response.status_code}.")

    message = ((data.get("choices") or [{}])[0].get("message") or {})
    text = message.get("content")
    if isinstance(text, list):
        text = "\n".join(part.get("text", "") for part in text if isinstance(part, dict))
    text = (text or "").strip()
    if not text:
        raise RuntimeError("The vision model returned no OCR text.")
    return text, {
        "engine": "page-image vision OCR",
        "model": data.get("model", model),
        "rendered_pages": len(pages),
        "render_dpi": 170,
    }

def money_to_float(s):
    if not s:
        return None
    s = s.replace(" ", "")
    m = re.search(r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)", s)
    return float(m.group(1).replace(",", "")) if m else None

def detect_company(text, filename):
    for pat, label in [
        (r"CBRE\s*\|?\s*WTW", "CBRE | WTW"),
        (r"IM\s+GLOBAL\s+PROPERTY\s+CONSULTANTS", "IM Global Property Consultants"),
        (r"RAHIM\s*&\s*CO(?:\s+CHESTERTONS)?", "Rahim & Co Chestertons"),
    ]:
        if re.search(pat, text, re.I):
            return label
    return Path(filename).stem.replace("_", " ").replace("-", " ")[:80]

def extract_rm_candidates(text):
    """Return explicit RM/MYR amounts found in the PDF, preserving document order."""
    clean = re.sub(r"[\u00a0\u202f]", " ", text)
    pattern = r"(?:RM|MYR)\s*[:\-]?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)"
    out = []
    seen = set()
    for m in re.finditer(pattern, clean, re.I):
        v = money_to_float(m.group(1))
        if v is not None and 1 <= v <= 500_000_000:
            key = (v, m.start())
            if key not in seen:
                seen.add(key)
                out.append({
                    "value": v,
                    "position": m.start(),
                    "text": m.group(0),
                })
    return out

def detect_fee(text):
    """
    Choose the RM amount closest to a fee-related heading/sentence.
    This is more robust than relying on one exact quotation layout.
    """
    clean = re.sub(r"[\u00a0\u202f]", " ", text)
    candidates = extract_rm_candidates(clean)
    if not candidates:
        return None

    fee_terms = list(re.finditer(
        r"(professional\s+fees?|fee\s+structure|total\s+professional\s+fee|professional\s+charges?)",
        clean, re.I
    ))

    # Prefer amounts occurring shortly AFTER a fee term.
    ranked = []
    for c in candidates:
        for term in fee_terms:
            distance = c["position"] - term.end()
            if 0 <= distance <= 900:
                # Penalise obvious deposit/payment amounts if the nearby text says initial/second/final payment.
                nearby = clean[max(0, c["position"]-90):c["position"]+90].lower()
                penalty = 500 if any(x in nearby for x in ["initial payment", "second payment", "final payment"]) else 0
                ranked.append((distance + penalty, c["value"]))

    if ranked:
        ranked.sort(key=lambda x: x[0])
        v = ranked[0][1]
        if 1000 <= v <= 5_000_000:
            return v

    # Fallback: plausible consultancy-fee-sized RM amounts.
    plausible = [c["value"] for c in candidates if 5000 <= c["value"] <= 500000]
    return plausible[0] if plausible else None

def detect_sst(text):
    clean = re.sub(r"\s+", " ", text)
    low = clean.lower()
    if "inclusive" in low and ("8% sst" in low or "8% of sst" in low or "8% sales and service tax" in low or "8% of sale and service tax" in low):
        return "Included"
    if re.search(r"(?:plus|\+)\s*8%\s*(?:sst|service tax|sales and service tax)", clean, re.I):
        return "Excluded / additional 8%"
    if "8%" in low and ("sst" in low or "service tax" in low):
        return "Mentioned – verify"
    return "Not stated"

def detect_disbursement(text):
    clean = re.sub(r"\s+", " ", text)
    low = clean.lower()
    has_disb = "disbursement" in low or "reimbursement" in low or "reimbursements" in low
    if not has_disb:
        return "Not stated"
    # Check exclusions before inclusions because "not inclusive" contains the word "inclusive".
    if re.search(r"(?:not\s+inclusive|excluding|exclusive\s+of).{0,100}(?:disbursement|reimbursement)", clean, re.I):
        if "charged at cost" in low:
            return "Excluded / charged separately at cost"
        return "Excluded / additional"
    if re.search(r"(?:disbursement|reimbursement).{0,100}(?:not\s+inclusive|excluding|exclusive\s+of)", clean, re.I):
        return "Excluded / additional"
    if "inclusive" in low:
        if "title search" in low and ("not included" in low or "excluded" in low):
            return "Included, except title search where applicable"
        return "Included"
    return "Mentioned – verify"

def detect_duration(text):
    patterns = [
        r"(?:six|6)\s*(?:-|to)\s*(?:eight|8)\s*weeks?",
        r"(?:three|3)\s*\(?3?\)?\s*(?:business\s+)?weeks?",
        r"(?:[A-Za-z]+\s*)?\(?(\d+)\)?\s*working\s+days?",
        r"(?:[A-Za-z]+\s*)?\(?(\d+)\)?\s*business\s+days?",
        r"(\d+)\s*(?:-|to)\s*(\d+)\s*weeks?",
        r"(?:[A-Za-z]+\s*)?\(?(\d+)\)?\s*weeks?",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(0)).strip()
    return ""

def duration_to_days(duration):
    if not duration:
        return None
    d = duration.lower()
    if ("six" in d or re.search(r"\b6\b", d)) and ("eight" in d or re.search(r"\b8\b", d)) and "week" in d:
        return 35
    if "three" in d and "week" in d:
        return 15
    m = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)\s*week", d)
    if m:
        return (int(m.group(1)) + int(m.group(2))) / 2 * 5
    m = re.search(r"(\d+)\s*week", d)
    if m:
        return int(m.group(1)) * 5
    m = re.search(r"(\d+)\s*(?:working|business)\s*day", d)
    return int(m.group(1)) if m else None

def snippet_around(text, keywords, size=700):
    low = text.lower()
    for k in keywords:
        idx = low.find(k.lower())
        if idx >= 0:
            return re.sub(r"\s+", " ", text[idx:idx+size]).strip()
    return ""


def extract_section(text, start_headings, stop_headings=None, max_chars=900):
    """Extract a heading-led section and stop at the next known heading when possible."""
    raw = text or ""
    start_match = None
    for heading in start_headings:
        m = re.search(heading, raw, re.I)
        if m and (start_match is None or m.start() < start_match.start()):
            start_match = m
    if not start_match:
        return ""
    start = start_match.start()
    end = min(len(raw), start + max_chars)
    for stop in stop_headings or []:
        m = re.search(stop, raw[start_match.end():], re.I)
        if m:
            candidate = start_match.end() + m.start()
            if candidate > start_match.end() and candidate < end:
                end = candidate
    return re.sub(r"\s+", " ", raw[start:end]).strip()


def detect_scope_summary(text):
    section = extract_section(
        text,
        [r"terms\s+of\s+reference", r"scope\s+of\s+works?", r"scopes\s+of\s+work"],
        [r"abortive\s+fee", r"time\s*frame", r"deliverables?", r"validity", r"terms\s+of\s+payment"],
        1300,
    )
    if section:
        return section
    return snippet_around(text, ["highest and best use", "method of valuation"], 1200)

def detect_payment_terms(text):
    section = extract_section(
        text,
        [r"terms\s+of\s+payment", r"payment\s+terms?"],
        [r"terms\s+of\s+reference", r"scope\s+of\s+works?", r"abortive\s+fee", r"time\s*frame", r"deliverables?", r"validity"],
        700,
    )
    if section:
        return section
    clean = re.sub(r"\s+", " ", text)
    patterns = [
        r"initial\s+payment.{0,350}",
        r"within\s+ninety\s*\(?90\)?\s+days.{0,200}",
        r"within\s+90\s+days.{0,200}",
        r"upon\s+confirmation.{0,300}",
    ]
    for pat in patterns:
        m = re.search(pat, clean, re.I)
        if m:
            return m.group(0).strip()
    return ""

def detect_deliverables(text):
    section = extract_section(
        text,
        [r"deliverables?", r"submission\s+of\s+report"],
        [r"validity", r"abortive\s+fee", r"time\s*frame", r"terms\s+of\s+payment"],
        550,
    )
    if section:
        return section
    return snippet_around(text, ["copies of valuation report", "soft copy", "hard copies"], 420)


def detect_other_terms(text):
    """Capture useful non-core commercial terms even if structured AI is unavailable."""
    notes = []
    abortive = extract_section(text, [r"abortive\s+fee"], [r"time\s*frame", r"deliverables?", r"validity"], 550)
    validity = extract_section(text, [r"validity"], [r"contact", r"yours\s+faithfully", r"acceptance"], 300)
    if abortive:
        notes.append("Abortive fee: " + abortive)
    if validity:
        notes.append("Validity: " + validity)
    clean = re.sub(r"\s+", " ", text or "").strip()
    m = re.search(r"(?:not\s+inclusive|excluded|exclusion).{0,260}", clean, re.I)
    if m:
        notes.append("Exclusion: " + m.group(0).strip())
    return "\n".join(notes)

def infer_scope_status(text, category):
    t = text.lower()
    mapping_land = {
        "Entire subject land / whole phase": ["entire", "phase 2", "763"],
        "Market Value": ["market value"],
        "As-is / existing condition": ["as-is", "existing condition"],
        "Physical inspection": ["physical inspection", "field visit"],
        "Title / legal search": ["title search", "legal", "particulars of title"],
        "Planning check": ["planning check", "planning provisions", "planning"],
        "Comparable sales evidence": ["comparable sales", "sale evidences", "comparables"],
        "Valuation methodology stated": ["comparison method", "method of valuation"],
        "Full valuation report": ["full valuation report", "narrative valuation report", "valuation report"],
    }
    mapping_market = {
        "Market overview": ["market overview", "property market", "market study"],
        "Site assessment": ["site assessment", "site analysis", "project assessment"],
        "Competitor analysis": ["competitor", "competing development", "comparables"],
        "Supply & demand": ["supply and demand", "supply & demand", "demand"],
        "Pricing analysis": ["selling price", "price range", "pricing", "future sales price"],
        "Planning considerations": ["planning consideration", "planning", "development order"],
        "Highest & Best Use": ["highest and best use", "highest & best use", "best use"],
        "SWOT / risk analysis": ["swot", "risk"],
        "Financial / commercial viability": ["financial analysis", "commercial viability", "viability"],
        "Recommendations": ["recommendation", "recommendations", "conclusion"],
    }
    mapping = mapping_land if category == "Land Valuation" else mapping_market
    out = {}
    for item, kws in mapping.items():
        hits = sum(1 for kw in kws if kw in t)
        out[item] = "Yes" if hits >= 2 or (hits == 1 and len(kws) == 1) else ("Partial" if hits == 1 else "No")
    return out

def scope_numeric(scope_status):
    vals = {"Yes": 100, "Partial": 60, "No": 0}
    return sum(vals.get(v, 0) for v in scope_status.values()) / max(1, len(scope_status))

def payment_numeric(text):
    t = (text or "").lower()
    if "90 days" in t or "ninety" in t: return 100
    if "60 days" in t: return 90
    if "30 days" in t: return 75
    if "upon completion" in t or "balance on completion" in t: return 60
    if "upon confirmation" in t or "initial payment" in t: return 50
    return 45 if not t else 55

def deliverable_numeric(text):
    t = (text or "").lower()
    score = 40
    for kw in ["soft copy", "hard copy", "report", "deliverable", "valid"]:
        if kw in t:
            score += 10
    return min(100, score)

def normalize(vals, reverse=False):
    known = [v for v in vals if v is not None]
    if not known:
        return [40 for _ in vals]
    lo, hi = min(known), max(known)
    out = []
    for v in vals:
        if v is None:
            out.append(40)
        elif lo == hi:
            out.append(100)
        else:
            x = ((hi-v)/(hi-lo) if reverse else (v-lo)/(hi-lo))*100
            out.append(round(x,1))
    return out

def compute_scores(records, category, weights):
    subset = [r for r in records if r["category"] == category]
    fees = [r.get("fee") for r in subset]
    days = [duration_to_days(r.get("duration","")) for r in subset]
    fee_scores = normalize(fees, reverse=True)
    time_scores = normalize(days, reverse=True)
    result = []
    for i, r in enumerate(subset):
        scope = scope_numeric(r["scope_status"])
        pay = payment_numeric(r.get("payment_terms",""))
        deli = deliverable_numeric(r.get("deliverables","") + " " + r.get("notes",""))
        if category == "Land Valuation":
            comp = {
                "Professional Fee": fee_scores[i],
                "Scope & Methodology": scope,
                "Completion Time": time_scores[i],
                "Payment Terms": pay,
                "Deliverables / Commercial Terms": deli,
            }
        else:
            hbu = {"Yes":100,"Partial":60,"No":0}.get(r["scope_status"].get("Highest & Best Use","No"),0)
            comp = {
                "Professional Fee": fee_scores[i],
                "Scope Depth": scope,
                "HBU / Strategic Usefulness": 0.6*hbu + 0.4*scope,
                "Completion Time": time_scores[i],
                "Payment & Deliverables": 0.5*pay + 0.5*deli,
            }
        total = sum(comp[k]*weights[k]/100 for k in weights)
        result.append((r, round(total,1), comp))
    return sorted(result, key=lambda x: x[1], reverse=True)

def make_record(uploaded, category, text_override=None, extraction_method=None, scan_meta=None):
    local_text = extract_pdf_text(uploaded)
    pages = pdf_page_count(uploaded)
    local_quality = assess_text_quality(local_text, pages)
    text = text_override if text_override is not None else local_text
    final_quality = assess_text_quality(text, pages)

    if extraction_method is None:
        extraction_method = "PDF text + heuristic"

    return {
        "id": f"{uploaded.name}-{len(st.session_state.records)+1}",
        "filename": uploaded.name,
        "category": category,
        "company": detect_company(text, uploaded.name),
        "fee": detect_fee(text),
        "fee_candidates": [c["value"] for c in extract_rm_candidates(text)],
        "sst": detect_sst(text),
        "disbursement": detect_disbursement(text),
        "duration": detect_duration(text),
        "payment_terms": detect_payment_terms(text),
        "scope_summary": detect_scope_summary(text),
        "deliverables": detect_deliverables(text),
        "notes": detect_other_terms(text),
        "raw_text": text,
        "scope_status": infer_scope_status(text, category),
        "page_count": pages,
        "text_quality_score": final_quality["score"],
        "text_quality_reasons": final_quality["reasons"],
        "local_text_quality_score": local_quality["score"],
        "local_text_quality_reasons": local_quality["reasons"],
        "extraction_method": extraction_method,
        "scan_meta": scan_meta or {},
    }



def split_text_pages(text):
    """Return {page_number: page_text} from recovered text with PAGE markers."""
    text = text or ""
    matches = list(re.finditer(r"---\s*PAGE\s+(\d+)\s*---", text, flags=re.I))
    if not matches:
        return {1: text}
    pages = {}
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        pages[int(match.group(1))] = text[start:end]
    return pages


def find_page_for_value(text, value, alternatives=None):
    if value is None or value == "":
        return None
    pages = split_text_pages(text)
    needles = []
    if isinstance(value, (int, float)):
        n = float(value)
        needles.extend([f"{n:,.0f}", f"{n:,.2f}", str(int(n)) if n.is_integer() else str(n)])
    else:
        v = re.sub(r"\s+", " ", str(value)).strip()
        if v:
            needles.append(v[:120])
            words = [w for w in re.findall(r"[A-Za-z0-9%]+", v) if len(w) >= 4]
            if len(words) >= 2:
                needles.append(" ".join(words[:4]))
    needles.extend(alternatives or [])
    for page_no, page_text in pages.items():
        normalized = re.sub(r"\s+", " ", page_text).lower()
        for needle in needles:
            if needle and re.sub(r"\s+", " ", str(needle)).lower() in normalized:
                return page_no
    return None


def build_field_evidence(record):
    """Generate field-level page references and practical confidence scores."""
    text = record.get("raw_text", "")
    method = record.get("extraction_method", "")
    ai_used = bool(record.get("ai_extracted"))
    text_quality = int(record.get("text_quality_score", 0) or 0)

    specs = {
        "Consultant": (record.get("company"), []),
        "Professional fee": (record.get("fee"), ["professional fee", "professional fees"]),
        "SST treatment": (record.get("sst"), ["service tax", "sst", "8%"]),
        "Completion period": (record.get("duration"), ["time frame", "timeframe", "working days", "weeks"]),
        "Payment terms": (record.get("payment_terms"), ["terms of payment", "payment terms", "initial expenses"]),
        "Scope / methodology": (record.get("scope_summary"), ["terms of reference", "scope of works", "scope of work", "method of valuation"]),
        "Deliverables": (record.get("deliverables"), ["deliverable", "deliverables", "valuation report"]),
        "Other terms / notes": (record.get("notes"), ["validity", "abortive fee", "exclusions", "limitations"]),
    }

    evidence = {}
    for field, (value, alternatives) in specs.items():
        populated = value not in (None, "", 0, 0.0, "Not stated")
        page = find_page_for_value(text, value, alternatives)
        if not populated:
            confidence = 25 if text_quality >= 70 else 15
        else:
            confidence = 66
            if page is not None:
                confidence += 18
            if ai_used:
                confidence += 7
            if "Vision OCR" in method or "PDF scan" in method:
                confidence -= 4
            if text_quality >= 80:
                confidence += 5
        confidence = max(0, min(98, int(confidence)))
        evidence[field] = {"page": page, "confidence": confidence}
    return evidence


def confidence_badge(confidence):
    if confidence >= 85:
        cls, label = "conf-high", "High"
    elif confidence >= 65:
        cls, label = "conf-med", "Medium"
    else:
        cls, label = "conf-low", "Low"
    return f'<span class="{cls}">{label} · {confidence}%</span>'


def show_field_meta(record, field_name):
    evidence = build_field_evidence(record).get(field_name, {})
    page = evidence.get("page")
    page_txt = f"Page {page}" if page else "Page not confirmed"
    st.markdown(
        f'<div class="field-meta">{confidence_badge(evidence.get("confidence", 0))} &nbsp;•&nbsp; {page_txt}</div>',
        unsafe_allow_html=True,
    )


AI_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "company": {"type": "string"},
        "professional_fee_rm": {"type": ["number", "null"]},
        "sst_treatment": {
            "type": "string",
            "enum": ["Included", "Excluded / additional 8%", "Mentioned – verify", "Not stated"]
        },
        "disbursement": {"type": "string"},
        "completion_period": {"type": "string"},
        "payment_terms": {"type": "string"},
        "scope_summary": {"type": "string"},
        "methodology": {"type": "string"},
        "deliverables": {"type": "string"},
        "validity_period": {"type": "string"},
        "exclusions_limitations": {"type": "string"},
        "highest_and_best_use": {
            "type": "string",
            "enum": ["Yes", "Partial", "No"]
        },
        "financial_commercial_viability": {
            "type": "string",
            "enum": ["Yes", "Partial", "No"]
        },
        "confidence_notes": {"type": "string"}
    },
    "required": [
        "company", "professional_fee_rm", "sst_treatment", "disbursement",
        "completion_period", "payment_terms", "scope_summary", "methodology",
        "deliverables", "validity_period", "exclusions_limitations",
        "highest_and_best_use", "financial_commercial_viability", "confidence_notes"
    ]
}

SYSTEM_INSTRUCTION = """You are a procurement quotation analyst.
Extract facts ONLY from the supplied consultant quotation text.
Do not invent missing terms. Use 'Not stated' or an empty string where appropriate.
For fees, identify the actual quoted professional fee for the selected assignment, not deposits,
section numbers, estimated property values, or payment instalments.
For scope, summarize the consultant's committed work accurately and concisely.
For Highest & Best Use and financial/commercial viability, classify Yes only if explicitly included,
Partial if related analysis is present but not clearly committed, and No if absent.
Preserve important exclusions, additional charges, validity periods, and conditions."""

def trim_text_for_ai(text, max_chars=50000):
    if len(text) <= max_chars:
        return text
    return text[:35000] + "\n\n[...middle truncated...]\n\n" + text[-15000:]

def parse_json_text(raw):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

def get_openrouter_client(api_key):
    if OpenAI is None:
        raise RuntimeError("The openai package is not installed. Run: python -m pip install openai")
    if not api_key:
        raise RuntimeError("Enter an OpenRouter API key in the sidebar or set OPENROUTER_API_KEY.")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={"X-OpenRouter-Title": "Quotation Comparison Dashboard"},
    )

def openrouter_extract_quotation(text, category, rfq_text, api_key, model):
    client = get_openrouter_client(api_key)
    prompt = f"""ASSIGNMENT TYPE: {category}\n\nCLIENT RFQ / REQUIREMENT (may be blank):\n{rfq_text or '[Not provided]'}\n\nCONSULTANT QUOTATION TEXT:\n{trim_text_for_ai(text)}"""
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": prompt},
    ]

    # First try OpenRouter structured outputs. If the selected model/provider does not
    # support JSON Schema, retry with explicit JSON-only instructions.
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "quotation_extraction",
                    "strict": True,
                    "schema": AI_SCHEMA,
                },
            },
            extra_body={"provider": {"require_parameters": True}},
            temperature=0,
        )
        return parse_json_text(completion.choices[0].message.content)
    except Exception as structured_error:
        fallback_messages = messages + [{
            "role": "user",
            "content": "Return ONLY valid JSON matching this schema exactly: " + json.dumps(AI_SCHEMA)
        }]
        completion = client.chat.completions.create(
            model=model,
            messages=fallback_messages,
            temperature=0,
        )
        try:
            return parse_json_text(completion.choices[0].message.content)
        except Exception as parse_error:
            raise RuntimeError(f"Structured output failed ({structured_error}); JSON fallback could not be parsed ({parse_error}).")

def get_gemini_client(api_key):
    if genai is None:
        raise RuntimeError("The google-genai package is not installed. Run: python -m pip install google-genai")
    if not api_key:
        raise RuntimeError("Enter a Gemini API key in the sidebar or set GEMINI_API_KEY.")
    return genai.Client(api_key=api_key)

def gemini_extract_quotation(text, category, rfq_text, api_key, model):
    client = get_gemini_client(api_key)
    prompt = f"""ASSIGNMENT TYPE: {category}\n\nCLIENT RFQ / REQUIREMENT (may be blank):\n{rfq_text or '[Not provided]'}\n\nCONSULTANT QUOTATION TEXT:\n{trim_text_for_ai(text)}"""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "response_mime_type": "application/json",
            "response_json_schema": AI_SCHEMA,
        },
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return parse_json_text(response.text)

def ai_extract_quotation(provider, text, category, rfq_text, api_key, model):
    if provider == "OpenRouter":
        return openrouter_extract_quotation(text, category, rfq_text, api_key, model)
    if provider == "Gemini Direct":
        return gemini_extract_quotation(text, category, rfq_text, api_key, model)
    raise RuntimeError("AI extraction is disabled.")

def apply_ai_result(record, result, provider):
    if result.get("company"):
        record["company"] = result["company"]
    if result.get("professional_fee_rm") is not None:
        record["fee"] = float(result["professional_fee_rm"])
    record["sst"] = result.get("sst_treatment") or record.get("sst", "Not stated")
    record["disbursement"] = result.get("disbursement") or "Not stated"
    record["duration"] = result.get("completion_period") or ""
    record["payment_terms"] = result.get("payment_terms") or ""
    scope = result.get("scope_summary") or ""
    methodology = result.get("methodology") or ""
    record["scope_summary"] = scope + (f"\n\nMethodology: {methodology}" if methodology else "")
    record["deliverables"] = result.get("deliverables") or ""
    extras = []
    if result.get("validity_period"):
        extras.append("Validity: " + result["validity_period"])
    if result.get("exclusions_limitations"):
        extras.append("Exclusions / limitations: " + result["exclusions_limitations"])
    if result.get("confidence_notes"):
        extras.append("AI extraction note: " + result["confidence_notes"])
    record["notes"] = "\n".join(extras)
    if record["category"] == "Market Study":
        record["scope_status"]["Highest & Best Use"] = result.get("highest_and_best_use", "No")
        record["scope_status"]["Financial / commercial viability"] = result.get("financial_commercial_viability", "No")
    record["ai_extracted"] = True
    record["ai_provider"] = provider
    return record


CSV_COLUMNS = [
    "Consultant",
    "Category",
    "Professional Fee RM",
    "SST Treatment",
    "Disbursement",
    "Completion Period",
    "Payment Terms",
    "Scope Summary",
    "Methodology",
    "Deliverables",
    "Highest and Best Use",
    "Financial Commercial Viability",
    "Validity Period",
    "Exclusions Limitations",
    "Source File",
    "Notes",
    "Scope Status JSON",
]


def clean_cell(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def parse_fee_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)
    text = clean_cell(value)
    if not text:
        return None
    m = re.search(r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)", text)
    return float(m.group(1).replace(",", "")) if m else None


def blank_scope_status(category):
    return {item: "No" for item in DEFAULT_SCOPE_ITEMS.get(category, [])}


def normalize_scope_status(status, category):
    allowed = {"Yes", "Partial", "No"}
    base = blank_scope_status(category)
    if isinstance(status, dict):
        for item in base:
            value = str(status.get(item, base[item])).strip().title()
            base[item] = value if value in allowed else "No"
    return base


def record_from_csv_row(row, row_number=1):
    category = clean_cell(row.get("Category")) or "Land Valuation"
    if category not in DEFAULT_SCOPE_ITEMS:
        # Be forgiving with common shorthand.
        low = category.lower()
        category = "Market Study" if "market" in low or "pricing" in low else "Land Valuation"

    consultant = clean_cell(row.get("Consultant")) or f"Consultant {row_number}"
    scope_summary = clean_cell(row.get("Scope Summary"))
    methodology = clean_cell(row.get("Methodology"))
    combined_scope = scope_summary
    if methodology:
        combined_scope += ("\n\n" if combined_scope else "") + "Methodology: " + methodology

    notes_bits = []
    notes = clean_cell(row.get("Notes"))
    validity = clean_cell(row.get("Validity Period"))
    exclusions = clean_cell(row.get("Exclusions Limitations"))
    if notes:
        notes_bits.append(notes)
    if validity:
        notes_bits.append("Validity: " + validity)
    if exclusions:
        notes_bits.append("Exclusions / limitations: " + exclusions)

    scope_status = None
    raw_scope = clean_cell(row.get("Scope Status JSON"))
    if raw_scope:
        try:
            scope_status = json.loads(raw_scope)
        except Exception:
            scope_status = None
    if not isinstance(scope_status, dict):
        scope_status = infer_scope_status(
            " ".join([combined_scope, clean_cell(row.get("Deliverables")), " ".join(notes_bits)]),
            category,
        )
    scope_status = normalize_scope_status(scope_status, category)

    hbu = clean_cell(row.get("Highest and Best Use")).title()
    viability = clean_cell(row.get("Financial Commercial Viability")).title()
    if category == "Market Study":
        if hbu in {"Yes", "Partial", "No"}:
            scope_status["Highest & Best Use"] = hbu
        if viability in {"Yes", "Partial", "No"}:
            scope_status["Financial / commercial viability"] = viability

    source_file = clean_cell(row.get("Source File"))
    return {
        "id": f"csv-{row_number}-{consultant}",
        "filename": source_file or "CSV record",
        "category": category,
        "company": consultant,
        "fee": parse_fee_value(row.get("Professional Fee RM")),
        "fee_candidates": [],
        "sst": clean_cell(row.get("SST Treatment")) or "Not stated",
        "disbursement": clean_cell(row.get("Disbursement")) or "Not stated",
        "duration": clean_cell(row.get("Completion Period")),
        "payment_terms": clean_cell(row.get("Payment Terms")),
        "scope_summary": combined_scope,
        "deliverables": clean_cell(row.get("Deliverables")),
        "notes": "\n".join(notes_bits),
        "raw_text": "",
        "scope_status": scope_status,
        "page_count": 0,
        "text_quality_score": 100,
        "text_quality_reasons": [],
        "local_text_quality_score": 100,
        "local_text_quality_reasons": [],
        "extraction_method": "CSV verified data",
        "scan_meta": {},
        "csv_source": True,
        "methodology": methodology,
        "validity_period": validity,
        "exclusions_limitations": exclusions,
    }


def csv_dataframe_to_records(df):
    # Accept files even when optional columns are absent.
    rename = {str(c).strip(): c for c in df.columns}
    normalized = pd.DataFrame()
    for col in CSV_COLUMNS:
        source = rename.get(col)
        normalized[col] = df[source] if source is not None else ""
    records = []
    warnings = []
    for i, row in normalized.iterrows():
        if not clean_cell(row.get("Consultant")) and not clean_cell(row.get("Professional Fee RM")):
            continue
        try:
            records.append(record_from_csv_row(row, i + 2))
        except Exception as e:
            warnings.append(f"Row {i + 2}: {e}")
    return records, warnings


def records_to_master_csv(records):
    rows = []
    for r in records:
        scope_text = r.get("scope_summary", "") or ""
        methodology = r.get("methodology", "") or ""
        if not methodology:
            m = re.search(r"(?:^|\n\n)Methodology:\s*(.*)$", scope_text, flags=re.I | re.S)
            if m:
                methodology = m.group(1).strip()
                scope_text = scope_text[:m.start()].strip()
        notes = r.get("notes", "") or ""
        validity = r.get("validity_period", "") or ""
        exclusions = r.get("exclusions_limitations", "") or ""
        if not validity:
            m = re.search(r"Validity:\s*([^\n]+)", notes, flags=re.I)
            if m:
                validity = m.group(1).strip()
        if not exclusions:
            m = re.search(r"Exclusions?\s*/?\s*limitations?:\s*([^\n]+)", notes, flags=re.I)
            if m:
                exclusions = m.group(1).strip()
        rows.append({
            "Consultant": r.get("company", ""),
            "Category": r.get("category", ""),
            "Professional Fee RM": r.get("fee") if r.get("fee") is not None else "",
            "SST Treatment": r.get("sst", ""),
            "Disbursement": r.get("disbursement", ""),
            "Completion Period": r.get("duration", ""),
            "Payment Terms": r.get("payment_terms", ""),
            "Scope Summary": scope_text,
            "Methodology": methodology,
            "Deliverables": r.get("deliverables", ""),
            "Highest and Best Use": r.get("scope_status", {}).get("Highest & Best Use", "") if r.get("category") == "Market Study" else "",
            "Financial Commercial Viability": r.get("scope_status", {}).get("Financial / commercial viability", "") if r.get("category") == "Market Study" else "",
            "Validity Period": validity,
            "Exclusions Limitations": exclusions,
            "Source File": r.get("filename", ""),
            "Notes": notes,
            "Scope Status JSON": json.dumps(r.get("scope_status", {}), ensure_ascii=False),
        })
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def empty_csv_template():
    return pd.DataFrame([{col: "" for col in CSV_COLUMNS}])


def merge_records(existing, incoming):
    """Update by Consultant + Category; otherwise append."""
    index = {(str(r.get("company", "")).strip().lower(), r.get("category")): i for i, r in enumerate(existing)}
    added = 0
    updated = 0
    for rec in incoming:
        key = (str(rec.get("company", "")).strip().lower(), rec.get("category"))
        if key in index:
            existing[index[key]] = rec
            updated += 1
        else:
            existing.append(rec)
            index[key] = len(existing) - 1
            added += 1
    return added, updated


def manual_blank_record(category):
    return {
        "id": f"manual-{len(st.session_state.records)+1}",
        "filename": "Manual entry",
        "category": category,
        "company": "",
        "fee": None,
        "fee_candidates": [],
        "sst": "Not stated",
        "disbursement": "Not stated",
        "duration": "",
        "payment_terms": "",
        "scope_summary": "",
        "deliverables": "",
        "notes": "",
        "raw_text": "",
        "scope_status": blank_scope_status(category),
        "page_count": 0,
        "text_quality_score": 100,
        "text_quality_reasons": [],
        "local_text_quality_score": 100,
        "local_text_quality_reasons": [],
        "extraction_method": "Manual verified data",
        "scan_meta": {},
        "csv_source": True,
        "methodology": "",
        "validity_period": "",
        "exclusions_limitations": "",
    }

def records_for_chat(records):
    slim = []
    for r in records:
        slim.append({
            "category": r.get("category"),
            "consultant": r.get("company"),
            "professional_fee_rm": r.get("fee"),
            "sst": r.get("sst"),
            "disbursement": r.get("disbursement"),
            "completion": r.get("duration"),
            "payment_terms": r.get("payment_terms"),
            "scope": r.get("scope_summary"),
            "deliverables": r.get("deliverables"),
            "notes": r.get("notes"),
            "scope_matrix": r.get("scope_status"),
        })
    return slim

def openrouter_chat(records, rfq_text, question, api_key, model):
    client = get_openrouter_client(api_key)
    context = json.dumps(records_for_chat(records), ensure_ascii=False, indent=2)
    messages = [
        {"role": "system", "content": "You are an internal procurement quotation analyst. Answer only from the RFQ and quotation data supplied. Clearly distinguish stated facts from your analysis. Do not invent missing terms. Be concise, commercially practical, and suitable for management review."},
        {"role": "user", "content": f"RFQ / REQUIREMENT:\n{rfq_text or '[Not provided]'}\n\nQUOTATION DATA:\n{context}\n\nQUESTION:\n{question}"},
    ]
    completion = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
    return completion.choices[0].message.content

st.markdown(
    """
    <div class="pro-header">
      <h1>Consultant Quotation Database</h1>
      <p>CSV-first consultant quotation database with optional PDF extraction, structured comparison and Management decision support.</p>
      <span class="pro-chip">Executive Blueprint</span>
      <span class="pro-chip">CSV source of truth</span>
      <span class="pro-chip">Manual review</span>
      <span class="pro-chip">Optional PDF assistant</span>
      <span class="pro-chip">Executive comparison</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Project / RFQ")
    st.text_area("RFQ / project requirement (optional)", key="rfq_text", height=180,
                 placeholder="Paste the requested scope here for reference...")

    st.divider()
    st.markdown('<div class="pro-section">AI extraction</div>', unsafe_allow_html=True)
    ai_provider = st.selectbox("AI provider", ["OpenRouter", "Gemini Direct", "Heuristic only"], index=0)
    ai_enabled = ai_provider != "Heuristic only"

    if ai_provider == "OpenRouter":
        env_key = os.getenv("OPENROUTER_API_KEY", "")
        api_key_input = st.text_input(
            "OpenRouter API key", value=env_key, type="password",
            help="Not saved to project JSON. You may alternatively set OPENROUTER_API_KEY in Windows."
        )
        ai_api_key = api_key_input or env_key
        st.caption("Recommended: set OPENROUTER_API_KEY in PowerShell. The app will load it automatically and will not store it in the project file.")
        preset = st.selectbox(
            "OpenRouter model",
            [
                "openrouter/free",
                "deepseek/deepseek-chat:free",
                "deepseek/deepseek-v3.2",
                "openai/gpt-5-mini",
                "google/gemini-2.5-flash",
                "google/gemini-2.5-flash-lite",
                "Custom model slug",
            ],
            index=0,
            help="For simple testing, use openrouter/free. To specifically use DeepSeek, choose a DeepSeek option."
        )
        if preset == "Custom model slug":
            ai_model = st.text_input("Model slug", value="deepseek/deepseek-chat:free")
        else:
            ai_model = preset
        st.markdown("**Scanned / image-only PDF recovery**")
        scan_mode = st.selectbox(
            "Scanned PDF handling",
            ["Auto scan when text is poor", "Always scan PDF", "Never scan PDF"],
            index=0,
            help="Auto mode first checks the PDF text layer. If it is empty/poor, the app renders each page as an image and uses vision OCR."
        )
        scan_engine_label = st.selectbox(
            "Recovery method",
            [
                "Page-image Vision OCR — recommended",
                "OpenRouter PDF parser — Mistral OCR",
                "OpenRouter PDF parser — Cloudflare AI",
            ],
            index=0,
        )
        if scan_engine_label.startswith("Page-image"):
            scan_engine = "vision-ocr"
            st.caption("Recommended for image-only quotations like the Rahim & Co PDF. Pages are rendered locally, then sent as images to the selected OpenRouter model.")
        elif "Mistral" in scan_engine_label:
            scan_engine = "mistral-ocr"
            st.caption("Uses OpenRouter's Mistral OCR PDF parser and may incur OCR charges.")
        else:
            scan_engine = "cloudflare-ai"
            st.caption("Free PDF parser; more suitable for digital PDFs than image-only scans.")

        if not ai_api_key:
            st.info("Add your OpenRouter key to enable AI extraction, PDF scanning and the AI Analyst tab.")
    elif ai_provider == "Gemini Direct":
        env_key = os.getenv("GEMINI_API_KEY", "")
        api_key_input = st.text_input(
            "Gemini API key", value=env_key, type="password",
            help="Not saved to project JSON. You may alternatively set GEMINI_API_KEY in Windows."
        )
        ai_api_key = api_key_input or env_key
        ai_model = st.selectbox("Gemini model", ["gemini-3.1-flash-lite", "gemini-3.6-flash"], index=0)
        scan_mode = "Never scan PDF"
        scan_engine = ""
    else:
        ai_api_key = ""
        ai_model = ""
        scan_mode = "Never scan PDF"
        scan_engine = ""

    st.divider()
    st.markdown('<div class="pro-section">Project data</div>', unsafe_allow_html=True)
    if st.button("Clear all quotations"):
        st.session_state.records = []
        st.rerun()
    if st.session_state.records:
        st.download_button("Download project JSON", json.dumps(st.session_state.records, indent=2),
                           "quotation_project.json", "application/json")
    restore = st.file_uploader("Restore project JSON", type=["json"], key="restore")
    if restore and st.button("Load project"):
        st.session_state.records = json.load(restore)
        st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. CSV Database",
    "2. PDF Assistant",
    "3. Comparison Dashboard",
    "4. Scope Matrix",
    "5. Export & Recommendation",
    "6. AI Analyst",
])

with tab1:
    st.subheader("CSV quotation database")
    st.markdown(
        '<div class="pro-note"><b>Recommended workflow:</b> treat the CSV as the verified source of truth. '
        'PDF extraction is optional and can be used only to help prepare a new record before it is reviewed and saved back to CSV.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.3, 1])
    with left:
        csv_upload = st.file_uploader(
            "Upload master quotation CSV",
            type=["csv"],
            key="master_csv_upload",
            help="The app accepts the V10 template. Missing optional columns are created automatically.",
        )
        if csv_upload is not None:
            replace_mode = st.radio(
                "When loading the CSV",
                ["Replace current database", "Merge / update current database"],
                horizontal=True,
                key="csv_load_mode",
            )
            if st.button("Load CSV database", type="primary", key="load_csv_database"):
                try:
                    df_in = pd.read_csv(csv_upload)
                    incoming, warnings = csv_dataframe_to_records(df_in)
                    if replace_mode == "Replace current database":
                        st.session_state.records = incoming
                        added, updated = len(incoming), 0
                    else:
                        added, updated = merge_records(st.session_state.records, incoming)
                    st.success(f"CSV loaded: {added} added, {updated} updated. {len(st.session_state.records)} total quotation record(s).")
                    for warning in warnings:
                        st.warning(warning)
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not load CSV: {e}")

    with right:
        template_csv = empty_csv_template().to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Download blank CSV template",
            template_csv,
            "quotation_master_template.csv",
            "text/csv",
            use_container_width=True,
        )
        if st.session_state.records:
            master_df = records_to_master_csv(st.session_state.records)
            st.download_button(
                "Download current master CSV",
                master_df.to_csv(index=False).encode("utf-8-sig"),
                "quotation_master.csv",
                "text/csv",
                use_container_width=True,
            )
        st.caption("UTF-8 CSV is used so the file opens cleanly in Excel and can be re-uploaded later.")

    st.divider()
    st.subheader("Manual verified entry")
    st.caption("Use this when you have already checked the quotation PDF yourself and only want to enter the confirmed commercial data.")
    mc1, mc2, mc3 = st.columns([1, 1.2, 1])
    manual_category = mc1.selectbox("Category", ["Land Valuation", "Market Study"], key="manual_category")
    manual_company = mc2.text_input("Consultant", key="manual_company")
    manual_fee = mc3.number_input("Professional fee (RM)", min_value=0.0, value=0.0, step=500.0, key="manual_fee")
    mm1, mm2, mm3 = st.columns(3)
    manual_sst = mm1.text_input("SST treatment", key="manual_sst", placeholder="e.g. Additional 8%")
    manual_duration = mm2.text_input("Completion period", key="manual_duration", placeholder="e.g. 14 working days")
    manual_source = mm3.text_input("Source PDF filename", key="manual_source", placeholder="e.g. Q V Citaglobal.pdf")
    manual_payment = st.text_area("Payment terms", key="manual_payment", height=80)
    manual_scope = st.text_area("Scope summary", key="manual_scope", height=100)
    manual_method = st.text_area("Methodology", key="manual_method", height=75)
    manual_deliverables = st.text_area("Deliverables", key="manual_deliverables", height=75)
    manual_notes = st.text_area("Notes / exclusions / validity", key="manual_notes", height=75)
    if st.button("Add verified record", key="add_manual_verified"):
        if not manual_company.strip():
            st.warning("Enter the consultant name first.")
        else:
            rec = manual_blank_record(manual_category)
            rec.update({
                "company": manual_company.strip(),
                "fee": manual_fee or None,
                "sst": manual_sst.strip() or "Not stated",
                "duration": manual_duration.strip(),
                "filename": manual_source.strip() or "Manual entry",
                "payment_terms": manual_payment.strip(),
                "scope_summary": manual_scope.strip() + (("\n\nMethodology: " + manual_method.strip()) if manual_method.strip() else ""),
                "methodology": manual_method.strip(),
                "deliverables": manual_deliverables.strip(),
                "notes": manual_notes.strip(),
            })
            rec["scope_status"] = infer_scope_status(
                " ".join([rec["scope_summary"], rec["deliverables"], rec["notes"]]),
                manual_category,
            )
            added, updated = merge_records(st.session_state.records, [rec])
            st.success(f"Verified record saved to the in-memory database ({added} added, {updated} updated). Download the master CSV to keep it permanently.")
            st.rerun()

    st.divider()
    st.subheader("Review database")
    if not st.session_state.records:
        st.info("No quotation records loaded yet. Upload the CSV template or add a verified record manually.")
    else:
        for idx, r in enumerate(st.session_state.records):
            source_tag = "CSV / verified" if r.get("csv_source") or "verified" in r.get("extraction_method", "").lower() else r.get("extraction_method", "PDF assistant")
            with st.expander(f'{r.get("company", "Consultant")} — {r.get("category", "")} · {source_tag}', expanded=False):
                a, b, c = st.columns([2, 1, 1])
                r["company"] = a.text_input("Consultant", r.get("company", ""), key=f"db-company-{idx}")
                r["fee"] = b.number_input("Professional fee (RM)", min_value=0.0, value=float(r.get("fee") or 0), step=500.0, key=f"db-fee-{idx}")
                r["duration"] = c.text_input("Completion period", r.get("duration", ""), key=f"db-duration-{idx}")
                d1, d2 = st.columns(2)
                r["sst"] = d1.text_input("SST treatment", r.get("sst", ""), key=f"db-sst-{idx}")
                r["disbursement"] = d2.text_input("Disbursement / reimbursements", r.get("disbursement", ""), key=f"db-disb-{idx}")
                r["payment_terms"] = st.text_area("Payment terms", r.get("payment_terms", ""), height=80, key=f"db-pay-{idx}")
                r["scope_summary"] = st.text_area("Scope / methodology", r.get("scope_summary", ""), height=120, key=f"db-scope-{idx}")
                r["deliverables"] = st.text_area("Deliverables", r.get("deliverables", ""), height=75, key=f"db-deliv-{idx}")
                r["notes"] = st.text_area("Notes / exclusions / validity", r.get("notes", ""), height=90, key=f"db-notes-{idx}")
                st.markdown("**Scope checklist**")
                cols = st.columns(3)
                r.setdefault("scope_status", blank_scope_status(r.get("category", "Land Valuation")))
                for j, item in enumerate(DEFAULT_SCOPE_ITEMS[r["category"]]):
                    current = r["scope_status"].get(item, "No")
                    if current not in ["Yes", "Partial", "No"]:
                        current = "No"
                    r["scope_status"][item] = cols[j % 3].selectbox(
                        item,
                        ["Yes", "Partial", "No"],
                        index=["Yes", "Partial", "No"].index(current),
                        key=f"db-scope-status-{idx}-{j}",
                    )
                if st.button("Remove record", key=f"db-remove-{idx}"):
                    st.session_state.records.pop(idx)
                    st.rerun()

with tab2:
    st.subheader("Optional PDF extraction assistant")
    st.markdown(
        '<div class="pro-note"><b>Important:</b> PDF extraction is an assistant only. Review the fields, then download the master CSV. '
        'The CSV remains the recommended source of truth for future comparisons.</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 2])
    category = c1.selectbox("Quotation type", ["Land Valuation", "Market Study"], key="pdf_category")
    uploads = c2.file_uploader("Upload consultant quotation PDF(s)", type=["pdf"], accept_multiple_files=True, key="pdf_uploads")
    if uploads and st.button("Extract PDF quotation(s)", type="primary", key="extract_pdfs"):
        incoming = []
        for u in uploads:
            rec = make_record(u, category)
            quality = assess_text_quality(rec["raw_text"], rec.get("page_count", 1))
            should_scan = (
                ai_provider == "OpenRouter"
                and scan_mode != "Never scan PDF"
                and (scan_mode == "Always scan PDF" or quality["poor"])
            )
            if should_scan:
                if not ai_api_key:
                    rec["scan_error"] = "OpenRouter API key is required for scanned-PDF recovery."
                    st.warning(f"{u.name}: image-only/poor text detected, but no OpenRouter key is available. The CSV workflow can still be used manually.")
                else:
                    try:
                        with st.spinner(f"Recovering scanned PDF {u.name}..."):
                            pdf_bytes = u.getvalue()
                            if scan_engine == "vision-ocr":
                                scanned_text, scan_meta = openrouter_vision_ocr(pdf_bytes, u.name, ai_api_key, ai_model)
                                method_label = "Page-image Vision OCR + heuristic"
                            else:
                                scanned_text, scan_meta = openrouter_pdf_scan(pdf_bytes, u.name, ai_api_key, ai_model, engine=scan_engine)
                                method_label = f"OpenRouter PDF scan ({scan_engine}) + heuristic"
                            rec = make_record(u, category, text_override=scanned_text, extraction_method=method_label, scan_meta=scan_meta)
                        st.success(f"{u.name}: scanned-PDF text recovered.")
                    except Exception as e:
                        rec["scan_error"] = str(e)
                        st.error(f"{u.name}: scanned-PDF recovery failed: {e}")
            if ai_enabled and ai_api_key:
                try:
                    with st.spinner(f"Structuring {u.name} with {ai_provider}..."):
                        ai_result = ai_extract_quotation(ai_provider, rec["raw_text"], category, st.session_state.get("rfq_text", ""), ai_api_key, ai_model)
                        rec = apply_ai_result(rec, ai_result, ai_provider)
                        rec["extraction_method"] = rec.get("extraction_method", "PDF") + " + AI structured extraction"
                except Exception as e:
                    rec["ai_error"] = str(e)
                    st.warning(f"{u.name}: structured AI extraction failed; heuristic results retained. {e}")
            rec["csv_source"] = False
            incoming.append(rec)
        added, updated = merge_records(st.session_state.records, incoming)
        st.success(f"PDF assistant finished: {added} added, {updated} updated. Review these records in the CSV Database tab and export the master CSV.")
        st.rerun()

    if st.session_state.records:
        st.markdown("### Current PDF-assisted / database records")
        preview = records_to_master_csv(st.session_state.records)[[
            "Consultant", "Category", "Professional Fee RM", "SST Treatment", "Completion Period", "Source File"
        ]]
        st.dataframe(preview, use_container_width=True, hide_index=True)

with tab3:
    cat = st.radio("View comparison", ["Land Valuation", "Market Study"], horizontal=True, key="comparison_category")
    subset = [r for r in st.session_state.records if r["category"] == cat]
    if not subset:
        st.info(f"No {cat} quotations loaded.")
    else:
        st.subheader("Scoring weights")
        cols = st.columns(len(DEFAULT_WEIGHTS[cat]))
        weights = {}
        for i, (k, v) in enumerate(DEFAULT_WEIGHTS[cat].items()):
            weights[k] = cols[i].number_input(k, 0, 100, v, 5, key=f"w-v10-{cat}-{i}")
        if sum(weights.values()) != 100:
            st.warning(f"Weights total {sum(weights.values())}%. Set them to 100% for a clean comparison.")
        scores = compute_scores(st.session_state.records, cat, weights)
        winner = scores[0]
        valid_fees = [float(r.get("fee") or 0) for r in subset if float(r.get("fee") or 0) > 0]
        lowest_fee = min(valid_fees) if valid_fees else 0
        valid_days = [(duration_to_days(r.get("duration", "")), r.get("duration", "")) for r in subset]
        valid_days = [x for x in valid_days if x[0] is not None]
        fastest_label = min(valid_days, key=lambda x: x[0])[1] if valid_days else "Not stated"
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Consultants reviewed", len(subset))
        k2.metric("Lowest quoted fee", f"RM {lowest_fee:,.0f}" if lowest_fee else "Not stated")
        k3.metric("Fastest completion", fastest_label or "Not stated")
        k4.metric("Current leader", f'{winner[0]["company"]} · {winner[1]}/100')
        st.markdown(
            f'<div class="pro-note"><b>Indicative recommendation:</b> {winner[0]["company"]} currently ranks highest at {winner[1]}/100 under the selected scoring weights. Confirm scope and commercial terms before appointment.</div>',
            unsafe_allow_html=True,
        )
        df = pd.DataFrame([{
            "Consultant": r["company"],
            "Data source": r.get("extraction_method", "CSV"),
            "Fee (RM)": r.get("fee"),
            "SST": r.get("sst", ""),
            "Disbursement": r.get("disbursement", ""),
            "Completion": r.get("duration", "") or "-",
            "Payment Terms": r.get("payment_terms", "") or "Not stated",
            "Scope Score": round(scope_numeric(r.get("scope_status", {})), 1),
            "Overall Score": total,
        } for r, total, _ in scores])
        st.dataframe(df, use_container_width=True, hide_index=True)
        chart = pd.DataFrame({"Consultant": [r["company"] for r, t, c in scores], "Overall Score": [t for r, t, c in scores]}).set_index("Consultant")
        st.bar_chart(chart)
        st.caption("The score is decision-support only. Verified CSV data should still be checked against the signed/final quotation before appointment.")

with tab4:
    cat = st.radio("Scope matrix", ["Land Valuation", "Market Study"], horizontal=True, key="scope_matrix_category")
    subset = [r for r in st.session_state.records if r["category"] == cat]
    if not subset:
        st.info(f"No {cat} quotations loaded.")
    else:
        rows = []
        for item in DEFAULT_SCOPE_ITEMS[cat]:
            row = {"Scope Item": item}
            for r in subset:
                row[r["company"]] = r.get("scope_status", {}).get(item, "No")
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

with tab5:
    if not st.session_state.records:
        st.info("No quotations loaded.")
    else:
        master_df = records_to_master_csv(st.session_state.records)
        st.subheader("Master CSV")
        st.dataframe(master_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download master quotation CSV",
            master_df.to_csv(index=False).encode("utf-8-sig"),
            "quotation_master.csv",
            "text/csv",
            type="primary",
        )
        st.caption("Keep this CSV as the verified database. Next time, load it directly in Tab 1; you do not need to OCR the same PDFs again.")

        lines = []
        for cat in ["Land Valuation", "Market Study"]:
            subset = [r for r in st.session_state.records if r["category"] == cat]
            if subset:
                scores = compute_scores(st.session_state.records, cat, DEFAULT_WEIGHTS[cat])
                r, score, _ = scores[0]
                lines.append(f"{cat}: Recommend {r['company']} based on the current scoring model ({score}/100), subject to final scope and commercial confirmation.")
        fallback_summary = "\n\n".join(lines)
        st.markdown("### Management recommendation")
        if st.button("Generate Management Recommendation", type="primary", key="v10_management_recommendation"):
            if ai_provider == "OpenRouter" and ai_api_key:
                try:
                    with st.spinner("Preparing Management recommendation..."):
                        st.session_state.management_recommendation = openrouter_chat(
                            st.session_state.records,
                            st.session_state.get("rfq_text", ""),
                            "Prepare a concise Management recommendation for consultant appointment. Use only the verified quotation database. Cover each category separately, state fees, scope strengths, completion, payment/commercial points, qualifications and overall value. Do not invent facts.",
                            ai_api_key,
                            ai_model,
                        )
                except Exception as e:
                    st.warning(f"AI recommendation unavailable ({e}). Showing scoring-based summary instead.")
                    st.session_state.management_recommendation = fallback_summary
            else:
                st.session_state.management_recommendation = fallback_summary
        st.text_area("Management-ready recommendation", st.session_state.get("management_recommendation", fallback_summary), height=240, key="v10_management_text")

with tab6:
    st.subheader("Optional AI quotation analyst")
    st.caption("The analyst reads the structured database, not the PDFs. This keeps PDF extraction separate from decision analysis.")
    if not st.session_state.records:
        st.info("Load the quotation CSV first.")
    elif ai_provider != "OpenRouter":
        st.info("The interactive analyst currently uses OpenRouter. Select OpenRouter in the sidebar if you want to use it.")
    elif not ai_api_key:
        st.warning("No OpenRouter key is loaded. The CSV comparison dashboard continues to work without AI.")
    else:
        examples = [
            "Which consultant offers the best overall value and why?",
            "Compare only the Market Study scope.",
            "What clarification questions should I send before appointment?",
            "Draft a concise Management recommendation.",
        ]
        chosen = st.selectbox("Quick question", ["Custom question"] + examples, key="v10_quick_question")
        question = st.text_area("Ask the analyst", value="" if chosen == "Custom question" else chosen, height=100, key="v10_question")
        if st.button("Ask AI Analyst", type="primary", key="v10_ask_ai"):
            if not question.strip():
                st.warning("Enter a question first.")
            else:
                try:
                    with st.spinner("Analysing verified quotation data..."):
                        answer = openrouter_chat(st.session_state.records, st.session_state.get("rfq_text", ""), question, ai_api_key, ai_model)
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"AI Analyst failed: {e}")

st.divider()
st.caption("V10 · CSV-first workflow. Keep the exported master CSV as the verified database; PDF/AI extraction is optional assistance only.")

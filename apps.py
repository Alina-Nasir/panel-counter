import streamlit as st
import os, io, re, textwrap, base64, csv
from collections import defaultdict, Counter
from PIL import Image, ImageDraw
import fitz  # PyMuPDF

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Electrical Drawing Component Counter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { background:#f8fafc; color:#0f172a; font-family:'Inter',sans-serif; }
    header,footer,#MainMenu { visibility:hidden; }

    .header-container {
        display:flex; align-items:center; gap:25px;
        background:linear-gradient(135deg,#1e40af 0%,#1d4ed8 100%);
        border-radius:16px; padding:32px 35px;
        margin-bottom:26px; box-shadow:0 10px 25px rgba(29,78,216,0.15);
    }
    .header-title { font-size:30px; font-weight:700; color:#fff; margin-bottom:6px; }
    .header-subtitle { font-size:15px; color:#bfdbfe; }
    .logo-wrapper {
        display:flex; flex-direction:column; align-items:center;
        background:#fff; padding:12px 16px; border-radius:16px;
        box-shadow:0 8px 25px rgba(0,0,0,0.2); gap:6px;
    }
    .logo-image { height:90px; width:130px; object-fit:contain; }

    .metric-container { display:flex; gap:12px; margin-bottom:22px; flex-wrap:wrap; }
    .metric-card {
        flex:1; min-width:105px; background:#fff; border:1px solid #e2e8f0;
        border-radius:14px; padding:16px 12px; text-align:center;
        box-shadow:0 4px 20px rgba(0,0,0,.05);
    }
    .metric-label {
        font-size:11px; color:#64748b; text-transform:uppercase;
        letter-spacing:1.3px; margin-bottom:5px; font-weight:600;
    }
    .metric-value { font-size:28px; font-weight:700; color:#1d4ed8; }
    .metric-total { background:linear-gradient(135deg,#1e40af,#1d4ed8); color:#fff; border:none; }
    .metric-total .metric-label { color:#bfdbfe; }
    .metric-total .metric-value { color:#fff; }

    div.stButton > button:first-child {
        background:linear-gradient(90deg,#3b82f6 0%,#1d4ed8 100%) !important;
        color:#fff !important; font-weight:700 !important;
        border:none !important; border-radius:8px !important;
        padding:12px 24px !important; font-size:16px !important;
        width:100% !important; box-shadow:0 4px 15px rgba(29,78,216,.2) !important;
    }
    div.stButton > button:first-child:hover { transform:translateY(-2px) !important; }

    div[data-testid="stFileUploader"] {
        border:2px dashed rgba(59,130,246,.3) !important;
        border-radius:12px !important; padding:15px !important;
        background:#fff !important;
    }

    .custom-table-container {
        width:100%; overflow-x:auto; border-radius:12px;
        border:1px solid #e2e8f0; background:#fff; margin-bottom:20px;
        box-shadow:0 4px 20px rgba(0,0,0,.02);
    }
    .custom-table { width:100%; border-collapse:collapse; font-size:13.5px; }
    .custom-table th {
        background:#f1f5f9; color:#1e293b; padding:11px 12px;
        font-weight:600; text-transform:uppercase; font-size:11px;
        letter-spacing:.8px; border-bottom:2px solid #e2e8f0;
    }
    .custom-table td { padding:10px 12px; border-bottom:1px solid #e2e8f0; color:#334155; }
    .custom-table tr:last-child td { border-bottom:none; }
    .custom-table tr:hover td { background:#f8fafc; }
    .spec-cell { font-weight:600; color:#0f172a; }
    .count-cell { font-weight:700; color:#1d4ed8; }

    .section-subheader {
        font-size:18px; font-weight:600; color:#0f172a;
        margin-bottom:14px; border-left:3.5px solid #3b82f6; padding-left:10px;
    }
    .scanning-card {
        background:#fff; border:1px solid #e2e8f0; border-radius:16px;
        padding:50px 20px; text-align:center; margin:20px 0;
        box-shadow:0 8px 30px rgba(0,0,0,.05);
    }
    .scanning-spinner {
        width:60px; height:60px; border:4px solid rgba(59,130,246,.1);
        border-top:4px solid #3b82f6; border-radius:50%;
        margin:0 auto 25px auto; animation:spin 1s linear infinite;
    }
    .scanning-text { font-size:20px; font-weight:600; color:#0f172a; margin-bottom:8px; }
    .scanning-subtext { font-size:14px; color:#64748b; }
    @keyframes spin { 0%{transform:rotate(0)} 100%{transform:rotate(360deg)} }

    .custom-alert {
        display:flex; align-items:flex-start; padding:16px;
        border-radius:10px; margin-bottom:20px; font-size:14.5px;
    }
    .error-alert   { background:rgba(239,68,68,.05); border:1px solid rgba(239,68,68,.15); color:#dc2626; }
    .info-alert    { background:rgba(59,130,246,.05); border:1px solid rgba(59,130,246,.15); color:#2563eb; }
    .warn-alert    { background:rgba(245,158,11,.05); border:1px solid rgba(245,158,11,.25); color:#b45309; }
    .success-alert { background:rgba(16,185,129,.05); border:1px solid rgba(16,185,129,.2); color:#059669; }
    .alert-icon { font-size:20px; margin-right:12px; }
    .alert-content strong { color:#0f172a; }

    .debug-block {
        background:#1e293b; color:#e2e8f0; padding:8px 12px;
        border-radius:6px; margin-bottom:6px; font-family:'Courier New',monospace;
        font-size:12.5px; word-break:break-all;
    }
    .debug-block .match   { color:#10b981; font-weight:700; }
    .debug-block .no-match { color:#f59e0b; }
    .debug-count { color:#3b82f6; font-size:11px; margin-left:8px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def show_info(msg):
    st.html(f'<div class="custom-alert info-alert"><span class="alert-icon">ℹ️</span>'
            f'<div class="alert-content"><strong>Status</strong><br>{msg}</div></div>')

def show_error(msg):
    st.html(f'<div class="custom-alert error-alert"><span class="alert-icon">⚠️</span>'
            f'<div class="alert-content"><strong>Error</strong><br>{msg}</div></div>')

def show_warn(msg):
    st.html(f'<div class="custom-alert warn-alert"><span class="alert-icon">🔶</span>'
            f'<div class="alert-content"><strong>Warning</strong><br>{msg}</div></div>')

def show_success(msg):
    st.html(f'<div class="custom-alert success-alert"><span class="alert-icon">✅</span>'
            f'<div class="alert-content"><strong>Success</strong><br>{msg}</div></div>')

def pdf_to_image(pdf_bytes, dpi=150):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) == 0: return None
        pix = doc.load_page(0).get_pixmap(dpi=dpi)
        return Image.open(io.BytesIO(pix.tobytes("png")))
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def get_iou(a, b):
    xA, yA = max(a[0], b[0]), max(a[1], b[1])
    xB, yB = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter <= 0: return 0.0
    aA = (a[2]-a[0])*(a[3]-a[1]); bB = (b[2]-b[0])*(b[3]-b[1])
    return inter / (aA + bB - inter + 1e-5)

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ============================================================
# COMPONENT DEFINITIONS
# ============================================================
PANEL_TAG_ORDER = ["MDB","SMDB","USMDB","LV","MLV","LPDB","UDB","DB",
                   "ACDB","DCDB","APFC","MLDB","PNL"]

PANEL_PATTERNS = [
    ("USMDB", re.compile(r'(?:^|\s)U[\s\.\-_]?S[\s\.\-_]?M[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("SMDB",  re.compile(r'(?:^|\s)S[\s\.\-_]?M[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("LPDB",  re.compile(r'(?:^|\s)L[\s\.\-_]?P[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("UDB",   re.compile(r'(?:^|\s)U[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("MLV",   re.compile(r'(?:^|\s)M[\s\.\-_]?L[\s\.\-_]?V(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("MDB",   re.compile(r'(?:^|\s)M[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,25})?\b', re.I)),
    ("LV",    re.compile(r'(?:^L[\s\.\-_]?V(?:[\s\.\-_/]*[\w()\-]{0,15})?|\sL[\s\.\-_]?V[\s\.\-_]*P(?:ANEL|NL)[\s\.\-_/]*[\w()\-]{0,15})\b', re.I)),
    ("DB",    re.compile(r'(?:^|\s)D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{1,25})?\b', re.I)),
    ("ACDB",  re.compile(r'(?:^|\s)A[\s\.\-_]?C[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("DCDB",  re.compile(r'(?:^|\s)D[\s\.\-_]?C[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("APFC",  re.compile(r'(?:^|\s)A[\s\.\-_]?P[\s\.\-_]?F[\s\.\-_]?C(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("MLDB",  re.compile(r'(?:^|\s)M[\s\.\-_]?L[\s\.\-_]?D[\s\.\-_]?B(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("PNL",   re.compile(r'(?:^|\s)P(?:ANEL|NL)[\s\.\-_/]*\d+[A-Z]?\b', re.I)),
]

BREAKER_AMPS_FIRST = re.compile(
    r'\b(ACB|MCCB|MCB|RCBO|RCCB|ELCB|FUSE|VCB|LBS|SFU)[\s\.\-:]*'
    r'(\d+)\s*A\s*[/\-]?\s*(\d)?\s*P?', re.I)

BREAKER_POLES_FIRST = re.compile(
    r'\b(ACB|MCCB|MCB|RCBO|RCCB|ELCB|FUSE|VCB|LBS|SFU)[\s\.\-:]*'
    r'(\d)\s*P\s*[/\-]?\s*(\d+)\s*A', re.I)

BARE_BREAKER = re.compile(r'\b(\d{1,4})\s*A\s*[/\-]?\s*(\d)\s*P\b', re.I)

BARE_PREFIX = re.compile(r'\b(ACB|MCCB|MCB|RCBO|RCCB|ELCB|FUSE|VCB|LBS|SFU)\b', re.I)

CABLE_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*C?\s*[xX×]\s*(\d+(?:\.\d+)?)\s*'
    r'(?:sq\.?\s*mm|mm²|mm2)'
    r'(?:[\s\/\-]*((?:AL|CU|ALUMINIUM|COPPER)))?'
    r'(?:[\s\/\-]*(?:XLPE|PVC|FRLS|LSZH|FRLSH|ARMOURED|UNARMOURED))*', re.I)

VALID_CONDUIT_SIZES = {16, 20, 25, 32, 40, 50, 65, 75, 90, 110, 125, 160, 200}

CONDUIT_PATTERN = re.compile(
    r'(?:(\d+)\s*-\s*)?'
    r'(?:[Øø#\u2300\u2205])?\s*'
    r'(\d+)\s*[\-\s]?(?:U\s*-\s*)?'
    r'(PVC|GI|EMT|IMC|RSC)'
    r'(?:\s*PIPE|\s*CONDUIT)?\b', re.I)

FIXTURE_PATTERN = re.compile(
    r'\b(LED|DOWNLIGHT|FLOODLIGHT|BATTEN|LUMINAIRE|FITTING|SPOTLIGHT|'
    r'PANEL\s*LIGHT|EMERGENCY\s*LIGHT)'
    r'(?:[\s\-:]*'
    r'((?:\d+\s*[xX×]\s*)?\d+)'
    r'\s*W\b)?', re.I)

VALID_BOX_DEPTHS = {30, 35, 40, 45, 47, 50, 60, 75, 100, 150}

BOX_PATTERN = re.compile(
    r'(\d+)\s*[xX×]\s*(\d+)\s*[xX×]\s*(\d+)\s*mm\s*'
    r'(ELE\.?\s*BOX|ELEC\.?\s*BOX|J\.?\s*BOX|JB|PULL\s*BOX)', re.I)

TRANSFORMER_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*kVA\s*'
    r'(?:(\d+(?:\.\d+)?)\s*kV\s*\/\s*(\d+(?:\.\d+)?)\s*(?:kV|V))?', re.I)

GENERATOR_PATTERN = re.compile(
    r'(?:'
        r'\bG\s*(\d+)\b[\s\-:]*'
        r'|'
        r'(?:NE\s+)?GENERATOR[\s\-]*(\d+)?[\s\-:]*'
    r')?'
    r'(\d+(?:\.\d+)?)\s*kVA\s*'
    r'(?:[\s\/]*(?:415)?\s*(?:V)?\s*)?'
    r'(DIESEL|GAS|NATURAL\s*GAS|PRIME\s*RATED)?',
    re.I)

MOTOR_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*kW\s*'
    r'(?:[\s\/\-]*(?:(\d)\s*PH(?:ASE)?))?'
    r'(?:[\s\/\-]*(\d+)\s*RPM)?'
    r'[\s\/\-]*(?:MOTOR|PUMP)', re.I)

COLOR_MAP = {
    "MDB":(220,38,38),"SMDB":(234,88,12),"USMDB":(217,119,6),
    "LV":(16,185,129),"MLV":(5,150,105),"LPDB":(59,130,246),
    "UDB":(139,92,246),"DB":(236,72,153),"ACDB":(168,85,247),
    "DCDB":(6,182,212),"APFC":(244,114,182),"MLDB":(34,197,94),"PNL":(100,116,139),
    "BREAKER":(255,140,0),"CABLE":(22,163,74),"CONDUIT":(6,148,162),
    "FIXTURE":(234,179,8),"BOX":(124,58,237),
    "TRANSFORMER":(190,24,93),"GENERATOR":(220,38,38),"MOTOR":(20,184,166),
}

# ============================================================
# CLASSIFIERS
# ============================================================
CORE_PANEL_TAGS = ["USMDB","SMDB","LPDB","UDB","MLV","MDB","LV",
                   "ACDB","DCDB","APFC","MLDB","DB"]

PANEL_SUFFIX_STOPWORDS = ("TCL", "MDL", "FT", "FOR", "RAW", "UPS",
                          "COMPARTMENT", "COMPART")

def classify_panels(tok):
    raw = tok.strip().upper()
    if len(raw) < 2: return []
    results, seen = [], set()
    for tag, pat in PANEL_PATTERNS:
        for m in pat.finditer(raw):
            frag = m.group(0)
            compact = re.sub(r'[\.\s_\-\/]+', '', frag.upper())
            for core in CORE_PANEL_TAGS:
                if not compact.startswith(core): continue
                suffix = compact[len(core):]
                for sw in PANEL_SUFFIX_STOPWORDS:
                    if sw in suffix:
                        suffix = suffix[:suffix.index(sw)]
                if "(" in suffix:
                    suffix = suffix.split("(")[0]
                suffix = suffix.strip("-()")
                label = core + ("-" + suffix if suffix else "")
                if core == "SMDB" and compact.startswith("USMDB"): continue
                if core == "DB" and any(compact.startswith(p) for p in
                        ("SMDB","USMDB","LPDB","UDB","MDB","LV","MLV","ACDB","DCDB","MLDB")):
                    continue
                if core == "LV" and compact.startswith("MLV"): continue
                key = (core, label)
                if key not in seen:
                    seen.add(key); results.append(key)
                break
    return results

def classify_breakers(tok):
    raw = tok.upper()
    results = []
    seen_spans = set()

    for m in BREAKER_AMPS_FIRST.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        btype = m.group(1).upper()
        amps = int(m.group(2))
        poles = int(m.group(3)) if m.group(3) else None
        if amps < 1 or amps > 10000: continue
        label = btype + f"-{amps}A" + (f"-{poles}P" if poles else "")
        results.append(("BREAKER", label))

    for m in BREAKER_POLES_FIRST.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        btype = m.group(1).upper()
        poles = int(m.group(2))
        amps = int(m.group(3))
        if amps < 1 or amps > 10000: continue
        label = btype + f"-{amps}A-{poles}P"
        results.append(("BREAKER", label))

    panel_context = any(kw in raw for kw in
                        ("FEEDER", "PILLAR", "PANEL", "DB-", "MDB-",
                         "SMDB-", "LPDB-", "UDB-", "SUBSTATION", "PUMP",
                         "CCTV", "UPS", "STADIUM", "ROOM", "BOQ"))
    bare_matches = list(BARE_BREAKER.finditer(raw))
    accept_bare = panel_context or len(bare_matches) > 1
    if accept_bare:
        for m in bare_matches:
            span = (m.start(), m.end())
            if span in seen_spans: continue
            seen_spans.add(span)
            amps = int(m.group(1))
            poles = int(m.group(2))
            if amps < 1 or amps > 10000: continue
            results.append(("BREAKER", f"CB-{amps}A-{poles}P"))

    for m in BARE_PREFIX.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        results.append(("BREAKER", m.group(1).upper()))

    return results

def classify_cables(tok):
    raw = tok.upper()
    results = []
    seen_spans = set()
    for m in CABLE_PATTERN.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        cores = m.group(1); size = m.group(2)
        material = (m.group(3) or "").upper()
        label = f"{cores}C x {size}mm²"
        if material: label += f" {material}"
        results.append(("CABLE", label))
    return results

def classify_conduits(tok):
    raw = tok.upper()
    results = []
    seen_spans = set()
    for m in CONDUIT_PATTERN.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        size = int(m.group(2)); mat = m.group(3).upper()
        if mat == "PVC" and size not in VALID_CONDUIT_SIZES: continue
        count = int(m.group(1)) if m.group(1) else 1
        results.append(("CONDUIT", f"{count}x {mat} {size}mm"))
    return results

def classify_fixtures(tok):
    raw = tok.upper()
    results = []
    seen_spans = set()
    for m in FIXTURE_PATTERN.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        ftype = re.sub(r'\s+', ' ', m.group(1)).upper()
        watt = (m.group(2) or "").strip()
        label = ftype + (f" {watt}W" if watt else "")
        results.append(("FIXTURE", label))
    return results

def classify_boxes(tok):
    raw = tok.upper()
    results = []
    seen_spans = set()
    for m in BOX_PATTERN.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        w, h, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        btype = re.sub(r'\s+', ' ', m.group(4).upper())
        if d not in VALID_BOX_DEPTHS: continue
        results.append(("BOX", f"{w}x{h}x{d}mm {btype}"))
    return results

def classify_transformers(tok):
    raw = tok.upper()
    if "GENERATOR" in raw: return []
    if any(kw in raw for kw in ("XLPE", "SQ.MM", "SQ MM", "MM²", "MM2",
                                 "C X ", "FRLS", "LSZH", "ARMOURED")):
        return []
    has_transformer = "TRANSFORMER" in raw
    has_ratio = "/" in raw and "KV" in raw
    if not has_transformer and not has_ratio: return []
    results, seen = [], set()
    for m in TRANSFORMER_PATTERN.finditer(raw):
        kva = m.group(1); hv, lv = m.group(2), m.group(3)
        if has_ratio and not (hv and lv): continue
        label = f"{kva}kVA"
        if hv and lv: label += f" {hv}kV/{lv}kV"
        if label not in seen:
            seen.add(label)
            results.append(("TRANSFORMER", label))
    return results

def classify_generators(tok):
    raw = tok.upper()
    if "GENERATOR" not in raw:
        return []
    results, seen = [], set()
    for m in GENERATOR_PATTERN.finditer(raw):
        gtag = m.group(1) or m.group(2)
        kva = m.group(3)
        fuel = m.group(4)
        label = "GEN"
        if gtag: label += f"-{gtag}"
        label += f" {kva}kVA"
        if fuel:
            fuel_clean = fuel.upper().replace(' ', '')
            if fuel_clean == "PRIMERATED":
                fuel_clean = "PRIME"
            label += f" {fuel_clean}"
        if label not in seen:
            seen.add(label)
            results.append(("GENERATOR", label))
    return results

def classify_motors(tok):
    raw = tok.upper()
    results = []
    seen_spans = set()
    for m in MOTOR_PATTERN.finditer(raw):
        span = (m.start(), m.end())
        if span in seen_spans: continue
        seen_spans.add(span)
        kw = m.group(1); ph = m.group(2); rpm = m.group(3)
        label = f"{kw}kW"
        if ph: label += f" {ph}PH"
        if rpm: label += f" {rpm}RPM"
        results.append(("MOTOR", label))
    return results

CLASSIFIERS = {
    "panels":       classify_panels,
    "breakers":     classify_breakers,
    "cables":       classify_cables,
    "conduits":     classify_conduits,
    "fixtures":     classify_fixtures,
    "boxes":        classify_boxes,
    "transformers": classify_transformers,
    "generators":   classify_generators,
    "motors":       classify_motors,
}

# ============================================================
# CORE ENGINE
# ============================================================
def _read_blocks(page, tb_x, tb_y):
    blocks = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0: continue
        bb = list(b["bbox"])
        if tb_x != float("inf") and bb[0] > tb_x - 10: continue
        if tb_y != float("inf") and bb[1] > tb_y - 10: continue
        txt = " ".join(s.get("text","").strip()
                      for l in b.get("lines",[]) for s in l.get("spans",[])
                      if s.get("text","").strip()).strip()
        if txt:
            blocks.append({"bbox":bb,"text":txt})
    return blocks

def _detect_title_block(page):
    tb_x = tb_y = float("inf")
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0: continue
        txt = " ".join(s.get("text","") for l in b.get("lines",[])
                       for s in l.get("spans",[])).upper()
        if any(k in txt for k in ("DRAWING NO","SCALE","REVISION",
                                   "DESCRIPTION","TENDER","PROJECT:")):
            bb = b["bbox"]
            if bb[0] > page.rect.width * 0.7: tb_x = min(tb_x, bb[0])
            if bb[1] > page.rect.height * 0.7: tb_y = min(tb_y, bb[1])
    return tb_x, tb_y

def _dedupe_iou(blocks):
    uniq = []
    for b in blocks:
        if any(b["text"] == u["text"] and get_iou(b["bbox"], u["bbox"]) > 0.85 for u in uniq):
            continue
        uniq.append(b)
    return uniq

def extract_all(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_hits = {k: [] for k in CLASSIFIERS}
    per_page = []
    diag = {"pages":0,"chars":0,"blocks":0,"after_dedup":0,"after_merge":0}

    for page_no, page in enumerate(doc, start=1):
        diag["pages"] += 1
        chars = len(page.get_text("text").strip())
        diag["chars"] += chars
        per_page.append({"page":page_no,"chars":chars})

        tb_x, tb_y = _detect_title_block(page)
        blocks = _read_blocks(page, tb_x, tb_y)
        diag["blocks"] += len(blocks)

        uniq = _dedupe_iou(blocks)
        diag["after_dedup"] += len(uniq)
        diag["after_merge"] += len(uniq)

        for b in uniq:
            for key, classifier in CLASSIFIERS.items():
                pairs = classifier(b["text"])
                for tag, label in pairs:
                    all_hits[key].append({
                        "tag": tag, "label": label, "page": page_no,
                        "bbox": tuple(round(v,1) for v in b["bbox"]),
                        "source": b["text"],
                    })

    return all_hits, diag, per_page

def cross_check(pdf_bytes):
    counts = {k: 0 for k in CLASSIFIERS}
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        tb_x, tb_y = _detect_title_block(page)
        for b in _read_blocks(page, tb_x, tb_y):
            for key, classifier in CLASSIFIERS.items():
                counts[key] += len(classifier(b["text"]))
    return counts

def debug_breaker_blocks(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    out = []
    for page_no, page in enumerate(doc, start=1):
        tb_x, tb_y = _detect_title_block(page)
        for b in _read_blocks(page, tb_x, tb_y):
            txt = b["text"]
            if not re.search(r'(MCB|MCCB|ACB|RCBO|RCCB|ELCB|FUSE|VCB|LBS|SFU|GENERATOR|\d+\s*A|\d+\s*P|\d+P\b)',
                            txt, re.I):
                continue
            matches = classify_breakers(txt) + classify_generators(txt)
            out.append({
                "page": page_no,
                "text": txt,
                "matches": matches,
                "match_count": len(matches),
                "bbox": b["bbox"],
            })
    return out

def render_overlay(pdf_bytes, all_hits, active_types):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page_no, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        draw = ImageDraw.Draw(img, "RGBA")
        sx, sy = img.width/page.rect.width, img.height/page.rect.height
        for key in active_types:
            for h in all_hits.get(key, []):
                if h["page"] != page_no: continue
                bx = h["bbox"]
                color = COLOR_MAP.get(h["tag"], (0,0,0))
                rect = [bx[0]*sx, bx[1]*sy, bx[2]*sx, bx[3]*sy]
                draw.rectangle(rect, outline=color, width=3)
                lbl = h["label"][:30]
                tw = draw.textlength(lbl)
                draw.rectangle([rect[0], rect[1]-12, rect[0]+tw+4, rect[1]], fill=color)
                draw.text((rect[0]+2, rect[1]-11), lbl, fill=(255,255,255))
        images.append((page_no, img))
    return images

# ============================================================
# TABLE RENDERERS
# ============================================================
def render_grouped_table(hits, headers, row_fn):
    agg = defaultdict(int)
    for h in hits:
        agg[h["label"]] += 1
    rows = ""
    for label, n in sorted(agg.items()):
        rows += row_fn(label, n)
    if not rows:
        rows = (f"<tr><td colspan='{len(headers)}' "
                "style='text-align:center;color:#94a3b8;padding:30px;'>No items detected.</td></tr>")
    th = "".join(f"<th>{h}</th>" for h in headers)
    return textwrap.dedent(f"""
    <div class="custom-table-container">
    <table class="custom-table">
    <thead><tr>{th}</tr></thead>
    <tbody>{rows}</tbody>
    </table></div>""")

def render_audit(hits):
    rows = ""
    for h in sorted(hits, key=lambda x:(x["tag"], x["label"], x["page"])):
        rows += (f"<tr><td class='spec-cell'>{h['tag']}</td>"
                 f"<td>{h['label']}</td>"
                 f"<td><code>{h['source'][:60]}</code></td>"
                 f"<td>{h['page']}</td>"
                 f"<td>{tuple(int(v) for v in h['bbox'])}</td></tr>")
    if not rows:
        rows = ("<tr><td colspan='5' style='text-align:center;"
                "color:#94a3b8;padding:30px;'>No data.</td></tr>")
    return textwrap.dedent(f"""
    <div class="custom-table-container">
    <table class="custom-table">
    <thead><tr><th>Tag</th><th>Label</th><th>Source Text</th>
    <th>Page</th><th>BBox</th></tr></thead>
    <tbody>{rows}</tbody>
    </table></div>""")

# ============================================================
# HEADER
# ============================================================
logo_html = ""
for candidate in ("JFF Consultants Logo-01-01.png","logo.png"):
    if os.path.exists(candidate):
        try:
            b64 = get_base64_image(candidate)
            logo_html = f'<div class="logo-wrapper"><img src="data:image/png;base64,{b64}" class="logo-image"></div>'
            break
        except: pass

st.html(f"""
<div class="header-container">
    {logo_html}
    <div>
        <div class="header-title">Electrical Drawing Component Counter</div>
        <div class="header-subtitle">
            Deterministic extraction: panels · breakers · cables · conduits ·
            fixtures · boxes · transformers · generators · motors
        </div>
    </div>
</div>""")

# ============================================================
# SESSION STATE
# ============================================================
for k in ("hits","current_file","diagnostics","overlay","file_bytes",
          "debug_results"):
    if k not in st.session_state: st.session_state[k] = None

col_upload, col_dash = st.columns([2, 3], gap="large")

# ============================================================
# UPLOAD — no debug checkbox anymore
# ============================================================
with col_upload:
    st.html('<div class="section-subheader">Upload Drawing</div>')
    uploaded = st.file_uploader("Upload CAD-exported PDF", type=["pdf"],
                                 label_visibility="collapsed")
    if uploaded is not None:
        fid = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.current_file != fid:
            st.session_state.current_file = fid
            st.session_state.hits = None
            st.session_state.diagnostics = None
            st.session_state.overlay = None
            st.session_state.debug_results = None

        file_bytes = uploaded.read()
        st.session_state.file_bytes = file_bytes
        preview = pdf_to_image(file_bytes, dpi=110)
        if preview:
            st.image(preview, use_container_width=True, caption=f"Loaded: {uploaded.name}")
            st.html("<div style='margin-top:14px;'></div>")
            if st.button("⚡ Extract All Components", use_container_width=True):
                st.session_state.hits = "LOADING"
                st.rerun()
    else:
        st.session_state.hits = None
        st.session_state.current_file = None
        st.session_state.diagnostics = None
        st.session_state.overlay = None
        st.session_state.file_bytes = None
        st.session_state.debug_results = None
        show_info("Upload a native CAD PDF to start. Scanned images won't work — re-export from CAD with 'Text as Text'.")

# ============================================================
# DASHBOARD
# ============================================================
with col_dash:
    st.html('<div class="section-subheader">Extraction Dashboard</div>')

    if st.session_state.hits == "LOADING":
        st.html("""
        <div class="scanning-card">
            <div class="scanning-spinner"></div>
            <div class="scanning-text">Extracting all components…</div>
            <div class="scanning-subtext">
                Panels · Breakers · Cables · Conduits · Fixtures · Boxes · Transformers · Generators · Motors
            </div>
        </div>""")
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_chars = sum(len(p.get_text("text").strip()) for p in doc)
            if total_chars < 100:
                raise Exception(f"Only {total_chars} extractable text characters. Re-export from CAD with TrueType fonts.")

            all_hits, diag, per_page = extract_all(file_bytes)
            cross = cross_check(file_bytes)
            overlay = render_overlay(file_bytes, all_hits, list(CLASSIFIERS.keys()))

            # Auto-generate debug data on every extraction
            st.session_state.debug_results = debug_breaker_blocks(file_bytes)

            st.session_state.hits = all_hits
            st.session_state.diagnostics = {
                "diag": diag, "per_page": per_page,
                "file": uploaded.name, "size": uploaded.size,
                "cross": cross,
            }
            st.session_state.overlay = overlay
            st.rerun()
        except Exception as e:
            st.session_state.hits = None
            show_error(str(e))
            if st.button("Retry"): st.rerun()

    elif isinstance(st.session_state.hits, dict):
        all_hits = st.session_state.hits
        diag_info = st.session_state.diagnostics
        cross = diag_info.get("cross", {})

        totals = {k: len(v) for k, v in all_hits.items()}
        grand_total = sum(totals.values())

        drift = {k: totals[k] - cross.get(k, totals[k]) for k in totals
                 if totals[k] != cross.get(k, totals[k])}
        if drift:
            show_warn(f"⚠️ Drift detected in: {', '.join(f'{k} ({totals[k]} vs {cross[k]})' for k in drift)}.")
        else:
            show_success(f"✅ Extracted **{grand_total} total items** across {diag_info['diag']['pages']} page(s) — "
                         "matches Diagnostics re-parse. Consistent.")

        labels = {
            "panels":("Panels","🔌"), "breakers":("Breakers","⚡"),
            "cables":("Cables","🔗"), "conduits":("Conduits","🧵"),
            "fixtures":("Fixtures","💡"), "boxes":("Boxes","📦"),
            "transformers":("Transformers","🔋"), "generators":("Generators","⚙️"),
            "motors":("Motors","🌀"),
        }
        cards = "".join(
            f'<div class="metric-card"><div class="metric-label">{labels[k][1]} {labels[k][0]}</div>'
            f'<div class="metric-value">{totals.get(k,0)}</div></div>'
            for k in CLASSIFIERS
        )
        cards += f'<div class="metric-card metric-total"><div class="metric-label">Total</div><div class="metric-value">{grand_total}</div></div>'
        st.html(f'<div class="metric-container">{cards}</div>')

        if all_hits["panels"]:
            pcounts = Counter(h["tag"] for h in all_hits["panels"])
            pcards = "".join(
                f'<div class="metric-card" style="min-width:90px;padding:12px 8px;">'
                f'<div class="metric-label">{t}</div>'
                f'<div class="metric-value" style="font-size:22px;">{pcounts.get(t,0)}</div></div>'
                for t in PANEL_TAG_ORDER
            )
            st.html(f'<div class="metric-container">{pcards}</div>')

        tab_panels, tab_breakers, tab_cables, tab_conduits, tab_fixtures, \
        tab_boxes, tab_transformers, tab_generators, tab_motors, \
        tab_audit, tab_debug, tab_diag = st.tabs([
            "Panels", "Breakers", "Cables", "Conduits",
            "Fixtures", "Boxes", "Transformers", "Generators",
            "Motors", "Audit", "Debug", "Diagnostics"
        ])

        with tab_panels:
            st.html(render_grouped_table(
                all_hits["panels"], ["Tag","Normalized Label","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l.split('-')[0]}</td><td>{l}</td><td class='count-cell'>{n}</td></tr>"))

        with tab_breakers:
            if not all_hits["breakers"]:
                show_info("No breakers detected on this drawing.")
            else:
                st.html(render_grouped_table(
                    all_hits["breakers"], ["Breaker Type","Amps","Poles","Count"],
                    lambda l, n: (
                        f"<tr><td class='spec-cell'>{l.split('-')[0]}</td>"
                        f"<td>{l.split('-')[1] if len(l.split('-'))>1 else '—'}</td>"
                        f"<td>{l.split('-')[2] if len(l.split('-'))>2 else '—'}</td>"
                        f"<td class='count-cell'>{n}</td></tr>")))

        with tab_cables:
            st.html(render_grouped_table(
                all_hits["cables"], ["Cable Specification","Cores","Size","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l}</td><td>{l.split('C')[0]}</td>"
                             f"<td>{l.split('x ')[1] if 'x ' in l else '—'}</td>"
                             f"<td class='count-cell'>{n}</td></tr>"))

        with tab_conduits:
            st.html(render_grouped_table(
                all_hits["conduits"], ["Conduit Specification","Material","Size (mm)","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l}</td>"
                             f"<td>{l.split()[1] if len(l.split())>1 else '—'}</td>"
                             f"<td>{l.split()[-1] if l.split() else '—'}</td>"
                             f"<td class='count-cell'>{n}</td></tr>"))

        with tab_fixtures:
            st.html(render_grouped_table(
                all_hits["fixtures"], ["Fixture Type","Wattage","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l}</td>"
                             f"<td>{l.split()[-1] if 'W' in l else '—'}</td>"
                             f"<td class='count-cell'>{n}</td></tr>"))

        with tab_boxes:
            st.html(render_grouped_table(
                all_hits["boxes"], ["Box Specification","Dimensions","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l}</td>"
                             f"<td>{l.split()[0] if l.split() else '—'}</td>"
                             f"<td class='count-cell'>{n}</td></tr>"))

        with tab_transformers:
            st.html(render_grouped_table(
                all_hits["transformers"], ["Rating","Voltage Ratio","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l}</td>"
                             f"<td>{' '.join(l.split()[1:]) if len(l.split())>1 else '—'}</td>"
                             f"<td class='count-cell'>{n}</td></tr>"))

        with tab_generators:
            st.html(render_grouped_table(
                all_hits["generators"], ["Generator","Rating","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l}</td>"
                             f"<td>{l.split()[1] if len(l.split())>1 else '—'}</td>"
                             f"<td class='count-cell'>{n}</td></tr>"))

        with tab_motors:
            st.html(render_grouped_table(
                all_hits["motors"], ["Rating","Phase","RPM","Count"],
                lambda l, n: f"<tr><td class='spec-cell'>{l.split()[0] if l.split() else '—'}</td>"
                             f"<td>{' '.join([x for x in l.split() if 'PH' in x]) or '—'}</td>"
                             f"<td>{' '.join([x for x in l.split() if 'RPM' in x]) or '—'}</td>"
                             f"<td class='count-cell'>{n}</td></tr>"))

        with tab_audit:
            all_combined = []
            for key, hits in all_hits.items():
                all_combined.extend(hits)
            st.html(render_audit(all_combined))

        # DEBUG — always populated now
        with tab_debug:
            if st.session_state.debug_results:
                st.markdown(f"### 🔬 Breaker-like Text Blocks — {len(st.session_state.debug_results)} total")
                st.caption(
                    "**Green** = matched by breaker/generator regex. "
                    "**Amber** = contains keyword but NOT matched — correctly excluded "
                    "(busway, meters, cable specs, phase labels)."
                )
                matched = [d for d in st.session_state.debug_results if d["match_count"] > 0]
                unmatched = [d for d in st.session_state.debug_results if d["match_count"] == 0]
                st.html(f"""
                <div class="custom-table-container" style="padding:12px 16px;">
                    <b>Total blocks:</b> {len(st.session_state.debug_results)} ·
                    <b>Matched:</b> <span style="color:#10b981;font-weight:700;">{len(matched)}</span> ·
                    <b>Correctly excluded:</b> <span style="color:#f59e0b;font-weight:700;">{len(unmatched)}</span>
                </div>""")

                if unmatched:
                    st.markdown("#### ⚠️ Non-Breaker Blocks (correctly excluded)")
                    for i, d in enumerate(unmatched[:50], 1):
                        safe = d["text"].replace("<","&lt;").replace(">","&gt;")[:120]
                        st.html(f'<div class="debug-block"><span class="no-match">[{i}] {safe}</span></div>')

                if matched:
                    st.markdown("#### ✅ Matched Blocks")
                    for i, d in enumerate(matched[:30], 1):
                        safe = d["text"].replace("<","&lt;").replace(">","&gt;")[:120]
                        match_str = ", ".join(f"{t}:{l}" for t, l in d["matches"][:3])
                        more = f" +{d['match_count']-3}" if d["match_count"] > 3 else ""
                        st.html(f'<div class="debug-block"><span class="match">[{i}] {safe}</span>'
                                f'<span class="debug-count">{match_str}{more}</span></div>')
            else:
                show_info("Extract a drawing to populate this tab.")

        with tab_diag:
            d = diag_info["diag"]
            st.html(f"""
            <div class="custom-table-container" style="padding:14px 16px;">
                <b>Pages:</b> {d['pages']} ·
                <b>Text chars:</b> {d['chars']} ·
                <b>Blocks (raw):</b> {d['blocks']} ·
                <b>After IoU dedup:</b> {d['after_dedup']} ·
                <b>After merge:</b> {d['after_merge']}
            </div>""")
            st.markdown("### Per-Type Summary")
            rows = "".join(
                f"<tr><td>{labels[k][1]} {labels[k][0]}</td>"
                f"<td class='count-cell'>{totals.get(k,0)}</td>"
                f"<td class='count-cell'>{cross.get(k,0)}</td>"
                f"<td>{'✅' if totals.get(k,0)==cross.get(k,0) else '⚠️'}</td></tr>"
                for k in CLASSIFIERS
            )
            st.html(f"""
            <div class="custom-table-container">
            <table class="custom-table">
            <thead><tr><th>Component Type</th><th>Extracted</th><th>Re-parse</th><th>Status</th></tr></thead>
            <tbody>{rows}</tbody></table></div>""")

        st.markdown("### Export Results")
        if st.button("Generate CSV Report"):
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["Component Type","Tag","Label","Page","BBox","Source"])
            for key, hits in all_hits.items():
                for h in hits:
                    w.writerow([key, h["tag"], h["label"], h["page"], h["bbox"], h["source"]])
            st.download_button("Download CSV", buf.getvalue(),
                              file_name="component_extraction.csv", mime="text/csv")

    else:
        st.html("""
        <div style="background:#fff;border:1px dashed #cbd5e1;border-radius:12px;
             padding:60px;text-align:center;color:#64748b;">
            <p style="font-size:16.5px;font-weight:500;color:#64748b;margin:0;">
                Upload a native CAD drawing (PDF) and click
                <b>Extract All Components</b> to count:
                panels · breakers · cables · conduits · fixtures · boxes ·
                transformers · generators · motors
            </p>
        </div>""")

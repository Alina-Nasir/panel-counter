import streamlit as st
import os, io, re, textwrap, base64
from collections import defaultdict, Counter
from PIL import Image, ImageDraw
import fitz  # PyMuPDF

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Panel & DB Counter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS — Light Premium Theme
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
        flex:1; min-width:110px; background:#fff; border:1px solid #e2e8f0;
        border-radius:14px; padding:16px 12px; text-align:center;
        box-shadow:0 4px 20px rgba(0,0,0,.05);
        transition: transform .25s ease, border-color .25s ease;
    }
    .metric-card:hover { transform:translateY(-3px); border-color:#3b82f6; }
    .metric-label {
        font-size:11px; color:#64748b; text-transform:uppercase;
        letter-spacing:1.3px; margin-bottom:5px; font-weight:600;
    }
    .metric-value { font-size:30px; font-weight:700; color:#1d4ed8; }
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
    div.stButton > button:first-child:hover {
        transform:translateY(-2px) !important;
        box-shadow:0 6px 20px rgba(29,78,216,.35) !important;
    }

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
    .error-alert {
        background:rgba(239,68,68,.05);
        border:1px solid rgba(239,68,68,.15); color:#dc2626;
    }
    .info-alert {
        background:rgba(59,130,246,.05);
        border:1px solid rgba(59,130,246,.15); color:#2563eb;
    }
    .warn-alert {
        background:rgba(245,158,11,.05);
        border:1px solid rgba(245,158,11,.25); color:#b45309;
    }
    .success-alert {
        background:rgba(16,185,129,.05);
        border:1px solid rgba(16,185,129,.2); color:#059669;
    }
    .alert-icon { font-size:20px; margin-right:12px; }
    .alert-content strong { color:#0f172a; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def show_info(msg):
    st.html(f"""<div class="custom-alert info-alert">
        <span class="alert-icon">ℹ️</span>
        <div class="alert-content"><strong>System Status</strong><br>{msg}</div>
    </div>""")

def show_error(msg):
    st.html(f"""<div class="custom-alert error-alert">
        <span class="alert-icon">⚠️</span>
        <div class="alert-content"><strong>Error</strong><br>{msg}</div>
    </div>""")

def show_warn(msg):
    st.html(f"""<div class="custom-alert warn-alert">
        <span class="alert-icon">🔶</span>
        <div class="alert-content"><strong>Warning</strong><br>{msg}</div>
    </div>""")

def show_success(msg):
    st.html(f"""<div class="custom-alert success-alert">
        <span class="alert-icon">✅</span>
        <div class="alert-content"><strong>Success</strong><br>{msg}</div>
    </div>""")

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
# PANEL TAG PATTERNS — PERMISSIVE
# ============================================================
TAG_ORDER = ["MDB","SMDB","USMDB","LV","MLV","LPDB","UDB","DB",
             "ACDB","DCDB","APFC","MLDB","PNL"]

PANEL_PATTERNS = [
    # USMDB variants
    ("USMDB", re.compile(
        r'(?:^|\s)U[\s\.\-_]?S[\s\.\-_]?M[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),

    # SMDB variants
    ("SMDB", re.compile(
        r'(?:^|\s)S[\s\.\-_]?M[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),

    # LPDB
    ("LPDB", re.compile(
        r'(?:^|\s)L[\s\.\-_]?P[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),

    # UDB
    ("UDB", re.compile(
        r'(?:^|\s)U[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),

    # MLV
    ("MLV", re.compile(
        r'(?:^|\s)M[\s\.\-_]?L[\s\.\-_]?V'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),

    # MDB
    ("MDB", re.compile(
        r'(?:^|\s)M[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,25})?\b', re.I)),

    # LV — MUST be either:
    #   (a) at string start: "L.V PANEL-01", "LV-1"
    #   (b) followed by PANEL/PNL: "... LV PANEL ..."
    # This rejects "Dis. from LV to OB." (LV mid-string, no PANEL suffix)
    ("LV", re.compile(
        r'(?:'
            r'^L[\s\.\-_]?V(?:[\s\.\-_/]*[\w()\-]{0,15})?'      # (a) ^LV...
            r'|'
            r'\sL[\s\.\-_]?V[\s\.\-_]*P(?:ANEL|NL)[\s\.\-_/]*[\w()\-]{0,15}'  # (b) " LV PANEL"
        r')\b', re.I)),

    # DB (bare)
    ("DB", re.compile(
        r'(?:^|\s)D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{1,25})?\b', re.I)),

    # Extras
    ("ACDB", re.compile(
        r'(?:^|\s)A[\s\.\-_]?C[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("DCDB", re.compile(
        r'(?:^|\s)D[\s\.\-_]?C[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("APFC", re.compile(
        r'(?:^|\s)A[\s\.\-_]?P[\s\.\-_]?F[\s\.\-_]?C'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("MLDB", re.compile(
        r'(?:^|\s)M[\s\.\-_]?L[\s\.\-_]?D[\s\.\-_]?B'
        r'(?:[\s\.\-_/]*[\w()\-]{0,15})?\b', re.I)),
    ("PNL", re.compile(
        r'(?:^|\s)P(?:ANEL|NL)[\s\.\-_/]*\d+[A-Z]?\b', re.I)),
]

COLOR_MAP = {
    "MDB":   (220, 38, 38),
    "SMDB":  (234, 88, 12),
    "USMDB": (217, 119, 6),
    "LV":    (16, 185, 129),
    "MLV":   (5, 150, 105),
    "LPDB":  (59, 130, 246),
    "UDB":   (139, 92, 246),
    "DB":    (236, 72, 153),
    "ACDB":  (168, 85, 247),
    "DCDB":  (6, 182, 212),
    "APFC":  (244, 114, 182),
    "MLDB":  (34, 197, 94),
    "PNL":   (100, 116, 139),
}

# ============================================================
# CLASSIFY — returns LIST of (tag, label), one per panel
# ============================================================
CORE_TAGS = ["USMDB","SMDB","LPDB","UDB","MLV","MDB","LV",
             "ACDB","DCDB","APFC","MLDB","DB"]

def classify_token(tok):
    """Return LIST of (tag, label) — one per distinct panel in the block."""
    raw = tok.strip().upper()
    if len(raw) < 2:
        return []

    results = []
    seen = set()
    for tag, pat in PANEL_PATTERNS:
        for m in pat.finditer(raw):          # finditer — all matches
            frag = m.group(0)
            compact = re.sub(r'[\.\s_\-\/]+', '', frag.upper())

            for core in CORE_TAGS:
                if not compact.startswith(core):
                    continue
                suffix = compact[len(core):]
                label = core + ("-" + suffix if suffix else "")

                # cross-tag guards
                if core == "SMDB" and compact.startswith("USMDB"): continue
                if core == "DB" and any(compact.startswith(p) for p in
                        ("SMDB","USMDB","LPDB","UDB","MDB","LV","MLV",
                         "ACDB","DCDB","MLDB")):
                    continue
                if core == "LV" and compact.startswith("MLV"): continue

                key = (core, label)
                if key not in seen:
                    seen.add(key)
                    results.append(key)
                break
    return results

# ============================================================
# CORE SPATIAL ENGINE
# ============================================================
MAX_MERGED_WIDTH_PT  = 400
MAX_MERGED_HEIGHT_PT = 120

# Panel keyword regex — used to make panel blocks ATOMIC during merge
_PANEL_KEYWORD = re.compile(
    r'\b(USMDB|SMDB|LPDB|UDB|MLV|MDB|LV|ACDB|DCDB|APFC|MLDB|DB|PNL)\b',
    re.I)

def extract_panels_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    hits = []
    per_page_stats = []
    diag = {"pages":0,"chars_total":0,"blocks":0,"after_dedup":0,"after_merge":0}

    for page_no, page in enumerate(doc, start=1):
        diag["pages"] += 1
        page_text_chars = len(page.get_text("text").strip())
        diag["chars_total"] += page_text_chars
        per_page_stats.append({"page":page_no,"chars":page_text_chars})

        # --- Title block detection ---
        tb_x = tb_y = float("inf")
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0: continue
            txt = " ".join(
                s.get("text","") for l in b.get("lines",[]) for s in l.get("spans",[])
            ).upper()
            if any(k in txt for k in ("DRAWING NO","SCALE","REVISION",
                                       "DESCRIPTION","TENDER","PROJECT:")):
                bb = b["bbox"]
                if bb[0] > page.rect.width * 0.7:
                    tb_x = min(tb_x, bb[0])
                if bb[1] > page.rect.height * 0.7:
                    tb_y = min(tb_y, bb[1])

        # --- Extract text blocks ---
        blocks = []
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0: continue
            bb = list(b["bbox"])
            if tb_x != float("inf") and bb[0] > tb_x - 10: continue
            if tb_y != float("inf") and bb[1] > tb_y - 10: continue
            txt = " ".join(
                s.get("text","").strip()
                for l in b.get("lines",[]) for s in l.get("spans",[])
                if s.get("text","").strip()
            ).strip()
            if txt:
                blocks.append({"bbox":bb,"text":txt})
        diag["blocks"] += len(blocks)

        # --- IoU dedup ---
        uniq = []
        for b in blocks:
            if any(b["text"] == u["text"] and get_iou(b["bbox"], u["bbox"]) > 0.85
                   for u in uniq):
                continue
            uniq.append(b)
        diag["after_dedup"] += len(uniq)

        # --- Sort deterministically (top-to-bottom, left-to-right) ---
        uniq.sort(key=lambda b: (round(b["bbox"][1], 1), b["bbox"][0]))

        # --- Neighbor merge WITH panel-aware + size guards ---
        merged = uniq
        for _ in range(2):
            new, used = [], set()
            for i, b1 in enumerate(merged):
                if i in used: continue
                bb, txt = list(b1["bbox"]), b1["text"]
                used.add(i)
                for j, b2 in enumerate(merged):
                    if j in used: continue

                    # 🔑 GUARD: panel blocks are ATOMIC — never merge them
                    if _PANEL_KEYWORD.search(txt) or _PANEL_KEYWORD.search(b2["text"]):
                        continue

                    yg = max(0, max(bb[1], b2["bbox"][1]) - min(bb[3], b2["bbox"][3]))
                    xg = max(0, max(bb[0], b2["bbox"][0]) - min(bb[2], b2["bbox"][2]))

                    new_x0 = min(bb[0], b2["bbox"][0])
                    new_x1 = max(bb[2], b2["bbox"][2])
                    new_y0 = min(bb[1], b2["bbox"][1])
                    new_y1 = max(bb[3], b2["bbox"][3])
                    if (new_x1 - new_x0) > MAX_MERGED_WIDTH_PT or \
                       (new_y1 - new_y0) > MAX_MERGED_HEIGHT_PT:
                        continue

                    if yg < 10 and xg < 25:
                        txt += b2["text"]
                        bb = [new_x0, new_y0, new_x1, new_y1]
                        used.add(j)
                new.append({"bbox":bb,"text":txt})
            merged = new
        diag["after_merge"] += len(merged)

        # --- Classify — one hit per panel per block ---
        for b in merged:
            pairs = classify_token(b["text"])
            for tag, label in pairs:
                hits.append({
                    "tag": tag, "label": label, "page": page_no,
                    "bbox": tuple(round(v,1) for v in b["bbox"]),
                    "source": b["text"],
                })

    return hits, diag, per_page_stats

# ============================================================
# CROSS-CHECK — re-parse raw blocks the way Diagnostics does
# ============================================================
def cross_check_count(pdf_bytes):
    total = 0
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0: continue
            txt = " ".join(
                s.get("text","").strip()
                for l in b.get("lines",[]) for s in l.get("spans",[])
                if s.get("text","").strip()
            ).strip()
            if txt:
                total += len(classify_token(txt))
    return total

# ============================================================
# DEBUG OVERLAY
# ============================================================
def render_debug_overlay(pdf_bytes, hits):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page_no, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        draw = ImageDraw.Draw(img, "RGBA")
        sx = img.width / page.rect.width
        sy = img.height / page.rect.height
        page_hits = [h for h in hits if h["page"] == page_no]
        for h in page_hits:
            bx = h["bbox"]
            color = COLOR_MAP.get(h["tag"], (0,0,0))
            rect = [bx[0]*sx, bx[1]*sy, bx[2]*sx, bx[3]*sy]
            draw.rectangle(rect, outline=color, width=4)
            label_text = h["label"]
            tw = draw.textlength(label_text)
            draw.rectangle([rect[0], rect[1]-14, rect[0]+tw+6, rect[1]],
                           fill=color)
            draw.text((rect[0]+3, rect[1]-13), label_text, fill=(255,255,255))
        images.append((page_no, img, len(page_hits)))
    return images

# ============================================================
# TABLE RENDERERS
# ============================================================
def render_summary_table(hits):
    agg = defaultdict(lambda: defaultdict(int))
    for h in hits:
        agg[h["tag"]][h["label"]] += 1
    rows = ""
    for tag in TAG_ORDER:
        if tag not in agg: continue
        for label, n in sorted(agg[tag].items()):
            rows += (f"<tr><td class='spec-cell'>{tag}</td>"
                     f"<td>{label}</td><td class='count-cell'>{n}</td></tr>")
    if not rows:
        rows = ("<tr><td colspan='3' style='text-align:center;"
                "color:#94a3b8;padding:30px;'>No panel tokens detected.</td></tr>")
    return textwrap.dedent(f"""
    <div class="custom-table-container">
    <table class="custom-table">
    <thead><tr><th>Tag</th><th>Normalized Label</th><th>Count</th></tr></thead>
    <tbody>{rows}</tbody>
    </table></div>""")

def render_audit_table(hits):
    rows = ""
    for h in sorted(hits, key=lambda x:(x["tag"], x["label"], x["page"])):
        rows += (f"<tr><td class='spec-cell'>{h['tag']}</td>"
                 f"<td>{h['label']}</td>"
                 f"<td><code>{h['source']}</code></td>"
                 f"<td>{h['page']}</td>"
                 f"<td>{tuple(int(v) for v in h['bbox'])}</td></tr>")
    if not rows:
        rows = ("<tr><td colspan='5' style='text-align:center;"
                "color:#94a3b8;padding:30px;'>No data.</td></tr>")
    return textwrap.dedent(f"""
    <div class="custom-table-container">
    <table class="custom-table">
    <thead><tr><th>Tag</th><th>Label</th><th>Source Text</th>
    <th>Page</th><th>BBox (pt)</th></tr></thead>
    <tbody>{rows}</tbody>
    </table></div>""")

# ============================================================
# HEADER
# ============================================================
logo_html = ""
for candidate in ("JFF Consultants Logo-01-01.png", "logo.png"):
    if os.path.exists(candidate):
        try:
            b64 = get_base64_image(candidate)
            logo_html = (f'<div class="logo-wrapper">'
                         f'<img src="data:image/png;base64,{b64}" class="logo-image">'
                         f'</div>')
            break
        except Exception:
            pass

st.html(f"""
<div class="header-container">
    {logo_html}
    <div>
        <div class="header-title">Panel &amp; Distribution Board Counter</div>
        <div class="header-subtitle">
            Deterministic spatial parsing of MDB · SMDB · USMDB · LV · MLV · LPDB · UDB · DB
            from native CAD-exported PDFs.
        </div>
    </div>
</div>""")

# ============================================================
# SESSION STATE
# ============================================================
for k in ("results", "current_file", "diagnostics", "overlay_images", "file_bytes"):
    if k not in st.session_state:
        st.session_state[k] = None

col_upload, col_dash = st.columns([2, 3], gap="large")

# ============================================================
# UPLOAD COLUMN
# ============================================================
with col_upload:
    st.html('<div class="section-subheader">Upload Drawing</div>')
    uploaded = st.file_uploader(
        "Upload CAD-exported PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded is not None:
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.current_file != file_id:
            st.session_state.current_file = file_id
            st.session_state.results = None
            st.session_state.diagnostics = None
            st.session_state.overlay_images = None

        file_bytes = uploaded.read()
        st.session_state.file_bytes = file_bytes
        preview = pdf_to_image(file_bytes, dpi=110)
        if preview:
            st.image(preview, use_container_width=True,
                     caption=f"Loaded: {uploaded.name}")
            st.html("<div style='margin-top:14px;'></div>")
            if st.button("⚡ Count Panels & Distribution Boards",
                         use_container_width=True):
                st.session_state.results = "LOADING"
                st.rerun()
    else:
        st.session_state.results = None
        st.session_state.current_file = None
        st.session_state.diagnostics = None
        st.session_state.overlay_images = None
        st.session_state.file_bytes = None
        show_info("Upload a native CAD PDF (with embedded text) to start. "
                  "Scanned images will not work — export from CAD with 'Text as Text'.")

# ============================================================
# DASHBOARD COLUMN
# ============================================================
with col_dash:
    st.html('<div class="section-subheader">Extraction Dashboard</div>')

    # ------------------ LOADING ------------------
    if st.session_state.results == "LOADING":
        st.html("""
        <div class="scanning-card">
            <div class="scanning-spinner"></div>
            <div class="scanning-text">Scanning page text blocks…</div>
            <div class="scanning-subtext">
                Clustering · IoU deduplication · panel-aware merge · tag classification
            </div>
        </div>""")
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            total_chars = sum(len(p.get_text("text").strip()) for p in doc)
            if total_chars < 100:
                raise Exception(
                    f"Only {total_chars} extractable text characters across "
                    f"{len(doc)} page(s). This PDF likely has outlined/scan "
                    "text, not machine-readable text. Re-export from CAD with "
                    "TrueType font embedding, or run `ocrmypdf` first."
                )

            hits, diag, per_page = extract_panels_from_pdf(file_bytes)
            cross = cross_check_count(file_bytes)
            overlay = render_debug_overlay(file_bytes, hits)

            st.session_state.results = hits
            st.session_state.diagnostics = {
                "diag": diag, "per_page": per_page,
                "file": uploaded.name, "size": uploaded.size,
                "cross_check": cross,
            }
            st.session_state.overlay_images = overlay
            st.rerun()

        except Exception as e:
            st.session_state.results = None
            show_error(str(e))
            if st.button("Retry"):
                st.rerun()

    # ------------------ RESULTS ------------------
    elif isinstance(st.session_state.results, list):
        hits = st.session_state.results
        diag_info = st.session_state.diagnostics
        cc = diag_info.get("cross_check", len(hits))

        # --- Cross-check banner ---
        if len(hits) == 0:
            show_warn(
                f"No panels matched after scanning {diag_info['diag']['pages']} "
                f"page(s) / {diag_info['diag']['chars_total']} text characters. "
                "Open the **🔍 Diagnostics** tab to see every extracted text "
                "block — look for yellow-highlighted rows that contain panel "
                "keywords and their real spelling."
            )
        elif cc == len(hits):
            show_success(
                f"✅ Found **{len(hits)} panel hit(s)** across "
                f"{diag_info['diag']['pages']} page(s) — matches Diagnostics "
                f"re-parse **{cc}**. Consistent."
            )
        else:
            show_warn(
                f"⚠️ Extraction **{len(hits)}** vs. Diagnostics re-parse **{cc}** "
                f"— difference of **{abs(cc - len(hits))}** panel(s). "
                "If drift persists, reduce `MAX_MERGED_WIDTH_PT`."
            )

        # --- Metrics row ---
        counts = Counter(h["tag"] for h in hits)
        cards = "".join(
            f'<div class="metric-card"><div class="metric-label">{tag}</div>'
            f'<div class="metric-value">{counts.get(tag, 0)}</div></div>'
            for tag in TAG_ORDER
        )
        grand = sum(counts.values())
        cards += (f'<div class="metric-card metric-total">'
                  f'<div class="metric-label">Total</div>'
                  f'<div class="metric-value">{grand}</div></div>')
        st.html(f'<div class="metric-container">{cards}</div>')

        # --- Tabs ---
        tab_sum, tab_audit, tab_debug, tab_diag = st.tabs(
            ["📊 Summary", "🧾 Audit Trail", "🖼️ Debug Overlay", "🔍 Diagnostics"]
        )

        with tab_sum:
            st.html(render_summary_table(hits))

        with tab_audit:
            st.html(render_audit_table(hits))

        with tab_debug:
            legend = " · ".join(
                f"<span style='color:rgb{COLOR_MAP[t]};font-weight:700;'>■ {t}</span>"
                for t in TAG_ORDER
            )
            st.html(f"""
            <div class="custom-table-container" style="padding:12px 16px;">
                <b>Color legend:</b> {legend}
            </div>""")
            for page_no, img, n in st.session_state.overlay_images:
                st.image(img,
                         caption=f"Page {page_no} — {n} panel hit(s)",
                         use_container_width=True)

        # =====================================================
        # DIAGNOSTICS TAB
        # =====================================================
        with tab_diag:
            d = diag_info["diag"]
            st.html(f"""
            <div class="custom-table-container" style="padding:14px 16px;">
                <b>Pages:</b> {d['pages']} ·
                <b>Text chars:</b> {d['chars_total']} ·
                <b>Blocks (raw):</b> {d['blocks']} ·
                <b>After IoU dedup:</b> {d['after_dedup']} ·
                <b>After merge:</b> {d.get('after_merge', '—')} ·
                <b>Panel hits (post-merge):</b> {len(hits)} ·
                <b>Diagnostics re-parse (raw):</b> {cc}
            </div>""")

            st.markdown("### 🔎 All Extracted Text Blocks (per page)")
            st.caption(
                "Yellow rows = panel keyword present but not classified. "
                "Green ✅ rows = correctly classified. "
                "This table re-parses the raw PDF blocks (pre-merge) so you "
                "can see every individual label."
            )

            dump_doc = fitz.open(stream=st.session_state.file_bytes, filetype="pdf")
            for pno, page in enumerate(dump_doc, start=1):
                blocks = []
                for b in page.get_text("dict")["blocks"]:
                    if b.get("type") != 0: continue
                    txt = " ".join(
                        s.get("text","").strip()
                        for l in b.get("lines",[]) for s in l.get("spans",[])
                        if s.get("text","").strip()
                    ).strip()
                    if not txt: continue
                    has_kw = bool(re.search(
                        r'(MDB|SMDB|USMDB|LV|MLV|LPDB|UDB|DB|ACDB|DCDB|APFC|MLDB|PNL)',
                        txt, re.I))
                    pairs = classify_token(txt)
                    counted = len(pairs) > 0
                    blocks.append((txt, b["bbox"], has_kw, counted, pairs))

                kw_count = sum(1 for x in blocks if x[2])
                ct_count = sum(len(x[4]) for x in blocks)

                with st.expander(
                    f"Page {pno} — {len(blocks)} blocks · "
                    f"{kw_count} with keywords · {ct_count} classified",
                    expanded=(pno == 1)
                ):
                    rows = ""
                    for txt, bb, has_kw, counted, pairs in blocks:
                        safe = txt.replace("<","&lt;").replace(">","&gt;")
                        if counted:
                            icon = "✅"
                            bg = "background:#dcfce7;"
                            tagcol = ", ".join(
                                f"<span style='color:#15803d;font-weight:700;'>{t}</span>"
                                for t, _ in pairs
                            )
                        elif has_kw:
                            icon = "🔶"
                            bg = "background:#fef3c7;"
                            tagcol = "<span style='color:#b45309;'>unclassified</span>"
                        else:
                            icon = ""
                            bg = ""
                            tagcol = "—"
                        rows += (f"<tr style='{bg}'>"
                                 f"<td>{icon} <code>{safe}</code></td>"
                                 f"<td>{tagcol}</td>"
                                 f"<td>{int(bb[0])},{int(bb[1])}</td>"
                                 f"<td>{int(bb[2]-bb[0])}×{int(bb[3]-bb[1])}</td></tr>")
                    if not rows:
                        rows = ("<tr><td colspan='4' style='text-align:center;'>"
                                "No text on this page.</td></tr>")
                    st.html(f"""
                    <div class="custom-table-container">
                    <table class="custom-table">
                    <thead><tr><th>Text</th><th>Classified As</th>
                    <th>Position (x,y)</th><th>Size (w×h)</th></tr></thead>
                    <tbody>{rows}</tbody>
                    </table></div>""")

            st.markdown("### 📄 Per-Page Character Summary")
            per_page_rows = "".join(
                f"<tr><td>Page {p['page']}</td>"
                f"<td class='count-cell'>{p['chars']}</td></tr>"
                for p in diag_info["per_page"]
            )
            st.html(f"""
            <div class="custom-table-container">
            <table class="custom-table">
            <thead><tr><th>Page</th><th>Extractable Text Chars</th></tr></thead>
            <tbody>{per_page_rows}</tbody>
            </table></div>""")

    # ------------------ EMPTY ------------------
    else:
        st.html("""
        <div style="background:#fff;border:1px dashed #cbd5e1;border-radius:12px;
             padding:60px;text-align:center;color:#64748b;
             box-shadow:0 4px 15px rgba(0,0,0,.01);">
            <p style="font-size:16.5px;font-weight:500;color:#64748b;margin:0;">
                Upload a native CAD drawing (PDF) and click
                <b>Count Panels &amp; Distribution Boards</b>
                to extract MDB · SMDB · USMDB · LV · MLV · LPDB · UDB · DB.
            </p>
        </div>""")
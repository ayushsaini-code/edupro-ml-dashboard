"""EduPro shared design system.

One place for the visual language of the dashboard: colour tokens, global CSS,
reusable HTML components (top bar, hero, KPI cards, callouts) and the Plotly
styling helper. app.py and ml_pages.py import from here so nothing is
duplicated.

Nothing in this module touches data, models or metrics.
"""

from __future__ import annotations

import html

import streamlit as st
from streamlit.errors import StreamlitAPIException

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------
BG = "#070b16"
SURFACE = "#0f1629"
TEXT = "#e8edf9"
MUTED = "#9aa7c4"
BLUE = "#3b82f6"
CYAN = "#22d3ee"
VIOLET = "#8b5cf6"
GRID = "rgba(148,163,205,0.12)"

# Twelve distinguishable colours (the dataset has 12 course categories).
PALETTE = [
    "#3b82f6", "#22d3ee", "#8b5cf6", "#38bdf8", "#6366f1", "#2dd4bf",
    "#a78bfa", "#60a5fa", "#06b6d4", "#818cf8", "#67e8f9", "#c4b5fd",
]

FONT_STACK = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"

# --------------------------------------------------------------------------
# Streamlit version compatibility
# --------------------------------------------------------------------------
# Newer Streamlit replaces use_container_width=True with width="stretch".
# requirements.txt is unpinned, so support both without hard-failing.


def _version_tuple() -> tuple:
    parts = []
    for piece in st.__version__.split(".")[:2]:
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts)


_NEW_WIDTH_API = _version_tuple() >= (1, 50)


def stretch(fn, *args, **kwargs):
    """Call a Streamlit element so that it fills the container width."""
    if _NEW_WIDTH_API:
        try:
            return fn(*args, width="stretch", **kwargs)
        except (TypeError, StreamlitAPIException):
            pass
    return fn(*args, use_container_width=True, **kwargs)


# --------------------------------------------------------------------------
# Global CSS
# --------------------------------------------------------------------------
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

:root {
    --bg: #070b16;
    --glass: rgba(14, 22, 42, 0.58);
    --glass-strong: rgba(16, 26, 50, 0.74);
    --border: rgba(110, 150, 255, 0.16);
    --border-strong: rgba(110, 150, 255, 0.30);
    --text: #e8edf9;
    --muted: #9aa7c4;
    --blue: #3b82f6;
    --cyan: #22d3ee;
    --violet: #8b5cf6;
    --radius: 18px;
    --ang: 0deg;
}

/* ====================================================================
   BACKGROUND STACK (all decorative, pointer-events: none)
   -4 moving glows · -3 digital grid · -2 neural canvas (bg_component.py)
   -1 readability overlay · app content sits above all of these
   ==================================================================== */
/* Base colour on <html> ONLY: an opaque <body> would paint over the negative-z layers below. */
html { background: #070b16 !important; }
body { background: transparent !important; }
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main { background: transparent !important; color: var(--text); }
.stApp { font-family: Inter, 'Segoe UI', system-ui, sans-serif; }

html::before {
    content: ""; position: fixed; inset: -20%; z-index: -4; pointer-events: none;
    background:
        radial-gradient(620px 440px at 18% 22%, rgba(59,130,246,.27), transparent 70%),
        radial-gradient(540px 400px at 82% 16%, rgba(34,211,238,.19), transparent 70%),
        radial-gradient(660px 480px at 70% 90%, rgba(139,92,246,.17), transparent 70%);
    animation: glowDrift 38s ease-in-out infinite alternate;
    will-change: transform;
}
body::before {
    content: ""; position: fixed; inset: -56px; z-index: -3; pointer-events: none;
    background-image:
        linear-gradient(rgba(90,150,255,.09) 1px, transparent 1px),
        linear-gradient(90deg, rgba(90,150,255,.09) 1px, transparent 1px);
    background-size: 56px 56px;
    -webkit-mask-image: radial-gradient(ellipse 85% 75% at 50% 35%, #000 25%, transparent 85%);
    mask-image: radial-gradient(ellipse 85% 75% at 50% 35%, #000 25%, transparent 85%);
    animation: gridDrift 80s linear infinite;
    will-change: transform;
}
body::after {
    content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background:
        radial-gradient(ellipse at 50% 35%, rgba(7,11,22,.04), rgba(7,11,22,.42) 100%),
        linear-gradient(180deg, rgba(7,11,22,.10), rgba(7,11,22,.18));
}

[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1480px; padding: 1.1rem 2.2rem 3rem; }
h1, h2, h3, h4 { font-family: Manrope, Inter, sans-serif; letter-spacing: -0.2px; }
hr { border-color: var(--border) !important; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: rgba(120,150,255,.24); border-radius: 8px; }
::-webkit-scrollbar-track { background: transparent; }

/* ---------- Sidebar: glass navigation panel ---------- */
[data-testid="stSidebar"] {
    background: rgba(8, 13, 28, 0.68) !important;
    -webkit-backdrop-filter: blur(20px) saturate(150%);
    backdrop-filter: blur(20px) saturate(150%);
    border-right: 1px solid var(--border);
    box-shadow: 1px 0 40px rgba(34,211,238,.05);
}
[data-testid="stSidebar"] > div { background: transparent !important; }
[data-testid="stSidebar"] * { color: var(--text); }
.brand { display: flex; align-items: center; gap: 12px; margin: 8px 0 6px; }
.brand-mark {
    width: 42px; height: 42px; border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
    font-size: 21px; color: #fff !important;
    background: linear-gradient(135deg, var(--blue), var(--cyan));
    box-shadow: 0 0 22px rgba(34,211,238,.38), inset 0 1px 0 rgba(255,255,255,.35);
}
.brand-name { font-family: Manrope, sans-serif; font-size: 20px; font-weight: 800; line-height: 1.1; }
.brand-sub { font-size: 11px; letter-spacing: 1.8px; color: var(--cyan) !important; font-weight: 700; }
.side-tagline { font-size: 12px; color: var(--muted) !important; margin: 4px 0 12px; }
.side-label { font-size: 10.5px; letter-spacing: 1.6px; font-weight: 700; color: var(--muted) !important; margin: 4px 0 6px; }
.side-source { font-size: 13px; font-weight: 600; margin: 2px 0; }
.side-meta { font-size: 11.5px; color: var(--muted) !important; }

.ai-status {
    display: flex; align-items: center; gap: 11px; padding: 10px 12px; border-radius: 12px;
    background: rgba(14,22,42,.6); border: 1px solid var(--border);
}
.ai-status .dot {
    width: 9px; height: 9px; border-radius: 50%; flex: none;
    background: #34d399; box-shadow: 0 0 10px #34d399; animation: pulse 2.6s ease-in-out infinite;
}
.ai-status.warn .dot { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; }
.ai-status .st-ttl { font-size: 11px; letter-spacing: 1.3px; font-weight: 700; color: #fff !important; }
.ai-status .st-sub { font-size: 11.5px; color: var(--muted) !important; margin-top: 1px; }

[data-testid="stSidebar"] [data-testid="stRadio"] > label p {
    font-size: 10.5px; letter-spacing: 1.6px; font-weight: 700; color: var(--muted) !important;
}
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    width: 100%; padding: 10px 13px; border-radius: 12px;
    border: 1px solid transparent; cursor: pointer;
    transition: background .22s ease, border-color .22s ease, transform .22s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(59,130,246,.11); transform: translateX(3px);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(59,130,246,.26), rgba(34,211,238,.07));
    border-color: rgba(59,130,246,.45);
    box-shadow: 0 0 20px rgba(59,130,246,.14), inset 2px 0 0 var(--cyan);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label p { font-size: 13.5px; font-weight: 500; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p { font-weight: 700; color: #fff !important; }

/* ---------- Top bar ---------- */
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; margin: 0 0 14px; }
.crumbs { font-size: 13px; color: var(--muted); display: flex; gap: 8px; align-items: center; }
.crumbs strong { color: var(--text); font-weight: 600; }
.crumbs .sep { opacity: .5; }
.pills { display: flex; gap: 8px; flex-wrap: wrap; }
.pill {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 5px 13px; border-radius: 999px; font-size: 12px; color: #cfdaf7;
    background: rgba(14,22,42,.62); border: 1px solid var(--border);
    -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
}
.pill .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 8px var(--cyan); animation: pulse 2.4s ease-in-out infinite; }

/* ---------- Shared glass-card base ---------- */
.hero, .kpi, .result, .glass {
    position: relative; overflow: hidden;
    -webkit-backdrop-filter: blur(16px) saturate(140%);
    backdrop-filter: blur(16px) saturate(140%);
}
/* Thin gradient border, drawn as a masked ring so the glass stays see-through */
.hero::before, .kpi::before, .result::before, .glass::before {
    content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1px;
    background: linear-gradient(135deg, var(--a1, #3b82f6), rgba(120,150,255,.10) 45%, var(--a2, #22d3ee));
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0);
    mask-composite: exclude;
    pointer-events: none; opacity: .75; transition: opacity .3s ease; z-index: 2;
}
/* Restrained animated highlight: result cards + hero always (slow), KPI/glass on hover */
@property --ang { syntax: "<angle>"; inherits: false; initial-value: 0deg; }
.hero::before { opacity: .9; }
.result::before {
    background: conic-gradient(from var(--ang, 0deg), rgba(120,150,255,.14), var(--a1, #3b82f6), var(--a2, #22d3ee), rgba(120,150,255,.14) 60%, rgba(120,150,255,.14));
    animation: borderSpin 12s steps(120) infinite;
}
.kpi:hover::before, .glass:hover::before {
    background: conic-gradient(from var(--ang, 0deg), rgba(120,150,255,.14), var(--a1, #3b82f6), var(--a2, #22d3ee), rgba(120,150,255,.14) 60%, rgba(120,150,255,.14));
    animation: borderSpin 6s steps(90) infinite; opacity: 1;
}

/* ---------- Hero ---------- */
.hero {
    --a1: #3b82f6; --a2: #22d3ee;
    padding: 30px 34px; margin-bottom: 22px; border-radius: 24px;
    background: linear-gradient(120deg, rgba(16,26,52,.66) 0%, rgba(20,34,78,.58) 55%, rgba(46,38,108,.50) 100%);
    box-shadow: 0 20px 56px rgba(0,0,0,.42), 0 0 44px rgba(59,130,246,.08);
    animation: fadeUp .55s ease both;
}
.hero::after {
    content: ""; position: absolute; top: 0; bottom: 0; width: 38%; left: 0;
    transform: translateX(-110%); will-change: transform;
    background: linear-gradient(100deg, transparent, rgba(120,200,255,.07), transparent);
    animation: sheen 11s ease-in-out infinite; pointer-events: none;
}
.hero > * { position: relative; z-index: 1; }
.hero .eyebrow { font-size: 11px; font-weight: 700; letter-spacing: 2.4px; color: var(--cyan); margin-bottom: 12px; }
.hero h1 { font-family: Manrope, sans-serif; font-size: 34px; font-weight: 800; margin: 0 0 8px; padding: 0; color: #fff !important; }
.hero p { font-size: 14px; color: #bccaea !important; margin: 0; max-width: 780px; }

/* ---------- Section headings ---------- */
.section-title { font-family: Manrope, sans-serif; font-size: 20px; font-weight: 800; margin: 28px 0 4px; color: var(--text); }
.section-subtitle { font-size: 13px; color: var(--muted); margin-bottom: 16px; }
.filter-label { font-size: 10.5px; letter-spacing: 1.6px; font-weight: 700; color: var(--muted); margin: 2px 0 6px; }

/* ---------- KPI + result cards ---------- */
.kpi, .result {
    --a1: #3b82f6; --a2: #22d3ee;
    background: linear-gradient(180deg, rgba(20,30,56,.62), rgba(12,19,38,.58));
    border-radius: var(--radius); padding: 20px 22px; min-height: 134px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.06), 0 12px 30px rgba(0,0,0,.32);
    transition: transform .28s ease, box-shadow .28s ease;
    animation: fadeUp .55s ease both;
}
.kpi > *, .result > * { position: relative; z-index: 1; }
.kpi::after, .result::after {
    content: ""; position: absolute; right: -46px; top: -46px; width: 150px; height: 150px;
    border-radius: 50%; background: radial-gradient(circle, var(--a1), transparent 70%);
    opacity: .14; transition: opacity .28s ease; pointer-events: none;
}
.kpi:hover, .result:hover {
    transform: translateY(-3px);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 18px 40px rgba(0,0,0,.40), 0 0 30px rgba(34,211,238,.12);
}
.kpi:hover::after, .result:hover::after { opacity: .26; }
.kpi-blue   { --a1: #3b82f6; --a2: #22d3ee; }
.kpi-cyan   { --a1: #22d3ee; --a2: #3b82f6; }
.kpi-violet { --a1: #8b5cf6; --a2: #3b82f6; }
.kpi-label { font-size: 11px; font-weight: 700; letter-spacing: 1.2px; color: var(--muted); margin-bottom: 12px; text-transform: uppercase; }
.kpi-value {
    font-family: Manrope, sans-serif; font-weight: 800; color: #fff;
    font-size: clamp(22px, 2.1vw, 30px); line-height: 1.2; letter-spacing: -0.5px; overflow-wrap: anywhere;
    text-shadow: 0 0 24px rgba(34,211,238,.18);
}
.kpi-sm .kpi-value { font-size: clamp(18px, 1.6vw, 22px); }
.kpi-note { font-size: 12px; color: var(--muted); margin-top: 8px; line-height: 1.45; }

.result { min-height: 168px; padding: 24px 26px; }
.result .kpi-value { font-size: clamp(28px, 3vw, 40px); }
.badge {
    display: inline-block; margin-top: 12px; padding: 3px 10px; border-radius: 999px;
    font-size: 11px; font-weight: 600; color: #c4edf8;
    background: rgba(34,211,238,.10); border: 1px solid rgba(34,211,238,.32);
}

/* ---------- Callouts, chips, glass cards ---------- */
.callout {
    display: flex; gap: 12px; align-items: flex-start;
    padding: 14px 18px; margin: 14px 0; border-radius: 14px;
    border: 1px solid var(--border); background: rgba(14,22,42,.62);
    -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px);
    animation: fadeUp .55s ease both;
}
.callout .ico { font-size: 16px; line-height: 1.4; }
.callout .ttl { font-weight: 700; font-size: 13.5px; margin-bottom: 2px; color: #fff; }
.callout .bdy { font-size: 13px; color: #c0cbe6; line-height: 1.55; }
.callout-info { border-left: 3px solid var(--blue); background: linear-gradient(90deg, rgba(59,130,246,.14), rgba(14,22,42,.62) 60%); }
.callout-warn { border-left: 3px solid #f59e0b; background: linear-gradient(90deg, rgba(245,158,11,.14), rgba(14,22,42,.62) 60%); }
.callout-note { border-left: 3px solid var(--violet); background: linear-gradient(90deg, rgba(139,92,246,.14), rgba(14,22,42,.62) 60%); }
.chip {
    display: inline-flex; padding: 4px 11px; margin: 0 6px 6px 0; border-radius: 999px;
    font-size: 12px; color: #c4d4ff;
    background: rgba(59,130,246,.13); border: 1px solid rgba(59,130,246,.30);
}
.glass {
    --a1: #3b82f6; --a2: #22d3ee;
    padding: 18px 20px; border-radius: var(--radius); height: 100%;
    background: var(--glass);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 10px 26px rgba(0,0,0,.28);
    transition: transform .28s ease; animation: fadeUp .55s ease both;
}
.glass > * { position: relative; z-index: 1; }
.glass:hover { transform: translateY(-2px); }
.glass .g-ttl { font-weight: 700; font-size: 14px; color: #fff; margin-bottom: 6px; }
.glass .g-bdy { font-size: 13px; color: #c0cbe6; line-height: 1.55; }

/* ---------- Native Streamlit elements ---------- */
[data-testid="stPlotlyChart"] {
    background: linear-gradient(180deg, rgba(18,27,50,.55), rgba(10,16,32,.52));
    border: 1px solid var(--border); border-radius: var(--radius);
    -webkit-backdrop-filter: blur(14px) saturate(130%); backdrop-filter: blur(14px) saturate(130%);
    padding: 6px 6px 0; box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 12px 30px rgba(0,0,0,.30);
    transition: border-color .28s ease, box-shadow .28s ease;
}
[data-testid="stPlotlyChart"]:hover { border-color: rgba(34,211,238,.38); box-shadow: inset 0 1px 0 rgba(255,255,255,.06), 0 14px 34px rgba(0,0,0,.36), 0 0 28px rgba(34,211,238,.09); }
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
    box-shadow: 0 10px 26px rgba(0,0,0,.28);
}
[data-testid="stForm"] {
    background: rgba(14,22,42,.56); border: 1px solid var(--border);
    -webkit-backdrop-filter: blur(16px) saturate(140%); backdrop-filter: blur(16px) saturate(140%);
    border-radius: 20px; padding: 22px 24px; box-shadow: 0 14px 36px rgba(0,0,0,.30);
}
[data-testid="stExpander"] details { background: rgba(14,22,42,.55); border: 1px solid var(--border) !important; border-radius: 14px; }
[data-testid="stWidgetLabel"] p { font-weight: 600; font-size: 13px; color: #cbd7f6; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: rgba(10,16,32,.72) !important;
    border-color: var(--border) !important; border-radius: 11px !important;
    transition: border-color .2s ease, box-shadow .2s ease;
}
[data-baseweb="select"] > div:hover, [data-baseweb="input"]:focus-within {
    border-color: rgba(34,211,238,.55) !important; box-shadow: 0 0 0 3px rgba(34,211,238,.10);
}
[data-baseweb="tag"] { background-color: rgba(59,130,246,.22) !important; border-radius: 8px !important; }
.stButton button, .stDownloadButton button, [data-testid^="stBaseButton"] {
    border-radius: 12px; font-weight: 600; transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}
button[kind^="primary"], [data-testid^="stBaseButton-primary"] {
    background: linear-gradient(90deg, #2563eb, #0ea5e9) !important;
    border: none !important; color: #fff !important; box-shadow: 0 6px 22px rgba(37,99,235,.38);
}
button[kind^="primary"]:hover, [data-testid^="stBaseButton-primary"]:hover { transform: translateY(-1px); box-shadow: 0 10px 28px rgba(34,211,238,.38); }
.stDownloadButton button { background: rgba(14,22,42,.7); border: 1px solid var(--border-strong); }
.stDownloadButton button:hover { border-color: var(--cyan); color: var(--cyan); }
[data-testid="stAlert"] { border-radius: 12px; }
.modebar { opacity: .35; }
.modebar:hover { opacity: 1; }

.footer { margin-top: 34px; padding-top: 14px; border-top: 1px solid var(--border); font-size: 11.5px; letter-spacing: .4px; color: var(--muted); }

/* ---------- Motion ---------- */
@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
@keyframes glowDrift {
    0% { transform: translate3d(0,0,0) scale(1); }
    50% { transform: translate3d(3%,2%,0) scale(1.06); }
    100% { transform: translate3d(-3%,-2%,0) scale(1.02); }
}
@keyframes gridDrift { to { transform: translate3d(56px, 56px, 0); } }
@keyframes borderSpin { to { --ang: 360deg; } }
@keyframes sheen { 0%, 55% { transform: translateX(-110%); } 100% { transform: translateX(330%); } }

/* Reduced motion: the stylesheet animations stop; bg_component.py draws one still frame */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* Browsers without backdrop-filter: use more opaque surfaces to keep text readable */
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
    .hero, .kpi, .result, .glass, .callout, [data-testid="stPlotlyChart"], [data-testid="stForm"] { background: rgba(14,22,42,.93); }
    [data-testid="stSidebar"] { background: rgba(8,13,28,.97) !important; }
}

/* ---------- Laptop / small screens ---------- */
@media (max-width: 1280px) {
    .block-container { padding: 1rem 1.4rem 2.5rem; }
    .hero h1 { font-size: 30px; }
}
@media (max-width: 768px) {
    .hero { padding: 22px 20px; border-radius: 18px; }
    .hero h1 { font-size: 25px; }
    .kpi, .result { padding: 16px; min-height: 0; }
    html::before { animation: none; }
    body::before { background-size: 44px 44px; }
}
</style>
"""


def inject_css() -> None:
    """Inject the global stylesheet. Call once, right after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# HTML components (all single-line, all text escaped)
# --------------------------------------------------------------------------
def _e(value) -> str:
    return html.escape(str(value))


def render(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def sidebar_brand() -> None:
    render(
        '<div class="brand"><div class="brand-mark">◈</div><div>'
        '<div class="brand-sub">EDUPRO</div>'
        '<div class="brand-name">Analytics Studio</div></div></div>'
        '<div class="side-tagline">Course intelligence platform</div>'
    )


def sidebar_status(ready: bool, detail: str) -> None:
    """Small status chip. `ready` must reflect something real (the caller
    checks that the saved model files exist); this only renders it."""
    title = "MODELS READY" if ready else "MODELS MISSING"
    css = "ai-status" if ready else "ai-status warn"
    render(
        f'<div class="{css}"><span class="dot"></span><div>'
        f'<div class="st-ttl">{_e(title)}</div>'
        f'<div class="st-sub">{_e(detail)}</div></div></div>'
    )


def sidebar_source(source: str, meta: str) -> None:
    render(
        '<div class="side-label">DATA SOURCE</div>'
        f'<div class="side-source">{_e(source)}</div>'
        f'<div class="side-meta">{_e(meta)}</div>'
    )


def topbar(page: str, pills: list[str]) -> None:
    pill_html = "".join(
        f'<span class="pill">{"<span class=dot></span>" if i == 0 else ""}{_e(p)}</span>'
        for i, p in enumerate(pills)
    )
    render(
        '<div class="topbar"><div class="crumbs"><span>EduPro</span>'
        f'<span class="sep">/</span><strong>{_e(page)}</strong></div>'
        f'<div class="pills">{pill_html}</div></div>'
    )


def hero(title: str, subtitle: str) -> None:
    render(
        '<div class="hero"><div class="eyebrow">EDUPRO · AI COMMAND CENTER</div>'
        f"<h1>{_e(title)}</h1><p>{_e(subtitle)}</p></div>"
    )


def section(title: str, subtitle: str = "") -> None:
    sub = f'<div class="section-subtitle">{_e(subtitle)}</div>' if subtitle else ""
    render(f'<div class="section-title">{_e(title)}</div>{sub}')


def filter_label(text: str) -> None:
    render(f'<div class="filter-label">{_e(text)}</div>')


def kpi_html(label, value, note="", accent="blue", small=False) -> str:
    notes = note if isinstance(note, (list, tuple)) else [note]
    note_html = "".join(f'<div class="kpi-note">{_e(n)}</div>' for n in notes if n)
    size = " kpi-sm" if small else ""
    return (
        f'<div class="kpi kpi-{accent}{size}"><div class="kpi-label">{_e(label)}</div>'
        f'<div class="kpi-value">{_e(value)}</div>{note_html}</div>'
    )


def kpi_row(items, small=False) -> None:
    """items: list of (label, value, note). Accent colours cycle."""
    accents = ["blue", "cyan", "violet", "blue"]
    cols = st.columns(len(items))
    for i, (col, (label, value, note)) in enumerate(zip(cols, items)):
        with col:
            render(kpi_html(label, value, note, accents[i % len(accents)], small))


def result_html(label, value, note, badge="", accent="blue") -> str:
    badge_html = f'<div class="badge">{_e(badge)}</div>' if badge else ""
    return (
        f'<div class="result kpi-{accent}"><div class="kpi-label">{_e(label)}</div>'
        f'<div class="kpi-value">{_e(value)}</div>'
        f'<div class="kpi-note">{_e(note)}</div>{badge_html}</div>'
    )


def callout(kind: str, title: str, body: str) -> None:
    """kind: 'info' | 'warn' | 'note'."""
    icon = {"info": "ⓘ", "warn": "⚠", "note": "✦"}.get(kind, "ⓘ")
    title_html = f'<div class="ttl">{_e(title)}</div>' if title else ""
    render(
        f'<div class="callout callout-{kind}"><div class="ico">{icon}</div>'
        f'<div>{title_html}<div class="bdy">{_e(body)}</div></div></div>'
    )


def glass_card(title: str, body: str) -> str:
    return (
        f'<div class="glass"><div class="g-ttl">{_e(title)}</div>'
        f'<div class="g-bdy">{_e(body)}</div></div>'
    )


def chips(values) -> None:
    render("".join(f'<span class="chip">{_e(v)}</span>' for v in values))


def footer(text: str) -> None:
    render(f'<div class="footer">{_e(text)}</div>')


# --------------------------------------------------------------------------
# Plotly
# --------------------------------------------------------------------------
def style_fig(fig, title=None, height=380, grid="y", legend_bottom=False):
    """Apply the EduPro dark chart style to any Plotly figure."""
    layout = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_STACK, size=12, color="#b6c2df"),
        colorway=PALETTE,
        height=height,
        margin=dict(l=16, r=22, t=64 if title else 26, b=16),
        hoverlabel=dict(
            bgcolor="#0f1629",
            bordercolor="rgba(34,211,238,.55)",
            font=dict(family=FONT_STACK, color=TEXT),
        ),
    )
    if title:
        layout["title"] = dict(
            text=title, x=0.02, xanchor="left", font=dict(size=16, color="#ffffff")
        )
    if legend_bottom:
        layout["legend"] = dict(
            orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0,
            font=dict(size=11), bgcolor="rgba(0,0,0,0)",
        )
    fig.update_layout(**layout)
    fig.update_xaxes(
        showgrid=grid in ("x", "both"), gridcolor=GRID, zeroline=False,
        linecolor=GRID, automargin=True,
    )
    fig.update_yaxes(
        showgrid=grid in ("y", "both"), gridcolor=GRID, zeroline=False,
        linecolor=GRID, automargin=True,
    )
    return fig


def show_chart(fig) -> None:
    stretch(st.plotly_chart, fig, config={"displaylogo": False})


def show_table(df, **kwargs) -> None:
    stretch(st.dataframe, df, hide_index=True, **kwargs)

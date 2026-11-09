"""Identidade visual da Liga DS (Manual da Marca). Funciona mesmo sem .streamlit/config.toml."""
import base64
from pathlib import Path
import streamlit as st
from core.config import TEAL, TEAL_L, AMARELO, AMARELO_L, TINTA

RAIZ = Path(__file__).resolve().parent.parent
LOGO = RAIZ / "assets" / "logo.png"
FAVICON = RAIZ / "assets" / "favicon.png"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inria+Serif:ital,wght@0,400;0,700;1,400&display=swap');
:root {{ --teal:{TEAL}; --teal-l:{TEAL_L}; --am:{AMARELO}; --am-l:{AMARELO_L}; --tinta:{TINTA}; }}

/* tipografia: títulos Poppins, subtítulos Inria Serif, corpo Arial (Manual da Marca) */
[data-testid="stAppViewContainer"] {{ font-family: Arial, Helvetica, sans-serif; color: var(--tinta); }}
h1,h2,h3,h4,[data-testid="stHeading"] h2,[data-testid="stHeading"] h3 {{ font-family: 'Poppins', Arial, sans-serif !important; color: var(--teal); letter-spacing:-.2px; }}
h3 {{ font-size:1.35rem !important; margin-top:.6rem; }}
h3::before {{ content:""; display:inline-block; width:8px; height:1.05em; background:var(--am); border-radius:3px; margin-right:.55rem; vertical-align:-.15em; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ font-family:'Inria Serif', Georgia, serif; font-size:.98rem; color:#4C6670 !important; opacity:1 !important; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ font-family:Arial, sans-serif; font-size:.85rem; color:var(--am-l) !important; }}
.block-container {{ padding-top: 1.6rem; max-width: 1250px; }}

/* faixa de título */
.hero {{ position:relative; overflow:hidden; background:linear-gradient(115deg,{TEAL} 0%, #0F7A94 60%, {TEAL_L} 100%);
  border-radius:20px; padding:26px 34px; margin:0 0 1.2rem 0; border-bottom:6px solid var(--am); box-shadow:0 6px 18px rgba(12,105,128,.18); }}
.hero h1 {{ font-family:'Poppins',Arial,sans-serif; font-weight:700; font-size:2.1rem; margin:0; color:#fff !important; line-height:1.15; }}
.hero p {{ font-family:'Inria Serif',Georgia,serif; font-size:1.08rem; margin:.45rem 0 0 0; color:var(--am-l); max-width:70%; }}
.hero .logo {{ position:absolute; right:30px; top:50%; transform:translateY(-50%); width:84px; height:84px; filter:drop-shadow(0 3px 6px rgba(0,0,0,.25)); }}
.hero svg.deco {{ position:absolute; right:0; top:0; height:100%; opacity:.95; pointer-events:none; }}

/* cartões de métrica */
[data-testid="stMetric"] {{ background:#fff; }}
div[data-testid="stMetricValue"] {{ font-family:'Poppins',Arial,sans-serif; font-weight:700; color:var(--teal); font-size:1.75rem; }}
[data-testid="stMetricLabel"] p {{ font-size:.86rem; color:#4C6670; font-weight:600; }}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stMetric"]) {{ border-top:4px solid var(--am); border-radius:14px; background:#fff; box-shadow:0 2px 8px rgba(12,105,128,.08); }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:14px; }}

[data-testid="stMetric"] {{ min-height:104px; }}
.hero h1 a, .hero [data-testid="stHeaderActionElements"] {{ display:none !important; }}

/* barra lateral */
[data-testid="stSidebar"] {{ background:linear-gradient(180deg,{TEAL} 0%, #0A5468 100%); }}
[data-testid="stSidebar"] * {{ color:#EAF6F9; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:var(--am-l); }}
[data-testid="stSidebarNavLink"] {{ border-radius:10px; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background:var(--am) !important; }}
[data-testid="stSidebarNavLink"][aria-current="page"] * {{ color:var(--tinta) !important; font-weight:700; }}
[data-testid="stSidebarNavLink"]:hover {{ background:rgba(255,255,255,.14); }}
[data-testid="stSidebar"] button:not([data-testid="stLogoLink"]) {{ background:var(--am); border:none; color:var(--tinta) !important; font-weight:700; }}
[data-testid="stSidebar"] button:not([data-testid="stLogoLink"]) * {{ color:var(--tinta) !important; }}
[data-testid="stSidebar"] hr {{ border-color:rgba(255,255,255,.25); }}

/* abas, filtros, botões, barras (cor da marca sem depender de config.toml) */
[data-testid="stTab"] {{ font-weight:600; }}
[data-testid="stTab"][data-selected="true"], [data-testid="stTab"][data-selected="true"] * {{ color:var(--teal) !important; }}
[data-testid="stTab"][data-selected="true"] {{ box-shadow:inset 0 -4px 0 var(--am); }}
[role="tablist"] > div:not([data-testid="stTab"]) {{ background:transparent !important; }}
button[data-variant="pills"][data-selected="true"] {{ background:var(--teal) !important; border-color:var(--teal) !important; }}
button[data-variant="pills"][data-selected="true"] * {{ color:#fff !important; }}
button[data-variant="pills"]:hover {{ border-color:var(--teal) !important; }}
button[data-variant^="segmented"][data-selected="true"] {{ background:var(--teal) !important; }}
button[data-variant^="segmented"][data-selected="true"] * {{ color:#fff !important; }}
[data-testid="stBaseButton-primary"], .stDownloadButton button, [data-testid="stFormSubmitButton"] button {{ background:var(--teal) !important; border-color:var(--teal) !important; color:#fff !important; }}
[data-testid="stSlider"] div[data-rac][style*="translate"] {{ background:var(--teal) !important; }}
[data-testid="stProgress"] [role="progressbar"] > div {{ background:var(--teal) !important; }}
a {{ color:var(--teal); }}

/* destaque de situação */
.situacao {{ display:flex; gap:14px; align-items:center; border-radius:14px; padding:14px 18px; margin:.2rem 0 1.1rem 0; background:#FFF7CC; border:1px solid var(--am); }}
.situacao.ok {{ background:#E5F3F7; border-color:var(--teal-l); }}
.situacao .ponto {{ width:14px; height:14px; border-radius:50%; background:var(--am); box-shadow:0 0 0 5px rgba(254,213,49,.35); flex:none; }}
.situacao.ok .ponto {{ background:var(--teal); box-shadow:0 0 0 5px rgba(12,105,128,.22); }}
.situacao b {{ font-family:'Poppins',Arial,sans-serif; color:var(--tinta); }}
.situacao span {{ color:#33505A; }}
</style>
"""

DECO = f"""<svg class="deco" viewBox="0 0 300 120" preserveAspectRatio="xMaxYMid slice" xmlns="http://www.w3.org/2000/svg">
<path d="M300 0 L300 120 L185 120 C170 90 200 70 215 48 C228 28 215 8 240 0 Z" fill="{TEAL_L}" opacity=".55"/>
<path d="M300 20 L300 120 L235 120 C228 98 250 86 262 66 C272 50 262 34 280 20 Z" fill="{TEAL}" opacity=".55"/>
<path d="M205 30 l6 -14 l6 14 l14 6 l-14 6 l-6 14 l-6 -14 l-14 -6 z" fill="{AMARELO}"/>
<path d="M170 92 l4 -9 l4 9 l9 4 l-9 4 l-4 9 l-4 -9 l-9 -4 z" fill="{AMARELO_L}"/>
</svg>"""


def _b64(p: Path) -> str:
    try:
        return base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""


def aplicar():
    st.markdown(CSS, unsafe_allow_html=True)


def banner(titulo: str, subtitulo: str = ""):
    img = _b64(LOGO)
    logo = f'<img class="logo" src="data:image/png;base64,{img}"/>' if img else ""
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(f'<div class="hero">{DECO}<div><h1>{titulo}</h1>{sub}</div>{logo}</div>', unsafe_allow_html=True)

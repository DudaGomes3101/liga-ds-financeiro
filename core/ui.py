"""Formatação e estilo compartilhados."""
import plotly.graph_objects as go
import streamlit as st
from core.config import CINZA_CLARO


def brl(v, sinal=False):
    if v is None or v != v:
        return "—"
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    pre = "-" if v < 0 else ("+" if sinal and v > 0 else "")
    return f"{pre}R$ {s}"


def md(s: str) -> str:
    """Escapa o cifrão para o markdown não tratá-lo como fórmula."""
    return s.replace("R$", "R\\$")


def tabela(df, moeda=(), datas=(), inteiros=()):
    """Tabela somente leitura com formatação brasileira (R$ 1.234,56, 18/10/2026)."""
    f = {c: brl for c in moeda}
    f.update({c: (lambda v: "—" if v != v else f"{v:%d/%m/%Y}") for c in datas})
    f.update({c: "{:.0f}" for c in inteiros})
    return df.style.format(f, na_rep="—")


def pct(v, d=0):
    return "—" if v is None or v != v else f"{v * 100:.{d}f}%".replace(".", ",")


def style(fig: go.Figure, h=380, legenda=True):
    fig.update_layout(
        height=h, margin=dict(l=8, r=8, t=40, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", size=13, color="#1F2430"),
        title=dict(font=dict(size=15), x=0, xanchor="left"), showlegend=legenda,
        legend=dict(orientation="h", y=-0.15, x=0), hoverlabel=dict(bgcolor="white", font_size=13),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=CINZA_CLARO)
    fig.update_yaxes(gridcolor=CINZA_CLARO, zeroline=True, zerolinecolor="#8A90A6", zerolinewidth=1)
    return fig


def cabecalho(titulo, pergunta=None):
    """Título da página. Dentro de uma aba (secoes/), mostra só a pergunta."""
    if not st.session_state.get("_em_aba"):
        st.title(titulo)
    if pergunta:
        st.caption(pergunta)


def aviso_confianca(n_pend, n_total):
    if n_pend:
        st.caption(f":material/info: {n_pend} de {n_total} lançamentos ainda aguardam confirmação. Os números podem mudar.")


def abas(titulo, subtitulo, secoes):
    """Página com abas. secoes = [(rótulo, ícone, arquivo em secoes/)]."""
    import runpy
    from pathlib import Path
    st.title(titulo)
    st.caption(subtitulo)
    tabs = st.tabs([f"{ic} {rot}" for rot, ic, _ in secoes])
    base = Path(__file__).resolve().parent.parent / "secoes"
    for tab, (_, _, arq) in zip(tabs, secoes):
        with tab:
            st.session_state["_em_aba"] = True
            try:
                runpy.run_path(str(base / arq))
            finally:
                st.session_state["_em_aba"] = False

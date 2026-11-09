import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core.config import TEAL, TEAL_L, AMARELO, AMARELO_L, TINTA, CINZA, CINZA_CLARO, VERDE, VERMELHO, PERFIL_COR
from scipy import stats
from core.config import TEAL, PERFIL_COR, CINZA
from core.data import get_dados, S
from core.ui import brl, style, cabecalho

D = get_dados()
ev, df = D.ev, D.df
cabecalho("Análises de dados", "Dispersão, regressão e o quanto dá para confiar nelas.")

st.subheader("Quanto o evento gasta × quanto arrecada")
pts = ev[(ev.receita > 0) & (ev.despesa > 0)].reset_index(drop=True)
if len(pts) < 4:
    st.info("Poucos eventos com receita e despesa para ajustar a reta.")
else:
    x, y = pts.despesa.values, pts.receita.values
    n = len(x)
    r = stats.linregress(x, y)
    xs = np.linspace(x.min(), x.max(), 60)
    yhat = r.intercept + r.slope * xs
    s = np.sqrt(np.sum((y - (r.intercept + r.slope * x)) ** 2) / (n - 2))
    sxx = np.sum((x - x.mean()) ** 2)
    t = stats.t.ppf(0.975, n - 2)
    band = t * s * np.sqrt(1 / n + (xs - x.mean()) ** 2 / sxx)

    fig = go.Figure()
    fig.add_scatter(x=np.r_[xs, xs[::-1]], y=np.r_[yhat + band, (yhat - band)[::-1]], fill="toself", fillcolor="rgba(90,63,192,0.12)",
                    line=dict(width=0), hoverinfo="skip", name="Intervalo de 95% da reta")
    fig.add_scatter(x=xs, y=yhat, mode="lines", line=dict(color=TEAL, dash="dash"), name="Reta de regressão")
    fig.add_scatter(x=x, y=y, mode="markers+text", text=pts.evento, textposition="top center", textfont=dict(size=11),
                    marker=dict(size=11, color=[PERFIL_COR.get(p, CINZA) for p in pts.perfil], line=dict(color="white", width=1)), name="Eventos",
                    hovertemplate="<b>%{text}</b><br>Despesa: R$ %{x:,.2f}<br>Receita: R$ %{y:,.2f}<extra></extra>")
    fig.update_layout(title="Receita × despesa por evento (R$)", xaxis_title="Despesa", yaxis_title="Receita")
    st.plotly_chart(style(fig, 480), width="stretch")

    # validação leave-one-out: o modelo bate o chute "receita = média"?
    e_mod, e_base = [], []
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        b1, b0 = np.polyfit(x[m], y[m], 1)
        e_mod.append(y[i] - (b0 + b1 * x[i]))
        e_base.append(y[i] - y[m].mean())
    rmse = lambda e: float(np.sqrt(np.mean(np.square(e))))
    rm, rb = rmse(e_mod), rmse(e_base)

    k = st.columns(4)
    k[0].metric("Eventos (n)", n, border=True)
    k[1].metric("R²", f"{r.rvalue ** 2:.2f}".replace(".", ","), border=True, help="Fração da variação da receita explicada pela despesa, nesses pontos.")
    k[2].metric("p-valor", f"{r.pvalue:.3f}".replace(".", ","), border=True, help="Abaixo de 0,05 indica relação distinguível do acaso. Com n pequeno, é difícil chegar lá.")
    k[3].metric("Erro médio do modelo", brl(rm), f"chute da média: {brl(rb)}", delta_color="off", border=True,
                help="Validação leave-one-out: prevê cada evento sem usá-lo no ajuste e compara com simplesmente prever a receita média dos outros.")
    if rm >= rb or r.pvalue > 0.05:
        st.warning(f"**Leitura honesta:** com {n} eventos a reta descreve o passado, mas não prevê o futuro com confiança"
                   f"{' e não vence o chute da média na validação' if rm >= rb else ''}. Use como indício, não como projeção. "
                   "A Festa Junina pesa muito na inclinação; mais edições mudarão o resultado.")
    else:
        st.success("A reta supera o chute da média na validação, mas ainda com poucos eventos. Use com cautela.")

st.subheader("Gasto por participante")
st.caption("Preencha os participantes (Data Journey: inscritos/presentes no Drive; Festa Junina: estimativa por corn dogs/waffles vendidos). Os números ficam só nesta sessão.")
base = ev[ev.despesa > 0][["evento", "despesa"]].copy()
base["participantes"] = np.nan
ed = st.data_editor(base, disabled=["evento", "despesa"], hide_index=True, width="stretch", key="part",
                    column_config={"evento": "Evento", "despesa": st.column_config.NumberColumn("Despesa (R$)", format="localized"),
                                   "participantes": st.column_config.NumberColumn("Participantes", min_value=1, step=1)})
ok = ed.dropna(subset=["participantes"])
if len(ok):
    ok = ok.assign(por_pessoa=ok.despesa / ok.participantes)
    f2 = go.Figure(go.Bar(x=ok.evento, y=ok.por_pessoa, marker_color=TEAL, text=[brl(v) for v in ok.por_pessoa], textposition="outside"))
    f2.update_layout(title="Despesa por participante (R$)")
    st.plotly_chart(style(f2, 340, legenda=False), width="stretch")

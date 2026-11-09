import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from core.config import TEAL, TEAL_L, AMARELO, AMARELO_L, TINTA, CINZA, CINZA_CLARO, VERDE, VERMELHO, PERFIL_COR
from core.config import CAT_PENDENTES, TEAL
from core.data import get_dados, S
from core.ui import brl, style, cabecalho, tabela

D = get_dados()
df = D.df[D.df.tipo == S].copy()
cabecalho("Para onde vai o dinheiro", "Despesas por categoria. O quadro maior é onde mais se gasta.")

anos = sorted(df.ano.unique())
sel = st.pills("Ano", anos, selection_mode="multi", default=anos, key="ano_categorias")
d = df[df.ano.isin(sel or anos)]
tot = d.valor.sum()
pend = d[d.categoria.isin(CAT_PENDENTES)].valor.sum()

c = st.columns(3)
c[0].metric("Despesa no período", brl(tot), border=True)
top = d.groupby("categoria").valor.sum().drop(labels=CAT_PENDENTES, errors="ignore").sort_values(ascending=False)
c[1].metric("Maior categoria", top.index[0] if len(top) else "—", brl(top.iloc[0]) if len(top) else None, delta_color="off", border=True)
c[2].metric("Sem itemização", f"{pend / tot * 100:.0f}%" if tot else "—", brl(pend), delta_color="off", border=True,
            help="Despesas registradas só pelo total ('A detalhar') ou sem classificação ('A confirmar').")
if tot and pend / tot > 0.15:
    st.warning("Boa parte das despesas ainda não foi itemizada (Festa Junina 2025 e 2026). Até levantar as notas, a análise por categoria subestima alimentação, decoração e brindes.")

paleta = [TEAL, TEAL_L, AMARELO, AMARELO_L, "#5F7480", "#8FA3AD", "#BFDCE6", "#2B3A42"]
tm = d.groupby(["categoria", "descricao"], as_index=False).valor.sum()
fig = px.treemap(tm, path=[px.Constant("Despesas"), "categoria", "descricao"], values="valor", color="categoria", color_discrete_sequence=paleta)
fig.update_traces(textinfo="label+value", texttemplate="%{label}<br>R$ %{value:,.0f}", marker=dict(cornerradius=4), root_color="#FAFAFC")
fig.update_layout(title="Despesas por categoria e item (clique para entrar)", uniformtext=dict(minsize=11, mode="hide"))
st.plotly_chart(style(fig, 460, legenda=False), width="stretch")

l, r = st.columns(2)
with l:
    pc = d.groupby(["categoria", "ano"], as_index=False).valor.sum()
    f2 = px.bar(pc, y="categoria", x="valor", color=pc.ano.astype(str), orientation="h", color_discrete_sequence=[AMARELO_L, TEAL_L, TEAL],
                labels={"valor": "R$", "categoria": "", "color": "Ano"})
    f2.update_layout(title="Categoria por ano (R$)", barmode="stack", yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(style(f2, 380), width="stretch")
with r:
    st.markdown("**Maiores lançamentos**")
    st.dataframe(tabela(d.sort_values("valor", ascending=False).head(10)[["data", "evento", "descricao", "valor"]], moeda=["valor"], datas=["data"]),
                 hide_index=True, width="stretch", column_config={"data": "Data", "evento": "Evento", "descricao": "Descrição", "valor": "Valor"})

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core.config import PERFIL_COR, VERDE, VERMELHO, ROXO
from core.data import get_dados, alertas, camisetas, maior_gasto_evento, S
from core.ui import brl, style, cabecalho

D = get_dados()
ev, df = D.ev, D.df
cabecalho("Resumo do caixa", "Estamos bem financeiramente? Os quatro números abaixo respondem em poucos segundos.")

# ---- KPIs
cam = camisetas(D.total)
maior = maior_gasto_evento(ev)
res = df[df.ano == 2026]
res26 = res[res.tipo == "Entrada"].valor.sum() - res[res.tipo == "Saída"].valor.sum()
res25 = df[df.ano == 2025]
res25 = res25[res25.tipo == "Entrada"].valor.sum() - res25[res25.tipo == "Saída"].valor.sum()
mens = df.assign(m=df.data.dt.to_period("M").dt.to_timestamp()).groupby("m").apply(
    lambda g: g[g.tipo == "Entrada"].valor.sum() - g[g.tipo == "Saída"].valor.sum(), include_groups=False).sort_index()

c = st.columns(4)
with c[0]:
    if D.saldo:
        st.metric(f"Caixa em {D.saldo['data']:%d/%m/%Y}", brl(D.saldo["liquido"]), f"bruto {brl(D.saldo['bruto'])}", delta_color="off",
                  border=True, help="Saldo líquido de IR informado no app do banco. Não é somado dos lançamentos porque a caixinha rende.")
    else:
        st.metric("Caixa", "n/d", "preencher a aba 'saldo'", delta_color="off", border=True)
with c[1]:
    if D.saldo and maior:
        n = D.saldo["liquido"] / maior
        st.metric("Eventos que o caixa cobre", f"{n:.1f}".replace(".", ","), f"maior evento: {brl(maior)}", delta_color="off",
                  border=True, help="Caixa dividido pelo maior gasto já registrado em um único evento. Mede o risco de chegar um evento e não ter dinheiro.")
    else:
        st.metric("Eventos que o caixa cobre", "n/d", border=True)
with c[2]:
    st.metric("Resultado de 2026", brl(res26), f"{brl(res26 - res25, True)} vs 2025 inteiro", border=True,

              help="Receitas menos despesas dos eventos de 2026. A Festa Junina 2026 usa receita bruta (lucro informado + despesas).")
with c[3]:
    st.metric("A receber das camisetas", brl(cam["falta"]), f"{cam['reembolsado'] / cam['pago'] * 100:.0f}% já reembolsado" if cam["pago"] else None,
              delta_color="off", border=True, help="Valor adiantado à fornecedora que os membros ainda não devolveram.")

# ---- atenção
st.subheader("O que merece atenção")
al = alertas(D)
if not al:
    st.success("Nada crítico no momento.")
else:
    cols = st.columns(len(al))
    for col, (sev, titulo, acao) in zip(cols, al):
        with col.container(border=True):
            st.markdown(f"{':red[:material/priority_high:]' if sev == 'alta' else ':orange[:material/schedule:]'} **{titulo}**")
            st.caption(f"Próximo passo: {acao}")

# ---- resultado por evento
st.subheader("Cada evento deu retorno?")
evg = ev[ev.lancamentos > 0].copy()
evg = evg[(evg.receita > 0) | (evg.despesa > 50)].sort_values("data")
fig = go.Figure(go.Bar(
    x=evg["evento"], y=evg["resultado"], marker_color=[PERFIL_COR.get(p, "#9AA0B4") for p in evg["perfil"]],
    customdata=np.stack([evg["receita"], evg["despesa"], evg["perfil"]], axis=-1),
    hovertemplate="<b>%{x}</b><br>Receita: R$ %{customdata[0]:,.2f}<br>Despesa: R$ %{customdata[1]:,.2f}<br>Resultado: R$ %{y:,.2f}<br>%{customdata[2]}<extra></extra>"))
fig.update_layout(title="Resultado por evento (R$)  ·  roxo = eventos que arrecadam, cinza/lilás = formação, membros e operação")
fig.update_xaxes(tickangle=-35)
st.plotly_chart(style(fig, 420, legenda=False), width="stretch")
st.caption("Eventos de formação e integração não existem para dar lucro: o resultado negativo deles é investimento nos membros. "
           "A classificação de cada tipo de evento está em `core/config.py` e deve ser validada com a Diretoria.")

# ---- evolução
c1, c2 = st.columns([3, 2])
with c1:
    por_ano = df.groupby(["ano", "tipo"])["valor"].sum().unstack(fill_value=0).reindex(columns=["Entrada", "Saída"], fill_value=0)
    f2 = go.Figure()
    f2.add_bar(x=por_ano.index.astype(str), y=por_ano["Entrada"], name="Receita", marker_color=ROXO)
    f2.add_bar(x=por_ano.index.astype(str), y=por_ano["Saída"], name="Despesa", marker_color="#B8BCCB")
    f2.update_layout(barmode="group", title="Receita e despesa por ano (R$)")
    st.plotly_chart(style(f2, 340), width="stretch")
with c2:
    fj = ev[ev.familia == "Festa Junina"].sort_values("ano")
    if len(fj):
        f3 = go.Figure(go.Bar(x=fj["ano"].astype(str), y=fj["resultado"], marker_color=ROXO,
                              text=[brl(v) for v in fj["resultado"]], textposition="outside", cliponaxis=False))
        f3.update_layout(title="Festa Junina: lucro por edição")
        f3.update_yaxes(showticklabels=False, zeroline=False)
        st.plotly_chart(style(f3, 340, legenda=False), width="stretch")
        st.caption("A Festa Junina é a principal fonte de receita da Liga.")

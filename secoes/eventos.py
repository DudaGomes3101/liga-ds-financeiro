import numpy as np
import plotly.graph_objects as go
import streamlit as st
from core.config import TEAL, TEAL_L, AMARELO, AMARELO_L, TINTA, CINZA, CINZA_CLARO, VERDE, VERMELHO, PERFIL_COR
from core.config import TEAL, VERDE, VERMELHO, CINZA, PERFIL_COR
from core.data import get_dados, S
from core.ui import brl, style, cabecalho, aviso_confianca, tabela

D = get_dados()
ev, df = D.ev, D.df
cabecalho("Eventos", "Quanto cada evento arrecadou, gastou e deixou de resultado.")

# ---- filtros
f1, f2 = st.columns([3, 2])
perfis = sorted(ev.perfil.unique())
sel_perfil = f1.pills("Tipo de evento", perfis, selection_mode="multi", default=[p for p in perfis if p != "A classificar"] or perfis)
anos = sorted(ev.ano.unique())
sel_ano = f2.pills("Ano", anos, selection_mode="multi", default=anos)
t = ev[ev.perfil.isin(sel_perfil or perfis) & ev.ano.isin(sel_ano or anos)].sort_values("data", ascending=False).copy()
t["custo_real"] = np.where(t.perfil == "Arrecadação", t.custo_real, np.nan)

vis = t[["evento", "perfil", "receita", "despesa", "resultado", "custo_real", "pendente"]].copy()
vis["custo_real"] = vis["custo_real"].map(lambda v: "—" if v != v else brl(v))
st.dataframe(
    tabela(vis, moeda=["receita", "despesa", "resultado"], inteiros=["pendente"]),
    hide_index=True, width="stretch",
    column_config={
        "evento": "Evento", "perfil": "Tipo", "receita": "Receita", "despesa": "Despesa", "resultado": "Resultado",
        "custo_real": st.column_config.Column("Custo por R$ 1 arrecadado", help="Só para eventos de arrecadação. Menor é melhor; acima de R$ 1,00 o evento deu prejuízo."),
        "pendente": st.column_config.Column("A confirmar", help="Lançamentos ainda não validados"),
    })

# ---- raio-x
st.subheader("Raio-X de um evento")
op = t[(t.receita > 0) | (t.despesa > 0)]
if not len(op):
    st.info("Nenhum evento nesse filtro.")
    st.stop()
padrao = op[op.perfil == "Arrecadação"].evento.tolist()
nome = st.selectbox("Evento", op.evento.tolist(), index=op.evento.tolist().index(padrao[0]) if padrao else 0)
r = ev[ev.evento == nome].iloc[0]
m = st.columns(4)
m[0].metric("Receita", brl(r.receita), border=True)
m[1].metric("Despesa", brl(r.despesa), border=True)
m[2].metric("Resultado", brl(r.resultado), "lucro" if r.resultado >= 0 else "investimento", delta_color="normal" if r.resultado >= 0 else "off", border=True)
if r.perfil == "Arrecadação":
    m[3].metric("Custo por R$ 1 arrecadado", brl(r.custo_real), border=True,
                help="Despesa dividida pela receita. Menor é melhor.")
else:
    m[3].metric("Tipo", r.perfil, "não visa lucro", delta_color="off", border=True)

lanc = df[df.evento == nome]
desp = lanc[lanc.tipo == S].groupby("categoria")["valor"].sum().sort_values(ascending=False)
meas = ["relative"] * (len(desp) + 1) + ["total"]
xs = ["Receita"] + list(desp.index) + ["Resultado"]
ys = [r.receita] + [-v for v in desp.values] + [0]
textos = [brl(r.receita)] + [brl(-v) for v in desp.values] + [brl(r.resultado)]
w = go.Figure(go.Waterfall(x=xs, y=ys, measure=meas, connector=dict(line=dict(color="#D9DCE8")),
                           increasing=dict(marker=dict(color=TEAL)), decreasing=dict(marker=dict(color=AMARELO)),
                           totals=dict(marker=dict(color=VERDE if r.resultado >= 0 else VERMELHO)),
                           text=textos, textposition="outside", hoverinfo="x+text"))
w.update_layout(title=f"De onde veio e para onde foi o dinheiro: {nome}")
st.plotly_chart(style(w, 380, legenda=False), width="stretch")
with st.expander(f"Ver os {len(lanc)} lançamentos"):
    st.dataframe(tabela(lanc.sort_values("data")[["data", "tipo", "categoria", "descricao", "valor", "confirmar"]], moeda=["valor"], datas=["data"]),
                 hide_index=True, width="stretch",
                 column_config={"data": "Data", "tipo": "Tipo", "categoria": "Categoria", "descricao": "Descrição", "valor": "Valor", "confirmar": "A confirmar"})
aviso_confianca(int(lanc.confirmar.sum()), len(lanc))

# ---- comparar edições
st.subheader("Comparar edições do mesmo evento")
fams = [f for f, g in ev[ev.perfil != "A classificar"].groupby("familia") if len(g) >= 2]
if fams:
    fam = st.selectbox("Evento", fams, index=fams.index("Festa Junina") if "Festa Junina" in fams else 0)
    g = ev[ev.familia == fam].sort_values("ano")
    fg = go.Figure()
    fg.add_bar(x=g.ano.astype(str), y=g.receita, name="Receita", marker_color=TEAL)
    fg.add_bar(x=g.ano.astype(str), y=g.despesa, name="Despesa", marker_color=AMARELO)
    fg.update_layout(barmode="group", title=f"{fam}: receita e despesa por edição (R$)")
    st.plotly_chart(style(fg, 340), width="stretch")
    if len(g) >= 2:
        a, b = g.iloc[-2], g.iloc[-1]
        k = st.columns(3)
        k[0].metric(f"Receita {int(b.ano)}", brl(b.receita), f"{brl(b.receita - a.receita, True)} vs {int(a.ano)}", border=True)
        k[1].metric(f"Despesa {int(b.ano)}", brl(b.despesa), f"{brl(b.despesa - a.despesa, True)} vs {int(a.ano)}", delta_color="inverse", border=True)
        k[2].metric(f"Resultado {int(b.ano)}", brl(b.resultado), f"{brl(b.resultado - a.resultado, True)} vs {int(a.ano)}", border=True)

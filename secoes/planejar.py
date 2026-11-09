import numpy as np
import pandas as pd
import streamlit as st
from core.config import ROXO
from core.data import get_dados, S
from core.ui import brl, style, cabecalho

D = get_dados()
ev, df = D.ev, D.df
cabecalho("Planejar um evento", "Quanto reservar para o próximo evento, com base no que as edições anteriores custaram.")

fams = sorted(f for f in ev.familia.unique() if f not in ("A confirmar",) and (ev[ev.familia == f].despesa.sum() > 0))
fam = st.selectbox("Qual evento você quer planejar?", fams, index=fams.index("Festa Junina") if "Festa Junina" in fams else 0)
hist = ev[ev.familia == fam].sort_values("ano")
n = len(hist)
if n < 2:
    st.warning(f"Só existe {n} edição registrada de {fam}. A sugestão abaixo é apenas essa edição; use com cuidado.")

# histórico por categoria × edição
mat = (df[(df.tipo == S) & df.evento.isin(hist.evento)].pivot_table(index="categoria", columns="evento", values="valor", aggfunc="sum", fill_value=0)
       .reindex(columns=hist.evento))
cols = st.columns([2, 1.3, 1])
base = cols[0].segmented_control("Base da sugestão", ["Média das edições", "Última edição", "Maior edição"], default="Média das edições")
ajuste = cols[1].slider("Ajuste (inflação, mais público)", -30, 50, 10, format="%d%%") / 100
perfil = hist.perfil.iloc[0]
if base == "Última edição":
    sug = mat.iloc[:, -1]
elif base == "Maior edição":
    sug = mat[mat.sum().idxmax()]
else:
    sug = mat.mean(axis=1)
sug = (sug * (1 + ajuste)).round(2)

st.markdown("**Orçamento por categoria** (edite os valores da coluna Orçamento)")
tab = pd.DataFrame({"Categoria": mat.index, **{c.replace(fam, "").strip() or c: mat[c].values for c in mat.columns}, "Orçamento": sug.values})
cfg = {c: st.column_config.NumberColumn(f"{c} (R$)", format="localized", disabled=True) for c in tab.columns if c not in ("Categoria", "Orçamento")}
cfg["Categoria"] = st.column_config.TextColumn(disabled=True)
cfg["Orçamento"] = st.column_config.NumberColumn("Orçamento (R$)", format="localized", min_value=0.0, step=5.0)
ed = st.data_editor(tab, column_config=cfg, hide_index=True, width="stretch", key=f"orc_{fam}_{base}_{ajuste}")
total = float(ed["Orçamento"].sum())

rec_hist = float(hist.receita.mean())
st.markdown("**Receita esperada**")
r1, r2 = st.columns([2, 3])
receita = r1.number_input("Receita esperada (R$)", min_value=0.0, value=round(rec_hist, 2), step=50.0,
                          help=f"Padrão: média das {n} edições ({brl(rec_hist)}). Para eventos que não arrecadam, deixe baixo.")
r2.caption("Seja conservador: o orçamento é uma decisão de gasto, a receita é uma estimativa.")

caixa = D.saldo["liquido"] if D.saldo else 0.0
c = st.columns(4)
c[0].metric("Orçamento de despesa", brl(total), border=True)
c[1].metric("Resultado esperado", brl(receita - total), "lucro" if receita >= total else "investimento", delta_color="normal" if receita >= total else "off", border=True)
c[2].metric("Pior caso (receita zero)", brl(caixa - total), f"caixa após gastar {brl(total)}", delta_color="off", border=True,
            help="Caixa líquido atual menos todo o orçamento, sem nenhuma receita.")
c[3].metric("Orçamento vs. última edição", brl(total - float(hist.despesa.iloc[-1]), True), f"última: {brl(float(hist.despesa.iloc[-1]))}", delta_color="off", border=True)
if caixa and caixa - total < 0:
    st.error("Nesse cenário o orçamento passa do caixa atual. Só é seguro se a receita vier.")
st.caption(f"Base: {n} edição(ões) de {fam} ({', '.join(str(int(a)) for a in hist.ano)}). Poucas edições, então trate como ponto de partida para a conversa com a Diretoria, não como previsão.")
if "A detalhar" in mat.index:
    st.caption(":material/info: Parte do histórico está como 'A detalhar' (sem itemização), então o orçamento por categoria fica agregado nessa linha.")

out = ed.rename(columns={"Orçamento": f"Orçamento {fam}"})[["Categoria", f"Orçamento {fam}"]]
st.download_button("Baixar orçamento (CSV)", out.to_csv(index=False).encode("utf-8-sig"), f"orcamento_{fam.lower().replace(' ', '_')}.csv", "text/csv")

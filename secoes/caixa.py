import numpy as np
import plotly.graph_objects as go
import streamlit as st
from core.config import TEAL, TEAL_L, AMARELO, AMARELO_L, TINTA, CINZA, CINZA_CLARO, VERDE, VERMELHO, PERFIL_COR
from core.config import TEAL, CINZA_CLARO, VERDE, VERMELHO
from core.data import get_dados, camisetas, maior_gasto_evento, reserva_alvo, gasto_por_ano
from core.ui import brl, style, cabecalho, md, tabela

D = get_dados()
ev, df = D.ev, D.df
cabecalho("Caixa e reserva de emergência", "Se chegar um evento grande e a receita não vier, o caixa aguenta?")

caixa = D.saldo["liquido"] if D.saldo else st.number_input("Saldo líquido da caixinha (R$)", min_value=0.0, value=0.0, step=50.0)
maior = maior_gasto_evento(ev)
ga = gasto_por_ano(df)

with st.container(border=True):
    st.markdown("**Defina a meta de reserva**")
    a, b, c = st.columns([2, 2, 2])
    metodo = a.segmented_control("Como medir", ["Eventos grandes", "Meses de gasto"], default="Eventos grandes",
                                 help="Eventos grandes: quantos eventos do tamanho do maior já feito a Liga consegue bancar sozinha. Meses de gasto: fração do gasto médio anual.")
    if metodo == "Meses de gasto":
        k = b.slider("Meses de gasto a cobrir", 1, 12, 6)
    else:
        k = b.slider("Eventos grandes a cobrir", 1, 3, 1)
    folga = c.slider("Margem de segurança", 0, 50, 20, format="%d%%") / 100
alvo = reserva_alvo(ev, df, "evento" if metodo != "Meses de gasto" else "meses", k, folga)

gap = caixa - alvo
fig = go.Figure(go.Indicator(
    mode="gauge", value=caixa,
    gauge=dict(shape="bullet", axis=dict(range=[0, max(caixa, alvo) * 1.25 or 1]), bar=dict(color=TEAL, thickness=0.5),
               threshold=dict(line=dict(color=TINTA, width=4), thickness=0.85, value=alvo),
               steps=[dict(range=[0, alvo * 0.5], color="#BFDCE6"), dict(range=[alvo * 0.5, alvo], color="#DCEDF3"),
                      dict(range=[alvo, max(caixa, alvo) * 1.25 or 1], color="#F0F7FA")])))
fig.update_layout(height=130, margin=dict(l=20, r=20, t=10, b=20), paper_bgcolor="rgba(0,0,0,0)")
st.markdown("**Caixa líquido (barra azul) contra a meta (traço escuro)**")
st.plotly_chart(fig, width="stretch")
st.caption("Barra azul = caixa atual. Traço escuro = meta. Faixas: abaixo de 50% da meta, entre 50% e 100%, e acima da meta.")

m = st.columns(4)
m[0].metric("Caixa líquido", brl(caixa), border=True)
m[1].metric("Meta de reserva", brl(alvo), border=True)
m[2].metric("Sobra" if gap >= 0 else "Falta", brl(abs(gap)), "meta atingida" if gap >= 0 else "abaixo da meta", delta_color="normal" if gap >= 0 else "inverse", border=True)
fj = ev[(ev.familia == "Festa Junina")]
if gap < 0 and len(fj) and fj.resultado.mean() > 0:
    m[3].metric("Equivale a", f"{abs(gap) / fj.resultado.mean():.1f} Festas Juninas".replace(".", ","), f"lucro médio {brl(fj.resultado.mean())}", delta_color="off", border=True)
elif maior:
    m[3].metric("Eventos cobertos", f"{caixa / maior:.1f}".replace(".", ","), f"maior: {brl(maior)}", delta_color="off", border=True)

with st.expander("Como a meta é calculada"):
    st.markdown(md(f"""
- **Eventos grandes:** maior despesa já registrada em um único evento ({brl(maior)}) × número de eventos × (1 + margem).
- **Meses de gasto:** gasto médio por ano ({brl(float(ga.mean())) if len(ga) else '—'}) ÷ 12 × meses × (1 + margem).
- É uma **regra de bolso para discussão**, não uma projeção. Há poucos eventos registrados, parte das despesas ainda está sem itemização e 2026 está incompleto, então o valor tende a estar subestimado.
- A meta final deve ser definida pela Diretoria.
"""))

st.subheader("Gasto por evento")
g = ev[ev.despesa > 0].sort_values("despesa")
f2 = go.Figure(go.Bar(y=g.evento, x=g.despesa, orientation="h", marker_color=[TEAL if v == g.despesa.max() else AMARELO for v in g.despesa]))
f2.update_layout(title="Despesa por evento (R$): o maior define a reserva", yaxis=dict(autorange=True))
st.plotly_chart(style(f2, max(320, 26 * len(g) + 80), legenda=False), width="stretch")

st.subheader("Dinheiro a receber")
cam = camisetas(D.total)
if cam["pago"]:
    p = cam["reembolsado"] / cam["pago"]
    cc = st.columns(3)
    cc[0].metric("Pago à fornecedora (2 parcelas)", brl(cam["pago"]), border=True)
    cc[1].metric("Já reembolsado", brl(cam["reembolsado"]), f"{p * 100:.0f}%", delta_color="off", border=True)
    cc[2].metric("Falta receber", brl(cam["falta"]), border=True)
    st.progress(min(p, 1.0), text=f"Camisetas 2026: {p * 100:.0f}% reembolsado")
    with st.expander("Ver lançamentos das camisetas"):
        st.dataframe(tabela(cam["linhas"].sort_values("data")[["data", "tipo", "valor", "descricao"]], moeda=["valor"], datas=["data"]), hide_index=True, width="stretch",
                     column_config={"data": "Data", "tipo": "Tipo", "valor": "Valor", "descricao": "Descrição"})
else:
    st.info("Sem lançamentos de camisetas em 2026.")

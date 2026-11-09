import streamlit as st
from core.config import TEAL, TEAL_L, AMARELO, AMARELO_L, TINTA, CINZA, CINZA_CLARO, VERDE, VERMELHO, PERFIL_COR
from core.config import CAT_PENDENTES
from core.data import get_dados, segredo, S
from core.ui import brl, cabecalho, tabela

D = get_dados()
cabecalho("Qualidade dos dados", "Quanto dá para confiar nos números e o que falta validar.")

t = D.total
conf = int(t.confirmar.sum())
valid = 1 - conf / len(t)
desp = D.df[D.df.tipo == S]
semitem = desp[desp.categoria.isin(CAT_PENDENTES)].valor.sum() / max(desp.valor.sum(), 1)
k = st.columns(3)
k[0].metric("Lançamentos validados", f"{valid * 100:.0f}%", f"{conf} de {len(t)} a confirmar", delta_color="off", border=True)
k[1].metric("Despesa itemizada", f"{(1 - semitem) * 100:.0f}%", f"{semitem * 100:.0f}% sem itemização", delta_color="off", border=True)
k[2].metric("Última movimentação", f"{t.data.max():%d/%m/%Y}", D.fonte, delta_color="off", border=True)

st.subheader("Checklist para fechar a base")
itens = [
    ("Itemizar despesas da Festa Junina 2025 e 2026", semitem < 0.05),
    ("Validar os lançamentos marcados com o Jomas", conf == 0),
    ("Informar o saldo da caixinha atualizado (aba `saldo`)", D.saldo is not None),
    ("Levantar participantes por evento", False),
    ("Definir quem alimenta a base e com que frequência", False),
]
for txt, ok in itens:
    st.markdown(f"{':green[:material/check_circle:]' if ok else ':gray[:material/radio_button_unchecked:]'} {txt}")

st.subheader("Lançamentos aguardando confirmação")
pend = t[t.confirmar].sort_values("data")
st.dataframe(tabela(pend[["data", "tipo", "valor", "evento", "categoria", "descricao"]], moeda=["valor"], datas=["data"]), hide_index=True, width="stretch",
             column_config={"data": "Data", "tipo": "Tipo", "valor": "Valor", "evento": "Evento", "categoria": "Categoria", "descricao": "Descrição"})

with st.expander("Decisões de modelagem (para a Diretoria conhecer)"):
    st.markdown("""
- **2023 fica fora das análises**, porque os custos daquele ano não foram registrados.
- **Camisetas** (adiantamento e reembolso) ficam fora das análises por evento e aparecem em *Caixa e reserva*.
- **"Lucro" informado** (Festa Junina 2026 e Calourada 2026) é líquido; a receita bruta é reconstruída somando as despesas do evento.
- **Tipo de evento** (arrecadação, formação, membros, operação) é uma classificação adotada pelo time e deve ser validada.
- **Caixa** é o saldo informado do banco, não a soma dos lançamentos, porque a caixinha rende.
""")
if segredo("app_password"):
    st.download_button("Baixar base completa (CSV)", t.to_csv(index=False).encode("utf-8-sig"), "fluxo_de_caixa.csv", "text/csv")

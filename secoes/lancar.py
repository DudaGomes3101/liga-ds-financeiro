import pandas as pd
import streamlit as st
from core.config import TEAL, TEAL_L, AMARELO, AMARELO_L, TINTA, CINZA, CINZA_CLARO, VERDE, VERMELHO, PERFIL_COR
from core.config import COLUNAS
from core.data import get_dados, segredo
from core.ui import tabela

D = get_dados()
st.caption("Registre cada entrada ou saída assim que acontecer. Quanto mais fresco o registro, mais confiável o painel.")

pode_escrever = bool(segredo("permitir_escrita")) and bool(segredo("gcp_service_account"))
eventos = sorted(D.total.evento.unique(), key=lambda e: D.total[D.total.evento == e].data.max(), reverse=True)
cats = [c for c in D.total.categoria.value_counts().index if c]

with st.form("lancamento", clear_on_submit=False):
    a, b, c = st.columns(3)
    data = a.date_input("Data", format="DD/MM/YYYY")
    tipo = b.segmented_control("Tipo", ["Saída", "Entrada"], default="Saída")
    valor = c.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
    d, e = st.columns(2)
    ev_sel = d.selectbox("Evento", eventos + ["+ Novo evento"])
    ev_novo = d.text_input("Nome do novo evento (se for novo)", placeholder="Ex.: Festa Junina 2027")
    cat = e.selectbox("Categoria", cats + ["Outra"])
    natureza = e.selectbox("Natureza", ["Despesa", "Receita", "Reembolso", "Adiantamento"], index=0)
    desc = st.text_input("Descrição", placeholder="Ex.: Assaí, 10 pacotes de pão de queijo")
    conf = st.checkbox("Marcar para validar depois (não tenho certeza)")
    enviado = st.form_submit_button("Adicionar", type="primary")

if enviado:
    evento = ev_novo.strip() if ev_sel == "+ Novo evento" else ev_sel
    erros = []
    if valor <= 0: erros.append("informe um valor maior que zero")
    if not evento: erros.append("informe o evento")
    if not desc.strip(): erros.append("descreva o lançamento")
    if tipo is None: erros.append("escolha entrada ou saída")
    if erros:
        st.error("Falta: " + "; ".join(erros) + ".")
    else:
        linha = {"data": data.strftime("%Y-%m-%d"), "tipo": tipo, "valor": float(valor), "evento": evento, "categoria": cat,
                 "descricao": desc.strip(), "confirmar": bool(conf), "natureza": natureza}
        if pode_escrever:
            try:
                import gspread
                gc = gspread.service_account_from_dict(dict(segredo("gcp_service_account")))
                ws = gc.open_by_key(segredo("sheet_id")).worksheet("movimentacoes")
                cab = ws.row_values(1)
                ws.append_row([linha.get(c, "") for c in cab], value_input_option="USER_ENTERED")
                st.cache_data.clear()
                st.toast("Lançamento adicionado.", icon=":material/check_circle:")
                st.success(f"Registrado: {tipo} de R$ {valor:,.2f} em {evento}.")
            except Exception as ex:
                st.error(f"Não consegui gravar na planilha ({type(ex).__name__}). Copie a linha abaixo e cole na aba movimentacoes.")
                st.code(",".join(str(linha[c]) for c in COLUNAS))
        else:
            st.info("Esta instalação está em modo somente leitura. Copie a linha abaixo e cole no fim da aba `movimentacoes` da planilha (ela aparece no painel em até 5 minutos).")
            st.code(",".join(str(linha[c]) for c in COLUNAS))

st.subheader("Últimos lançamentos")
st.dataframe(tabela(D.total.sort_values("data", ascending=False).head(10)[["data", "tipo", "valor", "evento", "descricao", "confirmar"]], moeda=["valor"], datas=["data"]),
             hide_index=True, width="stretch",
             column_config={"data": "Data", "tipo": "Tipo", "valor": "Valor", "evento": "Evento", "descricao": "Descrição", "confirmar": "A confirmar"})
if not pode_escrever:
    st.caption("Para gravar direto daqui, veja a seção 'Lançamento pelo app' do README.")

# -*- coding: utf-8 -*-
"""Liga DS | Controle Financeiro. Entrada do app: acesso, navegação e moldura comum."""
import streamlit as st
from core.data import segredo, get_dados

st.set_page_config(page_title="Liga DS | Caixa", page_icon=":material/account_balance_wallet:", layout="wide", initial_sidebar_state="expanded")


def gate():
    senha = segredo("app_password")
    if not senha or st.session_state.get("ok"):
        return
    _, c, _ = st.columns([1, 1.2, 1])
    with c:
        st.title("Liga DS | Caixa")
        st.caption("Acesso restrito à Diretoria.")
        tent = st.text_input("Senha", type="password")
        if tent:
            if tent == senha:
                st.session_state["ok"] = True
                st.rerun()
            st.error("Senha incorreta.")
    st.stop()


gate()

st.markdown("""
<style>
[data-testid="stMetricValue"] {font-size: 1.7rem;}
[data-testid="stMetricLabel"] p {font-size: .85rem; color:#5B6178;}
h1 {font-weight: 700; letter-spacing:-0.5px;}
.block-container {padding-top: 2.2rem; max-width: 1250px;}
</style>
""", unsafe_allow_html=True)

pg = st.navigation([
    st.Page("views/resumo.py", title="Resumo", icon=":material/dashboard:", default=True),
    st.Page("views/eventos.py", title="Eventos", icon=":material/celebration:"),
    st.Page("views/caixa.py", title="Caixa e planejamento", icon=":material/savings:"),
    st.Page("views/dados.py", title="Análises e dados", icon=":material/insights:"),
])

with st.sidebar:
    D = get_dados()
    st.caption(f"Fonte: {D.fonte}  \nÚltima movimentação: {D.total.data.max():%d/%m/%Y}")
    if st.button("Atualizar dados", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
        st.rerun()

pg.run()

# -*- coding: utf-8 -*-
"""Liga DS | Controle Financeiro (app Streamlit)

Os dados NÃO ficam no repositório. Ordem de leitura:
1) Google Sheets privado (st.secrets: gcp_service_account + sheet_id)  -> uso normal, publicado
2) arquivo data/fluxo_de_caixa.csv (local, ignorado pelo git)           -> desenvolvimento
3) upload do CSV na barra lateral                                       -> plano B
"""
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

st.set_page_config(page_title="Liga DS | Controle Financeiro", page_icon="💰", layout="wide")

E, S = "Entrada", "Saída"
EXCLUIR_ANOS = [2023]                      # 2023 sem custos registrados
NATUREZAS_FORA = ["Reembolso", "Adiantamento"]  # camisetas: não são receita/despesa de evento
COLS = ["data", "tipo", "valor", "evento", "categoria", "descricao", "confirmar", "natureza"]
brl = lambda v: "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- acesso
def segredo(chave, padrao=None):
    """Lê st.secrets sem quebrar quando não há secrets.toml (ex.: rodando local)."""
    try:
        return st.secrets[chave] if chave in st.secrets else padrao
    except Exception:
        return padrao


def gate():
    senha = segredo("app_password")
    if not senha:
        return
    if st.session_state.get("ok"):
        return
    st.title("💰 Liga DS | Controle Financeiro")
    tent = st.text_input("Senha de acesso", type="password")
    if tent:
        if tent == senha:
            st.session_state["ok"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()


# ---------------------------------------------------------------- dados
def _num(x):
    if isinstance(x, (int, float, np.number)):
        return float(x)
    x = str(x).strip().replace("R$", "").replace(" ", "")
    if "," in x:
        x = x.replace(".", "").replace(",", ".")
    return float(x)


def _prep(df):
    falt = [c for c in COLS if c not in df.columns]
    if falt:
        st.error(f"Colunas faltando na base: {falt}")
        st.stop()
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["valor"] = df["valor"].map(_num)
    df["confirmar"] = df["confirmar"].astype(str).str.lower().isin(["true", "1", "sim", "verdadeiro"])
    df["ano"] = df["data"].dt.year
    return df


@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def _ler_sheets():
    import gspread
    gc = gspread.service_account_from_dict(dict(segredo("gcp_service_account")))
    ws = gc.open_by_key(segredo("sheet_id")).worksheet(segredo("aba", "movimentacoes"))
    return pd.DataFrame(ws.get_all_records())


def carregar():
    if segredo("gcp_service_account") and segredo("sheet_id"):
        return _prep(_ler_sheets()), "Google Sheets (privado)"
    if os.path.exists("data/fluxo_de_caixa.csv"):
        return _prep(pd.read_csv("data/fluxo_de_caixa.csv")), "arquivo local"
    up = st.sidebar.file_uploader("Envie o fluxo_de_caixa.csv", type="csv")
    if up is not None:
        return _prep(pd.read_csv(up)), "upload"
    st.info("Nenhuma fonte de dados configurada. Envie o CSV na barra lateral ou configure o Google Sheets (veja o README).")
    st.stop()


@st.cache_data(ttl=300)
def carregar_saldo():
    """Saldo da caixinha informado (não é reconstruído dos lançamentos: depende de saldo inicial e rendimento).
    Aba 'saldo' do Sheets (colunas data, bruto, liquido; vale a última linha) ou data/saldo.csv."""
    try:
        if segredo("gcp_service_account") and segredo("sheet_id"):
            import gspread
            gc = gspread.service_account_from_dict(dict(segredo("gcp_service_account")))
            d = pd.DataFrame(gc.open_by_key(segredo("sheet_id")).worksheet("saldo").get_all_records())
        elif os.path.exists("data/saldo.csv"):
            d = pd.read_csv("data/saldo.csv")
        else:
            return None
        u = d.dropna().iloc[-1]
        return pd.to_datetime(u["data"]), _num(u["bruto"]), _num(u["liquido"])
    except Exception:
        return None


gate()
df_total, fonte = carregar()
saldo = carregar_saldo()
df = df_total[~df_total["ano"].isin(EXCLUIR_ANOS) & ~df_total["natureza"].isin(NATUREZAS_FORA)].copy()
ent, sai = df[df.tipo == E], df[df.tipo == S]

st.title("💰 Liga DS | Controle Financeiro")
st.caption(f"Fonte: {fonte} · {len(df)} movimentações nas análises ({len(df_total)} na base) · "
           f"2023 e camisetas ficam fora das análises por evento")

# tabela por evento
ev = pd.DataFrame({"Entradas": ent.groupby("evento")["valor"].sum(),
                   "Saídas": sai.groupby("evento")["valor"].sum()}).fillna(0)
ev["Resultado"] = ev["Entradas"] - ev["Saídas"]
ev["Custo por R$ 1 arrecadado"] = (ev["Saídas"] / ev["Entradas"].replace(0, np.nan)).round(3)
ev["Margem %"] = (ev["Resultado"] / ev["Entradas"].replace(0, np.nan) * 100).round(1)
ev = ev.sort_values("Resultado", ascending=False)

aba = st.tabs(["Visão geral", "Eventos", "Festa Junina", "Categorias",
               "Dispersão e regressão", "Reserva de emergência", "Camisetas", "Qualidade dos dados"])

# ---------------------------------------------------------------- 1 visão geral
with aba[0]:
    c = st.columns(5)
    if saldo:
        c[0].metric(f"Caixa (caixinha) em {saldo[0]:%d/%m/%Y}", brl(saldo[2]), f"bruto {brl(saldo[1])}", delta_color="off")
    else:
        c[0].metric("Caixa (caixinha)", "n/d", "informe na aba 'saldo'", delta_color="off")
    c[1].metric("Receita (eventos)", brl(ent.valor.sum()))
    c[2].metric("Despesa (eventos)", brl(sai.valor.sum()))
    c[3].metric("Resultado", brl(ent.valor.sum() - sai.valor.sum()))
    c[4].metric("Lançamentos a confirmar", int(df.confirmar.sum()))
    fig = px.bar(ev.reset_index(), x="Resultado", y="evento", orientation="h",
                 color=ev["Resultado"].reset_index(drop=True).ge(0).map({True: "Positivo", False: "Negativo"}),
                 color_discrete_map={"Positivo": "#2E7D5B", "Negativo": "#C0504D"},
                 title="Resultado por evento (R$)", labels={"evento": "", "color": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520)
    st.plotly_chart(fig, width="stretch")
    st.caption("O caixa é o saldo informado no app do banco (líquido de IR), não é somado dos lançamentos: a caixinha rende e o rendimento não entra na base. "
               "Receita, despesa e resultado referem-se só aos eventos analisados.")

# ---------------------------------------------------------------- 2 eventos
with aba[1]:
    st.subheader("Eficiência por evento")
    st.dataframe(ev.style.format({"Entradas": brl, "Saídas": brl, "Resultado": brl}), width="stretch")
    ger = ev[(ev["Entradas"] > 0)].sort_values("Custo por R$ 1 arrecadado")
    fig = px.bar(ger.reset_index(), x="Custo por R$ 1 arrecadado", y="evento", orientation="h",
                 title="Custo por R$ 1,00 arrecadado (menor é melhor)")
    fig.add_vline(x=1, line_dash="dash", line_color="red", annotation_text="equilíbrio")
    fig.update_layout(yaxis={"categoryorder": "total descending"}, height=480)
    st.plotly_chart(fig, width="stretch")
    st.caption("Data Journey e outros eventos de formação têm pouca receita por natureza: o custo por real só faz sentido nos eventos que arrecadam.")

# ---------------------------------------------------------------- 3 festa junina
with aba[2]:
    fj = df[df.evento.str.contains("Festa Junina", na=False)]
    t = fj.pivot_table(index="ano", columns="tipo", values="valor", aggfunc="sum", fill_value=0).reindex(columns=[E, S], fill_value=0)
    t["custo"] = (t[S] / t[E].replace(0, np.nan)).round(3)
    fig = go.Figure()
    fig.add_bar(x=t.index.astype(str), y=t[E], name="Receita", marker_color="#2E7D5B")
    fig.add_bar(x=t.index.astype(str), y=t[S], name="Despesa", marker_color="#C0504D")
    fig.add_scatter(x=t.index.astype(str), y=t["custo"], name="Custo por R$ 1", yaxis="y2", mode="lines+markers",
                    line=dict(dash="dash", color="#333"))
    fig.update_layout(barmode="group", title="Festa Junina: receita, despesa e custo por real arrecadado",
                      yaxis=dict(title="R$"), yaxis2=dict(title="Custo por R$ 1", overlaying="y", side="right", rangemode="tozero"),
                      height=480)
    st.plotly_chart(fig, width="stretch")
    st.caption("A Festa Junina é a principal receita da Liga. 2025 e 2026 têm despesa sem itemização; 2026 usa receita bruta reconstruída (lucro informado + despesas).")

# ---------------------------------------------------------------- 4 categorias
with aba[3]:
    cat = sai.pivot_table(index="categoria", columns="ano", values="valor", aggfunc="sum", fill_value=0)
    fig = px.bar(cat.reset_index().melt(id_vars="categoria", var_name="ano", value_name="valor"),
                 x="categoria", y="valor", color="ano", barmode="group", title="Despesa por categoria e ano (R$)")
    st.plotly_chart(fig, width="stretch")
    pend = sai[sai.categoria.isin(["A detalhar", "A confirmar"])].valor.sum()
    st.caption(f"{brl(pend)} das despesas ainda estão como 'A detalhar' / 'A confirmar' ({pend / max(sai.valor.sum(), 1) * 100:.0f}% do total).")
    st.dataframe(cat.style.format(brl), width="stretch")

# ---------------------------------------------------------------- 5 dispersão e regressão
with aba[4]:
    st.subheader("Dispersão: quanto cada evento gasta × quanto arrecada")
    pts = ev[(ev["Entradas"] > 0) & (ev["Saídas"] > 0)].reset_index()
    if len(pts) >= 3:
        r = stats.linregress(pts["Saídas"], pts["Entradas"])
        xs = np.linspace(pts["Saídas"].min(), pts["Saídas"].max(), 50)
        fig = px.scatter(pts, x="Saídas", y="Entradas", text="evento", title="Entradas × Saídas por evento (R$)")
        fig.update_traces(textposition="top center")
        fig.add_scatter(x=xs, y=r.intercept + r.slope * xs, mode="lines", name="Reta de regressão", line=dict(dash="dash"))
        st.plotly_chart(fig, width="stretch")
        c = st.columns(4)
        c[0].metric("n (eventos)", len(pts))
        c[1].metric("Inclinação", f"{r.slope:.2f}")
        c[2].metric("R²", f"{r.rvalue ** 2:.2f}")
        c[3].metric("p-valor", f"{r.pvalue:.3f}")
        st.warning(f"**Leitura honesta:** são só {len(pts)} eventos. O R² descreve esses pontos, mas não permite prever eventos futuros "
                   "com confiança. Use como indício exploratório, não como projeção. Pontos como a Festa Junina pesam muito na reta.")
    else:
        st.info("Poucos eventos com entrada e saída para ajustar a reta.")

    st.subheader("Gasto por participante (preencha para calcular)")
    st.caption("Inscritos/presentes (Data Journey, no Drive), estimativa por corn dog/waffle (Festa Junina). Os números ficam só nesta sessão.")
    base = pd.DataFrame({"evento": sai.groupby("evento")["valor"].sum().index,
                         "gasto": sai.groupby("evento")["valor"].sum().values, "participantes": np.nan})
    ed = st.data_editor(base, disabled=["evento", "gasto"], hide_index=True, width="stretch", key="part")
    ok = ed.dropna(subset=["participantes"])
    ok = ok[ok.participantes > 0]
    if len(ok):
        ok = ok.assign(gasto_por_participante=(ok.gasto / ok.participantes).round(2))
        st.dataframe(ok.style.format({"gasto": brl, "gasto_por_participante": brl}), width="stretch")

# ---------------------------------------------------------------- 6 reserva
with aba[5]:
    st.subheader("Base para a reserva de emergência")
    gasto_ev = sai.groupby("evento")["valor"].sum().sort_values(ascending=False)
    gasto_ano = sai.groupby("ano")["valor"].sum()
    maior = gasto_ev.iloc[0]
    c = st.columns(3)
    c[0].metric("Maior gasto em um evento", brl(maior), gasto_ev.index[0])
    c[1].metric("Média anual de gasto (anos registrados)", brl(gasto_ano.mean()))
    anos_cheios = gasto_ano[gasto_ano.index.isin([2024, 2025])]
    c[2].metric("Média 2024–2025", brl(anos_cheios.mean()) if len(anos_cheios) else "n/d")
    k = st.slider("Quantos eventos grandes a reserva deve cobrir?", 1, 3, 1)
    folga = st.slider("Margem de segurança (%)", 0, 50, 20)
    st.success(f"Reserva sugerida: **{brl(maior * k * (1 + folga / 100))}**  "
               f"(maior gasto em um evento × {k} × {1 + folga / 100:.2f})")
    st.caption("Heurística simples, para discussão com a Diretoria. 2023 ficou de fora, 2026 vai até ago/26 e há gastos sem itemização, "
               "então o valor tende a estar subestimado. Em eventos como a Data Journey, o gasto pode incluir lançamentos ainda a confirmar.")
    st.plotly_chart(px.bar(gasto_ev.reset_index(), x="valor", y="evento", orientation="h", title="Gasto por evento (R$)")
                    .update_layout(yaxis={"categoryorder": "total ascending"}, height=480), width="stretch")

# ---------------------------------------------------------------- 7 camisetas
with aba[6]:
    cam = df_total[df_total.evento.str.startswith("Camisetas 2026", na=False)]
    if len(cam):
        pago = cam[cam.natureza == "Adiantamento"].valor.sum()
        reemb = cam[cam.natureza == "Reembolso"].valor.sum()
        estrito = cam[cam.descricao.str.startswith("Reembolso", na=False)].valor.sum()
        c = st.columns(3)
        c[0].metric("Pago à fornecedora (parcelas)", brl(pago))
        c[1].metric("Reembolsado pelos membros", brl(reemb))
        c[2].metric("Falta receber", brl(pago - reemb), f"{reemb / pago * 100:.0f}% reembolsado")
        st.progress(min(reemb / pago, 1.0) if pago else 0)
        st.caption(f"Leitura estrita (só lançamentos 'Reembolso Camisetas'): {brl(estrito)}. "
                   "A ampla inclui os valores 'Camiseta da liga' de 22/05 e 16/06, marcados como Camisetas pelo Jomas.")
        st.dataframe(cam[["data", "tipo", "valor", "descricao", "natureza"]].sort_values("data"), hide_index=True, width="stretch")
    else:
        st.info("Sem lançamentos de Camisetas 2026 na base.")

# ---------------------------------------------------------------- 8 qualidade
with aba[7]:
    st.subheader("Lançamentos com interpretação a validar")
    pend = df_total[df_total.confirmar].sort_values("data")
    st.write(f"{len(pend)} de {len(df_total)} lançamentos. Quanto menor esse número, mais confiáveis os resultados.")
    st.dataframe(pend[["data", "tipo", "valor", "evento", "categoria", "descricao"]], hide_index=True, width="stretch")
    if segredo("app_password"):
        st.download_button("Baixar base completa (CSV)", df_total.to_csv(index=False).encode("utf-8"), "fluxo_de_caixa.csv", "text/csv")

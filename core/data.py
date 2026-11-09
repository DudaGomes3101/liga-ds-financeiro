"""Leitura dos dados (Sheets privado > arquivo local > upload) e tabelas derivadas."""
import os
from dataclasses import dataclass
import numpy as np
import pandas as pd
import streamlit as st
from core.config import (COLUNAS, EXCLUIR_ANOS, NATUREZAS_FORA, PERFIL_POR_FAMILIA, PERFIL_PADRAO,
                         CAT_PENDENTES, familia, ano_do_evento)

E, S = "Entrada", "Saída"


def segredo(chave, padrao=None):
    """Lê st.secrets sem quebrar quando não existe secrets.toml (ex.: rodando local)."""
    try:
        return st.secrets[chave] if chave in st.secrets else padrao
    except Exception:
        return padrao


def _num(x):
    if isinstance(x, (int, float, np.number)):
        return float(x)
    x = str(x).strip().replace("R$", "").replace(" ", "")
    if "," in x:
        x = x.replace(".", "").replace(",", ".")
    return float(x)


def _prep(df):
    falt = [c for c in COLUNAS if c not in df.columns]
    if falt:
        st.error(f"Colunas faltando na base: {falt}")
        st.stop()
    df = df.copy()
    d = df["data"].astype(str).str.strip().str[:10]   # aceita 2026-10-18 e 18/10/2026
    df["data"] = pd.to_datetime(d, format="%Y-%m-%d", errors="coerce").fillna(pd.to_datetime(d, format="%d/%m/%Y", errors="coerce"))
    df["valor"] = df["valor"].map(_num)
    df["confirmar"] = df["confirmar"].astype(str).str.lower().isin(["true", "1", "sim", "verdadeiro"])
    df["ano"] = df["data"].dt.year
    for c in ["evento", "categoria", "descricao", "natureza"]:
        df[c] = df[c].fillna("").astype(str)
    m = df["evento"] == "Operação da Liga"          # custo recorrente: separa por ano
    df.loc[m, "evento"] = "Operação da Liga " + df.loc[m, "ano"].astype(str)
    return df


@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def _ler_sheets(aba="movimentacoes"):
    import gspread
    gc = gspread.service_account_from_dict(dict(segredo("gcp_service_account")))
    return pd.DataFrame(gc.open_by_key(segredo("sheet_id")).worksheet(aba).get_all_records())


def _carregar_bruto():
    if segredo("gcp_service_account") and segredo("sheet_id"):
        return _ler_sheets(), "Google Sheets (privado)"
    if os.path.exists("data/fluxo_de_caixa.csv"):
        return pd.read_csv("data/fluxo_de_caixa.csv"), "arquivo local"
    up = st.sidebar.file_uploader("Envie o fluxo_de_caixa.csv", type="csv")
    if up is not None:
        return pd.read_csv(up), "upload"
    st.info("Nenhuma fonte de dados configurada. Envie o CSV na barra lateral ou configure o Google Sheets (veja o README).")
    st.stop()


@st.cache_data(ttl=300)
def carregar_saldo():
    """Saldo da caixinha informado (não é somado dos lançamentos: há rendimento). Aba 'saldo' ou data/saldo.csv."""
    try:
        if segredo("gcp_service_account") and segredo("sheet_id"):
            d = _ler_sheets("saldo")
        elif os.path.exists("data/saldo.csv"):
            d = pd.read_csv("data/saldo.csv")
        else:
            return None
        u = d.dropna().iloc[-1]
        return {"data": pd.to_datetime(str(u["data"])[:10], errors="coerce"), "bruto": _num(u["bruto"]), "liquido": _num(u["liquido"])}
    except Exception:
        return None


@dataclass
class Dados:
    total: pd.DataFrame      # base completa
    df: pd.DataFrame         # base das análises (sem 2023, sem reembolso/adiantamento)
    ev: pd.DataFrame         # 1 linha por evento
    saldo: dict | None
    fonte: str


def tabela_eventos(df):
    d = df.copy()
    d["familia"] = d["evento"].map(familia)
    d["ed"] = [ano_do_evento(e, a) for e, a in zip(d["evento"], d["ano"])]
    g = d.groupby("evento")
    ev = pd.DataFrame({
        "receita": d[d.tipo == E].groupby("evento")["valor"].sum(),
        "despesa": d[d.tipo == S].groupby("evento")["valor"].sum(),
    }).reindex(g.size().index).fillna(0.0)
    ev["familia"] = [familia(e) for e in ev.index]
    ev["ano"] = [ano_do_evento(e, g["ano"].max()[e]) for e in ev.index]
    ev["data"] = g["data"].min()
    ev["perfil"] = ev["familia"].map(PERFIL_POR_FAMILIA).fillna(PERFIL_PADRAO)
    ev["resultado"] = ev["receita"] - ev["despesa"]
    ev["custo_real"] = np.where(ev["receita"] > 0, ev["despesa"] / ev["receita"].replace(0, np.nan), np.nan)
    ev["margem"] = np.where(ev["receita"] > 0, ev["resultado"] / ev["receita"].replace(0, np.nan), np.nan)
    ev["pendente"] = g["confirmar"].sum()
    ev["lancamentos"] = g.size()
    return ev.reset_index().rename(columns={"index": "evento"}).sort_values("data").reset_index(drop=True)


def get_dados() -> Dados:
    bruto, fonte = _carregar_bruto()
    total = _prep(bruto)
    df = total[~total["ano"].isin(EXCLUIR_ANOS) & ~total["natureza"].isin(NATUREZAS_FORA)].copy()
    return Dados(total=total, df=df, ev=tabela_eventos(df), saldo=carregar_saldo(), fonte=fonte)


# ---------------------------------------------------------------- métricas de negócio
def camisetas(total):
    cam = total[total.evento.str.startswith("Camisetas", na=False) & (total.ano == 2026)]
    pago = cam[cam.natureza == "Adiantamento"].valor.sum()
    reemb = cam[cam.natureza == "Reembolso"].valor.sum()
    return {"pago": pago, "reembolsado": reemb, "falta": pago - reemb, "linhas": cam}


def gasto_por_ano(df):
    return df[df.tipo == S].groupby("ano")["valor"].sum()


def maior_gasto_evento(ev):
    return float(ev["despesa"].max()) if len(ev) else 0.0


def reserva_alvo(ev, df, metodo, k, folga):
    if metodo == "evento":
        return maior_gasto_evento(ev) * k * (1 + folga)
    ga = gasto_por_ano(df)
    return float(ga.mean()) * (k / 12) * (1 + folga) if len(ga) else 0.0


def alertas(D: Dados):
    """No máximo 3 pontos de atenção, do mais ao menos importante."""
    out = []
    desp = D.df[D.df.tipo == S]
    pend_val = desp[desp.categoria.isin(CAT_PENDENTES)].valor.sum()
    tot = desp.valor.sum()
    if tot and pend_val / tot > 0.15:
        out.append(("alta", f"{pend_val / tot * 100:.0f}% das despesas (R$ {pend_val:,.0f}) estão sem itemização".replace(",", "."),
                    "Levantar as notas da Festa Junina 2025 e 2026."))
    n = int(D.total.confirmar.sum())
    if n:
        out.append(("media", f"{n} lançamentos aguardam confirmação", "Validar com o Jomas (aba Qualidade dos dados)."))
    cam = camisetas(D.total)
    if cam["falta"] > 1:
        out.append(("media", f"Camisetas: faltam R$ {cam['falta']:,.2f} de reembolso".replace(",", "X").replace(".", ",").replace("X", "."),
                    "Cobrar os membros que ainda não devolveram."))
    return out[:3]

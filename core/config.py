"""Configurações e regras de negócio do app (edite aqui, não nas páginas)."""
import re

EXCLUIR_ANOS = [2023]                            # 2023: custos não registrados
NATUREZAS_FORA = ["Reembolso", "Adiantamento"]   # camisetas: não são receita/despesa de evento
COLUNAS = ["data", "tipo", "valor", "evento", "categoria", "descricao", "confirmar", "natureza"]

# Como cada "família" de evento é tratada. Classificação ADOTADA PELO TIME (validar com a Diretoria).
PERFIL_POR_FAMILIA = {
    "Festa Junina": "Arrecadação",
    "Calourada": "Arrecadação",
    "Data Journey": "Formação",
    "Data Class": "Formação",
    "Integração": "Membros",
    "Coffee RG": "Membros",
    "Operação da Liga": "Operação",
}
PERFIL_PADRAO = "A classificar"

ROXO = "#5A3FC0"
CINZA = "#9AA0B4"
CINZA_CLARO = "#D9DCE8"
VERDE = "#2E7D5B"
VERMELHO = "#C0504D"
PERFIL_COR = {"Arrecadação": ROXO, "Formação": CINZA, "Membros": "#B7A6E8", "Operação": "#6B7390", PERFIL_PADRAO: CINZA_CLARO}
CAT_PENDENTES = ["A detalhar", "A confirmar"]


def familia(evento: str) -> str:
    s = str(evento)
    for _ in range(3):
        s = re.sub(r"\s*(\([^)]*\)|20\d\d)\s*$", "", s)
    return s.strip()


def ano_do_evento(evento: str, ano_data: int) -> int:
    m = re.search(r"20(\d\d)", str(evento))
    if m:
        return 2000 + int(m.group(1))
    m = re.search(r"/(\d\d)\)", str(evento))
    return 2000 + int(m.group(1)) if m else int(ano_data)

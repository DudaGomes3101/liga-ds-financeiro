# Liga DS | Caixa (app Streamlit)

Painel financeiro da Liga: caixa, resultado por evento, para onde vai o dinheiro, reserva de emergência, planejamento de orçamento e qualidade dos dados.
**Os dados não ficam neste repositório** (ele é público): o app lê de um Google Sheets privado.

## Páginas (4, com abas)
| Página | Abas | Pergunta que responde |
|---|---|---|
| Resumo | | Estamos bem? Caixa, eventos cobertos, resultado do ano, alertas |
| Eventos | Por evento, Categorias | Cada evento deu retorno? Para onde vai o dinheiro? |
| Caixa e planejamento | Reserva, Planejar evento | O caixa aguenta um evento grande? Quanto reservar para o próximo? |
| Análises e dados | Regressão, Qualidade, Lançar | O que os dados dizem (com honestidade), o que falta validar, registrar movimentações |

## Identidade visual
Cores, fontes e logo seguem o Manual da Marca da Liga (azul #0C6980, amarelo #FED531, apoio #3891AC e #FFE684; títulos Poppins, subtítulos Inria Serif, texto Arial). O visual vem de `core/tema.py` e `assets/`, e **não depende** da pasta oculta `.streamlit`.
Para as cores de filtros e controles ficarem 100% na marca, crie também o arquivo `.streamlit/config.toml` (copie o conteúdo de `tema_config.toml`): no GitHub, **Add file > Create new file**, digite `.streamlit/config.toml` como nome e cole o conteúdo.

## Estrutura
```
app.py              entrada: senha, navegação, moldura
views/              as 4 páginas (finas, só montam as abas)
secoes/             o conteúdo de cada aba
core/config.py      regras de negócio (tipos de evento, anos excluídos, cores)
core/data.py        leitura dos dados e métricas
core/ui.py          formatação, estilo dos gráficos e helper de abas
core/tema.py        identidade visual (CSS, banner, logo)
assets/             logo e favicon da Liga
.streamlit/config.toml   tema
```

## Dados no Google Sheets (planilha privada)
Aba **`movimentacoes`** com as colunas `data, tipo, valor, evento, categoria, descricao, confirmar, natureza` (use o `fluxo_de_caixa.csv` gerado pelo notebook).
Aba **`saldo`** com `data, bruto, liquido` (ex.: `2026-10-18, 2307.47, 2269.65`). O app mostra a última linha.

## Secrets (Streamlit Cloud > Settings > Secrets)
```toml
sheet_id = "ID_DA_PLANILHA"
app_password = "UMA_SENHA_FORTE"
# permitir_escrita = true     # só se a conta de serviço for Editora da planilha (ver abaixo)

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

## Lançamento pelo app (opcional)
Por padrão o app só **lê**. Para a página *Lançar movimentação* gravar direto na planilha:
1. Compartilhe a planilha com o e-mail da conta de serviço como **Editor** (em vez de Leitor).
2. Adicione `permitir_escrita = true` nos Secrets.
Sem isso, a página gera a linha pronta para colar na aba `movimentacoes`.

## Rodar no computador
1. `pip install -r requirements.txt`
2. Crie a pasta `data/` com `fluxo_de_caixa.csv` e `saldo.csv` (colunas `data,bruto,liquido`). A pasta é ignorada pelo git.
3. `streamlit run app.py`

## Atualizar um app que já está publicado
No GitHub: **Add file > Upload files**, arraste `app.py`, `requirements.txt`, `README.md` e as pastas `core`, `views`, `secoes` e `.streamlit` (apague antes do repo os arquivos antigos de `views/`: categorias, planejar, analises, lancar, qualidade) e clique em **Commit changes**. O Streamlit Cloud reimplanta sozinho em 1 a 2 minutos. Não suba a pasta `data/`.

## Decisões de modelagem
- 2023 fica fora das análises (custos não registrados).
- Camisetas (adiantamento e reembolso) ficam fora das análises por evento e aparecem em *Caixa e reserva*.
- "Lucro" informado (Festa Junina 2026, Calourada 2026) é líquido: a receita bruta é reconstruída somando as despesas.
- O tipo de cada evento (arrecadação, formação, membros, operação) está em `core/config.py` e deve ser validado pela Diretoria.
- O caixa é o saldo informado no app do banco, não a soma dos lançamentos, porque a caixinha rende.
- A regressão é exploratória: poucos eventos não permitem previsão. A página mostra o intervalo de confiança e compara com o chute da média.

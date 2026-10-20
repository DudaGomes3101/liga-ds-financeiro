# Liga DS | Controle Financeiro

App Streamlit com a visão financeira dos eventos da Liga. **Os dados não ficam neste repositório** (ele é público): o app lê de um Google Sheets privado.

## 1. Rodar no seu computador (desenvolvimento)
1. `pip install -r requirements.txt`
2. Crie a pasta `data/` e coloque dentro o `fluxo_de_caixa.csv` gerado pelo notebook (a pasta é ignorada pelo git).
3. `streamlit run app.py`

## 2. Criar a base privada no Google Sheets (uma vez)
1. Crie uma planilha no Google Drive chamada `Liga DS Financeiro` e renomeie a primeira aba para **`movimentacoes`**.
2. Arquivo > Importar > Upload > `fluxo_de_caixa.csv` > "Substituir planilha atual". Colunas obrigatórias: `data, tipo, valor, evento, categoria, descricao, confirmar, natureza` (as demais são ignoradas).
3. No [Google Cloud Console](https://console.cloud.google.com): crie um projeto > ative **Google Sheets API** e **Google Drive API** > Credenciais > Criar **conta de serviço** > aba Chaves > Adicionar chave > JSON (baixa um arquivo).
4. Abra o JSON, copie o campo `client_email`, e **compartilhe a planilha** com esse e-mail (permissão de Leitor).
5. Copie o ID da planilha (trecho entre `/d/` e `/edit` na URL).

### Aba `saldo` (saldo da caixinha)
Crie uma segunda aba chamada **`saldo`** com as colunas `data, bruto, liquido` (ex.: `2026-10-18, 2307.47, 2269.65`). O app mostra a última linha. Atualize sempre que olhar o saldo no app do banco.

## 3. Publicar no Streamlit Community Cloud
1. Suba este repositório no GitHub (público, **sem** a pasta `data/`).
2. Em [share.streamlit.io](https://share.streamlit.io): New app > escolha o repositório, branch `main`, arquivo `app.py`.
3. Em Advanced settings > Secrets, cole (trocando pelos seus valores; o bloco `gcp_service_account` é o conteúdo do JSON em formato TOML):

```toml
sheet_id = "ID_DA_PLANILHA"
aba = "movimentacoes"
app_password = "escolha-uma-senha"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```
4. Deploy. O link só abre com a senha. Os dados são relidos da planilha a cada 5 minutos.

## 4. Como alimentar a base daqui pra frente
Quem cuida do caixa adiciona uma linha por movimentação na aba `movimentacoes` (data no formato AAAA-MM-DD; `tipo` = Entrada ou Saída; `natureza` = Receita, Despesa, Reembolso ou Adiantamento; `confirmar` = TRUE se ainda não foi validado). Não precisa mexer no código.

## Decisões de modelagem
- 2023 fica fora das análises (custos não registrados).
- Camisetas (Reembolso/Adiantamento) ficam fora das análises por evento e aparecem na aba própria.
- "Lucro" informado = valor líquido; a receita bruta é reconstruída somando as despesas do evento (feito no notebook).
- A regressão é exploratória: poucos eventos não permitem previsão.

# Argus — Copiloto de Auditoria Forense

> *Na mitologia grega, Argus Panoptes era o guardião de cem olhos que nunca dormia. Este projeto dá cem olhos ao auditor.*

**Argus** é um MVP que usa **análise de dados + IA generativa** para detectar e explicar fraudes
em transações financeiras, mesmo quando os dados são incompletos ou ruidosos.

Projeto desenvolvido para o **Hackathon da Ciência de Dados e GenAI** — desafio
*"The Ethical Supply Chain Guardian"* (Especialização em IA e Ciência de Dados).

Esta documentação segue o template **[arc42](https://arc42.org)**.

📄 Roteiro da apresentação (TEDx): [`docs/roteiro-apresentacao.md`](docs/roteiro-apresentacao.md)

---

## Como Executar

### Pré-requisitos

- **Python 3.11 ou superior** — [python.org/downloads](https://www.python.org/downloads/)
- Git (para clonar o repositório)

Verifique sua versão antes de começar:

```bash
python --version
```

---

### Passo 1 — Clone o repositório

```bash
git clone https://github.com/marise-san/argus.git
cd argus
```

---

### Passo 2 — Crie o ambiente virtual (`.venv`)

O ambiente virtual isola as dependências do projeto para não conflitar com outros projetos Python na sua máquina.

```bash
python -m venv .venv
```

---

### Passo 3 — Ative o ambiente virtual

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Prompt de Comando):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

> Quando ativo, o terminal mostrará `(.venv)` no início da linha.

Se o PowerShell bloquear por política de execução, rode antes:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

### Passo 4 — Instale as dependências

```bash
pip install -r requirements.txt
```

Isso instala: pandas, numpy, scipy, scikit-learn, streamlit, plotly, openai, pytest e demais libs.

---

### Passo 5 — Configure o `.env`

O Argus usa um arquivo `.env` para gerenciar chaves. Copie o template:

```bash
cp .env.example .env
```

Abra o `.env` gerado e configure:

1. **Inteligência Artificial (opcional)**: 
   - Deixe `ARGUS_LLM_PROVIDER=template` para rodar 100% offline (textos fixos).
   - Para usar IA real, mude para `openai` e coloque sua `OPENAI_API_KEY`.

2. **Dataset BankSim Real (opcional)**:
   - Se quiser que o Argus baixe os **dados reais do Kaggle** automaticamente, preencha as variáveis `KAGGLE_USERNAME` e `KAGGLE_KEY` com suas credenciais. 
   - Se não preencher, não tem problema! O Argus vai **gerar um dataset sintético** idêntico na hora, para que você não precise configurar chaves nem baixar nada manualmente.

```dotenv
# Para rodar com IA real (OpenAI):
ARGUS_LLM_PROVIDER=openai
ARGUS_LLM_MODELO=gpt-4o-mini
OPENAI_API_KEY=sk-...sua-chave-aqui...

# Para rodar offline sem gastar créditos (modo template):
# ARGUS_LLM_PROVIDER=template
```

> O app funciona completamente sem a chave OpenAI — nesse caso usa respostas pré-definidas baseadas nos dados calculados.

---

### Passo 6 — (Opcional) Dataset real BankSim

Por padrão o app usa **dados sintéticos** gerados automaticamente. Para usar o dataset real (~594 mil transações):

1. Acesse [kaggle.com/datasets/ntnu-testimon/banksim1](https://www.kaggle.com/datasets/ntnu-testimon/banksim1)
2. Baixe `bs140513_032310.csv`
3. Renomeie para `banksim.csv` e coloque em `data/raw/banksim.csv`

O app detecta o arquivo automaticamente e usa o dataset real.

---

### Passo 7 — Execute os testes

```bash
pytest tests/ -v
```

Todos os 20 testes devem passar em verde. Se algo falhar, verifique se o ambiente virtual está ativo e as dependências instaladas.

---

### Passo 8 — Inicie a aplicação

```bash
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`. Se não abrir, acesse o endereço manualmente.

Para encerrar: `Ctrl + C` no terminal.

---

### Resumo rápido (copie e cole)

```bash
# Uma vez, na primeira vez:
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
Copy-Item .env.example .env  # depois edite o .env

# Toda vez que for usar:
.venv\Scripts\Activate.ps1
streamlit run app.py
```

---

## Índice

1. [Introdução e Metas](#1-introdução-e-metas)
2. [Restrições da Arquitetura](#2-restrições-da-arquitetura)
3. [Escopo e Contexto do Sistema](#3-escopo-e-contexto-do-sistema)
4. [Estratégia de Solução](#4-estratégia-de-solução)
5. [Visão de Blocos de Construção](#5-visão-de-blocos-de-construção)
6. [Visão de Runtime](#6-visão-de-runtime)
7. [Visão de Implantação](#7-visão-de-implantação)
8. [Conceitos Transversais](#8-conceitos-transversais)
9. [Decisões de Arquitetura](#9-decisões-de-arquitetura)
10. [Requisitos de Qualidade](#10-requisitos-de-qualidade)
11. [Riscos e Dívida Técnica](#11-riscos-e-dívida-técnica)
12. [Glossário](#12-glossário)

---

## 1. Introdução e Metas

### 1.1 Visão geral do problema

Uma multinacional de planos de saúde não consegue monitorar a conformidade ética nem a
eficiência de sua cadeia de suprimentos global. Ela possui terabytes de dados estruturados
(transações, logs de transporte) e não estruturados (contratos, e-mails, relatórios de
auditoria). O desafio pede um produto mínimo, aplicável ao mundo real, para **detecção de
fraude e auditoria**, que use **IA generativa + análise de dados** para apoiar decisões em
**cenários com dados incompletos ou ruidosos**.

O auditor humano hoje consegue inspecionar apenas uma pequena amostra das transações. O
resto passa sem revisão. O Argus existe para varrer **100% das transações** e devolver ao
auditor um conjunto pequeno, priorizado e **explicado** de suspeitas.

### 1.2 Metas de qualidade

| Prioridade | Meta | Na prática |
|---|---|---|
| 1 | **Explicabilidade** | Cada alerta vem com a evidência estatística e uma explicação em texto. O auditor precisa rastrear de onde veio cada sinal. |
| 2 | **Transparência sobre incerteza** | O sistema mostra um score de confiança dos dados e avisa quando a amostra é pequena demais pra concluir qualquer coisa. |
| 3 | **Custo sob controle** | A estatística varre tudo; a GenAI só roda nos alertas que o auditor abre — não em cada linha do CSV. |

### 1.3 Stakeholders

| Stakeholder | Interesse |
|---|---|
| Equipe de desenvolvimento (hackathon) | Entregar um MVP defensável técnica e narrativamente |
| Orientador (MSc. Charles Marques) | Avaliar uso real de GenAI + análise de dados |
| Persona: **Auditor interno / analista de compliance** | Encontrar fraude sem se afogar em dados |
| Banca avaliadora | Verificar substância analítica, ética e aplicabilidade real |

---

## 2. Restrições da Arquitetura

| Tipo | Restrição |
|---|---|
| **Técnica** | Linguagem Python; interface em Streamlit; análise sobre dataset em CSV; IA generativa via API de LLM (chave paga já disponível). |
| **Dados** | Dataset principal: **BankSim** (`banksim1`, Kaggle) — ~594 mil transações sintéticas com colunas de fornecedor (`merchant`) e categoria (`category`). |
| **Organizacional** | Hackathon *concept-first*: a prioridade é o conceito de produto e a apresentação; a demo é enxuta, mas funcional ponta a ponta. Equipe pequena. |
| **Processo** | Construção segue os 5 módulos do cronograma do hackathon (ETL → GenAI & ML → Frontend → Pitch). |
| **Documentação** | Arquitetura documentada no padrão **arc42**, neste `README.md`. |
| **Ética** | A IA generativa **explica**, não decide. A decisão final é sempre humana. |

---

## 3. Escopo e Contexto do Sistema

### 3.1 Contexto de negócio

```
                  ┌──────────────────────────┐
   CSV de         │                          │   Alertas priorizados,
   transações ───►│          ARGUS           │──► explicações e rascunho
                  │                          │    de nota de auditoria
   Perguntas  ───►│  (copiloto de auditoria) │──► Respostas ancoradas
   do auditor     │                          │
                  └────────────┬─────────────┘
                               │ prompts ancorados nos resultados
                               ▼
                       ┌───────────────┐
                       │  API de LLM   │
                       └───────────────┘
```

| Parceiro | Entrada para o Argus | Saída do Argus |
|---|---|---|
| **Auditor** | Arquivo CSV de transações; perguntas em linguagem natural | Ranking de risco, explicações, rascunhos de nota, respostas |
| **API de LLM** | Resultados estruturados da análise (estatísticas, tabela de risco) | Texto explicativo gerado |

### 3.2 Contexto técnico

| Interface | Canal | Formato |
|---|---|---|
| Entrada de dados | Upload no Streamlit ou arquivo local | CSV |
| Interface do usuário | Navegador (localhost) | Aplicação Streamlit |
| Integração GenAI | HTTPS / SDK do provedor | JSON (prompt + contexto estruturado) |
| Configuração | Arquivo `.env` | Chave de API |

**O sistema não envia transações cruas para a API.** Apenas resultados agregados e
estatísticas calculadas — ver [§8](#8-conceitos-transversais).

---

## 4. Estratégia de Solução

| Meta de qualidade | Abordagem na arquitetura |
|---|---|
| Explicabilidade | A análise de dados produz evidência numérica; a GenAI traduz cada alerta em texto, sempre **ancorada** nessa evidência. |
| Honestidade sobre incerteza | Um componente dedicado (Raio-X de Qualidade) mede completude/ruído; fatias com amostra insuficiente são puladas, não estimadas. |
| Eficiência de custo | A Lei de Benford e o Isolation Forest são estatística pura (baratos). A GenAI roda só sob demanda, nos alertas. |
| Detecção robusta a ruído | A Lei de Benford analisa a **distribuição agregada** dos dígitos — funciona mesmo com registros faltantes. |

Na prática: a estatística faz o trabalho pesado e gera a evidência; a GenAI
entra onde o auditor precisa de texto — explicar o padrão, redigir nota,
responder perguntas. Ela não classifica nada como fraude.

---

## 5. Visão de Blocos de Construção

### 5.1 Nível 1 — Caixa branca do Argus

```
CSV de transações
      │
      ▼
[1] Ingestão & Limpeza ──► [2] Raio-X de Qualidade ──► score de confiança
      │
      ▼
┌──────────────────────────────────────────┐
│  [3] MOTOR DE DETECÇÃO                    │
│   ├─ 3a. Lei de Benford (multidimensional)│
│   └─ 3b. Anomalia ML (Isolation Forest)   │
│            │                              │
│            ▼                              │
│   3c. Agregador de Risco ──► ranking      │
└──────────────────────────────────────────┘
      │
      ▼
[4] Camada GenAI (acionada só nos alertas)
      │
      ▼
[5] Interface Streamlit
```

### 5.2 Estrutura de pastas planejada

```
hackaton/
├── README.md                 # esta documentação (arc42)
├── requirements.txt          # dependências Python
├── .env.example              # modelo de configuração (chave de API)
├── app.py                    # [5] interface Streamlit
├── data/
│   └── banksim.csv           # dataset BankSim
├── docs/
│   └── roteiro-apresentacao.md
└── src/
    ├── ingestao.py           # [1] carrega e valida o CSV
    ├── qualidade.py          # [2] raio-x de qualidade dos dados
    ├── benford.py            # [3a] motor da Lei de Benford
    ├── anomalia.py           # [3b] detecção de anomalia (Isolation Forest)
    ├── risco.py              # [3c] agregador de risco
    ├── genai.py              # [4] camada de IA generativa ancorada
    └── cenario.py            # injeta o cenário de demonstração plantado
```

### 5.3 Componentes (responsabilidade · interface · dependências)

| # | Componente | Responsabilidade | Interface (entrada → saída) | Depende de |
|---|---|---|---|---|
| 1 | **Ingestão** | Carrega o CSV, valida colunas obrigatórias, normaliza tipos | `caminho/arquivo → DataFrame` | Pandas |
| 2 | **Raio-X de Qualidade** | Mede completude e ruído; calcula um score de confiança 0–100% | `DataFrame → relatório de qualidade` | Pandas |
| 3a | **Benford** | Teste do 1º dígito por fornecedor e por categoria; estatística MAD | `DataFrame → desvios por entidade` | SciPy, NumPy |
| 3b | **Anomalia** | Isolation Forest sobre as features de transação | `DataFrame → score de anomalia por linha` | scikit-learn |
| 3c | **Agregador de Risco** | Funde desvio de Benford + anomalia num score de risco por fornecedor | `desvios + anomalias → ranking` | Pandas |
| 4 | **GenAI** | Gera explicação, rascunho de nota e respostas do chat, ancoradas nos resultados | `resultado estruturado → texto` | SDK do LLM |
| 5 | **Interface** | As 3 telas: Painel de Risco, Dossiê do Alerta, Pergunte ao Argus | — | Streamlit, Plotly |
| — | **Cenário** | Injeta o caso de fraude controlado (fragmentação de notas) para a demo | `DataFrame → DataFrame + linhas plantadas` | Pandas |

---

## 6. Visão de Runtime

### 6.1 Cenário: análise de um lote de transações

1. O auditor abre o Argus e carrega (ou usa o pré-carregado) o CSV de transações.
2. **Ingestão** valida e normaliza os dados.
3. **Raio-X de Qualidade** calcula o score de confiança e o exibe na tela.
4. **Benford** roda o teste do 1º dígito para cada fornecedor e categoria.
5. **Anomalia** treina o Isolation Forest e pontua cada transação.
6. **Agregador de Risco** combina os sinais e ordena os fornecedores por risco.
7. A **Tela 1 (Painel de Risco)** exibe o ranking. *Nenhuma chamada à GenAI até aqui.*

### 6.2 Cenário: drill-down em um alerta

1. O auditor clica num fornecedor do ranking.
2. A **Tela 2 (Dossiê do Alerta)** mostra o gráfico de Benford (curva esperada vs. real).
3. A **camada GenAI** recebe as estatísticas daquele fornecedor e gera a explicação em
   linguagem natural + o rascunho da nota de auditoria.
4. Se a API falhar, é exibida uma explicação por template (ver [§8](#8-conceitos-transversais)).

### 6.3 Cenário: pergunta ao Argus

1. O auditor digita uma pergunta na **Tela 3 (Pergunte ao Argus)**.
2. A **camada GenAI** responde usando como contexto **apenas** os resultados já calculados
   (tabela de risco, estatísticas de Benford) — nunca as transações cruas.

---

## 7. Visão de Implantação

| Item | Detalhe |
|---|---|
| Ambiente | Execução local, na máquina do apresentador |
| Pré-requisitos | Python 3.11+, dependências de `requirements.txt`, chave de API em `.env` |
| Comando de execução | `streamlit run app.py` |
| Acesso | Navegador em `http://localhost:8501` |
| Dados | `data/banksim.csv` carregado do disco |

Não há servidor, banco de dados ou autenticação no MVP — é uma aplicação de mesa única,
adequada a uma demonstração concept-first.

---

## 8. Conceitos Transversais

### 8.1 Ancoragem da GenAI

A GenAI recebe apenas os resultados agregados do motor de detecção
(estatísticas, ranking, scores) — nunca as transações cruas. Os prompts
instruem o modelo a se ater a esse contexto, sem inventar dados.

### 8.2 Tratamento de dados incompletos e ruidosos

O Raio-X de Qualidade calcula um score de confiança a partir de completude (campos vazios),
consistência (valores inválidos) e volume. A Lei de Benford é, por natureza, robusta a
ruído, pois analisa a distribuição agregada dos dígitos. Fatias com amostra abaixo do mínimo
estatístico (~300 registros) são **puladas com aviso** — o sistema declara que não sabe.

### 8.3 Tratamento de erros

| Situação | Comportamento |
|---|---|
| CSV inválido ou coluna faltando | Mensagem clara; oferece mapeamento manual de colunas |
| Fatia com poucos registros | Pula o teste de Benford e avisa o usuário |
| Falha na API de LLM | Cai para uma explicação por template — a demo não interrompe |

### 8.4 Ética

A IA sugere e explica; quem decide é o auditor. O Argus apresenta evidência e
padrões, mas a classificação final de fraude é sempre humana. O cenário
plantado na demo é declarado abertamente durante a apresentação.

### 8.5 Custo

A análise estatística (Benford, Isolation Forest) é computacionalmente barata e roda sobre
todo o dataset. A GenAI — o componente caro — é acionada apenas sob demanda, nos alertas que
o auditor abre. O custo cresce com o número de alertas inspecionados, não com o volume de
dados.

---

## 9. Decisões de Arquitetura

| ID | Decisão | Justificativa |
|---|---|---|
| **ADR-01** | Usar o dataset **BankSim** como base principal | É o único dos três datasets do briefing com colunas de fornecedor e categoria, essenciais para o Benford multidimensional. Tamanho moderado (~594k linhas) roda bem ao vivo. |
| **ADR-02** | **Lei de Benford** como motor primário de detecção | Sinalizada explicitamente no material do desafio; é técnica clássica de auditoria forense; robusta a dados ruidosos. |
| **ADR-03** | **Isolation Forest** não-supervisionado; o rótulo `fraud` **não** é usado no treino | Reflete o mundo real, onde rótulos de fraude são raros. O rótulo é reservado para **validação** (precisão@K). |
| **ADR-04** | GenAI **ancorada em prompts**, não *fine-tuning* | Mais barato, mais rápido de construir e mais explicável. O *fine-tuning* não traria ganho num MVP. |
| **ADR-05** | Injetar um **cenário de fraude plantado** (fragmentação de notas) | Garante um "momento herói" nítido e didático na demo. Declarado abertamente — reforça, não compromete, a credibilidade. |
| **ADR-06** | Interface em **Streamlit** | Permite uma aplicação web interativa com pouco código; adequada a uma demo ao vivo. |

---

## 10. Requisitos de Qualidade

### 10.1 Árvore de qualidade

- **Explicabilidade** (prioridade máxima)
- **Honestidade sobre incerteza**
- **Desempenho** na demo
- **Eficiência de custo**

### 10.2 Cenários de qualidade

| Atributo | Cenário | Resposta esperada |
|---|---|---|
| Explicabilidade | O auditor abre um alerta | Em ≤ 1 tela ele vê o gráfico de Benford, a explicação textual e o rascunho da nota |
| Honestidade | Um fornecedor tem só 50 transações | O Argus informa que a amostra é insuficiente e não emite veredito |
| Desempenho | Carga de ~594k transações | Análise estatística completa em poucos segundos |
| Validação | Ranking comparado ao rótulo `fraud` | Precisão@K reportada como métrica objetiva no pitch |
| Robustez | API de LLM indisponível | A demo continua com explicação por template |

---

## 11. Riscos e Dívida Técnica

### 11.1 Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Benford não acende em dados sintéticos "limpos" | Demo sem clímax | Cenário plantado de fragmentação de notas garante o pico |
| Falha de rede/API durante a apresentação | Demo trava | Fallback por template + capturas de tela de reserva |
| Amostra pequena gera Benford não confiável | Falso achado | Mínimo estatístico (~300 registros) por fatia |
| Custo de API acima do previsto | Estouro de orçamento | GenAI só nos alertas; resultados podem ser cacheados |

### 11.2 Dívida técnica assumida (consciente, fora do escopo do MVP)

- Sem persistência: cada sessão recomeça do zero.
- Sem RAG sobre documentos não estruturados (contratos, PDFs, e-mails) — **roadmap**.
- Sem conexão com banco SQL ou logs de transporte ao vivo — entrada apenas por CSV.
- Sem autenticação, multiusuário ou *deploy* em produção.
- Teste do 2º dígito e teste de somatório de Benford não implementados — **roadmap**.

---

## 12. Glossário

| Termo | Definição |
|---|---|
| **Lei de Benford** | Padrão estatístico segundo o qual, em conjuntos de números naturais, o 1º dígito é "1" em ~30% dos casos e "9" em ~5%. Desvios podem indicar números fabricados. |
| **Fragmentação de notas** | Fraude em que uma despesa grande é quebrada em várias notas menores para ficar abaixo de um teto de aprovação, evitando controles. |
| **MAD (Mean Absolute Deviation)** | Desvio absoluto médio entre a distribuição de dígitos observada e a esperada por Benford; quanto maior, maior a suspeita de manipulação. |
| **Isolation Forest** | Algoritmo não-supervisionado de detecção de anomalias que isola pontos atípicos com poucas divisões aleatórias. |
| **GenAI ancorada** | Uso de IA generativa restrito a um contexto de dados fornecido, para impedir alucinação. |
| **Precisão@K** | Proporção de alertas verdadeiramente fraudulentos entre os K primeiros do ranking de risco. |
| **Score de confiança** | Indicador 0–100% da qualidade dos dados de entrada, calculado pelo Raio-X de Qualidade. |
| **Momento herói** | O instante da apresentação em que a fraude se torna visível e inegável (o pico vermelho no gráfico de Benford). |
| **MVP** | Produto Mínimo Viável — a menor versão funcional que prova o conceito. |
| **BankSim** | Dataset sintético de pagamentos financeiros (Kaggle), base de dados deste projeto. |

---

*Documento de arquitetura — Hackathon da Ciência de Dados e GenAI · 2026.*

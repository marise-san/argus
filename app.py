"""Argus — interface Streamlit (ponto de entrada da aplicação).

Execute com:  streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Garante que o pacote `argus` seja encontrado sem precisar de `pip install`.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from argus.application.pipeline import PipelineAnaliseFraude
from argus.config import config
from argus.data.preparacao import preparar_dataset
from argus.domain.models import AlertaRisco, ResultadoAnalise
from argus.genai.client import criar_cliente_llm
from argus.genai.servico import ServicoGenAI

# ── Configuração da página ─────────────────────────────────────────────────────

st.set_page_config(
    page_title="Argus — Auditoria Forense",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeção de CSS customizado para acabamento premium
st.markdown("""
<style>
    # /* Reduz o padding gigante padrão do Streamlit no topo e na base */
    # .block-container {
    #     padding-top: 2rem !important;
    #     padding-bottom: 2rem !important;
    #     max-width: 95% !important;
    # }

    /* Ajuste de tipografia e espaçamento dos cards de métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
        color: #E8E6E1;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        font-weight: 500;
        color: #A0AABF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
    }
    
    /* Suaviza as divisórias */
    hr {
        border-color: #2e3b4e !important;
    }
    
    /* Melhoria no visual dos Containers com borda (Cards) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 0.5rem;
        border-color: #2e3b4e !important;
        background-color: rgba(15, 23, 42, 0.4);
    }

    /* Sidebar mais limpa */
    [data-testid="stSidebar"] {
        border-right: 1px solid #2e3b4e;
    }
</style>
""", unsafe_allow_html=True)

# ── Recursos em cache (instanciados uma vez por sessão) ───────────────────────


@st.cache_resource
def _pipeline() -> PipelineAnaliseFraude:
    return PipelineAnaliseFraude(config)


@st.cache_resource
def _servico() -> ServicoGenAI:
    return ServicoGenAI(criar_cliente_llm(config))


# ── Análise inicial (roda uma vez; resultado fica no session_state) ───────────


def _executar_analise() -> ResultadoAnalise:
    df, fonte = preparar_dataset(config)
    return _pipeline().executar(df, fonte=fonte)


if "resultado" not in st.session_state:
    with st.spinner("Carregando transações e executando análise..."):
        st.session_state["resultado"] = _executar_analise()

resultado: ResultadoAnalise = st.session_state["resultado"]
servico = _servico()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔍 Argus")
    st.caption("Copiloto de Auditoria Forense")
    st.divider()

    tela = st.radio(
        "Navegação",
        options=["Painel de Risco", "Dossiê do Alerta", "Pergunte ao Argus"],
        label_visibility="collapsed",
    )
    st.divider()

    rq = resultado.relatorio_qualidade
    with st.container(border=True):
        st.metric("Confiança dos dados", f"{rq.score_confianca:.0f} / 100")
        st.metric("Transações varridas", f"{resultado.total_transacoes:,}")
        st.metric("Tempo de análise", f"{resultado.tempo_processamento_s} s")

    if rq.problemas:
        with st.expander("⚠️ Avisos de qualidade"):
            for prob in rq.problemas:
                st.warning(prob, icon="⚠️")

    st.divider()
    st.caption(f"📂 {resultado.fonte_dados}")
    provedor = config.provedor_llm
    st.caption(
        "🟢 IA: OpenAI ativa" if provedor == "openai" else "⚪ IA: Template (offline)"
    )

    if st.button("🔄 Recarregar análise"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TELA 1 — PAINEL DE RISCO
# ══════════════════════════════════════════════════════════════════════════════

if tela == "Painel de Risco":
    st.header("Painel de Risco")
    st.caption(
        f"{resultado.total_transacoes:,} transações · "
        f"{resultado.fonte_dados} · "
        f"análise em {resultado.tempo_processamento_s} s"
    )

    alertas = resultado.alertas
    if not alertas:
        st.info("Nenhum alerta gerado. Verifique o dataset.")
        st.stop()

    # ── Cards dos 3 maiores riscos ─────────────────────────────────────────
    top3 = alertas[:3]
    icones = {"Alto": "🔴", "Médio": "🟡", "Baixo": "🟢"}
    cols = st.columns(len(top3))
    for col, alerta in zip(cols, top3):
        with col:
            with st.container(border=True):
                st.metric(
                    label=f"{icones[alerta.nivel]} {alerta.entidade}",
                    value=f"{alerta.score_risco:.2f}",
                    delta=f"{alerta.nivel} risco · {alerta.n_transacoes:,} transações",
                    delta_color="inverse" if alerta.nivel == "Alto" else "normal",
                )

    st.divider()

    # ── Tabela completa ────────────────────────────────────────────────────
    st.subheader("Ranking completo")

    linhas = []
    for a in alertas:
        rb = a.resultado_benford
        linhas.append({
            "Fornecedor": a.entidade,
            "Score Risco": a.score_risco,
            "Nível": a.nivel,
            "Benford": rb.conformidade.value,
            "Dígito ⚠": str(rb.digito_suspeito) if rb.digito_suspeito else "—",
            "MAD": rb.mad,
            "Anomalia": a.score_anomalia,
            "Transações": a.n_transacoes,
            "Valor Total (R$)": a.valor_total,
        })

    df_tabela = pd.DataFrame(linhas)

    def _cor_nivel(val: str) -> str:
        return {
            "Alto": "background-color: rgba(231, 76, 60, 0.15); color: #ff6b6b; font-weight: 600;",
            "Médio": "background-color: rgba(243, 156, 18, 0.15); color: #f39c12; font-weight: 600;",
        }.get(val, "")

    st.dataframe(
        df_tabela.style
        .map(_cor_nivel, subset=["Nível"])
        .format({
            "Score Risco": "{:.3f}",
            "MAD": "{:.4f}",
            "Anomalia": "{:.3f}",
            "Valor Total (R$)": "R$ {:,.2f}",
        }),
        width="stretch",
        hide_index=True,
    )
    st.caption("👆 Vá em **Dossiê do Alerta** para detalhar qualquer fornecedor.")

# ══════════════════════════════════════════════════════════════════════════════
# TELA 2 — DOSSIÊ DO ALERTA
# ══════════════════════════════════════════════════════════════════════════════

elif tela == "Dossiê do Alerta":
    st.header("Dossiê do Alerta")

    nomes = [a.entidade for a in resultado.alertas]
    nome_sel: str = st.selectbox("Selecione o fornecedor:", options=nomes)
    alerta: AlertaRisco = next(a for a in resultado.alertas if a.entidade == nome_sel)
    rb = alerta.resultado_benford

    # ── Métricas de cabeçalho ──────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.metric("Score de Risco", f"{alerta.score_risco:.3f}", alerta.nivel)
    with c2:
        with st.container(border=True):
            st.metric("Benford", rb.conformidade.value)
    with c3:
        with st.container(border=True):
            st.metric("Transações", f"{alerta.n_transacoes:,}")
    with c4:
        with st.container(border=True):
            st.metric("Valor Total", f"R$ {alerta.valor_total:,.0f}")

    st.divider()

    col_benford, col_genai = st.columns(2, gap="large")

    # ── Gráfico de Benford ─────────────────────────────────────────────────
    with col_benford:
        st.subheader("Lei de Benford")

        if rb.confiavel:
            digitos = list(range(1, 10))
            obs = [rb.distribuicao_observada[d] * 100 for d in digitos]
            esp = [rb.distribuicao_esperada[d] * 100 for d in digitos]

            cores = [
                "#E74C3C" if d == rb.digito_suspeito else "#3B82A0"
                for d in digitos
            ]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=digitos, y=obs,
                marker_color=cores,
                name="Observado",
                hovertemplate="Dígito %{x}<br>Observado: %{y:.1f}%<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=digitos, y=esp,
                mode="lines+markers",
                line=dict(color="#F39C12", width=2.5, dash="dash"),
                marker=dict(size=7),
                name="Esperado (Benford)",
                hovertemplate="Dígito %{x}<br>Esperado: %{y:.1f}%<extra></extra>",
            ))
            fig.update_layout(
                xaxis=dict(title="1º Dígito", tickvals=digitos, showgrid=False),
                yaxis=dict(title="Frequência (%)", showgrid=True, gridcolor="#2e3b4e"),
                legend=dict(orientation="h", y=-0.25),
                margin=dict(t=10, b=10, l=0, r=0),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A0AABF")
            )
            
            with st.container(border=True):
                st.plotly_chart(fig, width="stretch")

            if rb.digito_suspeito:
                pct_obs = rb.distribuicao_observada[rb.digito_suspeito] * 100
                pct_esp = rb.distribuicao_esperada[rb.digito_suspeito] * 100
                st.caption(
                    f"MAD: **{rb.mad:.4f}** · "
                    f"Dígito suspeito: **{rb.digito_suspeito}** · "
                    f"Observado {pct_obs:.1f}% vs {pct_esp:.1f}% esperado"
                )
        else:
            st.warning(
                f"Amostra insuficiente para o teste de Benford "
                f"({rb.n_amostras} transações — mínimo: {config.min_amostra_benford}). "
                "O Argus não emite veredito de Benford para este fornecedor.",
                icon="ℹ️",
            )

    # ── Painel da GenAI ────────────────────────────────────────────────────
    with col_genai:
        st.subheader("Análise da IA")

        chave_exp = f"explicacao__{nome_sel}"
        if chave_exp not in st.session_state:
            with st.spinner("Gerando análise..."):
                st.session_state[chave_exp] = servico.explicar(alerta)

        with st.container(border=True):
            st.markdown(st.session_state[chave_exp])

    st.divider()

    # ── Nota de auditoria ─────────────────────────────────────────────────
    st.subheader("Rascunho da Nota de Auditoria")

    chave_nota = f"nota__{nome_sel}"
    if chave_nota not in st.session_state:
        with st.spinner("Redigindo nota..."):
            st.session_state[chave_nota] = servico.redigir_nota(alerta)

    with st.container(border=True):
        st.markdown(st.session_state[chave_nota])
    st.download_button(
        label="⬇️ Baixar nota (.md)",
        data=st.session_state[chave_nota],
        file_name=f"nota_{nome_sel.replace(' ', '_')}.md",
        mime="text/markdown",
    )

# ══════════════════════════════════════════════════════════════════════════════
# TELA 3 — PERGUNTE AO ARGUS
# ══════════════════════════════════════════════════════════════════════════════

elif tela == "Pergunte ao Argus":
    st.header("Pergunte ao Argus")
    st.caption(
        "As respostas são ancoradas nos resultados calculados pelo motor de "
        "detecção — o Argus não inventa dados."
    )

    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    # Exibe o histórico.
    for msg in st.session_state["chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pergunta = st.chat_input("Ex.: Liste os 5 fornecedores mais suspeitos...")
    if pergunta:
        st.session_state["chat"].append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                resposta = servico.responder(pergunta, resultado)
            st.markdown(resposta)

        st.session_state["chat"].append({"role": "assistant", "content": resposta})

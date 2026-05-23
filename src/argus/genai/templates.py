"""Camada GenAI — explicações por template (zero API).

Gera texto legível a partir dos dados estruturados do alerta, sem depender
de nenhum modelo de linguagem externo. Funciona como:
  1. provedor padrão quando ``ARGUS_LLM_PROVIDER=template`` (padrão), e
  2. fallback automático quando a API está indisponível durante a demo.
"""
from __future__ import annotations

import datetime

from argus.domain.models import AlertaRisco, ResultadoAnalise


def explicacao_template(alerta: AlertaRisco) -> str:
    rb = alerta.resultado_benford
    digito = rb.digito_suspeito
    pct_obs = rb.distribuicao_observada.get(digito or 0, 0) * 100
    pct_esp = rb.distribuicao_esperada.get(digito or 0, 0) * 100

    linhas: list[str] = [
        f"**Análise do fornecedor {alerta.entidade}**\n",
        f"Com base em {alerta.n_transacoes:,} transações "
        f"(total de R$ {alerta.valor_total:,.2f}), o Argus identificou um "
        f"nível de risco **{alerta.nivel}** (score: {alerta.score_risco:.2f}).\n",
    ]

    if rb.confiavel and digito:
        excesso = pct_obs - pct_esp
        linhas.append(
            f"**Lei de Benford — {rb.conformidade.value}** (MAD: {rb.mad:.4f}): "
            f"{pct_obs:.1f}% das transações começam com o dígito **{digito}**, "
            f"enquanto o esperado seria {pct_esp:.1f}%. "
            f"Esse excesso de {excesso:.1f} pontos percentuais é o principal "
            f"sinal de alerta.\n"
        )
        if digito == 4:
            linhas.append(
                "O padrão é consistente com **fragmentação de notas**: emissão "
                "de múltiplas faturas logo abaixo de um teto de aprovação "
                "(ex.: R$ 5.000), para evitar revisão por comitê ou processo "
                "de licitação.\n"
            )
        elif digito in (8, 9):
            linhas.append(
                "O padrão pode indicar arredondamentos artificiais ou ajustes "
                "de valores para atingir metas ou limites específicos.\n"
            )
        else:
            linhas.append(
                "A concentração artificial de valores nessa faixa sugere "
                "definição não natural dos montantes. Recomenda-se investigar "
                "o critério utilizado para fixar os valores das faturas.\n"
            )
    elif not rb.confiavel:
        linhas.append(
            f"A amostra deste fornecedor ({rb.n_amostras} transações) é "
            f"insuficiente para o teste de Benford (mínimo: 300 registros). "
            f"A pontuação baseia-se principalmente no score de anomalia ML "
            f"({alerta.score_anomalia:.2f}).\n"
        )

    recomendacao = (
        f"**Recomendação:** revisar as {alerta.n_transacoes:,} transações "
        f"deste fornecedor, com atenção especial aos valores iniciados "
        f"pelo dígito {digito}."
        if digito
        else f"**Recomendação:** revisar as {alerta.n_transacoes:,} transações "
        f"deste fornecedor e solicitar documentação suporte."
    )
    linhas.append(recomendacao)
    return "\n".join(linhas)


def nota_template(alerta: AlertaRisco) -> str:
    rb = alerta.resultado_benford
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    digito = rb.digito_suspeito
    pct_obs = rb.distribuicao_observada.get(digito or 0, 0) * 100
    pct_esp = rb.distribuicao_esperada.get(digito or 0, 0) * 100

    return (
        f"**NOTA DE AUDITORIA — RASCUNHO**  |  Data: {hoje}\n\n"
        f"**Fornecedor analisado:** {alerta.entidade}\n\n"
        f"**Achado:** O fornecedor apresenta desvio estatístico significativo "
        f"na distribuição do 1º dígito dos valores transacionados "
        f"(Lei de Benford). O dígito {digito} aparece em {pct_obs:.1f}% das "
        f"transações (esperado: {pct_esp:.1f}%), resultando em MAD de "
        f"{rb.mad:.4f} — classificado como **{rb.conformidade.value}** "
        f"pelos limiares de Nigrini. Score de anomalia (Isolation Forest): "
        f"{alerta.score_anomalia:.2f}. Score de risco agregado: "
        f"{alerta.score_risco:.2f} ({alerta.nivel}).\n\n"
        f"**Base de evidência:** {alerta.n_transacoes:,} transações; "
        f"valor total R$ {alerta.valor_total:,.2f}.\n\n"
        f"**Recomendação:** Solicitar documentação suporte das faturas, "
        f"investigar se os valores foram definidos em relação a tetos de "
        f"aprovação internos e, se confirmado o padrão, encaminhar ao "
        f"comitê de compliance para apuração formal."
    )


def resposta_chat_template(pergunta: str, resultado: ResultadoAnalise) -> str:
    """Responde perguntas comuns sem chamar nenhuma API."""
    p = pergunta.lower()

    if any(w in p for w in ("suspeito", "risco", "top", "maior", "lista", "piores")):
        top = resultado.top(5)
        linhas = [
            f"Com base na análise de {resultado.total_transacoes:,} transações "
            f"({resultado.fonte_dados}), os fornecedores de maior risco são:\n"
        ]
        for i, a in enumerate(top, 1):
            linhas.append(
                f"{i}. **{a.entidade}** — risco {a.score_risco:.2f} ({a.nivel}), "
                f"Benford: {a.resultado_benford.conformidade.value}, "
                f"{a.n_transacoes:,} transações."
            )
        return "\n".join(linhas)

    if any(w in p for w in ("qualidade", "confiança", "dados", "ruído", "completo")):
        rq = resultado.relatorio_qualidade
        texto = (
            f"O score de confiança dos dados é **{rq.score_confianca:.0f}/100** "
            f"({rq.pct_completude:.1f}% de completude, "
            f"{rq.registros_invalidos} registros inválidos)."
        )
        if rq.problemas:
            texto += " Problemas: " + "; ".join(rq.problemas)
        return texto

    if any(w in p for w in ("benford", "lei", "dígito", "digito")):
        nao_conformes = [
            a for a in resultado.alertas
            if a.resultado_benford.conformidade.value == "Não conforme"
        ]
        return (
            f"{len(nao_conformes)} fornecedor(es) classificado(s) como "
            f"'Não conforme' pela Lei de Benford, de um total de "
            f"{len(resultado.alertas)} analisados."
        )

    return (
        f"Com base nos dados ({resultado.total_transacoes:,} transações, "
        f"{resultado.fonte_dados}), há {len(resultado.alertas)} fornecedores "
        f"no ranking de risco. Para respostas mais detalhadas, configure "
        f"ARGUS_LLM_PROVIDER=openai no arquivo .env."
    )

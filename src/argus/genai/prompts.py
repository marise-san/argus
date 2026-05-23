"""Camada GenAI — construtores de prompt para o LLM.

Cada prompt recebe dados estruturados do motor de detecção como contexto.
Transações cruas nunca vão pro modelo.
"""
from __future__ import annotations

from argus.domain.models import AlertaRisco, ResultadoAnalise

SYSTEM = (
    "Você é o Argus, um assistente de auditoria forense especializado em "
    "detecção de fraude. Sua função é EXPLICAR evidências estatísticas em "
    "português claro, como um auditor experiente faria. "
    "REGRAS ABSOLUTAS: (1) use apenas os dados fornecidos no contexto; "
    "(2) nunca afirme que há fraude confirmada — aponte padrões suspeitos; "
    "(3) seja objetivo e direto; "
    "(4) escreva sempre em português brasileiro."
)


def prompt_explicacao(alerta: AlertaRisco) -> str:
    rb = alerta.resultado_benford
    digito = rb.digito_suspeito
    pct_obs = rb.distribuicao_observada.get(digito or 0, 0) * 100
    pct_esp = rb.distribuicao_esperada.get(digito or 0, 0) * 100

    return (
        f"Analise o perfil do fornecedor abaixo e explique o padrão suspeito "
        f"em 2-3 parágrafos curtos, para um auditor humano que precisa "
        f"decidir se aprofunda a investigação.\n\n"
        f"**Fornecedor:** {alerta.entidade}\n"
        f"**Transações analisadas:** {alerta.n_transacoes}\n"
        f"**Valor total:** R$ {alerta.valor_total:,.2f}\n"
        f"**Score de risco:** {alerta.score_risco:.2f} ({alerta.nivel})\n\n"
        f"**Lei de Benford:**\n"
        f"  - Conformidade: {rb.conformidade.value}\n"
        f"  - MAD: {rb.mad:.4f}\n"
        f"  - Dígito mais suspeito: {digito} "
        f"(observado {pct_obs:.1f}% vs esperado {pct_esp:.1f}%)\n\n"
        f"**Score de anomalia (ML):** {alerta.score_anomalia:.2f}\n\n"
        f"Explique o que esses números sugerem e qual o possível mecanismo "
        f"de fraude. Não afirme que há fraude confirmada."
    )


def prompt_nota_auditoria(alerta: AlertaRisco) -> str:
    rb = alerta.resultado_benford
    return (
        f"Redija um rascunho formal de nota de auditoria (máximo 150 palavras) "
        f"para o achado abaixo. Inclua: Título, Achado, Evidência e "
        f"Recomendação. Use linguagem técnica de auditoria.\n\n"
        f"Fornecedor: {alerta.entidade}\n"
        f"Nº de transações: {alerta.n_transacoes}\n"
        f"Valor total: R$ {alerta.valor_total:,.2f}\n"
        f"Desvio de Benford (MAD): {rb.mad:.4f} — {rb.conformidade.value}\n"
        f"Dígito super-representado: {rb.digito_suspeito}\n"
        f"Score de anomalia (ML): {alerta.score_anomalia:.2f}\n"
        f"Score de risco agregado: {alerta.score_risco:.2f} ({alerta.nivel})"
    )


def prompt_chat(pergunta: str, resultado: ResultadoAnalise) -> str:
    contexto = "\n".join(
        f"- {a.entidade}: risco {a.score_risco:.2f} ({a.nivel}), "
        f"Benford {a.resultado_benford.conformidade.value}, "
        f"{a.n_transacoes} transações"
        for a in resultado.alertas
    )
    rq = resultado.relatorio_qualidade
    return (
        f"Contexto da análise:\n"
        f"Total de transações: {resultado.total_transacoes:,}\n"
        f"Fonte: {resultado.fonte_dados}\n"
        f"Qualidade dos dados: {rq.score_confianca:.0f}/100\n"
        f"Fornecedores analisados ({len(resultado.alertas)}):\n{contexto}\n\n"
        f"Pergunta do auditor: {pergunta}\n\n"
        f"Responda usando apenas o contexto acima. Se a pergunta não puder "
        f"ser respondida com esses dados, diga isso claramente."
    )

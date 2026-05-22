"""Motor de detecção — agregador de risco.

Funde os dois sinais — desvio da Lei de Benford e score de anomalia — num
único score de risco por fornecedor, e devolve a lista de alertas ordenada.
"""
from __future__ import annotations

import pandas as pd

from argus.config import Config, config as config_padrao
from argus.domain.models import AlertaRisco, ResultadoBenford


def _benford_normalizado(resultado: ResultadoBenford, config: Config) -> float:
    """Converte o MAD num score 0..1 (0 quando a amostra é insuficiente)."""
    if not resultado.confiavel:
        return 0.0
    return min(resultado.mad / config.mad_normalizacao, 1.0)


def agregar_risco(
    df: pd.DataFrame,
    benford: dict[str, ResultadoBenford],
    anomalia: dict[str, float],
    coluna_entidade: str = "merchant",
    coluna_valor: str = "amount",
    config: Config = config_padrao,
) -> list[AlertaRisco]:
    """Combina os sinais e devolve os alertas ordenados por risco (desc)."""
    resumo = df.groupby(coluna_entidade)[coluna_valor].agg(["count", "sum"])

    alertas: list[AlertaRisco] = []
    for entidade, resultado_benford in benford.items():
        score_benford = _benford_normalizado(resultado_benford, config)
        score_anomalia = anomalia.get(entidade, 0.0)
        score_risco = (
            config.peso_benford * score_benford
            + config.peso_anomalia * score_anomalia
        )

        if entidade in resumo.index:
            n = int(resumo.loc[entidade, "count"])
            total = float(resumo.loc[entidade, "sum"])
        else:
            n, total = 0, 0.0

        alertas.append(AlertaRisco(
            entidade=entidade,
            score_risco=round(float(score_risco), 4),
            n_transacoes=n,
            valor_total=round(total, 2),
            resultado_benford=resultado_benford,
            score_anomalia=round(float(score_anomalia), 4),
        ))

    alertas.sort(key=lambda a: a.score_risco, reverse=True)
    return alertas

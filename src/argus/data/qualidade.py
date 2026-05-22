"""Camada de dados — Raio-X de Qualidade.

Calcula score de confiança (0..100) com base em completude,
consistência e volume dos dados de entrada.
"""
from __future__ import annotations

import pandas as pd

from argus.domain.models import RelatorioQualidade


def avaliar_qualidade(df: pd.DataFrame) -> RelatorioQualidade:
    """Calcula o score de confiança (0..100) dos dados de entrada."""
    total = len(df)
    if total == 0:
        return RelatorioQualidade(0, 0.0, 0.0, 0, ["Dataset vazio."])

    problemas: list[str] = []

    # Completude: proporção média de células preenchidas.
    pct_completude = float(df.notna().mean().mean() * 100)
    if pct_completude < 99:
        problemas.append(f"{100 - pct_completude:.1f}% das células estão vazias.")

    # Consistência: valores de 'amount' inválidos (nulos ou não positivos).
    amount = pd.to_numeric(df.get("amount"), errors="coerce")
    invalidos = int((amount.isna() | (amount <= 0)).sum())
    if invalidos:
        problemas.append(
            f"{invalidos} transações com valor ausente ou não positivo."
        )

    # Volume: amostra pequena reduz a confiança na análise.
    if total < 1000:
        problemas.append(
            "Volume baixo de transações reduz a confiabilidade da análise."
        )

    # Score final: completude penalizada por inconsistência e baixo volume.
    score = pct_completude
    score -= (invalidos / total) * 100 * 0.5
    if total < 1000:
        score -= 10
    score = max(0.0, min(100.0, score))

    return RelatorioQualidade(
        total_registros=total,
        score_confianca=round(score, 1),
        pct_completude=round(pct_completude, 1),
        registros_invalidos=invalidos,
        problemas=problemas,
    )

"""Motor de detecção — Lei de Benford.

Teste do 1º dígito por entidade (fornecedor, categoria). Usa o MAD
(Mean Absolute Deviation) pra classificar conformidade segundo Nigrini.
"""
from __future__ import annotations

import math

import pandas as pd

from argus.config import Config, config as config_padrao
from argus.domain.models import Conformidade, ResultadoBenford

# Frequência esperada de cada 1º dígito (1..9), segundo a Lei de Benford.
FREQUENCIAS_ESPERADAS: dict[int, float] = {
    d: math.log10(1 + 1 / d) for d in range(1, 10)
}


def primeiro_digito(valor: float) -> int | None:
    """Retorna o 1º dígito significativo de um número (``None`` se inválido)."""
    try:
        v = abs(float(valor))
    except (TypeError, ValueError):
        return None
    if v == 0 or math.isnan(v) or math.isinf(v):
        return None
    while v < 1:
        v *= 10
    while v >= 10:
        v /= 10
    return int(v)


def distribuicao_digitos(valores: pd.Series) -> tuple[dict[int, float], int]:
    """Calcula a frequência observada de cada 1º dígito. Retorna ``(dist, n)``."""
    digitos = valores.map(primeiro_digito).dropna()
    n = len(digitos)
    if n == 0:
        return {d: 0.0 for d in range(1, 10)}, 0
    contagem = digitos.value_counts()
    dist = {d: float(contagem.get(d, 0)) / n for d in range(1, 10)}
    return dist, n


def calcular_mad(observada: dict[int, float]) -> float:
    """Desvio absoluto médio entre a distribuição observada e a de Benford."""
    return sum(
        abs(observada[d] - FREQUENCIAS_ESPERADAS[d]) for d in range(1, 10)
    ) / 9


def classificar_conformidade(
    mad: float, config: Config = config_padrao
) -> Conformidade:
    """Traduz o MAD num veredito de conformidade (limiares de Nigrini)."""
    if mad < config.mad_conformidade:
        return Conformidade.CONFORME
    if mad < config.mad_aceitavel:
        return Conformidade.ACEITAVEL
    if mad < config.mad_marginal:
        return Conformidade.MARGINAL
    return Conformidade.NAO_CONFORME


def analisar_benford(
    valores: pd.Series, entidade: str, config: Config = config_padrao
) -> ResultadoBenford:
    """Roda o teste de Benford sobre os valores de uma entidade."""
    valores = pd.to_numeric(valores, errors="coerce").dropna()
    valores = valores[valores > 0]
    observada, n = distribuicao_digitos(valores)

    # Amostra insuficiente: o Argus declara que não sabe, em vez de inventar.
    if n < config.min_amostra_benford:
        return ResultadoBenford(
            entidade=entidade,
            n_amostras=n,
            distribuicao_observada=observada,
            distribuicao_esperada=dict(FREQUENCIAS_ESPERADAS),
            mad=0.0,
            conformidade=Conformidade.AMOSTRA_INSUFICIENTE,
            digito_suspeito=None,
            excesso_suspeito=0.0,
        )

    mad = calcular_mad(observada)
    # Dígito mais super-representado em relação ao esperado.
    excessos = {d: observada[d] - FREQUENCIAS_ESPERADAS[d] for d in range(1, 10)}
    digito_suspeito = max(excessos, key=excessos.get)

    return ResultadoBenford(
        entidade=entidade,
        n_amostras=n,
        distribuicao_observada=observada,
        distribuicao_esperada=dict(FREQUENCIAS_ESPERADAS),
        mad=mad,
        conformidade=classificar_conformidade(mad, config),
        digito_suspeito=digito_suspeito,
        excesso_suspeito=excessos[digito_suspeito],
    )


def analisar_por_entidade(
    df: pd.DataFrame,
    coluna_entidade: str = "merchant",
    coluna_valor: str = "amount",
    config: Config = config_padrao,
) -> dict[str, ResultadoBenford]:
    """Aplica o teste de Benford a cada entidade (ex.: cada fornecedor)."""
    resultados: dict[str, ResultadoBenford] = {}
    for entidade, grupo in df.groupby(coluna_entidade):
        resultados[str(entidade)] = analisar_benford(
            grupo[coluna_valor], str(entidade), config
        )
    return resultados

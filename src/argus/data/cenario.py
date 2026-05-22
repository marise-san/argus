"""Camada de dados — injeção do cenário de demonstração plantado.

Adiciona um "fornecedor fantasma" que pratica FRAGMENTAÇÃO DE NOTAS: emite
dezenas de faturas logo abaixo do teto de aprovação para nunca passar pelo
comitê. Isso distorce visivelmente a Lei de Benford (pico no dígito 4) e
garante o "momento herói" da apresentação.

IMPORTANTE: este cenário é declarado abertamente durante o pitch — ele
demonstra a detecção, não a mascara.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from argus.config import Config, config as config_padrao


def injetar_cenario_fraude(
    df: pd.DataFrame, config: Config = config_padrao
) -> pd.DataFrame:
    """Acrescenta ao DataFrame as transações do fornecedor fraudulento plantado."""
    rng = np.random.default_rng(config.random_state)
    n_fraude = config.n_notas_fraudulentas
    n_normal = config.n_notas_normais_fraudador

    # Faturas fragmentadas: todas logo abaixo do teto -> 1º dígito sempre "4".
    piso = config.teto_aprovacao * 0.86       # ex.: 4300,00
    topo = config.teto_aprovacao * 0.998      # ex.: 4990,00
    valores_fraude = np.round(rng.uniform(piso, topo, size=n_fraude), 2)

    # Algumas faturas legítimas, para o fornecedor não ser 100% suspeito.
    valores_normais = np.round(rng.lognormal(mean=3.3, sigma=1.15, size=n_normal), 2)

    valores = np.concatenate([valores_fraude, valores_normais])
    rotulo = np.concatenate([np.ones(n_fraude, int), np.zeros(n_normal, int)])
    total = len(valores)

    linhas = pd.DataFrame({
        "step": rng.integers(0, 180, size=total),
        "customer": [f"C_{c}" for c in rng.integers(0, 5000, size=total)],
        "merchant": config.fornecedor_fraudulento,
        "category": "es_otherservices",
        "amount": valores,
        "fraud": rotulo,
    })

    # Alinha às colunas do DataFrame de destino (preenche ausentes com NaN).
    linhas = linhas.reindex(columns=df.columns)
    return pd.concat([df, linhas], ignore_index=True)

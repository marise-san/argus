"""Camada de dados — gerador de dataset sintético.

Quando o BankSim real não está disponível, gera um conjunto equivalente, com
a mesma estrutura de colunas. Os valores seguem uma distribuição log-normal —
que naturalmente adere à Lei de Benford —, de modo que fornecedores honestos
se mostram "conformes" e o cenário plantado se destaca de verdade.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CATEGORIAS = [
    "es_transportation", "es_food", "es_health", "es_wellnessandbeauty",
    "es_fashion", "es_barsandrestaurants", "es_hyper", "es_contents",
    "es_home", "es_tech", "es_sportsandtoys", "es_leisure", "es_travel",
    "es_hotelservices", "es_otherservices",
]


def gerar_dataset_sintetico(
    n_transacoes: int = 25_000,
    n_fornecedores: int = 40,
    seed: int = 42,
) -> pd.DataFrame:
    """Gera um DataFrame de transações no formato do BankSim."""
    rng = np.random.default_rng(seed)
    fornecedores = [f"M_{i:03d}" for i in range(n_fornecedores)]

    merchant = rng.choice(fornecedores, size=n_transacoes)
    category = rng.choice(CATEGORIAS, size=n_transacoes)
    step = rng.integers(0, 180, size=n_transacoes)
    customer = [f"C_{c}" for c in rng.integers(0, 5000, size=n_transacoes)]

    # Valor log-normal: abrange várias ordens de grandeza -> adere a Benford.
    amount = np.round(rng.lognormal(mean=3.3, sigma=1.15, size=n_transacoes), 2)

    # Fraude "natural" rara (~1-2%), concentrada em valores altos. Dá sinal
    # para a métrica de validação sem competir com o cenário plantado.
    limite_alto = np.quantile(amount, 0.95)
    prob_fraude = np.where(amount > limite_alto, 0.18, 0.004)
    fraud = (rng.random(n_transacoes) < prob_fraude).astype(int)

    return pd.DataFrame({
        "step": step,
        "customer": customer,
        "merchant": merchant,
        "category": category,
        "amount": amount,
        "fraud": fraud,
    })

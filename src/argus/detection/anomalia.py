"""Motor de detecção — anomalia com Isolation Forest.

Isolation Forest sobre features de transação (não-supervisionado).
Rótulo ``fraud`` reservado pra validação (precisão@K), não pro treino.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from argus.config import Config, config as config_padrao


def _construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """Monta as features numéricas usadas pelo Isolation Forest."""
    amount = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    feats = pd.DataFrame(index=df.index)
    feats["amount"] = amount
    feats["log_amount"] = np.log1p(amount.clip(lower=0))

    # Quão distante o valor está da média da sua categoria.
    if "category" in df.columns:
        media_categoria = amount.groupby(df["category"]).transform("mean")
        feats["desvio_categoria"] = amount - media_categoria

    if "step" in df.columns:
        feats["step"] = pd.to_numeric(df["step"], errors="coerce").fillna(0.0)

    return feats


def detectar_anomalias(
    df: pd.DataFrame, config: Config = config_padrao
) -> pd.Series:
    """Retorna um score de anomalia 0..1 por transação (maior = mais anômalo)."""
    feats = _construir_features(df)
    X = StandardScaler().fit_transform(feats)

    modelo = IsolationForest(
        contamination=config.contaminacao,
        random_state=config.random_state,
        n_estimators=120,
    )
    modelo.fit(X)

    # score_samples: quanto MENOR, mais anômalo. Invertemos e normalizamos 0..1.
    bruto = -modelo.score_samples(X)
    minimo, maximo = float(bruto.min()), float(bruto.max())
    if maximo - minimo < 1e-9:
        normalizado = np.zeros_like(bruto)
    else:
        normalizado = (bruto - minimo) / (maximo - minimo)

    return pd.Series(normalizado, index=df.index, name="score_anomalia")


def score_por_entidade(
    df: pd.DataFrame,
    scores: pd.Series,
    coluna_entidade: str = "merchant",
) -> dict[str, float]:
    """Agrega o score de anomalia por entidade (média das transações)."""
    agregado = scores.groupby(df[coluna_entidade]).mean()
    return {str(k): float(v) for k, v in agregado.items()}

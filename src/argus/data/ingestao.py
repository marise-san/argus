"""Camada de dados — ingestão e validação de transações.

Carrega o CSV do BankSim, valida as colunas necessárias e normaliza os tipos.
Isola o resto do sistema do formato bruto do arquivo.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Colunas mínimas que o pipeline precisa para funcionar.
COLUNAS_OBRIGATORIAS = ("merchant", "category", "amount")
# Colunas aproveitadas quando disponíveis (não obrigatórias).
COLUNAS_OPCIONAIS = ("step", "customer", "fraud")


class ErroIngestao(ValueError):
    """Erro de validação ao carregar o dataset."""


def carregar_transacoes(caminho: str | Path) -> pd.DataFrame:
    """Lê o CSV de transações do disco e devolve um DataFrame normalizado."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroIngestao(f"Arquivo não encontrado: {caminho}")
    return normalizar(pd.read_csv(caminho))


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa aspas, valida colunas e converte tipos numéricos."""
    df = df.copy()

    # O BankSim entrega strings entre aspas simples: 'M1823072687' -> M1823072687.
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.strip("'").str.strip()

    _validar_colunas(df)

    # 'amount' como número; valores inválidos viram NaN (tratados depois).
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "fraud" in df.columns:
        df["fraud"] = pd.to_numeric(df["fraud"], errors="coerce").fillna(0).astype(int)
    if "step" in df.columns:
        df["step"] = pd.to_numeric(df["step"], errors="coerce")

    return df


def _validar_colunas(df: pd.DataFrame) -> None:
    """Garante a presença das colunas obrigatórias — falha cedo e com clareza."""
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ErroIngestao(
            "Colunas obrigatórias ausentes: "
            + ", ".join(faltando)
            + f". Colunas encontradas: {', '.join(map(str, df.columns))}."
        )

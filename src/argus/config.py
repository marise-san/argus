"""Configuração central do Argus.

Centraliza caminhos, limiares estatísticos e parâmetros dos modelos
num dataclass imutável (``config``).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto: .../hackaton  (este arquivo é .../src/argus/config.py).
RAIZ_PROJETO = Path(__file__).resolve().parents[2]

# Carrega as variáveis do arquivo .env, se ele existir.
load_dotenv(RAIZ_PROJETO / ".env")


@dataclass(frozen=True)
class Config:
    """Parâmetros de execução do Argus (imutável)."""

    # --- Caminhos ---
    raiz: Path = RAIZ_PROJETO
    caminho_banksim: Path = RAIZ_PROJETO / "data" / "raw" / "banksim.csv"

    # --- Lei de Benford ---
    # Amostra mínima para o teste ser estatisticamente confiável.
    min_amostra_benford: int = 300
    # Limiares de MAD (Mean Absolute Deviation) — referência de Nigrini.
    mad_conformidade: float = 0.006   # abaixo deste valor: conforme
    mad_aceitavel: float = 0.012      # abaixo: aceitável
    mad_marginal: float = 0.015       # abaixo: marginal / acima: não conforme
    # Teto usado para normalizar o MAD num score 0..1.
    mad_normalizacao: float = 0.030

    # --- Detecção de anomalia ---
    contaminacao: float = 0.02        # fração esperada de anomalias
    random_state: int = 42

    # --- Agregador de risco (pesos da combinação dos sinais) ---
    peso_benford: float = 0.6
    peso_anomalia: float = 0.4

    # --- Cenário de demonstração plantado (fragmentação de notas) ---
    teto_aprovacao: float = 5000.0
    fornecedor_fraudulento: str = "Fornecedor_Fantasma_LTDA"
    n_notas_fraudulentas: int = 300
    n_notas_normais_fraudador: int = 600

    # --- IA generativa ---
    provedor_llm: str = field(
        default_factory=lambda: os.getenv("ARGUS_LLM_PROVIDER", "template").strip().lower()
    )
    modelo_llm: str = field(
        default_factory=lambda: os.getenv("ARGUS_LLM_MODELO", "gpt-4o-mini").strip()
    )
    chave_openai: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip()
    )


# Instância única, importada por todo o projeto.
config = Config()

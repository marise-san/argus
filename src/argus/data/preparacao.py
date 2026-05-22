"""Camada de dados — preparação do dataset para análise.

Estratégia de origem dos dados:
  1. usa o BankSim real (``data/raw/banksim.csv``), se existir;
  2. caso contrário, gera um dataset sintético equivalente.
Em ambos os casos, injeta o cenário de demonstração plantado.
"""
from __future__ import annotations

import pandas as pd

from argus.config import Config, config as config_padrao
from argus.data.cenario import injetar_cenario_fraude
from argus.data.ingestao import carregar_transacoes
from argus.data.sintetico import gerar_dataset_sintetico


def preparar_dataset(config: Config = config_padrao) -> tuple[pd.DataFrame, str]:
    """Retorna ``(DataFrame pronto para análise, descrição da fonte)``."""
    if config.caminho_banksim.exists():
        df = carregar_transacoes(config.caminho_banksim)
        fonte = "BankSim real"
    else:
        df = gerar_dataset_sintetico(seed=config.random_state)
        fonte = "Dataset sintético (BankSim indisponível)"

    df = injetar_cenario_fraude(df, config)
    return df, fonte

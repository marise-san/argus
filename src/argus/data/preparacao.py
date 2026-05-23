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


def _tentar_baixar_banksim(config: Config) -> None:
    """Tenta baixar o BankSim real caso as chaves do Kaggle existam."""
    import os
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        return

    destino = config.caminho_banksim.parent
    if not destino.exists():
        destino.mkdir(parents=True, exist_ok=True)

    try:
        import kaggle
        print("Baixando dataset real BankSim do Kaggle...")
        kaggle.api.dataset_download_files("ealaxi/banksim1", path=destino, unzip=True)
        
        # O Kaggle extrai com o nome original (ex: bs140513_032310.csv)
        # Precisamos renomear para banksim.csv
        for f in destino.glob("*.csv"):
            if f.name != "banksim.csv":
                f.rename(config.caminho_banksim)
                break
    except Exception as e:
        print(f"Falha ao tentar baixar do Kaggle: {e}")


def preparar_dataset(config: Config = config_padrao) -> tuple[pd.DataFrame, str]:
    """Retorna ``(DataFrame pronto para análise, descrição da fonte)``."""
    if not config.caminho_banksim.exists():
        _tentar_baixar_banksim(config)

    if config.caminho_banksim.exists():
        df = carregar_transacoes(config.caminho_banksim)
        fonte = "BankSim real"
    else:
        df = gerar_dataset_sintetico(seed=config.random_state)
        fonte = "Dataset sintético (BankSim indisponível)"

    df = injetar_cenario_fraude(df, config)
    return df, fonte

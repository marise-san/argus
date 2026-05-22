"""Camada de aplicação — pipeline de análise de fraude.

Fluxo: dados -> qualidade -> Benford -> anomalia -> risco.
GenAI fica na interface (sob demanda, quando o auditor abre um alerta).
"""
from __future__ import annotations

import time

import pandas as pd

from argus.config import Config, config as config_padrao
from argus.data.qualidade import avaliar_qualidade
from argus.detection import anomalia as det_anomalia
from argus.detection import benford as det_benford
from argus.detection import risco as det_risco
from argus.domain.models import ResultadoAnalise


class PipelineAnaliseFraude:
    """Executa a análise estatística completa sobre um DataFrame de transações.

    A sequência é: qualidade -> Benford por fornecedor -> anomalia ML ->
    agregação de risco. O resultado é um ``ResultadoAnalise`` com os alertas
    já ordenados por risco, pronto para ser exibido na interface.
    """

    def __init__(self, config: Config = config_padrao) -> None:
        self._config = config

    def executar(self, df: pd.DataFrame, fonte: str = "") -> ResultadoAnalise:
        inicio = time.perf_counter()

        # 1. Raio-X de qualidade dos dados (honestidade sobre incerteza).
        relatorio_qualidade = avaliar_qualidade(df)

        # 2. Lei de Benford multidimensional (por fornecedor).
        benford = det_benford.analisar_por_entidade(
            df,
            coluna_entidade="merchant",
            coluna_valor="amount",
            config=self._config,
        )

        # 3. Detecção de anomalia não-supervisionada (Isolation Forest).
        scores_transacao = det_anomalia.detectar_anomalias(df, self._config)
        scores_entidade = det_anomalia.score_por_entidade(
            df, scores_transacao, coluna_entidade="merchant"
        )

        # 4. Fusão dos sinais e ordenação por risco.
        alertas = det_risco.agregar_risco(
            df,
            benford=benford,
            anomalia=scores_entidade,
            coluna_entidade="merchant",
            coluna_valor="amount",
            config=self._config,
        )

        return ResultadoAnalise(
            total_transacoes=len(df),
            fonte_dados=fonte,
            relatorio_qualidade=relatorio_qualidade,
            alertas=alertas,
            tempo_processamento_s=round(time.perf_counter() - inicio, 2),
        )

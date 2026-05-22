"""Testes de integração do pipeline completo."""
from argus.application.pipeline import PipelineAnaliseFraude
from argus.config import Config
from argus.data.cenario import injetar_cenario_fraude
from argus.data.sintetico import gerar_dataset_sintetico
from argus.domain.models import Conformidade, ResultadoAnalise


def _dataset_com_cenario(config: Config):
    df = gerar_dataset_sintetico(n_transacoes=10_000, seed=42)
    return injetar_cenario_fraude(df, config)


def test_pipeline_retorna_resultado_analise():
    config = Config()
    df = _dataset_com_cenario(config)
    pipeline = PipelineAnaliseFraude(config)
    resultado = pipeline.executar(df, fonte="teste")
    assert isinstance(resultado, ResultadoAnalise)
    assert resultado.total_transacoes == len(df)
    assert len(resultado.alertas) > 0


def test_fornecedor_fantasma_lidera_ranking():
    """O fornecedor plantado deve ser o de maior risco."""
    config = Config()
    df = _dataset_com_cenario(config)
    pipeline = PipelineAnaliseFraude(config)
    resultado = pipeline.executar(df)
    topo = resultado.alertas[0]
    assert topo.entidade == config.fornecedor_fraudulento


def test_fornecedor_fantasma_nao_conforme_benford():
    """O fornecedor plantado deve ser classificado como Não conforme."""
    config = Config()
    df = _dataset_com_cenario(config)
    pipeline = PipelineAnaliseFraude(config)
    resultado = pipeline.executar(df)
    fantasma = next(
        a for a in resultado.alertas if a.entidade == config.fornecedor_fraudulento
    )
    assert fantasma.resultado_benford.conformidade == Conformidade.NAO_CONFORME
    assert fantasma.resultado_benford.digito_suspeito == 4


def test_qualidade_score_acima_de_80():
    config = Config()
    df = gerar_dataset_sintetico(n_transacoes=5_000, seed=0)
    pipeline = PipelineAnaliseFraude(config)
    resultado = pipeline.executar(df)
    assert resultado.relatorio_qualidade.score_confianca >= 80

"""Testes unitários do motor de Benford."""
import math

import numpy as np
import pandas as pd
import pytest

from argus.config import Config
from argus.detection.benford import (
    FREQUENCIAS_ESPERADAS,
    analisar_benford,
    calcular_mad,
    primeiro_digito,
)
from argus.domain.models import Conformidade


# ── Teste das frequências esperadas ───────────────────────────────────────────

def test_frequencias_somam_um():
    total = sum(FREQUENCIAS_ESPERADAS.values())
    assert abs(total - 1.0) < 1e-9


def test_frequencia_digito_1():
    assert abs(FREQUENCIAS_ESPERADAS[1] - math.log10(2)) < 1e-9


# ── Teste de primeiro_digito ───────────────────────────────────────────────────

@pytest.mark.parametrize("valor,esperado", [
    (1.0, 1), (10.0, 1), (9.99, 9), (4800.0, 4),
    (0.55, 5), (0.07, 7), (100, 1),
])
def test_primeiro_digito(valor, esperado):
    assert primeiro_digito(valor) == esperado


def test_primeiro_digito_zero():
    assert primeiro_digito(0) is None


def test_primeiro_digito_invalido():
    assert primeiro_digito("abc") is None


# ── Teste do MAD ──────────────────────────────────────────────────────────────

def test_mad_da_distribuicao_perfeita_e_zero():
    mad = calcular_mad(FREQUENCIAS_ESPERADAS)
    assert mad < 1e-12


def test_mad_de_distribuicao_uniforme_e_positivo():
    uniforme = {d: 1 / 9 for d in range(1, 10)}
    assert calcular_mad(uniforme) > 0


# ── Teste do analisar_benford ─────────────────────────────────────────────────

def test_lognormal_e_conforme():
    """Dados log-normais naturalmente seguem Benford."""
    rng = np.random.default_rng(42)
    valores = pd.Series(np.round(rng.lognormal(3.0, 1.2, size=2000), 2))
    resultado = analisar_benford(valores, "teste_lognormal")
    assert resultado.conformidade in (
        Conformidade.CONFORME, Conformidade.ACEITAVEL, Conformidade.MARGINAL
    )
    assert resultado.confiavel


def test_amostra_insuficiente():
    """Menos de 300 linhas retorna AMOSTRA_INSUFICIENTE."""
    valores = pd.Series([100.0] * 50)
    resultado = analisar_benford(valores, "pequeno")
    assert resultado.conformidade == Conformidade.AMOSTRA_INSUFICIENTE
    assert not resultado.confiavel


def test_cenario_plantado_nao_conforme():
    """O fornecedor fantasma (fragmentação de notas) deve ser NAO_CONFORME."""
    config = Config()
    rng = np.random.default_rng(42)
    # Faturas concentradas no dígito 4 (fragmentação abaixo de R$ 5000).
    fraudes = rng.uniform(4300, 4999, size=300)
    normais = rng.lognormal(3.3, 1.15, size=600)
    valores = pd.Series(np.concatenate([fraudes, normais]))

    resultado = analisar_benford(valores, "Fornecedor_Fantasma", config)
    assert resultado.conformidade == Conformidade.NAO_CONFORME
    assert resultado.digito_suspeito == 4

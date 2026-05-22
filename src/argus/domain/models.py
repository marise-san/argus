"""Modelos de domínio do Argus.

São estruturas de dados puras — sem dependência de pandas, scikit-learn,
Streamlit ou de qualquer API — que representam os resultados da análise.
Funcionam como contrato estável entre as camadas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Conformidade(str, Enum):
    """Veredito da aderência de uma distribuição à Lei de Benford."""

    CONFORME = "Conforme"
    ACEITAVEL = "Aceitável"
    MARGINAL = "Marginal"
    NAO_CONFORME = "Não conforme"
    AMOSTRA_INSUFICIENTE = "Amostra insuficiente"


@dataclass(frozen=True)
class ResultadoBenford:
    """Resultado do teste de Benford (1º dígito) para uma entidade."""

    entidade: str
    n_amostras: int
    distribuicao_observada: dict[int, float]  # dígito 1..9 -> frequência (0..1)
    distribuicao_esperada: dict[int, float]   # dígito 1..9 -> frequência (0..1)
    mad: float                                # desvio absoluto médio
    conformidade: Conformidade
    digito_suspeito: int | None               # dígito mais super-representado
    excesso_suspeito: float                   # (observado - esperado) nesse dígito

    @property
    def confiavel(self) -> bool:
        """True quando havia amostra suficiente para o teste valer."""
        return self.conformidade is not Conformidade.AMOSTRA_INSUFICIENTE


@dataclass(frozen=True)
class RelatorioQualidade:
    """Raio-X da qualidade dos dados de entrada (resposta a dados ruidosos)."""

    total_registros: int
    score_confianca: float    # 0..100
    pct_completude: float     # 0..100
    registros_invalidos: int
    problemas: list[str] = field(default_factory=list)


@dataclass
class AlertaRisco:
    """Um fornecedor sinalizado, com a evidência e (opcionalmente) o texto da IA.

    Os campos `explicacao` e `nota_auditoria` são preenchidos sob demanda pela
    camada GenAI — só quando o auditor abre o alerta. Por isso a classe é
    mutável (não `frozen`).
    """

    entidade: str
    score_risco: float          # 0..1
    n_transacoes: int
    valor_total: float
    resultado_benford: ResultadoBenford
    score_anomalia: float       # 0..1
    explicacao: str | None = None
    nota_auditoria: str | None = None

    @property
    def nivel(self) -> str:
        """Classifica o risco em Alto / Médio / Baixo."""
        if self.score_risco >= 0.70:
            return "Alto"
        if self.score_risco >= 0.40:
            return "Médio"
        return "Baixo"


@dataclass
class ResultadoAnalise:
    """Saída completa do pipeline de análise de fraude."""

    total_transacoes: int
    fonte_dados: str
    relatorio_qualidade: RelatorioQualidade
    alertas: list[AlertaRisco]           # ordenados por risco (desc)
    tempo_processamento_s: float

    def top(self, n: int = 10) -> list[AlertaRisco]:
        """Retorna os `n` alertas de maior risco."""
        return self.alertas[:n]

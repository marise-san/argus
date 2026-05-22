"""Camada GenAI — serviço de explicação e chat.

Orquestra o cliente LLM (ou os templates locais) para produzir explicações,
notas de auditoria e respostas de chat, sempre a partir dos resultados
do motor de detecção.
"""
from __future__ import annotations

from argus.domain.models import AlertaRisco, ResultadoAnalise
from argus.genai import prompts, templates
from argus.genai.client import ClienteLLM


class ServicoGenAI:
    """Combina o cliente LLM com prompts estruturados e fallback por template."""

    def __init__(self, cliente: ClienteLLM | None) -> None:
        # None = provedor template (offline, determinístico).
        self._cliente = cliente

    def _gerar(self, prompt: str) -> str | None:
        """Tenta chamar o LLM; retorna None em caso de falha."""
        if self._cliente is None:
            return None
        try:
            return self._cliente.gerar(prompt, system=prompts.SYSTEM)
        except Exception:
            return None

    # ── Interface pública ───────────────────────────────────────────────────

    def explicar(self, alerta: AlertaRisco) -> str:
        """Gera a explicação do padrão suspeito em linguagem natural."""
        resultado = self._gerar(prompts.prompt_explicacao(alerta))
        return resultado if resultado else templates.explicacao_template(alerta)

    def redigir_nota(self, alerta: AlertaRisco) -> str:
        """Gera um rascunho formal de nota de auditoria."""
        resultado = self._gerar(prompts.prompt_nota_auditoria(alerta))
        return resultado if resultado else templates.nota_template(alerta)

    def responder(self, pergunta: str, resultado_analise: ResultadoAnalise) -> str:
        """Responde uma pergunta do auditor ancorada nos resultados calculados."""
        resultado = self._gerar(prompts.prompt_chat(pergunta, resultado_analise))
        return resultado if resultado else templates.resposta_chat_template(
            pergunta, resultado_analise
        )

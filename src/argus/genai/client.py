"""Camada GenAI — interface e adaptadores de LLM.

Define o Protocol ``ClienteLLM`` e os adaptadores (ex.: OpenAI).
Troca de provedor acontece na fábrica ``criar_cliente_llm()``.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ClienteLLM(Protocol):
    """Interface mínima de qualquer provedor de LLM."""

    def gerar(self, prompt: str, system: str = "") -> str:
        ...


class ClienteOpenAI:
    """Adaptador para a API da OpenAI."""

    def __init__(self, chave: str, modelo: str) -> None:
        try:
            from openai import OpenAI as _OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Instale o pacote openai: pip install openai"
            ) from exc
        self._cliente = _OpenAI(api_key=chave)
        self._modelo = modelo

    def gerar(self, prompt: str, system: str = "") -> str:
        mensagens = []
        if system:
            mensagens.append({"role": "system", "content": system})
        mensagens.append({"role": "user", "content": prompt})
        resposta = self._cliente.chat.completions.create(
            model=self._modelo,
            messages=mensagens,
            temperature=0.3,
            max_tokens=600,
        )
        return resposta.choices[0].message.content or ""


def criar_cliente_llm(config) -> ClienteLLM | None:
    """Fábrica de clientes LLM.

    Retorna ``None`` quando o provedor é 'template' — o ``ServicoGenAI``
    usará os templates locais determinísticos.
    """
    if config.provedor_llm in ("template", ""):
        return None
    if config.provedor_llm == "openai":
        if not config.chave_openai:
            raise ValueError(
                "OPENAI_API_KEY não encontrada. "
                "Adicione ao .env ou use ARGUS_LLM_PROVIDER=template."
            )
        return ClienteOpenAI(config.chave_openai, config.modelo_llm)
    raise ValueError(
        f"Provedor desconhecido: '{config.provedor_llm}'. "
        "Valores aceitos: template, openai."
    )

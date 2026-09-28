"""Seam Provider: `chamar(prompt, transcricao) -> RespostaProvider`.

Os adapters reais (GatewayProvider, AnthropicProvider, GroqProvider,
ReplayProvider) chegam em T1/T3/T5/T6. Aqui só o tipo de retorno normalizado
que o Executor de Rodada (T2) consome.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RespostaProvider:
    texto: str
    motivo_parada: str
    modelo: str
    temperatura: float | None = None


class Provider(Protocol):
    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider: ...


class ErroProvider(Exception):
    """Erro do provider (timeout, limite de taxa, erro HTTP). Nunca vira Chamada
    nem resposta — quem chama o Provider decide o que fazer (T4: aborta a Rodada).
    """

    def __init__(self, mensagem: str, causa_provavel: str):
        super().__init__(mensagem)
        self.causa_provavel = causa_provavel

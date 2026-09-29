"""Seam Provider: `chamar(prompt, transcricao) -> RespostaProvider`.

GatewayProvider fala o formato Anthropic com o Gateway local. Os demais
adapters chegam nos tickets seguintes; todos devolvem o mesmo tipo normalizado.
"""

import json
import urllib.error
import urllib.request
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


_MOTIVOS_PARADA = {
    "end_turn": "fim_normal",
    "max_tokens": "truncada",
    "refusal": "recusa",
}


def _montar_corpo_anthropic(
    modelo: str, prompt: str, transcricao: str, max_tokens: int, temperatura: float
) -> dict:
    return {
        "model": modelo,
        "system": prompt,
        "messages": [{"role": "user", "content": transcricao}],
        "max_tokens": max_tokens,
        "temperature": temperatura,
    }


def _formato_anthropic_valido(dado: object) -> bool:
    return (
        isinstance(dado, dict)
        and dado.get("type") == "message"
        and isinstance(dado.get("model"), str)
        and bool(dado["model"])
        and isinstance(dado.get("stop_reason"), str)
        and bool(dado["stop_reason"])
        and isinstance(dado.get("content"), list)
        and not any(
            not isinstance(bloco, dict)
            or (bloco.get("type") == "text" and not isinstance(bloco.get("text"), str))
            for bloco in dado["content"]
        )
    )


def _normalizar_resposta_anthropic(dado: dict, nome_provider: str) -> RespostaProvider:
    """Mapeamento de `stop_reason` para o vocabulário fechado (fim_normal, truncada,
    recusa, outro) — vive aqui, nunca no Avaliador. Mesma normalização para todo
    adapter que fala o formato Anthropic (T6: GatewayProvider e AnthropicProvider
    precisam produzir o mesmo resultado a partir do mesmo corpo de resposta).
    """
    if not _formato_anthropic_valido(dado):
        raise ErroProvider(
            f"{nome_provider} devolveu resposta fora do formato Anthropic",
            f"{nome_provider} ou upstream incompatível; próximo passo: confira /v1/messages",
        )
    motivo = _MOTIVOS_PARADA.get(dado["stop_reason"], "outro")
    texto = "".join(bloco["text"] for bloco in dado["content"] if bloco.get("type") == "text")
    return RespostaProvider(texto, motivo, dado["model"], None)


class GatewayProvider:
    """Adapter do Gateway local para o contrato normalizado do Provider."""

    def __init__(
        self,
        endpoint_url: str,
        chave: str,
        modelo: str,
        max_tokens: int,
        temperatura: float,
        timeout_s: float = 30.0,
        abrir=urllib.request.urlopen,
    ):
        self._url = endpoint_url.rstrip("/") + "/v1/messages"
        self._chave = chave
        self._modelo = modelo
        self._max_tokens = max_tokens
        self._temperatura = temperatura
        self._timeout_s = timeout_s
        self._abrir = abrir

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        corpo = _montar_corpo_anthropic(self._modelo, prompt, transcricao, self._max_tokens, self._temperatura)
        pedido = urllib.request.Request(
            self._url,
            data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": self._chave,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with self._abrir(pedido, timeout=self._timeout_s) as resposta_http:
                dado = json.loads(resposta_http.read())
        except urllib.error.HTTPError as erro:
            if erro.code == 429:
                raise ErroProvider(
                    "Gateway retornou HTTP 429: limite de taxa",
                    "limite de taxa do provider; próximo passo: aguarde e reexecute uma nova Rodada",
                ) from None
            if erro.code in (401, 403):
                raise ErroProvider(
                    f"Gateway retornou HTTP {erro.code}: autenticação recusada",
                    "CXLAB_GATEWAY_KEY ausente ou inválida; "
                    "próximo passo: configure a chave local do Gateway fora do repositório",
                ) from None
            raise ErroProvider(
                f"Gateway retornou HTTP {erro.code}",
                "resposta HTTP do Gateway; próximo passo: confira o estado e a configuração do Gateway",
            ) from None
        except TimeoutError:
            raise ErroProvider(
                "Gateway excedeu o timeout da Chamada",
                "Gateway ou upstream lento; próximo passo: confira o serviço e inicie outra Rodada",
            ) from None
        except (urllib.error.URLError, OSError):
            raise ErroProvider(
                "Gateway inacessível",
                "CXLAB_GATEWAY_URL aponta para um Gateway indisponível; "
                "próximo passo: inicie o Gateway e confira o endpoint",
            ) from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ErroProvider(
                "Gateway devolveu corpo que não é JSON válido",
                "resposta fora do formato Anthropic; próximo passo: confira /v1/messages",
            ) from None
        return _normalizar_resposta_anthropic(dado, "Gateway")


class AnthropicProvider:
    """Adapter da API oficial da Anthropic para o contrato normalizado do
    Provider. Mesma seam do GatewayProvider (T6: mesmo resultado normalizado
    sobre o mesmo transporte falso — ver `testes/contrato_provider_test.py`).

    Este plano (CAR-8) não paga a API oficial: nenhum teste ordinário exercita
    esta classe contra a rede real; só o teste opt-in em
    `testes/anthropic_integracao_test.py`, desabilitado por padrão.
    """

    def __init__(
        self,
        chave: str,
        modelo: str,
        max_tokens: int,
        temperatura: float,
        timeout_s: float = 30.0,
        endpoint_url: str = "https://api.anthropic.com",
        abrir=urllib.request.urlopen,
    ):
        self._url = endpoint_url.rstrip("/") + "/v1/messages"
        self._chave = chave
        self._modelo = modelo
        self._max_tokens = max_tokens
        self._temperatura = temperatura
        self._timeout_s = timeout_s
        self._abrir = abrir

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        corpo = _montar_corpo_anthropic(self._modelo, prompt, transcricao, self._max_tokens, self._temperatura)
        pedido = urllib.request.Request(
            self._url,
            data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-api-key": self._chave,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with self._abrir(pedido, timeout=self._timeout_s) as resposta_http:
                dado = json.loads(resposta_http.read())
        except urllib.error.HTTPError as erro:
            if erro.code == 429:
                raise ErroProvider(
                    "Anthropic retornou HTTP 429: limite de taxa",
                    "limite de taxa da API oficial; próximo passo: aguarde e reexecute uma nova Rodada",
                ) from None
            if erro.code in (401, 403):
                raise ErroProvider(
                    f"Anthropic retornou HTTP {erro.code}: autenticação recusada",
                    "ANTHROPIC_API_KEY ausente ou inválida; "
                    "próximo passo: confira a chave da API oficial no ambiente local",
                ) from None
            raise ErroProvider(
                f"Anthropic retornou HTTP {erro.code}",
                "resposta HTTP da API oficial; próximo passo: confira a causa em api.anthropic.com/status",
            ) from None
        except TimeoutError:
            raise ErroProvider(
                "Anthropic excedeu o timeout da Chamada",
                "API oficial lenta ou indisponível; próximo passo: confira o serviço e inicie outra Rodada",
            ) from None
        except (urllib.error.URLError, OSError):
            raise ErroProvider(
                "Anthropic inacessível",
                "endpoint da API oficial indisponível a partir daqui; "
                "próximo passo: confira a rede e o endpoint configurado",
            ) from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ErroProvider(
                "Anthropic devolveu corpo que não é JSON válido",
                "resposta fora do formato Anthropic; próximo passo: confira /v1/messages",
            ) from None
        return _normalizar_resposta_anthropic(dado, "Anthropic")

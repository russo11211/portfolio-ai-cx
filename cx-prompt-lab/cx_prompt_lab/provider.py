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
        corpo = {
            "model": self._modelo,
            "system": prompt,
            "messages": [{"role": "user", "content": transcricao}],
            "max_tokens": self._max_tokens,
            "temperature": self._temperatura,
        }
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
        if (
            not isinstance(dado, dict)
            or dado.get("type") != "message"
            or not isinstance(dado.get("model"), str)
            or not dado["model"]
            or not isinstance(dado.get("stop_reason"), str)
            or not dado["stop_reason"]
            or not isinstance(dado.get("content"), list)
            or any(
                not isinstance(bloco, dict)
                or (bloco.get("type") == "text" and not isinstance(bloco.get("text"), str))
                for bloco in dado["content"]
            )
        ):
            raise ErroProvider(
                "Gateway devolveu resposta fora do formato Anthropic",
                "Gateway ou upstream incompatível; próximo passo: confira /v1/messages",
            )
        motivo = {
            "end_turn": "fim_normal",
            "max_tokens": "truncada",
            "refusal": "recusa",
        }.get(dado["stop_reason"], "outro")
        texto = "".join(bloco["text"] for bloco in dado["content"] if bloco.get("type") == "text")
        return RespostaProvider(texto, motivo, dado["model"], None)

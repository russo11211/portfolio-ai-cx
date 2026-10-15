"""T6: contrato entre providers.

GatewayProvider e AnthropicProvider, rodando sobre o mesmo transporte HTTP
falso, precisam produzir exatamente o mesmo RespostaProvider normalizado. O
mapeamento de motivo de parada para o vocabulário fechado (fim_normal,
truncada, recusa, outro) vive dentro de cada provider, nunca no Avaliador.
"""

import json

import pytest

from cx_prompt_lab.provider import AnthropicProvider, ErroProvider, GatewayProvider, RespostaProvider


class RespostaHTTP:
    def __init__(self, dado: dict):
        self.dado = dado

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.dado).encode("utf-8")


def _construir_providers(abrir):
    gateway = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="chave-gateway",
        modelo="modelo-pedido",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )
    anthropic = AnthropicProvider(
        chave="chave-anthropic",
        modelo="modelo-pedido",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )
    return gateway, anthropic


@pytest.mark.parametrize(
    ("stop_reason", "content", "motivo_esperado", "texto_esperado"),
    [
        ("end_turn", [{"type": "text", "text": "ok"}], "fim_normal", "ok"),
        ("max_tokens", [{"type": "text", "text": "trunc"}], "truncada", "trunc"),
        ("refusal", [{"type": "text", "text": "não posso"}], "recusa", "não posso"),
        ("stop_sequence", [{"type": "text", "text": "outro"}], "outro", "outro"),
        (
            "end_turn",
            [
                {"type": "text", "text": "primeira "},
                {"type": "tool_use", "id": "ignorado"},
                {"type": "text", "text": "segunda"},
            ],
            "fim_normal",
            "primeira segunda",
        ),
    ],
)
def test_gateway_e_anthropic_normalizam_igual_sobre_o_mesmo_transporte(
    stop_reason, content, motivo_esperado, texto_esperado
):
    def abrir(pedido, timeout):
        return RespostaHTTP(
            {
                "type": "message",
                "model": "modelo-devolvido",
                "stop_reason": stop_reason,
                "content": content,
            }
        )

    gateway, anthropic = _construir_providers(abrir)

    resposta_gateway = gateway.chamar("prompt", "transcrição")
    resposta_anthropic = anthropic.chamar("prompt", "transcrição")

    esperada = RespostaProvider(texto_esperado, motivo_esperado, "modelo-devolvido", None)
    assert resposta_gateway == esperada
    assert resposta_anthropic == esperada


def test_gateway_e_anthropic_nao_informam_temperatura_efetiva():
    def abrir(pedido, timeout):
        return RespostaHTTP(
            {
                "type": "message",
                "model": "modelo-devolvido",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "ok"}],
            }
        )

    gateway, anthropic = _construir_providers(abrir)

    assert gateway.chamar("prompt", "transcrição").temperatura is None
    assert anthropic.chamar("prompt", "transcrição").temperatura is None


def test_gateway_e_anthropic_recusam_ausencia_de_motivo_de_parada():
    def abrir(pedido, timeout):
        return RespostaHTTP(
            {
                "type": "message",
                "model": "modelo-devolvido",
                "stop_reason": None,
                "content": [{"type": "text", "text": "ok"}],
            }
        )

    gateway, anthropic = _construir_providers(abrir)

    with pytest.raises(ErroProvider, match="formato Anthropic"):
        gateway.chamar("prompt", "transcrição")
    with pytest.raises(ErroProvider, match="formato Anthropic"):
        anthropic.chamar("prompt", "transcrição")


@pytest.mark.parametrize("status", [429, 401, 500])
def test_gateway_e_anthropic_convertem_erro_http_em_erro_do_provider(status):
    from urllib.error import HTTPError

    def abrir(pedido, timeout):
        raise HTTPError(pedido.full_url, status, "erro", {}, None)

    gateway, anthropic = _construir_providers(abrir)

    with pytest.raises(ErroProvider):
        gateway.chamar("prompt", "transcrição")
    with pytest.raises(ErroProvider):
        anthropic.chamar("prompt", "transcrição")

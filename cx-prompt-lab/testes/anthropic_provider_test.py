import json
from urllib.error import HTTPError, URLError

import pytest

from cx_prompt_lab.provider import AnthropicProvider, ErroProvider, RespostaProvider


class RespostaHTTP:
    def __init__(self, dado: dict):
        self.dado = dado

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.dado).encode("utf-8")


def test_anthropic_envia_prompt_como_system_e_devolve_modelo_e_parada_observados():
    pedido_recebido = {}

    def abrir(pedido, timeout):
        pedido_recebido["url"] = pedido.full_url
        pedido_recebido["headers"] = {k.lower(): v for k, v in pedido.header_items()}
        pedido_recebido["corpo"] = json.loads(pedido.data)
        pedido_recebido["timeout"] = timeout
        return RespostaHTTP(
            {
                "type": "message",
                "model": "claude-sonnet-4-5-20250929",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "ok"}],
            }
        )

    provider = AnthropicProvider(
        chave="chave-real-de-teste",
        modelo="claude-sonnet-4-5-20250929",
        max_tokens=64,
        temperatura=0,
        timeout_s=30,
        abrir=abrir,
    )

    resposta = provider.chamar(
        prompt="Classifique a intenção da chamada.",
        transcricao="Cliente quer cancelar o plano.",
    )

    assert resposta == RespostaProvider("ok", "fim_normal", "claude-sonnet-4-5-20250929", None)
    assert pedido_recebido == {
        "url": "https://api.anthropic.com/v1/messages",
        "headers": {
            "content-type": "application/json",
            "x-api-key": "chave-real-de-teste",
            "anthropic-version": "2023-06-01",
        },
        "corpo": {
            "model": "claude-sonnet-4-5-20250929",
            "system": "Classifique a intenção da chamada.",
            "messages": [{"role": "user", "content": "Cliente quer cancelar o plano."}],
            "max_tokens": 64,
            "temperature": 0,
        },
        "timeout": 30,
    }


def test_anthropic_permite_sobrescrever_endpoint():
    def abrir(pedido, timeout):
        assert pedido.full_url == "https://proxy.exemplo.com/v1/messages"
        return RespostaHTTP(
            {
                "type": "message",
                "model": "modelo-devolvido",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "ok"}],
            }
        )

    provider = AnthropicProvider(
        chave="chave-real-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        endpoint_url="https://proxy.exemplo.com",
        abrir=abrir,
    )

    provider.chamar("prompt", "transcrição")


def test_limite_de_taxa_da_anthropic_vira_erro_do_provider_sem_expor_chave():
    def abrir(pedido, timeout):
        raise HTTPError(pedido.full_url, 429, "rate limit", {}, None)

    provider = AnthropicProvider(
        chave="segredo-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider) as erro:
        provider.chamar("prompt", "transcrição")

    assert "limite de taxa" in str(erro.value).lower()
    assert "segredo-de-teste" not in str(erro.value)
    assert "segredo-de-teste" not in erro.value.causa_provavel


def test_erro_de_autenticacao_indica_variavel_sem_expor_chave():
    def abrir(pedido, timeout):
        raise HTTPError(pedido.full_url, 401, "unauthorized", {}, None)

    provider = AnthropicProvider(
        chave="segredo-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider) as erro:
        provider.chamar("prompt", "transcrição")

    assert "HTTP 401" in str(erro.value)
    assert "ANTHROPIC_API_KEY" in erro.value.causa_provavel
    assert "segredo-de-teste" not in str(erro.value) + erro.value.causa_provavel


def test_anthropic_inacessivel_indica_passo_de_correcao():
    def abrir(pedido, timeout):
        raise URLError("Connection refused")

    provider = AnthropicProvider(
        chave="segredo-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider) as erro:
        provider.chamar("prompt", "transcrição")

    assert "Anthropic" in str(erro.value)
    assert "segredo-de-teste" not in str(erro.value) + erro.value.causa_provavel


def test_timeout_http_vira_erro_do_provider():
    def abrir(pedido, timeout):
        raise TimeoutError("timed out")

    provider = AnthropicProvider(
        chave="chave-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider, match="timeout"):
        provider.chamar("prompt", "transcrição")


def test_resposta_sem_motivo_de_parada_aborta_com_erro_de_formato():
    def abrir(pedido, timeout):
        return RespostaHTTP(
            {
                "type": "message",
                "model": "claude-sonnet-4-5-20250929",
                "stop_reason": None,
                "content": [{"type": "text", "text": "ok"}],
            }
        )

    provider = AnthropicProvider(
        chave="chave-de-teste",
        modelo="claude-sonnet-4-5-20250929",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider, match="formato Anthropic"):
        provider.chamar("prompt", "transcrição")


@pytest.mark.parametrize(
    ("motivo_nativo", "motivo_esperado"),
    [
        ("max_tokens", "truncada"),
        ("refusal", "recusa"),
        ("stop_sequence", "outro"),
    ],
)
def test_anthropic_normaliza_parada_e_concatena_blocos_de_texto(motivo_nativo, motivo_esperado):
    def abrir(pedido, timeout):
        return RespostaHTTP(
            {
                "type": "message",
                "model": "modelo-devolvido",
                "stop_reason": motivo_nativo,
                "content": [
                    {"type": "text", "text": "primeira "},
                    {"type": "tool_use", "id": "ignorado"},
                    {"type": "text", "text": "segunda"},
                ],
            }
        )

    provider = AnthropicProvider(
        chave="chave-de-teste",
        modelo="modelo-pedido",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    assert provider.chamar("prompt", "transcrição") == RespostaProvider(
        "primeira segunda", motivo_esperado, "modelo-devolvido", None
    )

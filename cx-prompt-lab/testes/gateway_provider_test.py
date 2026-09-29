import json
from urllib.error import HTTPError, URLError

import pytest

from cx_prompt_lab.provider import ErroProvider, GatewayProvider, RespostaProvider


class RespostaHTTP:
    def __init__(self, dado: dict):
        self.dado = dado

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.dado).encode("utf-8")


def test_gateway_envia_prompt_como_system_e_devolve_modelo_e_parada_observados():
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

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="chave-local-de-teste",
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
        "url": "http://127.0.0.1:8317/v1/messages",
        "headers": {
            "content-type": "application/json",
            "x-api-key": "chave-local-de-teste",
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


def test_limite_de_taxa_do_gateway_vira_erro_do_provider_sem_expor_chave():
    def abrir(pedido, timeout):
        raise HTTPError(pedido.full_url, 429, "rate limit", {}, None)

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
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

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="chave-local-de-teste",
        modelo="claude-sonnet-4-5-20250929",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider, match="formato Anthropic"):
        provider.chamar("prompt", "transcrição")


def test_gateway_inacessivel_indica_endpoint_e_passo_de_correcao():
    def abrir(pedido, timeout):
        raise URLError("Connection refused")

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="segredo-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider) as erro:
        provider.chamar("prompt", "transcrição")

    assert "Gateway inacessível" in str(erro.value)
    assert "CXLAB_GATEWAY_URL" in erro.value.causa_provavel
    assert "segredo-de-teste" not in str(erro.value) + erro.value.causa_provavel


def test_resposta_nao_json_e_erro_do_provider():
    class RespostaInvalida(RespostaHTTP):
        def read(self):
            return b"isto nao e json"

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="chave-local-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=lambda pedido, timeout: RespostaInvalida({}),
    )

    with pytest.raises(ErroProvider, match="JSON"):
        provider.chamar("prompt", "transcrição")


def test_erro_de_autenticacao_indica_variavel_sem_expor_chave():
    def abrir(pedido, timeout):
        raise HTTPError(pedido.full_url, 401, "unauthorized", {}, None)

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="segredo-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider) as erro:
        provider.chamar("prompt", "transcrição")

    assert "HTTP 401" in str(erro.value)
    assert "CXLAB_GATEWAY_KEY" in erro.value.causa_provavel
    assert "segredo-de-teste" not in str(erro.value) + erro.value.causa_provavel


def test_timeout_http_vira_erro_do_provider():
    def abrir(pedido, timeout):
        raise TimeoutError("timed out")

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="chave-local-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider, match="timeout"):
        provider.chamar("prompt", "transcrição")


@pytest.mark.parametrize(
    ("motivo_nativo", "motivo_esperado"),
    [
        ("max_tokens", "truncada"),
        ("refusal", "recusa"),
        ("stop_sequence", "outro"),
    ],
)
def test_gateway_normaliza_parada_e_concatena_blocos_de_texto(motivo_nativo, motivo_esperado):
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

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="chave-local-de-teste",
        modelo="modelo-pedido",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    assert provider.chamar("prompt", "transcrição") == RespostaProvider(
        "primeira segunda", motivo_esperado, "modelo-devolvido", None
    )


def test_conexao_interrompida_aborta_a_chamada_com_erro_do_provider():
    def abrir(pedido, timeout):
        raise ConnectionResetError("connection reset")

    provider = GatewayProvider(
        endpoint_url="http://127.0.0.1:8317",
        chave="chave-local-de-teste",
        modelo="modelo-de-teste",
        max_tokens=64,
        temperatura=0,
        abrir=abrir,
    )

    with pytest.raises(ErroProvider, match="Gateway inacessível"):
        provider.chamar("prompt", "transcrição")

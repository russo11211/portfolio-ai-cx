"""Teste real, opt-in, contra a API oficial da Anthropic.

Este plano (CAR-8) não paga a API oficial: este teste fica desabilitado.
Execução exige, além de ANTHROPIC_API_KEY, a habilitação explícita
CXLAB_TEST_ANTHROPIC=1 e CXLAB_MODEL. Sem a habilitação, o teste é *skipped*
com o motivo visível. Habilitado sem as variáveis de condição, falha com a
causa e o passo de correção — nunca fica silenciosamente verde nem chama a
API sem querer.

O relatório do CX Prompt Lab só afirma "Compatível com Anthropic": este
teste, quando ativado, prova só isso, nunca validação contra o modelo real.
"""

import os

import pytest

from cx_prompt_lab.provider import AnthropicProvider


def test_anthropic_real_devolve_resposta_normalizada():
    if os.environ.get("CXLAB_TEST_ANTHROPIC") != "1":
        pytest.skip(
            "Teste real da Anthropic desabilitado; defina CXLAB_TEST_ANTHROPIC=1 "
            "para chamar a API oficial (este plano não paga a API oficial — CAR-8)"
        )

    chave = os.environ.get("ANTHROPIC_API_KEY")
    modelo = os.environ.get("CXLAB_MODEL")
    if not chave or not modelo:
        pytest.fail(
            "Teste real habilitado sem configuração — próximo passo: defina "
            "ANTHROPIC_API_KEY e CXLAB_MODEL no ambiente local"
        )

    provider = AnthropicProvider(
        chave=chave,
        modelo=modelo,
        max_tokens=16,
        temperatura=0,
        timeout_s=30,
    )

    resposta = provider.chamar(
        prompt='Responda somente a palavra "ok".',
        transcricao="teste de fumaça do contrato Anthropic",
    )

    assert resposta.texto
    assert resposta.modelo
    assert resposta.motivo_parada in {"fim_normal", "truncada", "recusa", "outro"}

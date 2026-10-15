"""Integração local opt-in: três Chamadas reais, sem credenciais em arquivos.

Execução habilitada: CXLAB_TEST_GATEWAY=1, CXLAB_GATEWAY_KEY e CXLAB_MODEL
definidos no ambiente local. CXLAB_GATEWAY_URL pode sobrescrever o endereço.
"""

import os

import pytest

from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.executor import AbortoRodada, rodar
from cx_prompt_lab.gravacao import ProviderGravador, gravar, hash_texto
from cx_prompt_lab.provider import GatewayProvider


def test_gateway_real_grava_rodada_curta(tmp_path):
    if os.environ.get("CXLAB_TEST_GATEWAY") != "1":
        pytest.skip("Gateway desabilitado; defina CXLAB_TEST_GATEWAY=1 para chamar o modelo real")

    chave = os.environ.get("CXLAB_GATEWAY_KEY")
    modelo = os.environ.get("CXLAB_MODEL")
    if not chave or not modelo:
        pytest.fail(
            "Integração habilitada sem configuração — próximo passo: defina "
            "CXLAB_GATEWAY_KEY e CXLAB_MODEL no ambiente local"
        )

    dataset = Dataset(
        transcricoes=[
            Transcricao(
                id="integracao-1",
                texto="Cliente quer cancelar o plano de telefone.",
                rotulo_esperado="cancelamento",
            )
        ],
        rotulos_validos=["cancelamento"],
    )
    prompt_texto = (
        'Classifique a intenção. Responda somente um objeto JSON com "rotulo" e '
        '"justificativa". O único rótulo permitido é "cancelamento"; copie a '
        "justificativa literalmente da Transcrição."
    )
    provider = GatewayProvider(
        endpoint_url=os.environ.get("CXLAB_GATEWAY_URL", "http://127.0.0.1:8317"),
        chave=chave,
        modelo=modelo,
        max_tokens=64,
        temperatura=0,
        timeout_s=30,
    )
    gravador = ProviderGravador(
        provider,
        dataset,
        "integracao-real",
        hash_texto(prompt_texto),
        parametros_geracao={"max_tokens": 64},
    )

    try:
        rodada = rodar(
            "integracao",
            dataset,
            gravador,
            repeticoes=3,
            rodada_id="integracao-real",
            prompt_texto=prompt_texto,
        )
    except AbortoRodada as erro:
        pytest.fail(f"Integração habilitada falhou — {erro}")

    manifesto = gravar(
        diretorio_rodadas=tmp_path,
        rodada_id="integracao-real",
        versao_prompt="integracao",
        prompt_texto=prompt_texto,
        dataset=dataset,
        chamadas=gravador.chamadas,
        repeticoes=3,
        parametros_efetivos={"modelo_pedido": modelo, "temperature_pedida": 0, "max_tokens": 64},
    )

    assert len(rodada.contagens_por_repeticao) == 3
    assert manifesto.estado == "completa"
    assert len(gravador.chamadas) == 3
    assert all(
        c.modelo and c.motivo_parada in {"fim_normal", "truncada", "recusa", "outro"}
        for c in gravador.chamadas
    )

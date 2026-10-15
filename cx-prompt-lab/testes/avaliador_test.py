from cx_prompt_lab.avaliador import avaliar

ROTULOS_VALIDOS = ["cancelamento", "duvida", "reclamacao"]
TRANSCRICAO = "Cliente diz: quero cancelar o meu plano hoje mesmo."


def test_linha_a_rotulo_correto_e_justificativa_ancorada_nao_gera_metrica():
    resposta = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "ok"
    assert resultado.erro_de_acerto is False
    assert resultado.alucinacao_rotulo_inexistente is False
    assert resultado.alucinacao_justificativa_nao_ancorada is False


def test_linha_b_rotulo_valido_e_errado_conta_erro_de_acerto():
    resposta = '{"rotulo": "duvida", "justificativa": "quero cancelar o meu plano"}'

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "ok"
    assert resultado.erro_de_acerto is True
    assert resultado.alucinacao_rotulo_inexistente is False
    assert resultado.alucinacao_justificativa_nao_ancorada is False


def test_linha_c_rotulo_correto_mas_justificativa_nao_ancorada_conta_alucinacao():
    resposta = '{"rotulo": "cancelamento", "justificativa": "algo que nao esta na transcricao"}'

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "ok"
    assert resultado.erro_de_acerto is False
    assert resultado.alucinacao_rotulo_inexistente is False
    assert resultado.alucinacao_justificativa_nao_ancorada is True


def test_linha_d_rotulo_errado_e_justificativa_nao_ancorada_conta_ambas():
    resposta = '{"rotulo": "duvida", "justificativa": "algo que nao esta na transcricao"}'

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.erro_de_acerto is True
    assert resultado.alucinacao_justificativa_nao_ancorada is True
    assert resultado.alucinacao_rotulo_inexistente is False
    assert resultado.veredito_de_forma == "ok"


def test_linha_e_rotulo_fora_da_lista_conta_erro_de_acerto_e_alucinacao_rotulo_inexistente():
    resposta = '{"rotulo": "portabilidade", "justificativa": "quero cancelar o meu plano"}'

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "ok"
    assert resultado.erro_de_acerto is True
    assert resultado.alucinacao_rotulo_inexistente is True
    assert resultado.alucinacao_justificativa_nao_ancorada is False


def test_linha_f_resposta_vazia_conta_so_violacao_de_formato():
    resultado = avaliar(
        resposta_bruta="",
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"
    assert resultado.erro_de_acerto is False
    assert resultado.alucinacao_rotulo_inexistente is False
    assert resultado.alucinacao_justificativa_nao_ancorada is False


def test_linha_f_json_invalido_conta_so_violacao_de_formato():
    resultado = avaliar(
        resposta_bruta="isto nao e json",
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"
    assert resultado.erro_de_acerto is False
    assert resultado.alucinacao_rotulo_inexistente is False
    assert resultado.alucinacao_justificativa_nao_ancorada is False


def test_linha_f_campo_faltando_conta_so_violacao_de_formato():
    resultado = avaliar(
        resposta_bruta='{"rotulo": "cancelamento"}',
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"
    assert resultado.erro_de_acerto is False
    assert resultado.alucinacao_rotulo_inexistente is False
    assert resultado.alucinacao_justificativa_nao_ancorada is False


def test_linha_f_campo_de_tipo_errado_conta_so_violacao_de_formato():
    resultado = avaliar(
        resposta_bruta='{"rotulo": "cancelamento", "justificativa": 123}',
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"


def test_linha_f_justificativa_vazia_conta_so_violacao_de_formato():
    resultado = avaliar(
        resposta_bruta='{"rotulo": "cancelamento", "justificativa": ""}',
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"


def test_linha_f_justificativa_so_de_espacos_conta_so_violacao_de_formato():
    resultado = avaliar(
        resposta_bruta='{"rotulo": "cancelamento", "justificativa": "   "}',
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"


def test_linha_f_json_dentro_de_code_fence_conta_so_violacao_de_formato():
    resposta_com_code_fence = (
        '```json\n{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}\n```'
    )

    resultado = avaliar(
        resposta_bruta=resposta_com_code_fence,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"


def test_linha_f_json_com_prosa_ao_redor_conta_so_violacao_de_formato():
    resposta_com_prosa = (
        'Claro, aqui esta a classificacao: '
        '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
    )

    resultado = avaliar(
        resposta_bruta=resposta_com_prosa,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.veredito_de_forma == "violacao_de_formato"


def test_justificativa_parafraseada_nao_conta_como_ancorada():
    resposta = (
        '{"rotulo": "cancelamento", '
        '"justificativa": "o cliente quer encerrar a assinatura"}'
    )

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.alucinacao_justificativa_nao_ancorada is True


def test_rotulo_comparado_apos_aparar_espacos_mas_maiuscula_conta_diferenca():
    resposta = '{"rotulo": "  cancelamento", "justificativa": "quero cancelar o meu plano"}'

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert resultado.erro_de_acerto is False


def test_rotulo_com_maiuscula_diferente_conta_como_rotulo_diferente():
    resposta = '{"rotulo": "Cancelamento", "justificativa": "quero cancelar o meu plano"}'

    resultado = avaliar(
        resposta_bruta=resposta,
        rotulo_esperado="cancelamento",
        transcricao=TRANSCRICAO,
        rotulos_validos=ROTULOS_VALIDOS,
    )

    # "Cancelamento" (maiúscula) não está na lista fechada (case-sensitive) -> rótulo inexistente.
    assert resultado.alucinacao_rotulo_inexistente is True

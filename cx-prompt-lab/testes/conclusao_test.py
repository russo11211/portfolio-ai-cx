"""Testes da Conclusão (T10): contagens calculadas à mão, uma por caso da regra."""

from cx_prompt_lab.conclusao import CondicoesExecucao, concluir
from cx_prompt_lab.executor import Contagens

MESMAS = CondicoesExecucao(modelo="m", parametros={"temperature": 0.2, "max_tokens": 500})


def _reps(aluc, formato=None, acertos=None):
    formato = formato or [0] * len(aluc)
    acertos = acertos or [10] * len(aluc)
    return [
        Contagens(alucinacao_total=a, violacao_de_formato=f, acertos=c)
        for a, f, c in zip(aluc, formato, acertos)
    ]


def _resultado(v0, final, cond_v0=MESMAS, cond_final=MESMAS):
    return concluir(v0, final, cond_v0, cond_final).resultado


def test_nao_comparavel_por_modelo_mostra_a_diferenca():
    outro = CondicoesExecucao(modelo="outro", parametros=MESMAS.parametros)
    veredito = concluir(_reps([5, 6, 7]), _reps([0, 0, 0]), MESMAS, outro)
    assert veredito.resultado == "nao_comparavel"
    assert any("modelo" in d and "m" in d and "outro" in d for d in veredito.diferencas)


def test_nao_comparavel_por_parametros():
    outro = CondicoesExecucao(modelo="m", parametros={"temperature": 1.0, "max_tokens": 500})
    veredito = concluir(_reps([5, 6, 7]), _reps([0, 0, 0]), MESMAS, outro)
    assert veredito.resultado == "nao_comparavel"
    assert any("temperature" in d for d in veredito.diferencas)


def test_parametro_fora_de_temperature_e_max_tokens_nao_torna_nao_comparavel():
    com_timeout = CondicoesExecucao(
        modelo="m", parametros={"temperature": 0.2, "max_tokens": 500, "timeout_s": 99}
    )
    assert _resultado(_reps([5, 6, 7]), _reps([2, 3, 3]), MESMAS, com_timeout) == "melhora"


def test_nao_comparavel_por_max_tokens():
    outro = CondicoesExecucao(modelo="m", parametros={"temperature": 0.2, "max_tokens": 900})
    assert _resultado(_reps([5, 6, 7]), _reps([0, 0, 0]), MESMAS, outro) == "nao_comparavel"


def test_melhora_queda_de_2_em_todas_as_repeticoes():
    # min v0 = 5, max final = 3 -> 2 >= 2
    assert _resultado(_reps([5, 6, 7]), _reps([2, 3, 3])) == "melhora"


def test_queda_de_1_transcricao_e_inconclusivo():
    # min v0 = 5, max final = 4 -> 1 < 2
    assert _resultado(_reps([5, 6, 7]), _reps([2, 3, 4])) == "inconclusivo"


def test_queda_de_2_em_uma_so_repeticao_e_inconclusivo():
    # soma 15 < 18 (sem piora), mas min v0 5 - max final 6 = -1
    assert _resultado(_reps([5, 6, 7]), _reps([3, 6, 6])) == "inconclusivo"


def test_violacao_de_formato_que_aumenta_impede_melhora():
    final = _reps([2, 3, 3], formato=[0, 1, 0])
    assert _resultado(_reps([5, 6, 7]), final) == "inconclusivo"


def test_guarda_de_acuracia_que_falha_impede_melhora():
    # Alucinação cai 2, mas acertos caem de 10 para 9
    final = _reps([2, 3, 3], acertos=[9, 9, 9])
    assert _resultado(_reps([5, 6, 7]), final) == "inconclusivo"


def test_efeito_piso_e_inconclusivo_por_efeito_piso():
    # v0 tem uma Repetição com Alucinação total <= 1; sem piora (6*3 <= 8*3)
    assert _resultado(_reps([1, 3, 4]), _reps([0, 1, 1])) == "inconclusivo_efeito_piso"


def test_piora():
    # soma final 9 * 3 reps v0 = 27 > soma v0 6 * 3 reps final = 18
    assert _resultado(_reps([2, 2, 2]), _reps([3, 3, 3])) == "piora"


def test_efeito_piso_e_piora_ao_mesmo_tempo_vence_a_piora():
    assert _resultado(_reps([1, 1, 1]), _reps([2, 2, 2])) == "piora"


def test_repeticoes_com_variacao_zero():
    assert _resultado(_reps([5, 5, 5]), _reps([3, 3, 3])) == "melhora"


def test_repeticoes_em_numero_desigual_melhora():
    # 3 Repetições em v0, 4 na final; piora: 12*3=36 > 15*4=60? não
    assert _resultado(_reps([5, 5, 5]), _reps([3, 3, 3, 3])) == "melhora"


def test_repeticoes_em_numero_desigual_piora_por_multiplicacao_cruzada():
    # v0 [4,4,4] soma 12; final [4,4,4,5] soma 17; 17*3=51 > 12*4=48
    assert _resultado(_reps([4, 4, 4]), _reps([4, 4, 4, 5])) == "piora"

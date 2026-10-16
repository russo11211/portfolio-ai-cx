from math import comb

import pytest

from cx_prompt_lab import estatistica
from cx_prompt_lab.estatistica import binomial_bicaudal, bootstrap_por_transcricao, taxa

# Alias: um nome que começa com "test" no módulo seria coletado pelo pytest.
sinal = estatistica.teste_do_sinal


def test_binomial_bicaudal_bate_com_calculo_a_mao():
    # 2 de 10 sob p=0,5: 2 * (C(10,0)+C(10,1)+C(10,2)) / 2^10 = 2 * 56 / 1024
    assert binomial_bicaudal(2, 10) == pytest.approx(112 / 1024)
    # simétrico
    assert binomial_bicaudal(8, 10) == binomial_bicaudal(2, 10)


def test_binomial_bicaudal_resultado_extremo():
    assert binomial_bicaudal(0, 15) == pytest.approx(2 / 2**15)
    assert binomial_bicaudal(15, 15) == pytest.approx(2 / 2**15)


def test_binomial_bicaudal_centro_e_vazio_valem_um():
    assert binomial_bicaudal(5, 10) == 1.0
    assert binomial_bicaudal(0, 0) == 1.0


def test_binomial_bicaudal_recusa_k_fora_do_intervalo():
    with pytest.raises(ValueError):
        binomial_bicaudal(11, 10)


def test_teste_do_sinal_conta_favoraveis_e_descarta_empates():
    base = [3, 2, 0, 1, 5]
    candidata = [0, 2, 1, 0, 1]

    resultado = sinal(base, candidata)

    assert resultado.favoraveis_candidata == 3
    assert resultado.favoraveis_base == 1
    assert resultado.empates == 1
    assert resultado.p_valor == pytest.approx(binomial_bicaudal(3, 4))


def test_teste_do_sinal_tudo_empatado_da_p_um():
    assert sinal([1, 2], [1, 2]).p_valor == 1.0


def test_teste_do_sinal_exige_listas_pareadas():
    with pytest.raises(ValueError):
        sinal([1, 2], [1])


def test_teste_do_sinal_com_doze_a_zero_e_significativo():
    resultado = sinal([3] * 12, [0] * 12)
    assert resultado.p_valor == pytest.approx(2 * comb(12, 0) / 2**12)
    assert resultado.p_valor < 0.001


def test_taxa_divide_por_transcricoes_vezes_repeticoes():
    assert taxa([5, 0, 5, 0], 5) == 0.5


def test_bootstrap_e_reproduzivel_com_a_mesma_semente():
    base = [5, 4, 3, 0, 1, 2, 5, 5]
    candidata = [1, 0, 3, 0, 0, 1, 2, 0]
    a = bootstrap_por_transcricao(base, candidata, 5, reamostras=500, semente=7)
    b = bootstrap_por_transcricao(base, candidata, 5, reamostras=500, semente=7)
    assert a == b


def test_bootstrap_estimativa_e_a_diferenca_observada_e_o_ic_a_contem():
    base = [5, 4, 3, 0, 1, 2, 5, 5]
    candidata = [1, 0, 3, 0, 0, 1, 2, 0]

    ic = bootstrap_por_transcricao(base, candidata, 5, reamostras=2000, semente=1)

    assert ic.estimativa == pytest.approx(taxa(candidata, 5) - taxa(base, 5))
    assert ic.inferior <= ic.estimativa <= ic.superior
    assert ic.superior < 0  # efeito claro e consistente: o IC exclui zero


def test_bootstrap_sem_variacao_tem_ic_degenerado():
    ic = bootstrap_por_transcricao([2, 2, 2], [2, 2, 2], 5, reamostras=100, semente=1)
    assert (ic.estimativa, ic.inferior, ic.superior) == (0.0, 0.0, 0.0)


def test_bootstrap_de_uma_versao_so_da_ic_da_taxa():
    ic = bootstrap_por_transcricao([5, 0, 5, 0], None, 5, reamostras=1000, semente=3)
    assert ic.estimativa == 0.5
    assert 0.0 <= ic.inferior <= 0.5 <= ic.superior <= 1.0


def test_bootstrap_recusa_entrada_invalida():
    with pytest.raises(ValueError):
        bootstrap_por_transcricao([], None, 5)
    with pytest.raises(ValueError):
        bootstrap_por_transcricao([1, 2], [1], 5)

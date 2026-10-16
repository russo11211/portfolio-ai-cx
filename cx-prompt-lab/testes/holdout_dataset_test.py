"""O holdout do experimento confirmatório (CAR-23) é separado do Dataset de desenvolvimento
e está congelado nos hashes do pré-registro."""

from collections import Counter
from pathlib import Path

import pytest

from cx_prompt_lab.dataset import carregar
from cx_prompt_lab.gravacao import hash_dataset

RAIZ = Path(__file__).resolve().parent.parent
DEV = RAIZ / "dataset" / "transcricoes.json"
HOLDOUT = {
    "holdout_a": RAIZ / "dataset" / "holdout_a.json",
    "holdout_b": RAIZ / "dataset" / "holdout_b.json",
}
# Mesmos valores de docs/spec/cx-prompt-lab-preregistro-holdout.md. Mudar o holdout depois
# do pré-registro invalida o experimento; este teste falha se alguém tentar.
HASHES_PREREGISTRADOS = {
    "holdout_a": "775552356466b96063309085e3c902bbcf88f115b636b9ae4052459b37536fa8",
    "holdout_b": "e6d64b422e3d5329d9c197aff5a4fa4c91e9a9ed3e1aac2080fca4fde69054c5",
}


def _normalizado(texto: str) -> str:
    return " ".join(texto.lower().split())


@pytest.mark.parametrize("nome", sorted(HOLDOUT))
def test_holdout_passa_na_validacao_e_esta_equilibrado(nome):
    dataset = carregar(HOLDOUT[nome])

    assert len(dataset.transcricoes) == 30
    contagem = Counter(t.rotulo_esperado for t in dataset.transcricoes)
    assert set(contagem) == set(dataset.rotulos_validos)
    assert set(contagem.values()) == {5}
    assert sum(t.intencao_dupla for t in dataset.transcricoes) == 6
    assert sum(t.ambiguo for t in dataset.transcricoes) == 6


@pytest.mark.parametrize("nome", sorted(HOLDOUT))
def test_holdout_congelado_no_hash_preregistrado(nome):
    assert hash_dataset(carregar(HOLDOUT[nome])) == HASHES_PREREGISTRADOS[nome]


def test_holdout_usa_os_mesmos_rotulos_e_regra_do_desenvolvimento():
    dev = carregar(DEV)
    for caminho in HOLDOUT.values():
        holdout = carregar(caminho)
        assert holdout.rotulos_validos == dev.rotulos_validos
        assert holdout.regra_desempate == dev.regra_desempate


def test_nenhuma_transcricao_repete_entre_desenvolvimento_e_holdout():
    conjuntos = [carregar(DEV)] + [carregar(c) for c in HOLDOUT.values()]
    textos = [_normalizado(t.texto) for d in conjuntos for t in d.transcricoes]
    ids = [t.id for d in conjuntos for t in d.transcricoes]

    assert len(textos) == len(set(textos))
    assert len(ids) == len(set(ids))


def test_nenhuma_transcricao_do_holdout_aparece_nos_prompts():
    prompts = [_normalizado(p.read_text(encoding="utf-8")) for p in (RAIZ / "prompts").glob("*.md")]
    for caminho in HOLDOUT.values():
        for transcricao in carregar(caminho).transcricoes:
            corpo = _normalizado(transcricao.texto.split("Cliente:", 1)[-1])
            assert not any(corpo in prompt for prompt in prompts), transcricao.id

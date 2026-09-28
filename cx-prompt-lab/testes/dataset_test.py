import json
from pathlib import Path

import pytest

from cx_prompt_lab.dataset import (
    MAXIMO_TRANSCRICOES,
    MINIMO_TRANSCRICOES,
    RecusaDataset,
    carregar,
)

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_DATASET_REAL = RAIZ_PROJETO / "dataset" / "transcricoes.json"


def _dado_valido_minimo() -> dict:
    rotulos = ["cancelamento", "duvida", "reclamacao"]
    transcricoes = []
    for i in range(MINIMO_TRANSCRICOES):
        rotulo = rotulos[i % len(rotulos)]
        transcricoes.append(
            {
                "id": f"t{i:02d}",
                "texto": f"Transcrição fictícia número {i} sobre {rotulo}.",
                "rotulo_esperado": rotulo,
            }
        )
    # ao menos um caso de intenção dupla, marcado
    transcricoes[0]["intencao_dupla"] = True
    transcricoes[0]["ambiguo"] = True
    return {
        "rotulos_validos": rotulos,
        "regra_desempate": "Vale a intenção verbalizada primeiro no texto.",
        "transcricoes": transcricoes,
    }


def _escrever(tmp_path: Path, dado: dict) -> Path:
    caminho = tmp_path / "transcricoes.json"
    caminho.write_text(json.dumps(dado, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def test_carrega_dataset_valido_minimo(tmp_path):
    caminho = _escrever(tmp_path, _dado_valido_minimo())

    dataset = carregar(caminho)

    assert len(dataset.transcricoes) == MINIMO_TRANSCRICOES
    assert dataset.regra_desempate.strip() != ""


def test_recusa_ids_duplicados(tmp_path):
    dado = _dado_valido_minimo()
    dado["transcricoes"][1]["id"] = dado["transcricoes"][0]["id"]
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match="[Dd]uplicad"):
        carregar(caminho)


def test_recusa_rotulo_fora_da_lista_fechada(tmp_path):
    dado = _dado_valido_minimo()
    dado["transcricoes"][0]["rotulo_esperado"] = "rotulo_inexistente"
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match="fora da lista"):
        carregar(caminho)


def test_recusa_menos_de_20_transcricoes(tmp_path):
    dado = _dado_valido_minimo()
    dado["transcricoes"] = dado["transcricoes"][:-1]
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match=str(MINIMO_TRANSCRICOES)):
        carregar(caminho)


def test_recusa_mais_de_30_transcricoes(tmp_path):
    dado = _dado_valido_minimo()
    rotulos = dado["rotulos_validos"]
    for i in range(MINIMO_TRANSCRICOES, MAXIMO_TRANSCRICOES + 1):
        rotulo = rotulos[i % len(rotulos)]
        dado["transcricoes"].append(
            {"id": f"t{i:02d}", "texto": f"Transcrição extra {i}.", "rotulo_esperado": rotulo}
        )
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match=str(MAXIMO_TRANSCRICOES)):
        carregar(caminho)


def test_recusa_rotulo_da_lista_sem_nenhuma_transcricao(tmp_path):
    dado = _dado_valido_minimo()
    dado["rotulos_validos"].append("rotulo_orfao")
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match="rotulo_orfao"):
        carregar(caminho)


def test_recusa_regra_desempate_ausente(tmp_path):
    dado = _dado_valido_minimo()
    dado["regra_desempate"] = "   "
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match="desempate"):
        carregar(caminho)


def test_recusa_sem_nenhum_caso_de_intencao_dupla(tmp_path):
    dado = _dado_valido_minimo()
    for t in dado["transcricoes"]:
        t["intencao_dupla"] = False
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match="intenção dupla"):
        carregar(caminho)


def test_recusa_sem_nenhum_caso_ambiguo(tmp_path):
    dado = _dado_valido_minimo()
    for t in dado["transcricoes"]:
        t["ambiguo"] = False
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match="ambígu"):
        carregar(caminho)


def test_recusa_arquivo_inexistente(tmp_path):
    with pytest.raises(RecusaDataset, match="não encontrado"):
        carregar(tmp_path / "nao-existe.json")


def test_recusa_json_invalido(tmp_path):
    caminho = tmp_path / "transcricoes.json"
    caminho.write_text("{ isso nao é json valido", encoding="utf-8")

    with pytest.raises(RecusaDataset, match="não é um JSON válido"):
        carregar(caminho)


def test_recusa_campo_obrigatorio_ausente(tmp_path):
    dado = _dado_valido_minimo()
    del dado["transcricoes"][0]["rotulo_esperado"]
    caminho = _escrever(tmp_path, dado)

    with pytest.raises(RecusaDataset, match="campo obrigatório ausente"):
        carregar(caminho)


def test_dataset_real_carrega_e_passa_na_validacao():
    dataset = carregar(CAMINHO_DATASET_REAL)

    assert MINIMO_TRANSCRICOES <= len(dataset.transcricoes) <= MAXIMO_TRANSCRICOES
    ids = [t.id for t in dataset.transcricoes]
    assert len(ids) == len(set(ids))
    rotulos_cobertos = {t.rotulo_esperado for t in dataset.transcricoes}
    assert rotulos_cobertos == set(dataset.rotulos_validos)
    assert any(t.intencao_dupla for t in dataset.transcricoes)
    assert any(t.ambiguo for t in dataset.transcricoes)
    assert dataset.regra_desempate.strip() != ""


def test_nenhuma_transcricao_do_dataset_aparece_em_exemplo_de_prompt():
    dataset = carregar(CAMINHO_DATASET_REAL)
    diretorio_prompts = RAIZ_PROJETO / "prompts"
    arquivos_prompt = sorted(diretorio_prompts.glob("*.md")) if diretorio_prompts.exists() else []

    vazamentos = []
    for caminho_prompt in arquivos_prompt:
        texto_prompt = caminho_prompt.read_text(encoding="utf-8")
        for transcricao in dataset.transcricoes:
            if transcricao.texto in texto_prompt:
                vazamentos.append((caminho_prompt.name, transcricao.id))

    assert vazamentos == []

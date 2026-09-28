import json

import pytest

from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.executor import rodar
from cx_prompt_lab.gravacao import ProviderGravador, gravar, hash_texto
from cx_prompt_lab.provider import RespostaProvider
from cx_prompt_lab.replay import RecusaReplay, substituir

ROTULOS_VALIDOS = ["cancelamento", "duvida", "reclamacao"]

RESPOSTA_CORRETA = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
RESPOSTA_ERRADA = '{"rotulo": "duvida", "justificativa": "quero cancelar o meu plano"}'
RESPOSTA_QUEBRADA = "isto nao e json"


class FakeProvider:
    def __init__(self, respostas: list[str]):
        self._respostas = respostas
        self._indice = 0
        self.chamadas_reais = 0

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        self.chamadas_reais += 1
        texto = self._respostas[self._indice]
        self._indice += 1
        return RespostaProvider(texto=texto, motivo_parada="fim_normal", modelo="fake-model", temperatura=0.2)


def _dataset() -> Dataset:
    return Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Cliente quer cancelar o plano.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Cliente tem uma duvida sobre a fatura.", rotulo_esperado="duvida"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )


def _gravar_rodada_de_exemplo(tmp_path, dataset, prompt_texto="v0", rodada_id="rodada-1", repeticoes=3):
    respostas = [RESPOSTA_CORRETA, RESPOSTA_ERRADA] * repeticoes
    fake = FakeProvider(respostas)
    gravador = ProviderGravador(
        provider=fake,
        dataset=dataset,
        rodada_id=rodada_id,
        hash_prompt=hash_texto(prompt_texto),
    )

    rodada_original = rodar(
        versao_prompt=prompt_texto, dataset=dataset, provider=gravador, repeticoes=repeticoes
    )

    gravar(
        diretorio_rodadas=tmp_path,
        rodada_id=rodada_id,
        versao_prompt=prompt_texto,
        prompt_texto=prompt_texto,
        dataset=dataset,
        chamadas=gravador.chamadas,
        repeticoes=repeticoes,
        parametros_efetivos={"temperature": 0.2},
    )

    return rodada_original, fake


def test_replay_reproduz_as_mesmas_contagens_da_rodada_original_e_nao_chama_provider(tmp_path):
    dataset = _dataset()
    rodada_original, fake = _gravar_rodada_de_exemplo(tmp_path, dataset)
    chamadas_antes = fake.chamadas_reais

    rodada_replay = substituir(
        caminho_rodada=tmp_path / "rodada-1",
        dataset=dataset,
        prompt_texto="v0",
        repeticoes=3,
    )

    assert fake.chamadas_reais == chamadas_antes  # nenhum provider real foi chamado
    assert len(rodada_replay.contagens_por_repeticao) == len(rodada_original.contagens_por_repeticao)
    for original, replay in zip(rodada_original.contagens_por_repeticao, rodada_replay.contagens_por_repeticao):
        assert replay == original


def test_replay_recusa_prompt_divergente(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)

    with pytest.raises(RecusaReplay, match="hash esperado"):
        substituir(
            caminho_rodada=tmp_path / "rodada-1",
            dataset=dataset,
            prompt_texto="v0 alterado depois da gravacao",
            repeticoes=3,
        )


def test_replay_recusa_dataset_divergente(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)

    dataset_alterado = Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Cliente quer cancelar o plano JA.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Cliente tem uma duvida sobre a fatura.", rotulo_esperado="duvida"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )

    with pytest.raises(RecusaReplay, match="hash esperado"):
        substituir(
            caminho_rodada=tmp_path / "rodada-1",
            dataset=dataset_alterado,
            prompt_texto="v0",
            repeticoes=3,
        )


def _ler_manifesto(diretorio_rodada):
    return json.loads((diretorio_rodada / "manifest.json").read_text(encoding="utf-8"))


def _escrever_manifesto(diretorio_rodada, manifesto):
    (diretorio_rodada / "manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")


def test_replay_recusa_versao_de_esquema_desconhecida(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    manifesto = _ler_manifesto(diretorio_rodada)
    manifesto["versao_esquema"] = 999
    _escrever_manifesto(diretorio_rodada, manifesto)

    with pytest.raises(RecusaReplay, match="esquema"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_rodada_nao_completa(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    manifesto = _ler_manifesto(diretorio_rodada)
    manifesto["estado"] = "iniciada"
    _escrever_manifesto(diretorio_rodada, manifesto)

    with pytest.raises(RecusaReplay, match="completa"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_chamada_faltando(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    arquivos_chamada = [p for p in diretorio_rodada.glob("*.json") if p.name != "manifest.json"]
    arquivos_chamada[0].unlink()

    with pytest.raises(RecusaReplay, match="faltando"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_chamada_extra(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    arquivos_chamada = [p for p in diretorio_rodada.glob("*.json") if p.name != "manifest.json"]
    dado = json.loads(arquivos_chamada[0].read_text(encoding="utf-8"))
    dado["repeticao"] = 99
    (diretorio_rodada / "extra.json").write_text(json.dumps(dado), encoding="utf-8")

    with pytest.raises(RecusaReplay, match="extra"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_chamada_duplicada(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    arquivos_chamada = [p for p in diretorio_rodada.glob("*.json") if p.name != "manifest.json"]
    conteudo = arquivos_chamada[0].read_text(encoding="utf-8")
    (diretorio_rodada / "duplicata.json").write_text(conteudo, encoding="utf-8")

    with pytest.raises(RecusaReplay, match="duplicada"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_chamada_corrompida_arquivo_truncado(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    arquivos_chamada = [p for p in diretorio_rodada.glob("*.json") if p.name != "manifest.json"]
    conteudo = arquivos_chamada[0].read_text(encoding="utf-8")
    arquivos_chamada[0].write_text(conteudo[: len(conteudo) // 2], encoding="utf-8")

    with pytest.raises(RecusaReplay, match="corrompida"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_versao_de_ferramenta_com_major_diferente(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    manifesto = _ler_manifesto(diretorio_rodada)
    manifesto["ferramenta_versao"] = "9.0.0"
    _escrever_manifesto(diretorio_rodada, manifesto)

    with pytest.raises(RecusaReplay, match="git checkout"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_chamada_com_identidade_de_rodada_trocada(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    arquivos_chamada = [p for p in diretorio_rodada.glob("*.json") if p.name != "manifest.json"]
    dado = json.loads(arquivos_chamada[0].read_text(encoding="utf-8"))
    dado["rodada_id"] = "rodada-de-outro-experimento"
    arquivos_chamada[0].write_text(json.dumps(dado), encoding="utf-8")

    with pytest.raises(RecusaReplay, match="identidade"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_transcricao_fora_do_dataset(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    arquivos_chamada = [p for p in diretorio_rodada.glob("*.json") if p.name != "manifest.json"]
    dado = json.loads(arquivos_chamada[0].read_text(encoding="utf-8"))
    dado["transcricao_id"] = "t-inexistente"
    arquivos_chamada[0].write_text(json.dumps(dado), encoding="utf-8")

    with pytest.raises(RecusaReplay, match="fora do Dataset"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_replay_recusa_menos_de_3_repeticoes(tmp_path):
    # Uma Rodada gravada com só 2 Repetições (a gravação em si não impõe o
    # piso; quem impõe é o Executor, que o Replay reusa) precisa ser recusada
    # pelo Replay ao recalcular, não silenciosamente aceita.
    from cx_prompt_lab.gravacao import Chamada, gravar, hash_texto

    dataset = _dataset()
    prompt_texto = "v0"
    hash_prompt = hash_texto(prompt_texto)
    chamadas = [
        Chamada(
            rodada_id="rodada-2-repeticoes",
            hash_prompt=hash_prompt,
            transcricao_id=t.id,
            repeticao=r,
            modelo="fake-model",
            motivo_parada="fim_normal",
            temperatura=0.2,
            max_tokens=None,
            resposta=RESPOSTA_CORRETA,
        )
        for r in (1, 2)
        for t in dataset.transcricoes
    ]
    gravar(
        diretorio_rodadas=tmp_path,
        rodada_id="rodada-2-repeticoes",
        versao_prompt=prompt_texto,
        prompt_texto=prompt_texto,
        dataset=dataset,
        chamadas=chamadas,
        repeticoes=2,
        parametros_efetivos={},
    )

    with pytest.raises(ValueError, match="repeticoes"):
        substituir(
            caminho_rodada=tmp_path / "rodada-2-repeticoes",
            dataset=dataset,
            prompt_texto=prompt_texto,
            repeticoes=2,
        )


def test_toda_mensagem_de_recusa_segue_o_formato_fixo_da_adr(tmp_path):
    dataset = _dataset()
    _gravar_rodada_de_exemplo(tmp_path, dataset)
    diretorio_rodada = tmp_path / "rodada-1"

    manifesto = _ler_manifesto(diretorio_rodada)
    manifesto["estado"] = "iniciada"
    _escrever_manifesto(diretorio_rodada, manifesto)

    with pytest.raises(RecusaReplay) as excinfo:
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)

    mensagem = str(excinfo.value)
    assert mensagem.startswith("Recusa:")
    assert "ação: reexecute com 'reexecutar' ou restaure o commit" in mensagem
    assert "link:" in mensagem

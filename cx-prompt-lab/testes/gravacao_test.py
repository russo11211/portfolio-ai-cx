import pytest

from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.executor import AbortoRodada, rodar
from cx_prompt_lab.gravacao import (
    ESTADO_ABORTADA,
    Chamada,
    ProviderGravador,
    RecusaGravacao,
    gravar,
    hash_dataset,
    hash_texto,
)
from cx_prompt_lab.provider import ErroProvider, RespostaProvider
from cx_prompt_lab.replay import RecusaReplay, substituir

ROTULOS_VALIDOS = ["cancelamento", "duvida", "reclamacao"]


class FakeProvider:
    def __init__(self, respostas: list[str]):
        self._respostas = respostas
        self._indice = 0

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        texto = self._respostas[self._indice]
        self._indice += 1
        return RespostaProvider(texto=texto, motivo_parada="fim_normal", modelo="fake-model", temperatura=0.2)


def _dataset_duas_transcricoes() -> Dataset:
    return Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Cliente quer cancelar o plano.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Cliente tem uma duvida sobre a fatura.", rotulo_esperado="duvida"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )


RESPOSTA = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'


def test_provider_gravador_registra_uma_chamada_por_transcricao_e_repeticao():
    dataset = _dataset_duas_transcricoes()
    fake = FakeProvider([RESPOSTA] * 6)
    gravador = ProviderGravador(
        provider=fake,
        dataset=dataset,
        rodada_id="rodada-1",
        hash_prompt=hash_texto("v0"),
    )

    rodar(versao_prompt="v0", dataset=dataset, provider=gravador, repeticoes=3)

    assert len(gravador.chamadas) == 6
    assert all(c.rodada_id == "rodada-1" for c in gravador.chamadas)


def test_provider_gravador_conta_repeticao_por_transcricao_nao_por_ordem_global():
    dataset = _dataset_duas_transcricoes()
    fake = FakeProvider([RESPOSTA] * 6)
    gravador = ProviderGravador(
        provider=fake,
        dataset=dataset,
        rodada_id="rodada-1",
        hash_prompt=hash_texto("v0"),
    )

    rodar(versao_prompt="v0", dataset=dataset, provider=gravador, repeticoes=3)

    repeticoes_t1 = sorted(c.repeticao for c in gravador.chamadas if c.transcricao_id == "t1")
    repeticoes_t2 = sorted(c.repeticao for c in gravador.chamadas if c.transcricao_id == "t2")
    assert repeticoes_t1 == [1, 2, 3]
    assert repeticoes_t2 == [1, 2, 3]


def test_chamada_gravada_nao_contem_credencial_ou_cabecalho_de_autenticacao():
    chamada = Chamada(
        rodada_id="rodada-1",
        hash_prompt="abc",
        transcricao_id="t1",
        repeticao=1,
        modelo="fake-model",
        motivo_parada="fim_normal",
        temperatura=0.2,
        max_tokens=256,
        resposta=RESPOSTA,
        criado_em="2026-09-28T10:00:00Z",
    )

    dado = chamada.para_dict()

    proibidos = {"authorization", "api_key", "apikey", "header", "headers", "token", "credential", "credencial"}
    assert not (set(dado.keys()) & proibidos)


def _chamadas_para_dataset(dataset: Dataset, hash_prompt: str, rodada_id: str, repeticoes: int) -> list[Chamada]:
    chamadas = []
    for r in range(1, repeticoes + 1):
        for t in dataset.transcricoes:
            chamadas.append(
                Chamada(
                    rodada_id=rodada_id,
                    hash_prompt=hash_prompt,
                    transcricao_id=t.id,
                    repeticao=r,
                    modelo="fake-model",
                    motivo_parada="fim_normal",
                    temperatura=0.2,
                    max_tokens=256,
                    resposta=RESPOSTA,
                    criado_em="2026-09-28T10:00:00Z",
                )
            )
    return chamadas


def test_gravar_escreve_manifesto_e_um_arquivo_por_chamada(tmp_path):
    dataset = _dataset_duas_transcricoes()
    hash_prompt = hash_texto("v0")
    chamadas = _chamadas_para_dataset(dataset, hash_prompt, "rodada-1", repeticoes=3)

    manifesto = gravar(
        diretorio_rodadas=tmp_path,
        rodada_id="rodada-1",
        versao_prompt="v0",
        prompt_texto="v0",
        dataset=dataset,
        chamadas=chamadas,
        repeticoes=3,
        parametros_efetivos={"temperature": 0.2, "max_tokens": 256},
    )

    diretorio_rodada = tmp_path / "rodada-1"
    arquivos = sorted(p.name for p in diretorio_rodada.glob("*.json"))
    assert "manifest.json" in arquivos
    assert len(arquivos) == 1 + 6  # manifesto + 2 transcricoes * 3 repeticoes

    assert manifesto.estado == "completa"
    assert manifesto.numero_esperado_chamadas == 6
    assert manifesto.hash_prompt == hash_prompt
    assert manifesto.hash_dataset == hash_dataset(dataset)


def test_gravar_recusa_sobrescrever_rodada_existente(tmp_path):
    dataset = _dataset_duas_transcricoes()
    hash_prompt = hash_texto("v0")
    chamadas = _chamadas_para_dataset(dataset, hash_prompt, "rodada-1", repeticoes=3)

    gravar(
        diretorio_rodadas=tmp_path,
        rodada_id="rodada-1",
        versao_prompt="v0",
        prompt_texto="v0",
        dataset=dataset,
        chamadas=chamadas,
        repeticoes=3,
        parametros_efetivos={},
    )

    with pytest.raises(RecusaGravacao):
        gravar(
            diretorio_rodadas=tmp_path,
            rodada_id="rodada-1",
            versao_prompt="v0",
            prompt_texto="v0",
            dataset=dataset,
            chamadas=chamadas,
            repeticoes=3,
            parametros_efetivos={},
        )


def test_gravar_recusa_quando_chamadas_nao_batem_com_o_esperado_e_nao_publica_nada(tmp_path):
    dataset = _dataset_duas_transcricoes()
    hash_prompt = hash_texto("v0")
    chamadas_incompletas = _chamadas_para_dataset(dataset, hash_prompt, "rodada-1", repeticoes=3)[:-1]

    with pytest.raises(RecusaGravacao):
        gravar(
            diretorio_rodadas=tmp_path,
            rodada_id="rodada-1",
            versao_prompt="v0",
            prompt_texto="v0",
            dataset=dataset,
            chamadas=chamadas_incompletas,
            repeticoes=3,
            parametros_efetivos={},
        )

    assert not (tmp_path / "rodada-1").exists()
    assert list(tmp_path.glob("*")) == []


class ProviderComErroNaSegundaChamada:
    def __init__(self):
        self.chamadas = 0

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        self.chamadas += 1
        if self.chamadas == 1:
            return RespostaProvider(texto=RESPOSTA, motivo_parada="fim_normal", modelo="fake-model", temperatura=0.2)
        raise ErroProvider("erro HTTP 500", causa_provavel="provider instável")


def test_rodada_abortada_grava_manifesto_com_estado_abortada_e_replay_a_recusa(tmp_path):
    dataset = _dataset_duas_transcricoes()
    hash_prompt = hash_texto("v0")
    provider_falho = ProviderComErroNaSegundaChamada()
    gravador = ProviderGravador(
        provider=provider_falho,
        dataset=dataset,
        rodada_id="rodada-abortada",
        hash_prompt=hash_prompt,
    )

    with pytest.raises(AbortoRodada):
        rodar(
            versao_prompt="v0",
            dataset=dataset,
            provider=gravador,
            repeticoes=3,
            rodada_id="rodada-abortada",
        )

    # a Chamada que teve sucesso antes do erro foi gravada pelo ProviderGravador
    assert len(gravador.chamadas) == 1

    manifesto = gravar(
        diretorio_rodadas=tmp_path,
        rodada_id="rodada-abortada",
        versao_prompt="v0",
        prompt_texto="v0",
        dataset=dataset,
        chamadas=gravador.chamadas,
        repeticoes=3,
        parametros_efetivos={},
        estado=ESTADO_ABORTADA,
    )

    assert manifesto.estado == ESTADO_ABORTADA

    diretorio_rodada = tmp_path / "rodada-abortada"
    arquivos_chamada = [p for p in diretorio_rodada.glob("*.json") if p.name != "manifest.json"]
    assert len(arquivos_chamada) == 1  # só a Chamada concluída antes do aborto

    with pytest.raises(RecusaReplay, match="não está completa"):
        substituir(caminho_rodada=diretorio_rodada, dataset=dataset, prompt_texto="v0", repeticoes=3)


def test_provider_gravador_registra_criado_em_usando_o_relogio_injetado():
    dataset = _dataset_duas_transcricoes()
    fake = FakeProvider([RESPOSTA] * 6)
    marcas = iter(f"2026-09-28T10:00:{i:02d}Z" for i in range(6))
    gravador = ProviderGravador(
        provider=fake,
        dataset=dataset,
        rodada_id="rodada-1",
        hash_prompt=hash_texto("v0"),
        relogio=lambda: next(marcas),
    )

    rodar(versao_prompt="v0", dataset=dataset, provider=gravador, repeticoes=3)

    assert [c.criado_em for c in gravador.chamadas] == [
        f"2026-09-28T10:00:{i:02d}Z" for i in range(6)
    ]


def test_hash_dataset_muda_quando_conteudo_do_dataset_muda():
    dataset_a = _dataset_duas_transcricoes()
    dataset_b = Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Cliente quer cancelar o plano AGORA.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Cliente tem uma duvida sobre a fatura.", rotulo_esperado="duvida"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )

    assert hash_dataset(dataset_a) != hash_dataset(dataset_b)

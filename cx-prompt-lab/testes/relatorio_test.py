from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.executor import rodar
from cx_prompt_lab.gravacao import ESTADO_ABORTADA, ProviderGravador, gravar, hash_texto
from cx_prompt_lab.provider import RespostaProvider
from cx_prompt_lab.relatorio import coletar_resumos, gerar_relatorio

ROTULOS_VALIDOS = ["cancelamento", "duvida", "reclamacao"]

RESPOSTA_CORRETA = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
RESPOSTA_ERRADA = '{"rotulo": "duvida", "justificativa": "quero cancelar o meu plano"}'


class FakeProvider:
    def __init__(self, respostas: list[str], modelo: str = "fake-model"):
        self._respostas = respostas
        self._indice = 0
        self._modelo = modelo

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        texto = self._respostas[self._indice]
        self._indice += 1
        return RespostaProvider(texto=texto, motivo_parada="fim_normal", modelo=self._modelo, temperatura=0.2)


def _dataset() -> Dataset:
    return Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Cliente quer cancelar o plano.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Cliente tem uma duvida sobre a fatura.", rotulo_esperado="duvida"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )


def _prompts_por_versao(textos: dict[str, str]):
    def carregar(versao: str) -> str:
        return textos[versao]

    return carregar


def _gravar_rodada_completa(tmp_path, dataset, prompt_texto, rodada_id, repeticoes=3, modelo="fake-model"):
    respostas = [RESPOSTA_CORRETA, RESPOSTA_ERRADA] * repeticoes
    fake = FakeProvider(respostas, modelo=modelo)
    gravador = ProviderGravador(
        provider=fake,
        dataset=dataset,
        rodada_id=rodada_id,
        hash_prompt=hash_texto(prompt_texto),
    )
    rodar(versao_prompt=prompt_texto, dataset=dataset, provider=gravador, repeticoes=repeticoes)
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


def test_relatorio_reproduz_contagens_sem_chamar_provider(tmp_path):
    dataset = _dataset()
    _gravar_rodada_completa(tmp_path, dataset, "v0", "rodada-v0", repeticoes=3)

    texto = gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({"v0": "v0"}),
    )

    assert "v0" in texto
    assert "Repetição 1" in texto
    assert "Repetição 3" in texto


def test_relatorio_lista_rodada_completa_abortada_experimento_anterior_e_descartada_com_motivo(tmp_path):
    dataset = _dataset()

    # Rodada completa, dentro do experimento (dataset atual).
    _gravar_rodada_completa(tmp_path, dataset, "v0", "rodada-completa", repeticoes=3)

    # Rodada abortada: gravada com estado abortada, Chamadas parciais.
    fake_abortada = FakeProvider([RESPOSTA_CORRETA])
    gravador_abortada = ProviderGravador(
        provider=fake_abortada, dataset=dataset, rodada_id="rodada-abortada", hash_prompt=hash_texto("v0")
    )
    gravador_abortada.chamar(prompt="v0", transcricao=dataset.transcricoes[0].texto)
    gravar(
        diretorio_rodadas=tmp_path,
        rodada_id="rodada-abortada",
        versao_prompt="v0",
        prompt_texto="v0",
        dataset=dataset,
        chamadas=gravador_abortada.chamadas,
        repeticoes=3,
        parametros_efetivos={},
        estado=ESTADO_ABORTADA,
    )

    # Rodada de experimento anterior: dataset diferente.
    dataset_anterior = Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Texto antigo diferente.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Outro texto antigo.", rotulo_esperado="duvida"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )
    _gravar_rodada_completa(tmp_path, dataset_anterior, "v0", "rodada-experimento-anterior", repeticoes=3)

    # Rodada completa, mas descartada.
    _gravar_rodada_completa(tmp_path, dataset, "v0", "rodada-descartada", repeticoes=3)
    diretorio_descartadas = tmp_path / "descartadas"
    diretorio_descartadas.mkdir()
    (tmp_path / "rodada-descartada").rename(diretorio_descartadas / "rodada-descartada")

    resumos = coletar_resumos(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({"v0": "v0"}),
    )
    por_id = {r.id: r for r in resumos}

    assert set(por_id) == {
        "rodada-completa",
        "rodada-abortada",
        "rodada-experimento-anterior",
        "rodada-descartada",
    }

    assert por_id["rodada-completa"].no_experimento is True

    assert por_id["rodada-abortada"].no_experimento is False
    assert "abortada" in por_id["rodada-abortada"].motivo_fora

    assert por_id["rodada-experimento-anterior"].no_experimento is False
    assert "outro experimento" in por_id["rodada-experimento-anterior"].motivo_fora

    assert por_id["rodada-descartada"].no_experimento is False
    assert por_id["rodada-descartada"].descartada is True
    assert "descartada" in por_id["rodada-descartada"].motivo_fora

    texto = gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({"v0": "v0"}),
    )
    for rodada_id in por_id:
        assert rodada_id in texto
    assert "fora do experimento" in texto


def test_relatorio_imprime_modelo_e_data_das_chamadas(tmp_path):
    dataset = _dataset()
    _gravar_rodada_completa(tmp_path, dataset, "v0", "rodada-v0", repeticoes=3, modelo="llama-3.3-70b")

    texto = gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({"v0": "v0"}),
    )

    assert "llama-3.3-70b" in texto
    assert "data das Chamadas" in texto


def test_relatorio_usa_o_criado_em_gravado_na_chamada_nao_o_mtime_do_arquivo(tmp_path):
    # ADR 0002: a data vem do campo `criado_em` gravado em cada Chamada, não do
    # mtime do arquivo (que muda em todo `git clone`/checkout).
    dataset = _dataset()
    respostas = [RESPOSTA_CORRETA, RESPOSTA_ERRADA] * 3
    fake = FakeProvider(respostas)
    marcas = iter(["2020-01-01T00:00:00Z"] * 6)
    gravador = ProviderGravador(
        provider=fake,
        dataset=dataset,
        rodada_id="rodada-v0",
        hash_prompt=hash_texto("v0"),
        relogio=lambda: next(marcas),
    )
    rodar(versao_prompt="v0", dataset=dataset, provider=gravador, repeticoes=3)
    gravar(
        diretorio_rodadas=tmp_path,
        rodada_id="rodada-v0",
        versao_prompt="v0",
        prompt_texto="v0",
        dataset=dataset,
        chamadas=gravador.chamadas,
        repeticoes=3,
        parametros_efetivos={},
    )

    texto = gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({"v0": "v0"}),
    )

    assert "2020-01-01T00:00:00Z" in texto


def test_relatorio_declara_exploratorio_limite_do_replay_e_distincao_com_reexecucao(tmp_path):
    dataset = _dataset()
    _gravar_rodada_completa(tmp_path, dataset, "v0", "rodada-v0", repeticoes=3)

    texto = gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({"v0": "v0"}),
    )

    assert "exploratório" in texto
    assert "Replay" in texto and "Reexecução" in texto
    assert "prova o cálculo" in texto


def test_relatorio_nao_afirma_validacao_contra_anthropic(tmp_path):
    dataset = _dataset()
    _gravar_rodada_completa(tmp_path, dataset, "v0", "rodada-v0", repeticoes=3)

    texto = gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({"v0": "v0"}),
    )

    assert "validado contra a Anthropic" not in texto
    assert "não é validação contra a API oficial" in texto
    assert "Compatível com Anthropic" in texto


def test_relatorio_sem_nenhuma_rodada(tmp_path):
    dataset = _dataset()
    texto = gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({}),
    )
    assert "exploratório" in texto

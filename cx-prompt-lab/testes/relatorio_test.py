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


# --- T10: veredito v0 × versão final e lista de Transcrições que mudaram ---

ANCORADA_CANCELAMENTO = '{"rotulo": "cancelamento", "justificativa": "cancelar o plano"}'
ANCORADA_DUVIDA = '{"rotulo": "duvida", "justificativa": "duvida sobre a fatura"}'
NAO_ANCORADA_CANCELAMENTO = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
NAO_ANCORADA_DUVIDA = '{"rotulo": "duvida", "justificativa": "tenho uma pergunta"}'
INVALIDA = "isto não é JSON"


def _gravar_versao(tmp_path, dataset, versao, rodada_id, repeticoes, modelo="fake-model", temperatura=0.2):
    """`repeticoes` é a lista de respostas por Repetição, uma por Transcrição, na ordem do Dataset."""
    respostas = [r for repeticao in repeticoes for r in repeticao]
    gravador = ProviderGravador(
        provider=FakeProvider(respostas, modelo=modelo),
        dataset=dataset,
        rodada_id=rodada_id,
        hash_prompt=hash_texto(versao),
    )
    rodar(versao_prompt=versao, dataset=dataset, provider=gravador, repeticoes=len(repeticoes))
    gravar(
        diretorio_rodadas=tmp_path,
        rodada_id=rodada_id,
        versao_prompt=versao,
        prompt_texto=versao,
        dataset=dataset,
        chamadas=gravador.chamadas,
        repeticoes=len(repeticoes),
        parametros_efetivos={"temperature": temperatura},
    )


def _relatorio(tmp_path, dataset, versoes):
    return gerar_relatorio(
        diretorio_rodadas=tmp_path,
        dataset=dataset,
        prompt_texto_por_versao=_prompts_por_versao({v: v for v in versoes}),
    )


V0_RUIM = [[NAO_ANCORADA_CANCELAMENTO, NAO_ANCORADA_DUVIDA]] * 3  # Alucinação total 2 por Repetição
V1_BOA = [[ANCORADA_CANCELAMENTO, ANCORADA_DUVIDA]] * 3  # Alucinação total 0 por Repetição


def test_relatorio_imprime_veredito_melhora_e_a_palavra_exploratorio(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V0_RUIM)
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", V1_BOA)

    texto = _relatorio(tmp_path, dataset, ["v0", "v1"])

    assert "Veredito v0 × v1: melhora" in texto
    assert "exploratório" in texto
    assert "Repetição 3: erro de acerto=0, alucinação=2" in texto  # contagens de v0
    assert "Repetição 3: erro de acerto=0, alucinação=0" in texto  # contagens de v1


def test_veredito_so_usa_rodadas_do_experimento_identificado(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V0_RUIM)
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", V1_BOA)
    dataset_anterior = Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Texto antigo diferente.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Outro texto antigo.", rotulo_esperado="duvida"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )
    # Ordena depois de r-v1 e, se entrasse no veredito, viraria "piora" (Alucinação 2 em v1).
    _gravar_versao(tmp_path, dataset_anterior, "v1", "z-anterior", V0_RUIM)

    texto = _relatorio(tmp_path, dataset, ["v0", "v1"])

    assert "Veredito v0 × v1: melhora" in texto
    assert "z-anterior (versão v1, estado completa): fora do experimento" in texto


def test_veredito_nao_comparavel_mostra_a_diferenca(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V0_RUIM)
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", V1_BOA, modelo="outro-modelo")

    texto = _relatorio(tmp_path, dataset, ["v0", "v1"])

    assert "Veredito v0 × v1: não comparável" in texto
    assert "modelo: v0 usou 'fake-model', versão final usou 'outro-modelo'" in texto


def test_pares_intermediarios_sao_informativos_sem_veredito(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V0_RUIM)
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", V1_BOA)
    _gravar_versao(tmp_path, dataset, "v2", "r-v2", V1_BOA)

    texto = _relatorio(tmp_path, dataset, ["v0", "v1", "v2"])

    assert "Veredito v0 × v2: melhora" in texto
    assert "v0 → v1: informativo, sem veredito" in texto
    assert "v1 Repetição 3: erro de acerto=0, alucinação=0, violação de formato=0, acertos=2" in texto
    assert "v1 → v2: informativo, sem veredito" in texto
    assert "Veredito v0 × v1" not in texto
    assert "Veredito v1 × v2" not in texto


def test_sem_versao_final_nao_ha_veredito(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V0_RUIM)

    texto = _relatorio(tmp_path, dataset, ["v0"])

    assert "Veredito: indisponível" in texto


def test_versao_final_e_a_ultima_em_ordem_numerica(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V0_RUIM)
    _gravar_versao(tmp_path, dataset, "v2", "r-v2", V1_BOA)
    _gravar_versao(tmp_path, dataset, "v10", "r-v10", V1_BOA)

    texto = _relatorio(tmp_path, dataset, ["v0", "v2", "v10"])

    assert "Veredito v0 × v10: melhora" in texto


def test_lista_de_mudancas_e_ilustrativa_e_usa_repeticao_1(tmp_path):
    dataset = Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Cliente quer cancelar o plano.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Cliente tem uma duvida sobre a fatura.", rotulo_esperado="duvida"),
            Transcricao(id="t3", texto="Cliente reclama do atendimento.", rotulo_esperado="reclamacao"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )
    reclamacao = '{"rotulo": "reclamacao", "justificativa": "reclama do atendimento"}'
    v0 = [[ANCORADA_CANCELAMENTO, ANCORADA_DUVIDA, reclamacao]] * 3
    v1 = [
        [ANCORADA_DUVIDA, INVALIDA, reclamacao],  # Repetição 1: t1 muda, t2 vira "sem rótulo válido", t3 igual
        [ANCORADA_CANCELAMENTO, ANCORADA_DUVIDA, reclamacao],  # Repetição 2 não entra na lista
        [ANCORADA_CANCELAMENTO, ANCORADA_DUVIDA, reclamacao],
    ]
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", v0)
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", v1)

    texto = _relatorio(tmp_path, dataset, ["v0", "v1"])

    assert "ilustrativa" in texto
    assert "- t1: cancelamento → duvida" in texto
    assert "- t2: duvida → sem rótulo válido" in texto
    secao = texto.split("## Transcrições que mudaram", 1)[1].split("## Todas as Rodadas")[0]
    assert "- t3:" not in secao
    assert "- t1:" in secao and "- t2:" in secao


def test_lista_de_mudancas_de_sem_rotulo_valido_para_rotulo_e_rotulo_inexistente(tmp_path):
    dataset = _dataset()
    inexistente = '{"rotulo": "inventado", "justificativa": "cancelar o plano"}'
    v0 = [[INVALIDA, ANCORADA_DUVIDA]] * 3
    v1 = [[ANCORADA_CANCELAMENTO, inexistente]] * 3
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", v0)
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", v1)

    texto = _relatorio(tmp_path, dataset, ["v0", "v1"])

    assert "- t1: sem rótulo válido → cancelamento" in texto
    assert "- t2: duvida → sem rótulo válido" in texto


def test_piora_e_efeito_piso_aparecem_no_texto_do_relatorio(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V1_BOA)  # Alucinação 0 por Repetição
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", V0_RUIM)  # Alucinação 2 por Repetição

    texto = _relatorio(tmp_path, dataset, ["v0", "v1"])

    assert "Veredito v0 × v1: piora" in texto  # 6*3 > 0*3 vence o efeito piso de v0


def test_efeito_piso_imprime_erro_de_acerto_como_metrica_secundaria(tmp_path):
    dataset = _dataset()
    _gravar_versao(tmp_path, dataset, "v0", "r-v0", V1_BOA)
    _gravar_versao(tmp_path, dataset, "v1", "r-v1", V1_BOA)

    texto = _relatorio(tmp_path, dataset, ["v0", "v1"])

    assert "Veredito v0 × v1: inconclusivo por efeito piso" in texto
    assert "Métrica secundária (Erro de acerto por Repetição): v0 [0, 0, 0], v1 [0, 0, 0]" in texto

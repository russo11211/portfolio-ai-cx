import time

import pytest

from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.executor import AbortoRodada, rodar
from cx_prompt_lab.provider import ErroProvider, RespostaProvider

ROTULOS_VALIDOS = ["cancelamento", "duvida", "reclamacao"]


class ProviderFalso:
    """Provider roteirizado: devolve as respostas na ordem em que `chamar` é invocado."""

    def __init__(self, respostas: list[str]):
        self._respostas = respostas
        self._indice = 0
        self.chamadas: list[tuple[str, str]] = []

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        self.chamadas.append((prompt, transcricao))
        texto = self._respostas[self._indice]
        self._indice += 1
        return RespostaProvider(
            texto=texto, motivo_parada="fim_normal", modelo="fake-model", temperatura=0.0
        )


def _dataset_de_uma_transcricao() -> Dataset:
    return Dataset(
        transcricoes=[
            Transcricao(
                id="t1",
                texto="Cliente diz: quero cancelar o meu plano hoje mesmo.",
                rotulo_esperado="cancelamento",
            )
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )


def test_provider_e_dependencia_injetada_e_e_chamado_uma_vez_por_transcricao_e_repeticao():
    dataset = _dataset_de_uma_transcricao()
    resposta_correta = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
    provider = ProviderFalso(respostas=[resposta_correta] * 3)

    rodada = rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3)

    assert len(provider.chamadas) == 3
    assert len(rodada.contagens_por_repeticao) == 3


def test_rodada_envia_texto_do_prompt_ao_provider_sem_perder_a_versao():
    dataset = _dataset_de_uma_transcricao()
    resposta_correta = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
    provider = ProviderFalso(respostas=[resposta_correta] * 3)

    rodada = rodar(
        versao_prompt="v0",
        prompt_texto="Classifique a Transcrição e responda em JSON.",
        dataset=dataset,
        provider=provider,
        repeticoes=3,
    )

    assert rodada.versao_prompt == "v0"
    assert provider.chamadas == [
        ("Classifique a Transcrição e responda em JSON.", dataset.transcricoes[0].texto)
    ] * 3


def test_contagens_saem_por_repeticao_nao_so_no_total():
    dataset = _dataset_de_uma_transcricao()
    resposta_correta = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
    resposta_errada = '{"rotulo": "duvida", "justificativa": "quero cancelar o meu plano"}'
    # Repetição 1: acerto. Repetição 2: erro de acerto. Repetição 3: acerto.
    provider = ProviderFalso(respostas=[resposta_correta, resposta_errada, resposta_correta])

    rodada = rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3)

    assert rodada.contagens_por_repeticao[0].erro_de_acerto == 0
    assert rodada.contagens_por_repeticao[1].erro_de_acerto == 1
    assert rodada.contagens_por_repeticao[2].erro_de_acerto == 0


def test_resposta_pode_contar_em_erro_de_acerto_e_alucinacao_ao_mesmo_tempo():
    dataset = _dataset_de_uma_transcricao()
    # rótulo errado (duvida) + justificativa não ancorada -> linha (d): as duas contam.
    resposta = '{"rotulo": "duvida", "justificativa": "algo que nao esta na transcricao"}'
    provider = ProviderFalso(respostas=[resposta] * 3)

    rodada = rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3)

    contagem = rodada.contagens_por_repeticao[0]
    assert contagem.erro_de_acerto == 1
    assert contagem.alucinacao_total == 1


def test_violacao_de_formato_nao_conta_em_erro_de_acerto_nem_em_alucinacao():
    dataset = _dataset_de_uma_transcricao()
    resposta_quebrada = "isto nao e json"
    provider = ProviderFalso(respostas=[resposta_quebrada] * 3)

    rodada = rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3)

    contagem = rodada.contagens_por_repeticao[0]
    assert contagem.violacao_de_formato == 1
    assert contagem.erro_de_acerto == 0
    assert contagem.alucinacao_total == 0


@pytest.mark.parametrize("motivo_parada", ["truncada", "recusa"])
def test_parada_truncada_ou_recusa_conta_so_como_violacao_de_formato(motivo_parada):
    class ProviderComParada:
        def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
            return RespostaProvider(
                texto='{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}',
                motivo_parada=motivo_parada,
                modelo="modelo-observado",
            )

    rodada = rodar("v0", _dataset_de_uma_transcricao(), ProviderComParada(), repeticoes=3)

    assert all(c.violacao_de_formato == 1 for c in rodada.contagens_por_repeticao)
    assert all(c.erro_de_acerto == 0 and c.alucinacao_total == 0 for c in rodada.contagens_por_repeticao)


def test_alucinacao_total_conta_uma_transcricao_por_vez_nao_por_subtipo():
    dataset = Dataset(
        transcricoes=[
            Transcricao(id="t1", texto="Cliente quer cancelar o plano.", rotulo_esperado="cancelamento"),
            Transcricao(id="t2", texto="Cliente tem uma duvida sobre a fatura.", rotulo_esperado="duvida"),
            Transcricao(id="t3", texto="Cliente quer fazer uma reclamacao.", rotulo_esperado="reclamacao"),
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )
    # t1: rótulo fora da lista -> alucinação (rótulo inexistente).
    resposta_t1 = '{"rotulo": "portabilidade", "justificativa": "quer cancelar o plano"}'
    # t2: rótulo válido, correto, mas justificativa não ancorada -> alucinação (outro subtipo).
    resposta_t2 = '{"rotulo": "duvida", "justificativa": "algo que nao esta na transcricao"}'
    # t3: rótulo correto e ancorado -> nenhuma métrica.
    resposta_t3 = '{"rotulo": "reclamacao", "justificativa": "fazer uma reclamacao"}'
    provider = ProviderFalso(respostas=[resposta_t1, resposta_t2, resposta_t3] * 3)

    rodada = rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3)

    # duas Transcrições (t1, t2) geraram alucinação, cada uma de um subtipo -> total 2, não 1.
    assert rodada.contagens_por_repeticao[0].alucinacao_total == 2


def test_rodada_recusa_menos_de_3_repeticoes_com_mensagem():
    dataset = _dataset_de_uma_transcricao()
    provider = ProviderFalso(respostas=[])

    with pytest.raises(ValueError, match="repeticoes"):
        rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=2)


@pytest.mark.parametrize("versao_prompt", ["v0", "v1", "v2"])
def test_rodada_recusa_menos_de_3_repeticoes_em_qualquer_versao(versao_prompt):
    dataset = _dataset_de_uma_transcricao()
    provider = ProviderFalso(respostas=[])

    with pytest.raises(ValueError, match="repeticoes"):
        rodar(versao_prompt=versao_prompt, dataset=dataset, provider=provider, repeticoes=2)


class ProviderComErro:
    """Provider roteirizado que falha (timeout/limite de taxa/HTTP) numa Chamada."""

    def __init__(self, respostas_antes_do_erro: list[str], mensagem: str, causa_provavel: str):
        self._respostas = respostas_antes_do_erro
        self._indice = 0
        self._mensagem = mensagem
        self._causa_provavel = causa_provavel
        self.chamadas = 0

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        self.chamadas += 1
        if self._indice < len(self._respostas):
            texto = self._respostas[self._indice]
            self._indice += 1
            return RespostaProvider(texto=texto, motivo_parada="fim_normal", modelo="fake-model", temperatura=0.0)
        raise ErroProvider(self._mensagem, causa_provavel=self._causa_provavel)


class ProviderLento:
    """Provider que demora mais que o timeout configurado."""

    def __init__(self, atraso_s: float):
        self._atraso_s = atraso_s

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        time.sleep(self._atraso_s)
        return RespostaProvider(texto="{}", motivo_parada="fim_normal", modelo="fake-model", temperatura=0.0)


def test_erro_do_provider_aborta_a_rodada_sem_virar_chamada_nem_resposta():
    dataset = _dataset_de_uma_transcricao()
    resposta_correta = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
    provider = ProviderComErro(
        respostas_antes_do_erro=[resposta_correta],
        mensagem="limite de taxa excedido",
        causa_provavel="limite de taxa do provider atingido",
    )

    with pytest.raises(AbortoRodada):
        rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3)

    # a Chamada 1 teve sucesso; a Chamada 2 (que falhou) não conta como resultado
    assert provider.chamadas == 2


def test_erro_do_provider_nao_gera_retentativa_automatica():
    dataset = _dataset_de_uma_transcricao()
    provider = ProviderComErro(
        respostas_antes_do_erro=[], mensagem="erro HTTP 500", causa_provavel="provider instável"
    )

    with pytest.raises(AbortoRodada):
        rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3)

    assert provider.chamadas == 1  # nenhuma segunda tentativa da mesma Chamada


def test_timeout_por_chamada_aborta_a_rodada():
    dataset = _dataset_de_uma_transcricao()
    provider = ProviderLento(atraso_s=0.3)

    with pytest.raises(AbortoRodada, match="timeout"):
        rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3, timeout_s=0.05)


def test_progresso_reporta_chamada_n_de_m():
    dataset = _dataset_de_uma_transcricao()
    resposta_correta = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'
    provider = ProviderFalso(respostas=[resposta_correta] * 3)
    mensagens: list[str] = []

    rodar(
        versao_prompt="v0",
        dataset=dataset,
        provider=provider,
        repeticoes=3,
        on_progresso=mensagens.append,
    )

    assert mensagens == ["Chamada 1 de 3", "Chamada 2 de 3", "Chamada 3 de 3"]


def test_mensagem_de_aborto_contem_problema_causa_proximo_passo_rodada_transcricao_comando_e_aviso():
    dataset = _dataset_de_uma_transcricao()
    provider = ProviderComErro(
        respostas_antes_do_erro=[], mensagem="timeout de conexão", causa_provavel="rede instável"
    )

    with pytest.raises(AbortoRodada) as excinfo:
        rodar(versao_prompt="v0", dataset=dataset, provider=provider, repeticoes=3, rodada_id="rodada-42")

    mensagem = str(excinfo.value)
    assert "problema" in mensagem
    assert "causa provável" in mensagem
    assert "próximo passo" in mensagem
    assert "Rodada rodada-42" in mensagem
    assert "Transcrição t1" in mensagem
    assert "reexecutar" in mensagem
    assert "serão repetidas" in mensagem


def test_acertos_contam_rotulo_valido_e_correto_com_ou_sem_justificativa_ancorada():
    dataset = _dataset_de_uma_transcricao()
    respostas = [
        '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}',  # (a)
        '{"rotulo": "cancelamento", "justificativa": "texto inventado"}',  # (c)
        '{"rotulo": "duvida", "justificativa": "quero cancelar o meu plano"}',  # (b)
    ]
    rodada = rodar("v0", dataset, ProviderFalso(respostas), repeticoes=3)

    assert [c.acertos for c in rodada.contagens_por_repeticao] == [1, 1, 0]
    assert rodada.rotulos_por_repeticao == [
        {"t1": "cancelamento"},
        {"t1": "cancelamento"},
        {"t1": "duvida"},
    ]


def test_rotulo_inexistente_e_violacao_de_formato_ficam_sem_rotulo_valido():
    dataset = _dataset_de_uma_transcricao()
    respostas = [
        '{"rotulo": "inventado", "justificativa": "quero cancelar o meu plano"}',
        "não é JSON",
        '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}',
    ]
    rodada = rodar("v0", dataset, ProviderFalso(respostas), repeticoes=3)

    assert rodada.rotulos_por_repeticao == [{"t1": None}, {"t1": None}, {"t1": "cancelamento"}]
    assert [c.acertos for c in rodada.contagens_por_repeticao] == [0, 0, 1]

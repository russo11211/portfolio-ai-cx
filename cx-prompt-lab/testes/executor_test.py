import pytest

from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.executor import rodar
from cx_prompt_lab.provider import RespostaProvider

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

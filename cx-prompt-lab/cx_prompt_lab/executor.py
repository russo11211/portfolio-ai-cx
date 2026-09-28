"""Executor de Rodada: orquestra Provider + Avaliador.

`rodar(versao_prompt, dataset, provider, repeticoes>=3) -> Rodada`. Timeout,
progresso e aborto de Rodada real (T4) e gravação em disco (T3) ficam para
tickets futuros; aqui só a orquestração em memória e as contagens por
Repetição, que é o que T2 exige.
"""

from dataclasses import dataclass, field

from cx_prompt_lab.avaliador import avaliar
from cx_prompt_lab.dataset import Dataset
from cx_prompt_lab.provider import Provider

REPETICOES_MINIMAS = 3


@dataclass
class Contagens:
    erro_de_acerto: int = 0
    alucinacao_rotulo_inexistente: int = 0
    alucinacao_justificativa_nao_ancorada: int = 0
    # Uma Transcrição conta uma vez se a resposta tiver ao menos um subtipo de
    # Alucinação, mesmo que ambos ocorram (ver Further Notes da spec).
    alucinacao_total: int = 0
    violacao_de_formato: int = 0


@dataclass
class Rodada:
    versao_prompt: str
    contagens_por_repeticao: list[Contagens] = field(default_factory=list)


def rodar(versao_prompt: str, dataset: Dataset, provider: Provider, repeticoes: int) -> Rodada:
    if repeticoes < REPETICOES_MINIMAS:
        raise ValueError(
            f"repeticoes deve ser >= {REPETICOES_MINIMAS}, recebido {repeticoes}"
        )

    rodada = Rodada(versao_prompt=versao_prompt)

    for _ in range(repeticoes):
        contagens = Contagens()
        for transcricao in dataset.transcricoes:
            resposta = provider.chamar(prompt=versao_prompt, transcricao=transcricao.texto)
            resultado = avaliar(
                resposta_bruta=resposta.texto,
                rotulo_esperado=transcricao.rotulo_esperado,
                transcricao=transcricao.texto,
                rotulos_validos=dataset.rotulos_validos,
            )

            if resultado.veredito_de_forma == "violacao_de_formato":
                contagens.violacao_de_formato += 1
                continue

            if resultado.erro_de_acerto:
                contagens.erro_de_acerto += 1
            if resultado.alucinacao_rotulo_inexistente:
                contagens.alucinacao_rotulo_inexistente += 1
            if resultado.alucinacao_justificativa_nao_ancorada:
                contagens.alucinacao_justificativa_nao_ancorada += 1
            if resultado.alucinacao_rotulo_inexistente or resultado.alucinacao_justificativa_nao_ancorada:
                contagens.alucinacao_total += 1

        rodada.contagens_por_repeticao.append(contagens)

    return rodada

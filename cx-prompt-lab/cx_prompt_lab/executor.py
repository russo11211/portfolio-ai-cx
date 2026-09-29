"""Executor de Rodada: orquestra Provider + Avaliador.

`rodar(versao_prompt, dataset, provider, repeticoes>=3) -> Rodada`. Na Reexecução,
`prompt_texto` envia o conteúdo ao Provider e mantém `versao_prompt` como identidade. Gravação
em disco (T3) é transparente a este módulo (o Provider passado já pode ser um
`ProviderGravador`). Timeout por Chamada, progresso e aborto de Rodada (T4)
vivem aqui: erro do Provider (`ErroProvider`) ou timeout nunca viram Chamada
nem resposta — a Rodada aborta com `AbortoRodada` sem retentativa automática,
e quem chama decide como gravar o estado "abortada" (ver `gravacao.gravar`).
"""

import concurrent.futures
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from cx_prompt_lab.avaliador import avaliar
from cx_prompt_lab.dataset import Dataset
from cx_prompt_lab.provider import ErroProvider, Provider

REPETICOES_MINIMAS = 3
TIMEOUT_PADRAO_S = 30.0
COMANDO_REEXECUTAR = "python -m cx_prompt_lab reexecutar --prompt {versao_prompt} --repeticoes {repeticoes}"


@dataclass
class Contagens:
    erro_de_acerto: int = 0
    alucinacao_rotulo_inexistente: int = 0
    alucinacao_justificativa_nao_ancorada: int = 0
    # Uma Transcrição conta uma vez se a resposta tiver ao menos um subtipo de
    # Alucinação, mesmo que ambos ocorram (ver Further Notes da spec).
    alucinacao_total: int = 0
    violacao_de_formato: int = 0
    # Rótulo válido e correto, com ou sem Justificativa ancorada (linhas (a) e (c)).
    acertos: int = 0


@dataclass
class Rodada:
    versao_prompt: str
    contagens_por_repeticao: list[Contagens] = field(default_factory=list)
    # Por Repetição: id da Transcrição -> Rótulo válido devolvido, ou None
    # ("sem rótulo válido": Violação de formato ou rótulo fora da lista).
    rotulos_por_repeticao: list[dict[str, str | None]] = field(default_factory=list)


class AbortoRodada(Exception):
    """A Rodada abortou (erro do Provider ou timeout de Chamada). Não é
    retomável: as Chamadas já concluídas ficam gravadas, mas o manifesto sai
    com estado "abortada" e o Replay nunca aceita essa Rodada — recomeçar cria
    uma Rodada nova.
    """


def _mensagem_aborto(
    *,
    rodada_id: str,
    problema: str,
    causa_provavel: str,
    transcricao_id: str,
    numero_chamada: int,
    total_chamadas: int,
    versao_prompt: str,
    repeticoes: int,
) -> str:
    comando = COMANDO_REEXECUTAR.format(versao_prompt=versao_prompt, repeticoes=repeticoes)
    return (
        f"Aborto: Rodada {rodada_id}; problema: {problema} "
        f"(Transcrição {transcricao_id}, Chamada {numero_chamada} de {total_chamadas}); "
        f"causa provável: {causa_provavel}; "
        f"próximo passo: corrija a causa e comece uma nova Rodada — "
        f"as Chamadas já concluídas serão repetidas; "
        f"comando: {comando}"
    )


def rodar(
    versao_prompt: str,
    dataset: Dataset,
    provider: Provider,
    repeticoes: int,
    timeout_s: float = TIMEOUT_PADRAO_S,
    rodada_id: str | None = None,
    on_progresso: Callable[[str], None] | None = None,
    prompt_texto: str | None = None,
) -> Rodada:
    if repeticoes < REPETICOES_MINIMAS:
        raise ValueError(
            f"repeticoes deve ser >= {REPETICOES_MINIMAS}, recebido {repeticoes}"
        )

    rodada = Rodada(versao_prompt=versao_prompt)
    identificador_rodada = rodada_id if rodada_id is not None else f"(sem id, versão {versao_prompt})"
    total_chamadas = len(dataset.transcricoes) * repeticoes
    numero_chamada = 0

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        for _ in range(repeticoes):
            contagens = Contagens()
            rotulos: dict[str, str | None] = {}
            for transcricao in dataset.transcricoes:
                numero_chamada += 1
                if on_progresso is not None:
                    on_progresso(f"Chamada {numero_chamada} de {total_chamadas}")

                futuro = pool.submit(
                    provider.chamar,
                    prompt=versao_prompt if prompt_texto is None else prompt_texto,
                    transcricao=transcricao.texto,
                )
                try:
                    resposta = futuro.result(timeout=timeout_s)
                except concurrent.futures.TimeoutError:
                    raise AbortoRodada(
                        _mensagem_aborto(
                            rodada_id=identificador_rodada,
                            problema="timeout do provider",
                            causa_provavel=f"a Chamada excedeu o timeout de {timeout_s:g}s",
                            transcricao_id=transcricao.id,
                            numero_chamada=numero_chamada,
                            total_chamadas=total_chamadas,
                            versao_prompt=versao_prompt,
                            repeticoes=repeticoes,
                        )
                    ) from None
                except ErroProvider as erro:
                    raise AbortoRodada(
                        _mensagem_aborto(
                            rodada_id=identificador_rodada,
                            problema=str(erro),
                            causa_provavel=erro.causa_provavel,
                            transcricao_id=transcricao.id,
                            numero_chamada=numero_chamada,
                            total_chamadas=total_chamadas,
                            versao_prompt=versao_prompt,
                            repeticoes=repeticoes,
                        )
                    ) from erro

                if resposta.motivo_parada in ("truncada", "recusa"):
                    contagens.violacao_de_formato += 1
                    rotulos[transcricao.id] = None
                    continue

                resultado = avaliar(
                    resposta_bruta=resposta.texto,
                    rotulo_esperado=transcricao.rotulo_esperado,
                    transcricao=transcricao.texto,
                    rotulos_validos=dataset.rotulos_validos,
                )

                if resultado.veredito_de_forma == "violacao_de_formato":
                    contagens.violacao_de_formato += 1
                    rotulos[transcricao.id] = None
                    continue

                rotulos[transcricao.id] = (
                    None if resultado.alucinacao_rotulo_inexistente else resultado.rotulo
                )
                if not resultado.erro_de_acerto:
                    contagens.acertos += 1
                else:
                    contagens.erro_de_acerto += 1

                if resultado.alucinacao_rotulo_inexistente:
                    contagens.alucinacao_rotulo_inexistente += 1
                if resultado.alucinacao_justificativa_nao_ancorada:
                    contagens.alucinacao_justificativa_nao_ancorada += 1
                if resultado.alucinacao_rotulo_inexistente or resultado.alucinacao_justificativa_nao_ancorada:
                    contagens.alucinacao_total += 1

            rodada.contagens_por_repeticao.append(contagens)
            rodada.rotulos_por_repeticao.append(rotulos)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    return rodada

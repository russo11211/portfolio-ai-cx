"""Replay: recalcula uma Rodada gravada sem chamar nenhum provider.

`substituir(...)` valida o manifesto e as Chamadas gravadas (hash do prompt,
hash do Dataset, versão de esquema, estado completo, integridade por Chamada)
e então roda o Executor de Rodada (T2) de novo com `ReplayProvider`, que
devolve as respostas gravadas em vez de rede — assim o cálculo é
exatamente o mesmo código que gerou a Rodada original, sem duplicar a lógica
de contagem. Qualquer divergência recusa com mensagem, na forma fixada pela
ADR do E7 (0001-arquitetura-cx-prompt-lab.md, exigência 6).
"""

import json
import os
from pathlib import Path

from cx_prompt_lab.dataset import Dataset
from cx_prompt_lab.executor import Rodada, rodar
from cx_prompt_lab.gravacao import (
    ESTADO_COMPLETA,
    FERRAMENTA_VERSAO,
    VERSAO_ESQUEMA,
    Chamada,
    ContadorDeRepeticaoPorTranscricao,
    Manifesto,
    hash_dataset,
    hash_texto,
)
from cx_prompt_lab.provider import RespostaProvider

ACAO_PADRAO = "reexecute com 'reexecutar' ou restaure o commit"


class RecusaReplay(Exception):
    """Recusa de integridade do Replay: hash, esquema, estado ou Chamada."""


def _caminho_relativo(caminho: Path | str) -> str:
    try:
        return os.path.relpath(caminho)
    except ValueError:
        # caminho em outro drive (Windows) ou sem raiz comum: melhor mostrar o absoluto
        # do que levantar um erro dentro de uma mensagem de recusa.
        return str(caminho)


def _recusa(tipo: str, identificador: str, detalhe: str, caminho: Path | str, acao: str = ACAO_PADRAO) -> RecusaReplay:
    return RecusaReplay(
        f"Recusa: {tipo} {identificador}; {detalhe}; "
        f"ação: {acao}; "
        f"link: {_caminho_relativo(caminho)}"
    )


def _major(versao_semver: str) -> str:
    return versao_semver.split(".", 1)[0]


class ReplayProvider:
    """Adapter do seam Provider que lê Chamadas gravadas em vez da rede."""

    def __init__(self, dataset: Dataset, chamadas_por_identidade: dict[tuple[str, int], Chamada]):
        self._contador = ContadorDeRepeticaoPorTranscricao(dataset)
        self._chamadas = chamadas_por_identidade

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        transcricao_id, repeticao = self._contador.proxima(transcricao)

        chamada = self._chamadas[(transcricao_id, repeticao)]
        return RespostaProvider(
            texto=chamada.resposta,
            motivo_parada=chamada.motivo_parada,
            modelo=chamada.modelo,
            temperatura=chamada.temperatura,
        )


def substituir(caminho_rodada: Path, dataset: Dataset, prompt_texto: str, repeticoes: int) -> Rodada:
    caminho_rodada = Path(caminho_rodada)
    caminho_manifesto = caminho_rodada / "manifest.json"

    if not caminho_manifesto.exists():
        raise _recusa("arquivo", str(caminho_manifesto), "manifesto ausente", caminho_rodada)

    try:
        manifesto_dado = json.loads(caminho_manifesto.read_text(encoding="utf-8"))
        manifesto = Manifesto.de_dict(manifesto_dado)
    except (json.JSONDecodeError, KeyError):
        raise _recusa("arquivo", str(caminho_manifesto), "manifesto corrompido", caminho_rodada) from None

    if manifesto.versao_esquema != VERSAO_ESQUEMA:
        raise _recusa(
            "Rodada",
            manifesto.rodada_id,
            f"versão de esquema incompatível: esperada {VERSAO_ESQUEMA}, encontrada {manifesto.versao_esquema}",
            caminho_rodada,
        )

    if _major(manifesto.ferramenta_versao) != _major(FERRAMENTA_VERSAO):
        raise _recusa(
            "Rodada",
            manifesto.rodada_id,
            f"versão da ferramenta incompatível (major): manifesto {manifesto.ferramenta_versao}, "
            f"instalada {FERRAMENTA_VERSAO}",
            caminho_rodada,
            acao=f"git checkout <tag> compatível com a versão {manifesto.ferramenta_versao}",
        )

    if manifesto.estado != ESTADO_COMPLETA:
        raise _recusa(
            "Rodada",
            manifesto.rodada_id,
            f"Rodada não está completa (estado: {manifesto.estado})",
            caminho_rodada,
        )

    hash_prompt_atual = hash_texto(prompt_texto)
    if hash_prompt_atual != manifesto.hash_prompt:
        raise _recusa(
            "Rodada",
            manifesto.rodada_id,
            f"hash esperado {manifesto.hash_prompt}, encontrado {hash_prompt_atual}",
            caminho_rodada,
        )

    hash_dataset_atual = hash_dataset(dataset)
    if hash_dataset_atual != manifesto.hash_dataset:
        raise _recusa(
            "Rodada",
            manifesto.rodada_id,
            f"hash esperado {manifesto.hash_dataset}, encontrado {hash_dataset_atual}",
            caminho_rodada,
        )

    ids_validos = {t.id for t in dataset.transcricoes}
    identidades_esperadas = {(t.id, r) for t in dataset.transcricoes for r in range(1, repeticoes + 1)}

    chamadas_por_identidade: dict[tuple[str, int], Chamada] = {}
    for caminho_arquivo in sorted(caminho_rodada.glob("*.json")):
        if caminho_arquivo.name == "manifest.json":
            continue

        try:
            dado = json.loads(caminho_arquivo.read_text(encoding="utf-8"))
            chamada = Chamada.de_dict(dado)
        except (json.JSONDecodeError, KeyError):
            raise _recusa(
                "Chamada", caminho_arquivo.name, "Chamada corrompida", caminho_arquivo
            ) from None

        if chamada.rodada_id != manifesto.rodada_id or chamada.hash_prompt != manifesto.hash_prompt:
            raise _recusa(
                "Chamada",
                caminho_arquivo.name,
                "Chamada corrompida (identidade de Rodada ou de prompt não bate com o manifesto)",
                caminho_arquivo,
            )

        if chamada.transcricao_id not in ids_validos:
            raise _recusa(
                "Chamada",
                caminho_arquivo.name,
                f"Transcrição {chamada.transcricao_id!r} fora do Dataset",
                caminho_arquivo,
            )

        identidade = (chamada.transcricao_id, chamada.repeticao)
        if identidade in chamadas_por_identidade:
            raise _recusa(
                "Chamada", caminho_arquivo.name, "Chamada duplicada", caminho_arquivo
            )

        if identidade not in identidades_esperadas:
            raise _recusa(
                "Chamada",
                caminho_arquivo.name,
                "Chamada extra (não esperada para esta Rodada)",
                caminho_arquivo,
            )

        chamadas_por_identidade[identidade] = chamada

    faltando = identidades_esperadas - set(chamadas_por_identidade.keys())
    if faltando:
        transcricao_id, repeticao = sorted(faltando)[0]
        raise _recusa("Chamada", f"{transcricao_id}#{repeticao}", "Chamada faltando", caminho_rodada)

    provider = ReplayProvider(dataset=dataset, chamadas_por_identidade=chamadas_por_identidade)
    return rodar(versao_prompt=manifesto.versao_prompt, dataset=dataset, provider=provider, repeticoes=repeticoes)

"""Gravação: grava cada Chamada de uma Rodada em arquivo commitado, mais o manifesto.

`ProviderGravador` envolve o Provider real (T1/T5/T6) e registra cada Chamada
sem modificar o seam Provider nem o Executor de Rodada (T2) — a gravação é
transparente para os dois; a Repetição de uma Chamada é contada por
Transcrição (via o texto, que é a única informação que o seam Provider
recebe), não pela ordem de iteração do Executor.

`gravar(...)` escreve com reserva de diretório de staging → escreve → valida
→ publica com rename atômico. Uma Rodada existente nunca é sobrescrita.
"""

import hashlib
import json
import os
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from cx_prompt_lab.dataset import Dataset
from cx_prompt_lab.provider import RespostaProvider

VERSAO_ESQUEMA = 2
FERRAMENTA_VERSAO = "0.1.0"
AVALIADOR_VERSAO = "0.1.0"

ESTADO_INICIADA = "iniciada"
ESTADO_COMPLETA = "completa"
ESTADO_ABORTADA = "abortada"


class RecusaGravacao(Exception):
    """A gravação não pode prosseguir (Rodada já existe, Chamadas não batem)."""


def hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_dataset(dataset: Dataset) -> str:
    canonico = json.dumps(
        {
            "rotulos_validos": dataset.rotulos_validos,
            "transcricoes": [
                {"id": t.id, "texto": t.texto, "rotulo_esperado": t.rotulo_esperado}
                for t in dataset.transcricoes
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hash_texto(canonico)


def hash_chamada(rodada_id: str, hash_prompt: str, transcricao_id: str, repeticao: int) -> str:
    identidade = f"{rodada_id}:{hash_prompt}:{transcricao_id}:{repeticao}"
    return hash_texto(identidade)


def agora_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Chamada:
    rodada_id: str
    hash_prompt: str
    transcricao_id: str
    repeticao: int
    modelo: str
    motivo_parada: str
    temperatura: float | None
    max_tokens: int | None
    resposta: str
    criado_em: str

    def identidade_hash(self) -> str:
        return hash_chamada(self.rodada_id, self.hash_prompt, self.transcricao_id, self.repeticao)

    def para_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def de_dict(dado: dict) -> "Chamada":
        return Chamada(
            rodada_id=dado["rodada_id"],
            hash_prompt=dado["hash_prompt"],
            transcricao_id=dado["transcricao_id"],
            repeticao=dado["repeticao"],
            modelo=dado["modelo"],
            motivo_parada=dado["motivo_parada"],
            temperatura=dado.get("temperatura"),
            max_tokens=dado.get("max_tokens"),
            resposta=dado["resposta"],
            criado_em=dado["criado_em"],
        )


@dataclass(frozen=True)
class Manifesto:
    versao_esquema: int
    rodada_id: str
    versao_prompt: str
    hash_prompt: str
    hash_dataset: str
    parametros_efetivos: dict
    numero_esperado_chamadas: int
    estado: str
    ferramenta_versao: str
    avaliador_versao: str

    def para_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def de_dict(dado: dict) -> "Manifesto":
        return Manifesto(
            versao_esquema=dado["versao_esquema"],
            rodada_id=dado["rodada_id"],
            versao_prompt=dado["versao_prompt"],
            hash_prompt=dado["hash_prompt"],
            hash_dataset=dado["hash_dataset"],
            parametros_efetivos=dado["parametros_efetivos"],
            numero_esperado_chamadas=dado["numero_esperado_chamadas"],
            estado=dado["estado"],
            ferramenta_versao=dado["ferramenta_versao"],
            avaliador_versao=dado["avaliador_versao"],
        )


class ContadorDeRepeticaoPorTranscricao:
    """Conta, para cada Transcrição (identificada pelo texto), quantas vezes
    ela já foi vista — 1-based. Usado por `ProviderGravador` e `ReplayProvider`
    para achar a Repetição de uma Chamada sem depender da ordem de iteração
    do Executor de Rodada.
    """

    def __init__(self, dataset: Dataset):
        self._texto_para_id = {t.texto: t.id for t in dataset.transcricoes}
        self._contagem_por_transcricao: dict[str, int] = {}

    def proxima(self, transcricao_texto: str) -> tuple[str, int]:
        transcricao_id = self._texto_para_id.get(transcricao_texto)
        if transcricao_id is None:
            raise ValueError("Transcrição fora do Dataset informado")

        repeticao = self._contagem_por_transcricao.get(transcricao_id, 0) + 1
        self._contagem_por_transcricao[transcricao_id] = repeticao
        return transcricao_id, repeticao


class ProviderGravador:
    """Envolve um Provider e registra cada Chamada, sem alterar o seam Provider."""

    def __init__(
        self,
        provider,
        dataset: Dataset,
        rodada_id: str,
        hash_prompt: str,
        parametros_geracao: dict | None = None,
        relogio: Callable[[], str] = agora_iso,
    ):
        self._provider = provider
        self._rodada_id = rodada_id
        self._hash_prompt = hash_prompt
        self._parametros_geracao = parametros_geracao or {}
        self._contador = ContadorDeRepeticaoPorTranscricao(dataset)
        self._relogio = relogio
        self.chamadas: list[Chamada] = []

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        resposta = self._provider.chamar(prompt=prompt, transcricao=transcricao)

        transcricao_id, repeticao = self._contador.proxima(transcricao)

        self.chamadas.append(
            Chamada(
                rodada_id=self._rodada_id,
                hash_prompt=self._hash_prompt,
                transcricao_id=transcricao_id,
                repeticao=repeticao,
                modelo=resposta.modelo,
                motivo_parada=resposta.motivo_parada,
                temperatura=self._parametros_geracao.get("temperature"),
                max_tokens=self._parametros_geracao.get("max_tokens"),
                resposta=resposta.texto,
                criado_em=self._relogio(),
            )
        )
        return resposta


def gravar(
    diretorio_rodadas: Path,
    rodada_id: str,
    versao_prompt: str,
    prompt_texto: str,
    dataset: Dataset,
    chamadas: list[Chamada],
    repeticoes: int,
    parametros_efetivos: dict,
    estado: str = ESTADO_COMPLETA,
) -> Manifesto:
    diretorio_rodadas = Path(diretorio_rodadas)
    hash_prompt_valor = hash_texto(prompt_texto)
    hash_dataset_valor = hash_dataset(dataset)
    numero_esperado = len(dataset.transcricoes) * repeticoes

    identidades_esperadas = {
        (hash_prompt_valor, t.id, r) for t in dataset.transcricoes for r in range(1, repeticoes + 1)
    }
    identidades_recebidas_lista = [(c.hash_prompt, c.transcricao_id, c.repeticao) for c in chamadas]
    identidades_recebidas = set(identidades_recebidas_lista)

    if len(identidades_recebidas) != len(chamadas):
        raise RecusaGravacao(f"Recusa: Rodada {rodada_id}; Chamadas duplicadas entre as recebidas para gravação")

    if estado == ESTADO_COMPLETA:
        if identidades_recebidas != identidades_esperadas:
            faltando = identidades_esperadas - identidades_recebidas
            extra = identidades_recebidas - identidades_esperadas
            raise RecusaGravacao(
                f"Recusa: Rodada {rodada_id}; Chamadas recebidas não batem com o esperado "
                f"({len(faltando)} faltando, {len(extra)} extra); numero esperado {numero_esperado}"
            )
    else:
        # Rodada abortada (T4): as Chamadas gravadas são as concluídas antes do
        # aborto, sem bater com o esperado por definição — só extras são recusa.
        extra = identidades_recebidas - identidades_esperadas
        if extra:
            raise RecusaGravacao(
                f"Recusa: Rodada {rodada_id}; {len(extra)} Chamada(s) fora do esperado para esta Rodada abortada"
            )

    diretorio_final = diretorio_rodadas / rodada_id
    if diretorio_final.exists():
        raise RecusaGravacao(
            f"Recusa: Rodada {rodada_id} já existe em {diretorio_final}; "
            "uma Rodada existente nunca é sobrescrita; "
            "ação: escolha outro identificador de Rodada"
        )

    manifesto = Manifesto(
        versao_esquema=VERSAO_ESQUEMA,
        rodada_id=rodada_id,
        versao_prompt=versao_prompt,
        hash_prompt=hash_prompt_valor,
        hash_dataset=hash_dataset_valor,
        parametros_efetivos=parametros_efetivos,
        numero_esperado_chamadas=numero_esperado,
        estado=estado,
        ferramenta_versao=FERRAMENTA_VERSAO,
        avaliador_versao=AVALIADOR_VERSAO,
    )

    diretorio_rodadas.mkdir(parents=True, exist_ok=True)
    diretorio_staging = diretorio_rodadas / f".{rodada_id}.staging"
    if diretorio_staging.exists():
        shutil.rmtree(diretorio_staging)
    diretorio_staging.mkdir(parents=True)

    try:
        for chamada in chamadas:
            caminho = diretorio_staging / f"{chamada.identidade_hash()}.json"
            caminho.write_text(
                json.dumps(chamada.para_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        (diretorio_staging / "manifest.json").write_text(
            json.dumps(manifesto.para_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        os.rename(diretorio_staging, diretorio_final)
    except BaseException:
        if diretorio_staging.exists():
            shutil.rmtree(diretorio_staging)
        raise

    return manifesto

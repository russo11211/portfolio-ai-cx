"""Dataset: Transcrições fictícias e a lista fechada de Rótulos.

`carregar(caminho) -> Dataset` lê `dataset/transcricoes.json` e valida: IDs
únicos, rótulo esperado dentro da lista fechada, entre 20 e 30 Transcrições,
ao menos uma Transcrição por Rótulo, regra de desempate escrita, e ao menos
um caso de intenção dupla e um caso ambíguo (visíveis no próprio arquivo, via
os campos `intencao_dupla` e `ambiguo`).
"""

import json
from dataclasses import dataclass
from pathlib import Path

MINIMO_TRANSCRICOES = 20
MAXIMO_TRANSCRICOES = 30


class RecusaDataset(Exception):
    """O Dataset carregado não passa na validação."""


@dataclass(frozen=True)
class Transcricao:
    id: str
    texto: str
    rotulo_esperado: str
    intencao_dupla: bool = False
    ambiguo: bool = False
    observacao: str = ""


@dataclass(frozen=True)
class Dataset:
    transcricoes: list[Transcricao]
    rotulos_validos: list[str]
    regra_desempate: str = ""


def carregar(caminho: Path) -> Dataset:
    caminho = Path(caminho)
    try:
        dado = json.loads(caminho.read_text(encoding="utf-8"))
        transcricoes = [
            Transcricao(
                id=t["id"],
                texto=t["texto"],
                rotulo_esperado=t["rotulo_esperado"],
                intencao_dupla=t.get("intencao_dupla", False),
                ambiguo=t.get("ambiguo", False),
                observacao=t.get("observacao", ""),
            )
            for t in dado["transcricoes"]
        ]
        dataset = Dataset(
            transcricoes=transcricoes,
            rotulos_validos=dado["rotulos_validos"],
            regra_desempate=dado.get("regra_desempate", ""),
        )
    except FileNotFoundError as erro:
        raise RecusaDataset(
            f"Recusa: Dataset {caminho} não encontrado — causa provável: caminho errado ou arquivo "
            "não criado — próximo passo: confira o caminho e crie dataset/transcricoes.json"
        ) from erro
    except json.JSONDecodeError as erro:
        raise RecusaDataset(
            f"Recusa: Dataset {caminho} não é um JSON válido — causa provável: {erro} "
            "— próximo passo: corrija a sintaxe do arquivo e recarregue"
        ) from erro
    except KeyError as erro:
        raise RecusaDataset(
            f"Recusa: Dataset {caminho} com campo obrigatório ausente — causa provável: falta a chave {erro} "
            "— próximo passo: adicione o campo no arquivo e recarregue"
        ) from erro

    _validar(dataset, caminho)
    return dataset


def _validar(dataset: Dataset, caminho: Path) -> None:
    problemas = []

    ids = [t.id for t in dataset.transcricoes]
    duplicados = sorted({i for i in ids if ids.count(i) > 1})
    if duplicados:
        problemas.append(f"IDs duplicados: {duplicados}")

    total = len(dataset.transcricoes)
    if not (MINIMO_TRANSCRICOES <= total <= MAXIMO_TRANSCRICOES):
        problemas.append(
            f"{total} Transcrições no Dataset; esperado entre {MINIMO_TRANSCRICOES} e {MAXIMO_TRANSCRICOES}"
        )

    fora_da_lista = sorted(
        {t.rotulo_esperado for t in dataset.transcricoes if t.rotulo_esperado not in dataset.rotulos_validos}
    )
    if fora_da_lista:
        problemas.append(f"Rótulo(s) fora da lista fechada: {fora_da_lista}")

    rotulos_cobertos = {t.rotulo_esperado for t in dataset.transcricoes}
    orfaos = sorted(set(dataset.rotulos_validos) - rotulos_cobertos)
    if orfaos:
        problemas.append(f"Rótulo(s) sem nenhuma Transcrição: {orfaos}")

    if not dataset.regra_desempate.strip():
        problemas.append("regra de desempate para intenção dupla ausente ou vazia")

    if not any(t.intencao_dupla for t in dataset.transcricoes):
        problemas.append("nenhuma Transcrição marcada como intenção dupla")

    if not any(t.ambiguo for t in dataset.transcricoes):
        problemas.append("nenhuma Transcrição marcada como ambígua")

    if problemas:
        raise RecusaDataset(
            f"Recusa: Dataset {caminho} inválido — causa provável: {'; '.join(problemas)} "
            "— próximo passo: corrija o arquivo e recarregue"
        )

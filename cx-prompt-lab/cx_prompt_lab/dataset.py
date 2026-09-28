"""Dataset: Transcrições fictícias e a lista fechada de Rótulos.

O carregamento a partir de disco (dataset/transcricoes.json) é T7. Aqui só o
tipo mínimo que o Executor de Rodada (T2) precisa.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Transcricao:
    id: str
    texto: str
    rotulo_esperado: str


@dataclass(frozen=True)
class Dataset:
    transcricoes: list[Transcricao]
    rotulos_validos: list[str]

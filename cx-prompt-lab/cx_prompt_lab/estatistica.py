"""Estatística do experimento confirmatório (holdout): funções puras, só stdlib.

A unidade de análise é a Transcrição, não a Chamada: as Repetições de uma mesma
Transcrição são correlacionadas (mesmo texto, mesmo prompt), então tratar cada
Chamada como independente subestimaria a incerteza. Por isso:

- `teste_do_sinal`: teste do sinal exato, bicaudal, sobre a diferença pareada
  por Transcrição (contagem de falhas na versão base menos na candidata).
  Empates (diferença 0) saem do teste. É o análogo do McNemar exato quando o
  par é a Transcrição.
- `bootstrap_por_transcricao`: intervalo de confiança percentil por bootstrap
  de clusters (reamostra Transcrições com reposição, mantendo as Repetições
  de cada uma juntas), com semente fixa para o resultado ser reproduzível.

Ver docs/spec/cx-prompt-lab-preregistro-holdout.md (pré-registro, CAR-23).
"""

import random
from dataclasses import dataclass
from math import comb


@dataclass(frozen=True)
class ResultadoSinal:
    favoraveis_candidata: int  # Transcrições em que a candidata falhou menos
    favoraveis_base: int  # Transcrições em que a base falhou menos
    empates: int
    p_valor: float  # bicaudal, exato


@dataclass(frozen=True)
class IntervaloBootstrap:
    estimativa: float
    inferior: float
    superior: float
    reamostras: int
    semente: int


def binomial_bicaudal(k: int, n: int) -> float:
    """p-valor exato bicaudal de observar k sucessos em n sob p = 0,5."""
    if n < 0 or not 0 <= k <= n:
        raise ValueError(f"k e n inválidos: k={k}, n={n}")
    if n == 0:
        return 1.0
    menor = min(k, n - k)
    cauda = sum(comb(n, i) for i in range(menor + 1)) / 2**n
    return min(1.0, 2 * cauda)


def teste_do_sinal(falhas_base: list[int], falhas_candidata: list[int]) -> ResultadoSinal:
    """Pareado por Transcrição: listas alinhadas pelo mesmo índice de Transcrição."""
    if len(falhas_base) != len(falhas_candidata):
        raise ValueError("as duas listas precisam ter uma entrada por Transcrição, na mesma ordem")
    a_favor_candidata = sum(1 for b, c in zip(falhas_base, falhas_candidata) if b > c)
    a_favor_base = sum(1 for b, c in zip(falhas_base, falhas_candidata) if b < c)
    empates = len(falhas_base) - a_favor_candidata - a_favor_base
    n = a_favor_candidata + a_favor_base
    return ResultadoSinal(
        favoraveis_candidata=a_favor_candidata,
        favoraveis_base=a_favor_base,
        empates=empates,
        p_valor=binomial_bicaudal(a_favor_candidata, n),
    )


def _percentil(ordenados: list[float], q: float) -> float:
    """Percentil por interpolação linear (mesma convenção do 'linear' do numpy)."""
    posicao = q * (len(ordenados) - 1)
    baixo = int(posicao)
    alto = min(baixo + 1, len(ordenados) - 1)
    fracao = posicao - baixo
    return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * fracao


def taxa(falhas: list[int], repeticoes: int) -> float:
    return sum(falhas) / (len(falhas) * repeticoes)


def bootstrap_por_transcricao(
    falhas_base: list[int],
    falhas_candidata: list[int] | None,
    repeticoes: int,
    reamostras: int = 10_000,
    semente: int = 20261016,
    confianca: float = 0.95,
) -> IntervaloBootstrap:
    """IC percentil por bootstrap de clusters (Transcrições).

    Com `falhas_candidata=None`, o intervalo é da taxa da base. Com as duas
    listas, é da diferença de taxas (candidata menos base), reamostrando a
    mesma Transcrição nas duas versões para preservar o pareamento.
    """
    if repeticoes < 1 or reamostras < 1 or not falhas_base:
        raise ValueError("repeticoes, reamostras e a lista de falhas precisam ser positivos/não vazios")
    if falhas_candidata is not None and len(falhas_candidata) != len(falhas_base):
        raise ValueError("as duas listas precisam ter uma entrada por Transcrição, na mesma ordem")

    def estatistica(indices: list[int]) -> float:
        base = taxa([falhas_base[i] for i in indices], repeticoes)
        if falhas_candidata is None:
            return base
        return taxa([falhas_candidata[i] for i in indices], repeticoes) - base

    n = len(falhas_base)
    gerador = random.Random(semente)
    valores = sorted(estatistica([gerador.randrange(n) for _ in range(n)]) for _ in range(reamostras))
    alfa = 1 - confianca
    return IntervaloBootstrap(
        estimativa=estatistica(list(range(n))),
        inferior=_percentil(valores, alfa / 2),
        superior=_percentil(valores, 1 - alfa / 2),
        reamostras=reamostras,
        semente=semente,
    )

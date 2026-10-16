"""Experimento confirmatório (CAR-23): base × candidata no holdout, com teste estatístico.

Reaproveita o pipeline existente sem mudar a arquitetura:

1. `relatorio.coletar_resumos` acha, em cada split, a Rodada completa de cada
   versão (mesmo hash de Dataset) e já passa cada uma pelo `replay.substituir`,
   que confere hashes, esquema e integridade das Chamadas gravadas.
2. Para ter o resultado por Transcrição (unidade de análise do pré-registro),
   o Executor de Rodada roda de novo, uma Transcrição por vez, com o mesmo
   `ReplayProvider` do Replay. Assim a classificação de cada Chamada é
   exatamente a do Executor + Avaliador, sem lógica de contagem duplicada.
3. `estatistica` calcula o teste do sinal e o bootstrap por Transcrição.

As regras de decisão estão no pré-registro
(docs/spec/cx-prompt-lab-preregistro-holdout.md) e foram commitadas antes de
qualquer Chamada no holdout. Este módulo só as aplica.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from cx_prompt_lab.dataset import Dataset
from cx_prompt_lab.estatistica import (
    IntervaloBootstrap,
    ResultadoSinal,
    bootstrap_por_transcricao,
    taxa,
    teste_do_sinal,
)
from cx_prompt_lab.executor import rodar
from cx_prompt_lab.gravacao import Chamada
from cx_prompt_lab.relatorio import ResumoRodada, coletar_resumos
from cx_prompt_lab.replay import ReplayProvider

ALFA = 0.05
MARGEM_EQUIVALENCIA = 0.10  # 10 pontos percentuais de taxa
REAMOSTRAS = 10_000
SEMENTE = 20261016

MELHORA_CONFIRMADA = "melhora confirmada"
PIORA_CONFIRMADA = "piora confirmada"
SEM_DIFERENCA_RELEVANTE = "sem diferença relevante (equivalência dentro de ±10 pp)"
INCONCLUSIVO = "inconclusivo"


class RecusaConfirmatorio(Exception):
    """Faltou Rodada, sobrou Rodada, ou os splits não batem com o pré-registro."""


@dataclass(frozen=True)
class Split:
    nome: str
    diretorio_rodadas: Path
    dataset: Dataset


@dataclass(frozen=True)
class ResultadoTranscricao:
    split: str
    transcricao_id: str
    violacoes: int  # Repetições com Violação de formato
    nao_acertos: int  # Repetições sem Rótulo válido e correto
    erros_de_acerto: int
    alucinacoes: int


@dataclass(frozen=True)
class AnaliseMetrica:
    nome: str
    falhas_base: list[int]
    falhas_candidata: list[int]
    sinal: ResultadoSinal
    ic_base: IntervaloBootstrap
    ic_candidata: IntervaloBootstrap
    ic_diferenca: IntervaloBootstrap


@dataclass(frozen=True)
class Analise:
    base: str
    candidata: str
    repeticoes: int
    transcricoes: int
    rodadas: list[str]
    primaria: AnaliseMetrica
    secundaria: AnaliseMetrica
    descritivo: dict[str, tuple[int, int]]  # métrica -> (base, candidata), em Chamadas
    modelos: set[str]
    veredito: str


def _rodada_unica(resumos: list[ResumoRodada], versao: str, split: str) -> ResumoRodada:
    candidatas = [r for r in resumos if r.no_experimento and r.versao_prompt == versao]
    if len(candidatas) != 1:
        proximo = (
            "grave a Rodada com 'reexecutar'"
            if not candidatas
            else "mova as excedentes para descartadas/"
        )
        raise RecusaConfirmatorio(
            f"Recusa: split {split}, versão {versao}: {len(candidatas)} Rodadas completas no experimento; "
            f"o pré-registro exige exatamente uma — próximo passo: {proximo}"
        )
    return candidatas[0]


def _chamadas(caminho_rodada: Path) -> dict[tuple[str, int], Chamada]:
    chamadas = {}
    for caminho in sorted(caminho_rodada.glob("*.json")):
        if caminho.name == "manifest.json":
            continue
        chamada = Chamada.de_dict(json.loads(caminho.read_text(encoding="utf-8")))
        chamadas[(chamada.transcricao_id, chamada.repeticao)] = chamada
    return chamadas


def resultados_por_transcricao(
    caminho_rodada: Path, dataset: Dataset, repeticoes: int, split: str
) -> list[ResultadoTranscricao]:
    """Uma entrada por Transcrição, na ordem do Dataset. Supõe Rodada já validada pelo Replay."""
    chamadas = _chamadas(caminho_rodada)
    resultados = []
    for transcricao in dataset.transcricoes:
        so_esta = Dataset(
            transcricoes=[transcricao],
            rotulos_validos=dataset.rotulos_validos,
            regra_desempate=dataset.regra_desempate,
        )
        provider = ReplayProvider(
            dataset=so_esta,
            chamadas_por_identidade={
                chave: valor for chave, valor in chamadas.items() if chave[0] == transcricao.id
            },
        )
        rodada = rodar(versao_prompt="replay", dataset=so_esta, provider=provider, repeticoes=repeticoes)
        contagens = rodada.contagens_por_repeticao
        resultados.append(
            ResultadoTranscricao(
                split=split,
                transcricao_id=transcricao.id,
                violacoes=sum(c.violacao_de_formato for c in contagens),
                nao_acertos=repeticoes - sum(c.acertos for c in contagens),
                erros_de_acerto=sum(c.erro_de_acerto for c in contagens),
                alucinacoes=sum(c.alucinacao_total for c in contagens),
            )
        )
    return resultados


def _conferir_contra_replay(resultados: list[ResultadoTranscricao], resumo: ResumoRodada) -> None:
    """Rede de segurança: a soma por Transcrição tem de bater com as contagens do Replay."""
    total_replay = sum(c.violacao_de_formato for c in resumo.contagens_por_repeticao)
    total_aqui = sum(r.violacoes for r in resultados)
    if total_replay != total_aqui:
        raise RecusaConfirmatorio(
            f"Recusa: Rodada {resumo.id}: soma por Transcrição ({total_aqui}) diverge do Replay ({total_replay})"
        )


def decidir(sinal: ResultadoSinal, ic_diferenca: IntervaloBootstrap) -> str:
    """Regra pré-registrada. A decisão de melhora/piora é do teste do sinal (primário);
    a equivalência usa o IC da diferença de taxas (candidata − base)."""
    if sinal.p_valor < ALFA:
        if sinal.favoraveis_candidata > sinal.favoraveis_base:
            return MELHORA_CONFIRMADA
        return PIORA_CONFIRMADA
    if -MARGEM_EQUIVALENCIA <= ic_diferenca.inferior and ic_diferenca.superior <= MARGEM_EQUIVALENCIA:
        return SEM_DIFERENCA_RELEVANTE
    return INCONCLUSIVO


def _metrica(nome: str, base: list[int], candidata: list[int], repeticoes: int) -> AnaliseMetrica:
    return AnaliseMetrica(
        nome=nome,
        falhas_base=base,
        falhas_candidata=candidata,
        sinal=teste_do_sinal(base, candidata),
        ic_base=bootstrap_por_transcricao(base, None, repeticoes, REAMOSTRAS, SEMENTE),
        ic_candidata=bootstrap_por_transcricao(candidata, None, repeticoes, REAMOSTRAS, SEMENTE),
        ic_diferenca=bootstrap_por_transcricao(base, candidata, repeticoes, REAMOSTRAS, SEMENTE),
    )


def analisar(
    splits: list[Split],
    base: str,
    candidata: str,
    prompt_texto_por_versao: Callable[[str], str],
) -> Analise:
    if not splits:
        raise RecusaConfirmatorio("Recusa: nenhum split informado")

    por_versao: dict[str, list[ResultadoTranscricao]] = {base: [], candidata: []}
    rodadas: list[str] = []
    modelos: set[str] = set()
    repeticoes_vistas: set[int] = set()

    for split in splits:
        resumos = coletar_resumos(split.diretorio_rodadas, split.dataset, prompt_texto_por_versao)
        for versao in (base, candidata):
            resumo = _rodada_unica(resumos, versao, split.nome)
            repeticoes = len(resumo.contagens_por_repeticao)
            repeticoes_vistas.add(repeticoes)
            resultados = resultados_por_transcricao(
                split.diretorio_rodadas / resumo.id, split.dataset, repeticoes, split.nome
            )
            _conferir_contra_replay(resultados, resumo)
            por_versao[versao].extend(resultados)
            rodadas.append(f"{split.nome}/{resumo.id}")
            if resumo.modelo:
                modelos.add(resumo.modelo)

    if len(repeticoes_vistas) != 1:
        raise RecusaConfirmatorio(
            f"Recusa: número de Repetições diferente entre Rodadas ({sorted(repeticoes_vistas)})"
        )
    repeticoes = repeticoes_vistas.pop()

    rb, rc = por_versao[base], por_versao[candidata]
    if [(r.split, r.transcricao_id) for r in rb] != [(r.split, r.transcricao_id) for r in rc]:
        raise RecusaConfirmatorio("Recusa: as Transcrições da base e da candidata não estão pareadas")

    primaria = _metrica(
        "Violação de formato", [r.violacoes for r in rb], [r.violacoes for r in rc], repeticoes
    )
    secundaria = _metrica(
        "Não acerto (sem Rótulo válido e correto)",
        [r.nao_acertos for r in rb],
        [r.nao_acertos for r in rc],
        repeticoes,
    )
    descritivo = {
        "Erro de acerto": (sum(r.erros_de_acerto for r in rb), sum(r.erros_de_acerto for r in rc)),
        "Alucinação": (sum(r.alucinacoes for r in rb), sum(r.alucinacoes for r in rc)),
    }
    return Analise(
        base=base,
        candidata=candidata,
        repeticoes=repeticoes,
        transcricoes=len(rb),
        rodadas=rodadas,
        primaria=primaria,
        secundaria=secundaria,
        descritivo=descritivo,
        modelos=modelos,
        veredito=decidir(primaria.sinal, primaria.ic_diferenca),
    )


def _pct(valor: float) -> str:
    return f"{100 * valor:.1f}%"


def _pp(valor: float) -> str:
    return f"{100 * valor:+.1f} pp"


def _p(valor: float) -> str:
    return f"{valor:.2e}" if valor < 0.001 else f"{valor:.3f}"


def _linhas_metrica(m: AnaliseMetrica, analise: Analise) -> list[str]:
    r = analise.repeticoes
    chamadas = analise.transcricoes * r
    s = m.sinal
    return [
        f"| {analise.base} | {sum(m.falhas_base)}/{chamadas} | {_pct(taxa(m.falhas_base, r))} | "
        f"{_pct(m.ic_base.inferior)} a {_pct(m.ic_base.superior)} |",
        f"| {analise.candidata} | {sum(m.falhas_candidata)}/{chamadas} | {_pct(taxa(m.falhas_candidata, r))} | "
        f"{_pct(m.ic_candidata.inferior)} a {_pct(m.ic_candidata.superior)} |",
        "",
        f"Diferença ({analise.candidata} − {analise.base}): {_pp(m.ic_diferenca.estimativa)}, "
        f"IC 95% {_pp(m.ic_diferenca.inferior)} a {_pp(m.ic_diferenca.superior)}.",
        f"Teste do sinal (por Transcrição): {s.favoraveis_candidata} a favor de {analise.candidata}, "
        f"{s.favoraveis_base} a favor de {analise.base}, {s.empates} empates; p = {_p(s.p_valor)} (bicaudal, exato).",
    ]


def renderizar(analise: Analise) -> str:
    cabecalho = "| Versão | Chamadas com falha | Taxa | IC 95% (bootstrap por Transcrição) |"
    separador = "|---|---:|---:|---|"
    linhas = [
        f"# Experimento confirmatório (holdout): {analise.base} × {analise.candidata}",
        "",
        "Regras de decisão pré-registradas em docs/spec/cx-prompt-lab-preregistro-holdout.md, "
        "commitadas antes de qualquer Chamada no holdout. Calculado offline a partir das Chamadas gravadas.",
        "",
        f"Transcrições do holdout: {analise.transcricoes}; Repetições por Transcrição: {analise.repeticoes}; "
        f"Chamadas por versão: {analise.transcricoes * analise.repeticoes}.",
        f"Modelo devolvido: {', '.join(sorted(analise.modelos)) or 'desconhecido'}.",
        f"Rodadas: {', '.join(analise.rodadas)}.",
        f"Bootstrap: {REAMOSTRAS} reamostras de Transcrições, semente {SEMENTE}, IC percentil.",
        "",
        f"## Métrica primária: {analise.primaria.nome}",
        "",
        cabecalho,
        separador,
        *_linhas_metrica(analise.primaria, analise),
        "",
        f"## Métrica secundária: {analise.secundaria.nome}",
        "",
        cabecalho,
        separador,
        *_linhas_metrica(analise.secundaria, analise),
        "",
        "## Descritivo (sem teste)",
        "",
    ]
    for nome, (b, c) in analise.descritivo.items():
        linhas.append(f"- {nome}: {analise.base} {b}, {analise.candidata} {c} (Chamadas)")
    linhas += [
        "",
        "## Veredito pré-registrado",
        "",
        f"Veredito {analise.base} × {analise.candidata} na métrica primária: **{analise.veredito}** "
        f"(α = {ALFA}, margem de equivalência ±{100 * MARGEM_EQUIVALENCIA:.0f} pp).",
        "Escopo: um modelo, via Gateway local, temperatura efetiva desconhecida (ADR 0002); "
        "Dataset fictício. Não é validação contra a API oficial da Anthropic.",
    ]
    return "\n".join(linhas) + "\n"

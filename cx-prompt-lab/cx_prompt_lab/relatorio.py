"""Relatório: tabela por versão e todas as Rodadas, a partir do Replay (T3).

`gerar_relatorio(...)` varre `rodadas/` (e `rodadas/descartadas/`), identifica
o experimento atual pelo hash do Dataset e chama `replay.substituir` (T3) só
para as Rodadas completas desse experimento — o cálculo nunca duplica a
lógica de contagem do Executor. As demais Rodadas do repositório (abortadas,
de experimentos anteriores, descartadas ou que o Replay recusou) aparecem na
listagem como "fora do experimento" com o motivo; descartar uma Rodada não a
apaga nem a sobrescreve (ela continua em `rodadas/descartadas/<id>/`).

O veredito v0 × versão final e a lista de Transcrições que mudaram são do T10
(`veredito` fica de fora deste módulo); o teste de honestidade sobre os três
textos commitados é do T12. Este módulo só garante que o texto gerado carrega
o limite do Replay, a distinção Replay × Reexecução e o rótulo "exploratório".
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from cx_prompt_lab.dataset import Dataset
from cx_prompt_lab.executor import Contagens
from cx_prompt_lab.gravacao import Chamada, Manifesto, hash_dataset
from cx_prompt_lab.replay import RecusaReplay, substituir

NOME_DIRETORIO_DESCARTADAS = "descartadas"

LIMITE_REPLAY = (
    "Limite do Replay: este comando prova o cálculo a partir das Chamadas já "
    "gravadas, não que o modelo responderia igual hoje. Replay recalcula "
    "offline, sem chamar nenhum provider; Reexecução chama o provider de novo "
    "e pode produzir Chamadas diferentes."
)

RESULTADO_EXPLORATORIO = (
    "Resultado declarado como exploratório: as taxas abaixo não são prova "
    "estatística formal, servem para julgar a iteração do candidato entre "
    "versões de prompt."
)

AVISO_ANTHROPIC = (
    "Compatível com Anthropic: o formato de pedido/resposta segue o vocabulário "
    "da API Anthropic. Isto não é validação contra a API oficial."
)


@dataclass(frozen=True)
class ResumoRodada:
    id: str
    versao_prompt: str
    estado: str
    descartada: bool
    no_experimento: bool
    motivo_fora: str | None = None
    modelo: str | None = None
    data: str | None = None
    contagens_por_repeticao: list[Contagens] = field(default_factory=list)


def _ler_manifesto(caminho_manifesto: Path) -> Manifesto | None:
    try:
        return Manifesto.de_dict(json.loads(caminho_manifesto.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def _metadados_das_chamadas(caminho_rodada: Path) -> tuple[str | None, str | None]:
    """Modelo (o primeiro encontrado) e intervalo de `criado_em` das Chamadas
    gravadas — não o mtime do arquivo, que não sobrevive a um `git clone`
    (ver ADR 0002)."""
    modelo: str | None = None
    datas: list[str] = []

    for caminho in sorted(caminho_rodada.glob("*.json")):
        if caminho.name == "manifest.json":
            continue
        try:
            chamada = Chamada.de_dict(json.loads(caminho.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError):
            continue
        if modelo is None:
            modelo = chamada.modelo
        datas.append(chamada.criado_em)

    if not datas:
        return modelo, None

    minimo, maximo = min(datas), max(datas)
    data_texto = minimo if minimo == maximo else f"{minimo} a {maximo}"
    return modelo, data_texto


def _resumo_fora(manifesto: Manifesto, descartada: bool, motivo: str) -> ResumoRodada:
    return ResumoRodada(
        id=manifesto.rodada_id,
        versao_prompt=manifesto.versao_prompt,
        estado=manifesto.estado,
        descartada=descartada,
        no_experimento=False,
        motivo_fora=motivo,
    )


def coletar_resumos(
    diretorio_rodadas: Path,
    dataset: Dataset,
    prompt_texto_por_versao: Callable[[str], str],
) -> list[ResumoRodada]:
    diretorio_rodadas = Path(diretorio_rodadas)
    hash_dataset_atual = hash_dataset(dataset)
    total_transcricoes = len(dataset.transcricoes)

    candidatos: list[tuple[Path, bool]] = []
    if diretorio_rodadas.exists():
        for item in sorted(diretorio_rodadas.iterdir()):
            if not item.is_dir() or item.name == NOME_DIRETORIO_DESCARTADAS:
                continue
            candidatos.append((item, False))

        diretorio_descartadas = diretorio_rodadas / NOME_DIRETORIO_DESCARTADAS
        if diretorio_descartadas.exists():
            for item in sorted(diretorio_descartadas.iterdir()):
                if item.is_dir():
                    candidatos.append((item, True))

    resumos: list[ResumoRodada] = []
    for caminho_rodada, descartada in candidatos:
        manifesto = _ler_manifesto(caminho_rodada / "manifest.json")
        if manifesto is None:
            continue

        if descartada:
            resumos.append(
                _resumo_fora(manifesto, True, f"descartada (ver {caminho_rodada})")
            )
            continue

        if manifesto.estado != "completa":
            resumos.append(
                _resumo_fora(manifesto, False, f"não completa (estado: {manifesto.estado})")
            )
            continue

        if manifesto.hash_dataset != hash_dataset_atual:
            resumos.append(
                _resumo_fora(manifesto, False, "dataset diferente (outro experimento)")
            )
            continue

        if total_transcricoes == 0 or manifesto.numero_esperado_chamadas % total_transcricoes != 0:
            resumos.append(
                _resumo_fora(manifesto, False, "número de Chamadas não bate com o Dataset atual")
            )
            continue

        repeticoes_da_rodada = manifesto.numero_esperado_chamadas // total_transcricoes

        try:
            prompt_texto = prompt_texto_por_versao(manifesto.versao_prompt)
            rodada = substituir(
                caminho_rodada=caminho_rodada,
                dataset=dataset,
                prompt_texto=prompt_texto,
                repeticoes=repeticoes_da_rodada,
            )
        except (RecusaReplay, ValueError, KeyError, FileNotFoundError) as erro:
            resumos.append(_resumo_fora(manifesto, False, f"Replay recusou: {erro}"))
            continue

        modelo, data = _metadados_das_chamadas(caminho_rodada)
        resumos.append(
            ResumoRodada(
                id=manifesto.rodada_id,
                versao_prompt=manifesto.versao_prompt,
                estado=manifesto.estado,
                descartada=False,
                no_experimento=True,
                modelo=modelo,
                data=data,
                contagens_por_repeticao=rodada.contagens_por_repeticao,
            )
        )

    return resumos


def _percentual(numerador: int, denominador: int) -> str:
    if denominador == 0:
        return "n/d"
    return f"{100 * numerador / denominador:.1f}%"


def renderizar(resumos: list[ResumoRodada], dataset: Dataset) -> str:
    total_transcricoes = len(dataset.transcricoes)
    por_versao = {r.versao_prompt: r for r in resumos if r.no_experimento}

    linhas: list[str] = []
    linhas.append("# Relatório (Replay)")
    linhas.append("")
    linhas.append(RESULTADO_EXPLORATORIO)
    linhas.append(LIMITE_REPLAY)
    linhas.append("")

    linhas.append("## Tabela por versão")
    linhas.append("")
    if not por_versao:
        linhas.append("Nenhuma Rodada completa do experimento atual foi encontrada.")
    else:
        linhas.append("| Versão | Erro de acerto | Alucinação | Violação de formato |")
        linhas.append("|---|---|---|---|")
        for versao in sorted(por_versao):
            resumo = por_versao[versao]
            total_chamadas = total_transcricoes * len(resumo.contagens_por_repeticao)
            soma_erro = sum(c.erro_de_acerto for c in resumo.contagens_por_repeticao)
            soma_aluc = sum(c.alucinacao_total for c in resumo.contagens_por_repeticao)
            soma_formato = sum(c.violacao_de_formato for c in resumo.contagens_por_repeticao)
            linhas.append(
                f"| {versao} | {_percentual(soma_erro, total_chamadas)} | "
                f"{_percentual(soma_aluc, total_chamadas)} | {_percentual(soma_formato, total_chamadas)} |"
            )
            linhas.append(
                f"  modelo: {resumo.modelo or 'desconhecido'}; data das Chamadas: {resumo.data or 'desconhecida'}"
            )

    linhas.append("")
    linhas.append("## Resultado de cada Repetição")
    linhas.append("")
    if not por_versao:
        linhas.append("n/d — nenhuma Rodada do experimento atual.")
    for versao in sorted(por_versao):
        resumo = por_versao[versao]
        linhas.append(f"Versão {versao}:")
        for indice, contagens in enumerate(resumo.contagens_por_repeticao, start=1):
            linhas.append(
                f"  Repetição {indice}: erro de acerto={contagens.erro_de_acerto}, "
                f"alucinação={contagens.alucinacao_total}, "
                f"violação de formato={contagens.violacao_de_formato}"
            )

    linhas.append("")
    linhas.append("## Todas as Rodadas do repositório")
    linhas.append("")
    if not resumos:
        linhas.append("Nenhuma Rodada gravada em disco.")
    for resumo in resumos:
        if resumo.no_experimento:
            linhas.append(
                f"- {resumo.id} (versão {resumo.versao_prompt}, estado {resumo.estado}): no experimento atual"
            )
        else:
            linhas.append(
                f"- {resumo.id} (versão {resumo.versao_prompt}, estado {resumo.estado}): "
                f"fora do experimento — {resumo.motivo_fora}"
            )

    linhas.append("")
    linhas.append(AVISO_ANTHROPIC)

    return "\n".join(linhas) + "\n"


def gerar_relatorio(
    diretorio_rodadas: Path,
    dataset: Dataset,
    prompt_texto_por_versao: Callable[[str], str],
) -> str:
    resumos = coletar_resumos(diretorio_rodadas, dataset, prompt_texto_por_versao)
    return renderizar(resumos, dataset)

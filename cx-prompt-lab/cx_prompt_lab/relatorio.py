"""Relatório: tabela por versão e todas as Rodadas, a partir do Replay (T3).

`gerar_relatorio(...)` varre `rodadas/` (e `rodadas/descartadas/`), identifica
o experimento atual pelo hash do Dataset e chama `replay.substituir` (T3) só
para as Rodadas completas desse experimento — o cálculo nunca duplica a
lógica de contagem do Executor. As demais Rodadas do repositório (abortadas,
de experimentos anteriores, descartadas ou que o Replay recusou) aparecem na
listagem como "fora do experimento" com o motivo; descartar uma Rodada não a
apaga nem a sobrescreve (ela continua em `rodadas/descartadas/<id>/`).

O veredito v0 × versão final vem de `conclusao.concluir` (T10) e usa só as
Rodadas do experimento; pares intermediários e a lista ilustrativa de
Transcrições que mudaram (Repetição 1 de cada versão) são informativos. O
teste de honestidade sobre os três textos commitados é do T12. Este módulo
garante que o texto gerado carrega o limite do Replay, a distinção
Replay × Reexecução e o rótulo "exploratório".
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from cx_prompt_lab.conclusao import (
    EFEITO_PISO,
    INCONCLUSIVO,
    MELHORA,
    NAO_COMPARAVEL,
    PIORA,
    CondicoesExecucao,
    concluir,
)
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
    rotulos_por_repeticao: list[dict[str, str | None]] = field(default_factory=list)
    parametros: dict = field(default_factory=dict)


ROTULO_DO_VEREDITO = {
    NAO_COMPARAVEL: "não comparável",
    PIORA: "piora",
    EFEITO_PISO: "inconclusivo por efeito piso",
    MELHORA: "melhora",
    INCONCLUSIVO: "inconclusivo",
}
SEM_ROTULO_VALIDO = "sem rótulo válido"


def _ordem_versao(versao: str) -> tuple[int, int, str]:
    """v0 < v1 < v2 < v10; nomes fora do padrão vN vão depois, em ordem alfabética."""
    encontrado = re.fullmatch(r"v(\d+)", versao)
    if encontrado:
        return (0, int(encontrado.group(1)), versao)
    return (1, 0, versao)


def _ler_manifesto(caminho_manifesto: Path) -> Manifesto | None:
    try:
        return Manifesto.de_dict(json.loads(caminho_manifesto.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def _metadados_das_chamadas(caminho_rodada: Path) -> tuple[str | None, str | None]:
    """Modelo (o primeiro encontrado) e intervalo de `criado_em` das Chamadas
    gravadas — não o mtime do arquivo, que não sobrevive a um `git clone`
    (ver ADR 0002)."""
    modelos: set[str] = set()
    datas: list[str] = []

    for caminho in sorted(caminho_rodada.glob("*.json")):
        if caminho.name == "manifest.json":
            continue
        try:
            chamada = Chamada.de_dict(json.loads(caminho.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError):
            continue
        modelos.add(chamada.modelo)
        datas.append(chamada.criado_em)

    modelo = ", ".join(sorted(modelos)) if modelos else None
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
                rotulos_por_repeticao=rodada.rotulos_por_repeticao,
                parametros=manifesto.parametros_efetivos,
            )
        )

    return resumos


def _condicoes(resumo: ResumoRodada) -> CondicoesExecucao:
    return CondicoesExecucao(modelo=resumo.modelo, parametros=resumo.parametros)


def _secao_veredito(por_versao: dict[str, ResumoRodada]) -> list[str]:
    linhas = ["", "## Veredito (exploratório)", ""]
    versoes = sorted(por_versao, key=_ordem_versao)

    if "v0" not in por_versao:
        linhas.append("Veredito: indisponível — nenhuma Rodada completa de v0 no experimento atual.")
        return linhas
    if len(versoes) < 2:
        linhas.append("Veredito: indisponível — só v0 tem Rodada completa; falta uma versão final.")
        return linhas

    final = versoes[-1]
    veredito = concluir(
        por_versao["v0"].contagens_por_repeticao,
        por_versao[final].contagens_por_repeticao,
        _condicoes(por_versao["v0"]),
        _condicoes(por_versao[final]),
    )
    linhas.append(f"Veredito v0 × {final}: {ROTULO_DO_VEREDITO[veredito.resultado]}")
    for diferenca in veredito.diferencas:
        linhas.append(f"  diferença: {diferenca}")
    if veredito.resultado == EFEITO_PISO:
        erro_v0 = [c.erro_de_acerto for c in por_versao["v0"].contagens_por_repeticao]
        erro_final = [c.erro_de_acerto for c in por_versao[final].contagens_por_repeticao]
        linhas.append(
            f"Métrica secundária (Erro de acerto por Repetição): v0 {erro_v0}, {final} {erro_final}; "
            "nenhuma melhora é declarada."
        )
    linhas.append(
        "Só v0 × versão final tem veredito; resultado exploratório, sem prova estatística formal."
    )

    intermediarios = list(zip(versoes, versoes[1:])) if len(versoes) > 2 else []
    if intermediarios:
        linhas.append("")
        linhas.append("Pares intermediários (informativos, sem veredito):")
        for antes, depois in intermediarios:
            linhas.append(f"- {antes} → {depois}: informativo, sem veredito")
            for versao in (antes, depois):
                for indice, c in enumerate(por_versao[versao].contagens_por_repeticao, start=1):
                    linhas.append(
                        f"    {versao} Repetição {indice}: erro de acerto={c.erro_de_acerto}, "
                        f"alucinação={c.alucinacao_total}, violação de formato={c.violacao_de_formato}, "
                        f"acertos={c.acertos}"
                    )
    return linhas


def _secao_mudancas(por_versao: dict[str, ResumoRodada]) -> list[str]:
    linhas = ["", "## Transcrições que mudaram de Rótulo (ilustrativa)", ""]
    versoes = sorted(por_versao, key=_ordem_versao)
    if len(versoes) < 2:
        linhas.append("n/d — é preciso ao menos duas versões com Rodada completa.")
        return linhas

    linhas.append(
        "Lista ilustrativa: compara só a Repetição 1 de cada versão consecutiva; "
        f'resposta sem Rótulo válido aparece como "{SEM_ROTULO_VALIDO}".'
    )
    for antes, depois in zip(versoes, versoes[1:]):
        rotulos_antes = por_versao[antes].rotulos_por_repeticao[0]
        rotulos_depois = por_versao[depois].rotulos_por_repeticao[0]
        linhas.append("")
        linhas.append(f"{antes} → {depois} (Repetição 1):")
        mudou = False
        for transcricao_id in rotulos_antes:
            rotulo_antes = rotulos_antes[transcricao_id] or SEM_ROTULO_VALIDO
            rotulo_depois = rotulos_depois.get(transcricao_id) or SEM_ROTULO_VALIDO
            if rotulo_antes != rotulo_depois:
                mudou = True
                linhas.append(f"- {transcricao_id}: {rotulo_antes} → {rotulo_depois}")
        if not mudou:
            linhas.append("- nenhuma Transcrição mudou de Rótulo")
    return linhas


METRICAS_DA_MARGEM = (
    ("erro_de_acerto", "erro de acerto"),
    ("alucinacao_total", "alucinação"),
    ("violacao_de_formato", "violação de formato"),
)

TEXTO_MARGEM = (
    "Margem de variação: amplitude (maior menos menor) da taxa entre as Repetições "
    "da versão, em pontos percentuais de taxa. A margem vale para a Reexecução: "
    "diferença menor que ela entre Rodadas novas pode ser ruído. O Replay não "
    "tem ruído, o Replay bate exatamente. A margem é só descritiva e não decide "
    "nenhum veredito (o veredito é o da seção acima)."
)


def margem_de_variacao(contagens: list[Contagens], total_transcricoes: int) -> dict[str, float]:
    """Amplitude (máx − mín) da taxa por Repetição, em pontos percentuais, por métrica."""
    margens: dict[str, float] = {}
    for atributo, _ in METRICAS_DA_MARGEM:
        taxas = [100 * getattr(c, atributo) / total_transcricoes for c in contagens]
        margens[atributo] = max(taxas) - min(taxas)
    return margens


def _pp(valor: float) -> str:
    return f"{valor:.1f} pp"


def _secao_margem(por_versao: dict[str, ResumoRodada], total_transcricoes: int) -> list[str]:
    linhas = ["", "## Margem de variação da Reexecução", "", TEXTO_MARGEM, ""]
    if not por_versao or total_transcricoes == 0:
        linhas.append("n/d — nenhuma Rodada do experimento atual.")
        return linhas
    for versao in sorted(por_versao, key=_ordem_versao):
        margens = margem_de_variacao(por_versao[versao].contagens_por_repeticao, total_transcricoes)
        partes = ", ".join(f"{nome} {_pp(margens[atributo])}" for atributo, nome in METRICAS_DA_MARGEM)
        linhas.append(f"- {versao}: {partes}")
    return linhas


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
                f"violação de formato={contagens.violacao_de_formato}, "
                f"acertos={contagens.acertos}"
            )

    linhas.extend(_secao_veredito(por_versao))
    linhas.extend(_secao_margem(por_versao, total_transcricoes))
    linhas.extend(_secao_mudancas(por_versao))

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

"""Conclusão: veredito v0 × versão final, função pura sobre contagens (sem I/O).

Só v0 × versão final tem veredito; pares intermediários são informativos e não
passam por aqui. Todas as comparações usam contagens inteiras. Ordem de
precedência, parando na primeira condição que valer: não comparável, piora,
inconclusivo por efeito piso, melhora, inconclusivo. Ver "Regra de melhora"
em docs/spec/cx-prompt-lab.md (CAR-18).
"""

from dataclasses import dataclass, field

from cx_prompt_lab.executor import Contagens

NAO_COMPARAVEL = "nao_comparavel"
PIORA = "piora"
EFEITO_PISO = "inconclusivo_efeito_piso"
MELHORA = "melhora"
INCONCLUSIVO = "inconclusivo"

# Parâmetros de geração que a pré-condição de comparabilidade exige iguais.
PARAMETROS_COMPARADOS = ("temperature", "max_tokens")
QUEDA_MINIMA_ALUCINACAO = 2
PISO_ALUCINACAO = 1


@dataclass(frozen=True)
class CondicoesExecucao:
    modelo: str | None
    parametros: dict


@dataclass(frozen=True)
class Veredito:
    resultado: str
    diferencas: list[str] = field(default_factory=list)


def _diferencas(v0: CondicoesExecucao, final: CondicoesExecucao) -> list[str]:
    diferencas: list[str] = []
    if v0.modelo != final.modelo:
        diferencas.append(f"modelo: v0 usou {v0.modelo!r}, versão final usou {final.modelo!r}")
    for chave in PARAMETROS_COMPARADOS:
        valor_v0, valor_final = v0.parametros.get(chave), final.parametros.get(chave)
        if valor_v0 != valor_final:
            diferencas.append(f"{chave}: v0 usou {valor_v0!r}, versão final usou {valor_final!r}")
    return diferencas


def concluir(
    contagens_v0: list[Contagens],
    contagens_final: list[Contagens],
    condicoes_v0: CondicoesExecucao,
    condicoes_final: CondicoesExecucao,
) -> Veredito:
    diferencas = _diferencas(condicoes_v0, condicoes_final)
    if diferencas:
        return Veredito(NAO_COMPARAVEL, diferencas)

    aluc_v0 = [c.alucinacao_total for c in contagens_v0]
    aluc_final = [c.alucinacao_total for c in contagens_final]

    if sum(aluc_final) * len(aluc_v0) > sum(aluc_v0) * len(aluc_final):
        return Veredito(PIORA)

    if any(a <= PISO_ALUCINACAO for a in aluc_v0):
        return Veredito(EFEITO_PISO)

    formato_v0 = [c.violacao_de_formato for c in contagens_v0]
    formato_final = [c.violacao_de_formato for c in contagens_final]
    acertos_v0 = [c.acertos for c in contagens_v0]
    acertos_final = [c.acertos for c in contagens_final]

    if (
        min(aluc_v0) - max(aluc_final) >= QUEDA_MINIMA_ALUCINACAO
        and max(formato_final) <= min(formato_v0)
        and min(acertos_final) >= max(acertos_v0)
    ):
        return Veredito(MELHORA)

    return Veredito(INCONCLUSIVO)

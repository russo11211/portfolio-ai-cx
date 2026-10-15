"""Avaliador: aplica o Contrato de saída e classifica a resposta.

Contrato de saída: objeto JSON com dois campos de texto, "rotulo" e
"justificativa". Parser estrito: não remove code fence nem prosa ao redor;
campos extras são ignorados. Ver docs/spec/cx-prompt-lab.md, tabela de
contagem (a)-(f).
"""

import json
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Resultado:
    veredito_de_forma: str  # "ok" | "violacao_de_formato"
    erro_de_acerto: bool
    alucinacao_rotulo_inexistente: bool
    alucinacao_justificativa_nao_ancorada: bool
    rotulo: str | None = None
    justificativa: str | None = None


def _violacao_de_formato() -> Resultado:
    return Resultado(
        veredito_de_forma="violacao_de_formato",
        erro_de_acerto=False,
        alucinacao_rotulo_inexistente=False,
        alucinacao_justificativa_nao_ancorada=False,
    )


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.replace(" ", " ")
    texto = " ".join(texto.split())
    return texto.strip()


def avaliar(
    resposta_bruta: str,
    rotulo_esperado: str,
    transcricao: str,
    rotulos_validos: list[str],
) -> Resultado:
    if not resposta_bruta or not resposta_bruta.strip():
        return _violacao_de_formato()

    try:
        dado = json.loads(resposta_bruta)
    except json.JSONDecodeError:
        return _violacao_de_formato()

    if not isinstance(dado, dict):
        return _violacao_de_formato()

    rotulo_bruto = dado.get("rotulo")
    justificativa_bruta = dado.get("justificativa")

    if not isinstance(rotulo_bruto, str) or not isinstance(justificativa_bruta, str):
        return _violacao_de_formato()

    rotulo = rotulo_bruto.strip()
    if not rotulo:
        return _violacao_de_formato()

    if not justificativa_bruta.strip():
        return _violacao_de_formato()

    if rotulo not in rotulos_validos:
        return Resultado(
            veredito_de_forma="ok",
            erro_de_acerto=True,
            alucinacao_rotulo_inexistente=True,
            alucinacao_justificativa_nao_ancorada=False,
            rotulo=rotulo,
            justificativa=justificativa_bruta,
        )

    erro_de_acerto = rotulo != rotulo_esperado

    justificativa_ancorada = _normalizar(justificativa_bruta) in _normalizar(transcricao)

    return Resultado(
        veredito_de_forma="ok",
        erro_de_acerto=erro_de_acerto,
        alucinacao_rotulo_inexistente=False,
        alucinacao_justificativa_nao_ancorada=not justificativa_ancorada,
        rotulo=rotulo,
        justificativa=justificativa_bruta,
    )

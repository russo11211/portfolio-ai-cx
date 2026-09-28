"""CLI: seam fino, só chama os módulos de domínio.

Por enquanto só o subcomando `replay` (T9). Os demais (`reexecutar`, `rodada
--descartar`) chegam nos tickets que os exigem (T1, T3, T4, T5).
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from cx_prompt_lab.dataset import Dataset, RecusaDataset, carregar
from cx_prompt_lab.relatorio import gerar_relatorio

BANNER_REPLAY = "REPLAY (offline, nenhum modelo chamado)"


def _prompt_texto_por_versao(diretorio_prompts: Path) -> Callable[[str], str]:
    def carregar_prompt(versao: str) -> str:
        caminho = diretorio_prompts / f"{versao}.md"
        return caminho.read_text(encoding="utf-8")

    return carregar_prompt


def _cmd_replay(args: argparse.Namespace) -> int:
    print(BANNER_REPLAY)

    try:
        dataset: Dataset = carregar(Path(args.dataset))
    except RecusaDataset as erro:
        print(str(erro), file=sys.stderr)
        return 1

    texto = gerar_relatorio(
        diretorio_rodadas=Path(args.rodadas),
        dataset=dataset,
        prompt_texto_por_versao=_prompt_texto_por_versao(Path(args.prompts)),
    )
    print(texto)
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cx_prompt_lab")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    replay = subparsers.add_parser(
        "replay",
        help="Recalcula o Relatório offline a partir das Chamadas gravadas, sem chave e sem Gateway.",
    )
    replay.add_argument(
        "--rodada",
        dest="rodadas",
        default="rodadas",
        help=(
            "Diretório-raiz com as Rodadas gravadas, uma subpasta por Rodada "
            "(default: rodadas/). O Relatório lista todas as Rodadas encontradas "
            "aqui, não só uma."
        ),
    )
    replay.add_argument(
        "--dataset",
        default="dataset/transcricoes.json",
        help="Caminho do Dataset (default: dataset/transcricoes.json).",
    )
    replay.add_argument(
        "--prompts",
        default="prompts",
        help="Diretório com os arquivos de prompt, um por versão (default: prompts/).",
    )
    replay.set_defaults(func=_cmd_replay)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI: seam fino para Replay e Reexecução de Rodada."""

import argparse
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from cx_prompt_lab import confirmatorio
from cx_prompt_lab.dataset import Dataset, RecusaDataset, carregar
from cx_prompt_lab.executor import AbortoRodada, rodar
from cx_prompt_lab.gravacao import (
    ESTADO_ABORTADA,
    ESTADO_COMPLETA,
    ProviderGravador,
    RecusaGravacao,
    gravar,
    hash_texto,
)
from cx_prompt_lab.provider import GatewayProvider
from cx_prompt_lab.relatorio import gerar_relatorio

BANNER_REPLAY = "REPLAY (offline, nenhum modelo chamado)"
BANNER_REEXECUCAO = "REEXECUÇÃO (ao vivo)"
BANNER_CONFIRMAR = "CONFIRMATÓRIO (offline, nenhum modelo chamado)"
SPLITS_PREREGISTRADOS = (
    ("holdout_a", "rodadas-holdout/holdout_a", "dataset/holdout_a.json"),
    ("holdout_b", "rodadas-holdout/holdout_b", "dataset/holdout_b.json"),
)


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


def _cmd_confirmar(args: argparse.Namespace) -> int:
    print(BANNER_CONFIRMAR)
    try:
        splits = [
            confirmatorio.Split(nome=nome, diretorio_rodadas=Path(rodadas), dataset=carregar(Path(dataset)))
            for nome, rodadas, dataset in (args.splits or SPLITS_PREREGISTRADOS)
        ]
        analise = confirmatorio.analisar(
            splits=splits,
            base=args.base,
            candidata=args.candidata,
            prompt_texto_por_versao=_prompt_texto_por_versao(Path(args.prompts)),
        )
    except (RecusaDataset, confirmatorio.RecusaConfirmatorio) as erro:
        print(str(erro), file=sys.stderr)
        return 1
    print(confirmatorio.renderizar(analise))
    return 0


def _cmd_reexecutar(args: argparse.Namespace) -> int:
    print(BANNER_REEXECUCAO)

    if args.provider != "gateway":
        print(
            f"Reexecução indisponível: provider {args.provider} ainda não implementado — "
            "próximo passo: use --provider gateway",
            file=sys.stderr,
        )
        return 2
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.prompt):
        print("Versão de prompt inválida — próximo passo: use um nome como v0", file=sys.stderr)
        return 2
    if args.rodada_id is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.rodada_id):
        print(
            "Identificador de Rodada inválido — próximo passo: use letras, números, _ ou -",
            file=sys.stderr,
        )
        return 2
    if not args.modelo:
        print("Modelo ausente — próximo passo: use --modelo ou CXLAB_MODEL", file=sys.stderr)
        return 2
    chave = os.environ.get("CXLAB_GATEWAY_KEY")
    if not chave:
        print(
            "Chave local do Gateway ausente — próximo passo: configure CXLAB_GATEWAY_KEY no ambiente",
            file=sys.stderr,
        )
        return 2
    if args.repeticoes < 3 or args.max_tokens < 1 or args.timeout_s <= 0 or not 0 <= args.temperatura <= 1:
        print(
            "Parâmetros inválidos — próximo passo: use --repeticoes >= 3, --max-tokens >= 1, "
            "--timeout-s > 0 e --temperatura entre 0 e 1",
            file=sys.stderr,
        )
        return 2

    try:
        dataset = carregar(Path(args.dataset))
        caminho_prompt = Path(args.prompts) / f"{args.prompt}.md"
        prompt_texto = caminho_prompt.read_text(encoding="utf-8")
    except RecusaDataset as erro:
        print(str(erro), file=sys.stderr)
        return 1
    except OSError:
        print(
            f"Prompt {caminho_prompt} não pôde ser lido — próximo passo: confira --prompts e --prompt",
            file=sys.stderr,
        )
        return 2

    rodada_id = args.rodada_id or f"rodada-{uuid4().hex[:12]}"
    parametros_pedidos = {
        "provider": "gateway",
        "modelo_pedido": args.modelo,
        "temperature_pedida": args.temperatura,
        "max_tokens": args.max_tokens,
    }
    provider = GatewayProvider(
        endpoint_url=args.endpoint_url,
        chave=chave,
        modelo=args.modelo,
        max_tokens=args.max_tokens,
        temperatura=args.temperatura,
        timeout_s=args.timeout_s,
    )
    gravador = ProviderGravador(
        provider=provider,
        dataset=dataset,
        rodada_id=rodada_id,
        hash_prompt=hash_texto(prompt_texto),
        parametros_geracao={"max_tokens": args.max_tokens},
    )
    estado = ESTADO_COMPLETA
    aborto = None
    try:
        rodar(
            versao_prompt=args.prompt,
            prompt_texto=prompt_texto,
            dataset=dataset,
            provider=gravador,
            repeticoes=args.repeticoes,
            timeout_s=args.timeout_s,
            rodada_id=rodada_id,
        )
    except AbortoRodada as erro:
        estado = ESTADO_ABORTADA
        aborto = erro

    try:
        gravar(
            diretorio_rodadas=Path(args.rodadas),
            rodada_id=rodada_id,
            versao_prompt=args.prompt,
            prompt_texto=prompt_texto,
            dataset=dataset,
            chamadas=gravador.chamadas,
            repeticoes=args.repeticoes,
            parametros_efetivos=parametros_pedidos,
            estado=estado,
        )
    except RecusaGravacao as erro:
        print(str(erro), file=sys.stderr)
        return 2

    print(f"Rodada {rodada_id} {estado}: {len(gravador.chamadas)} Chamadas gravadas em {args.rodadas}")
    if aborto is not None:
        print(str(aborto), file=sys.stderr)
        return 2
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

    confirmar = subparsers.add_parser(
        "confirmar",
        help=(
            "Experimento confirmatório pré-registrado (holdout): teste do sinal e bootstrap "
            "por Transcrição, offline, a partir das Chamadas gravadas."
        ),
    )
    confirmar.add_argument("--base", default="v0", help="Versão de referência (default: v0).")
    confirmar.add_argument("--candidata", default="v1", help="Versão candidata (default: v1).")
    confirmar.add_argument("--prompts", default="prompts", help="Diretório dos prompts.")
    confirmar.add_argument(
        "--split",
        dest="splits",
        nargs=3,
        action="append",
        metavar=("NOME", "RODADAS", "DATASET"),
        help="Split do holdout (repetível). Default: os dois splits pré-registrados.",
    )
    confirmar.set_defaults(func=_cmd_confirmar)

    reexecutar = subparsers.add_parser(
        "reexecutar",
        help="Executa uma nova Rodada ao vivo pelo Gateway e grava as Chamadas.",
    )
    reexecutar.add_argument("--prompt", required=True, help="Versão de prompt, como v0.")
    reexecutar.add_argument("--prompts", default="prompts", help="Diretório dos prompts.")
    reexecutar.add_argument("--dataset", default="dataset/transcricoes.json")
    reexecutar.add_argument("--rodadas", default="rodadas")
    reexecutar.add_argument("--rodada-id", default=None, help="Identificador único opcional da Rodada.")
    reexecutar.add_argument("--repeticoes", type=int, default=3)
    reexecutar.add_argument(
        "--provider", choices=("gateway", "anthropic", "groq"),
        default=os.environ.get("CXLAB_PROVIDER", "gateway"),
    )
    reexecutar.add_argument(
        "--endpoint-url", default=os.environ.get("CXLAB_GATEWAY_URL", "http://127.0.0.1:8317")
    )
    reexecutar.add_argument("--modelo", default=os.environ.get("CXLAB_MODEL"))
    reexecutar.add_argument("--max-tokens", type=int, default=256)
    reexecutar.add_argument("--temperatura", type=float, default=0)
    reexecutar.add_argument("--timeout-s", type=float, default=30)
    reexecutar.set_defaults(func=_cmd_reexecutar)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

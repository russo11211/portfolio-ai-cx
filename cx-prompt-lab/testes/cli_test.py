import json
import subprocess
import sys
from pathlib import Path

from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.executor import rodar
from cx_prompt_lab.gravacao import ProviderGravador, gravar, hash_texto
from cx_prompt_lab.provider import RespostaProvider

ROTULOS_VALIDOS = ["cancelamento", "duvida"]
RESPOSTA_CORRETA = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o meu plano"}'


class FakeProvider:
    def __init__(self, respostas: list[str]):
        self._respostas = respostas
        self._indice = 0

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        texto = self._respostas[self._indice]
        self._indice += 1
        return RespostaProvider(texto=texto, motivo_parada="fim_normal", modelo="fake-model", temperatura=0.2)


def _preparar_projeto(base: Path) -> None:
    transcricoes_brutas = [
        {
            "id": f"t{indice:02d}",
            "texto": (
                f"Cliente {indice} quer cancelar o plano."
                if indice % 2
                else f"Cliente {indice} tem duvida sobre a fatura."
            ),
            "rotulo_esperado": "cancelamento" if indice % 2 else "duvida",
        }
        for indice in range(1, 21)
    ]
    transcricoes_brutas[0]["intencao_dupla"] = True
    transcricoes_brutas[1]["ambiguo"] = True

    diretorio_dataset = base / "dataset"
    diretorio_dataset.mkdir()
    (diretorio_dataset / "transcricoes.json").write_text(
        json.dumps(
            {
                "rotulos_validos": ROTULOS_VALIDOS,
                "transcricoes": transcricoes_brutas,
                "regra_desempate": "sem empate possível neste dataset de teste",
            }
        ),
        encoding="utf-8",
    )

    dataset_real = Dataset(
        transcricoes=[
            Transcricao(id=t["id"], texto=t["texto"], rotulo_esperado=t["rotulo_esperado"])
            for t in transcricoes_brutas
        ],
        rotulos_validos=ROTULOS_VALIDOS,
    )

    diretorio_prompts = base / "prompts"
    diretorio_prompts.mkdir()
    prompt_texto = "v0: responda em JSON com rotulo e justificativa"
    (diretorio_prompts / "v0.md").write_text(prompt_texto, encoding="utf-8")

    repeticoes = 3
    respostas = [RESPOSTA_CORRETA] * (len(dataset_real.transcricoes) * repeticoes)
    fake = FakeProvider(respostas)
    gravador = ProviderGravador(
        provider=fake,
        dataset=dataset_real,
        rodada_id="rodada-v0",
        hash_prompt=hash_texto(prompt_texto),
    )
    rodar(versao_prompt=prompt_texto, dataset=dataset_real, provider=gravador, repeticoes=repeticoes)
    gravar(
        diretorio_rodadas=base / "rodadas",
        rodada_id="rodada-v0",
        versao_prompt="v0",
        prompt_texto=prompt_texto,
        dataset=dataset_real,
        chamadas=gravador.chamadas,
        repeticoes=repeticoes,
        parametros_efetivos={"temperature": 0.2},
    )


def test_comando_replay_imprime_banner_e_relatorio_sem_rede(tmp_path):
    _preparar_projeto(tmp_path)

    resultado = subprocess.run(
        [sys.executable, "-m", "cx_prompt_lab", "replay"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.startswith("REPLAY (offline, nenhum modelo chamado)")
    assert "Tabela por versão" in resultado.stdout
    assert "rodada-v0" in resultado.stdout

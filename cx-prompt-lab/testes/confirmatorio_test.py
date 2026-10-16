import json
import subprocess
import sys
from pathlib import Path

import pytest

from cx_prompt_lab.confirmatorio import (
    INCONCLUSIVO,
    MELHORA_CONFIRMADA,
    PIORA_CONFIRMADA,
    SEM_DIFERENCA_RELEVANTE,
    RecusaConfirmatorio,
    Split,
    analisar,
    decidir,
    renderizar,
)
from cx_prompt_lab.dataset import Dataset, Transcricao
from cx_prompt_lab.estatistica import IntervaloBootstrap, ResultadoSinal
from cx_prompt_lab.executor import rodar
from cx_prompt_lab.gravacao import ProviderGravador, gravar, hash_texto
from cx_prompt_lab.provider import RespostaProvider

ROTULOS = ["cancelamento"]
PROMPTS = {"v0": "prompt v0 de teste", "v1": "prompt v1 de teste"}
REPETICOES = 3


def _dataset(prefixo: str, n: int = 6) -> Dataset:
    return Dataset(
        transcricoes=[
            Transcricao(id=f"{prefixo}{i}", texto=f"Cliente {prefixo}{i}: quero cancelar o plano.", rotulo_esperado="cancelamento")
            for i in range(n)
        ],
        rotulos_validos=ROTULOS,
        regra_desempate="vale a primeira intenção",
    )


class ProviderRoteirizado:
    """Responde em bloco de código (Violação de formato) para as Transcrições em `falha`,
    e em JSON correto para as demais."""

    def __init__(self, falha: set[str], modelo: str = "modelo-teste"):
        self._falha = falha
        self._modelo = modelo

    def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
        corpo = '{"rotulo": "cancelamento", "justificativa": "quero cancelar o plano"}'
        id_transcricao = transcricao.split(":")[0].removeprefix("Cliente ")
        texto = f"```json\n{corpo}\n```" if id_transcricao in self._falha else corpo
        return RespostaProvider(texto=texto, motivo_parada="fim_normal", modelo=self._modelo, temperatura=None)


def _gravar_rodada(diretorio: Path, dataset: Dataset, versao: str, falha: set[str], rodada_id: str) -> None:
    prompt = PROMPTS[versao]
    gravador = ProviderGravador(
        provider=ProviderRoteirizado(falha),
        dataset=dataset,
        rodada_id=rodada_id,
        hash_prompt=hash_texto(prompt),
    )
    rodar(versao_prompt=versao, prompt_texto=prompt, dataset=dataset, provider=gravador, repeticoes=REPETICOES)
    gravar(
        diretorio_rodadas=diretorio,
        rodada_id=rodada_id,
        versao_prompt=versao,
        prompt_texto=prompt,
        dataset=dataset,
        chamadas=gravador.chamadas,
        repeticoes=REPETICOES,
        parametros_efetivos={"temperature_pedida": 0, "max_tokens": 256},
    )


def _splits(tmp_path: Path, falha_v0: set[str], falha_v1: set[str]) -> list[Split]:
    splits = []
    for nome in ("a", "b"):
        dataset = _dataset(nome)
        diretorio = tmp_path / nome
        _gravar_rodada(diretorio, dataset, "v0", {f"{nome}{i}" for i in falha_v0}, f"{nome}-v0")
        _gravar_rodada(diretorio, dataset, "v1", {f"{nome}{i}" for i in falha_v1}, f"{nome}-v1")
        splits.append(Split(nome=nome, diretorio_rodadas=diretorio, dataset=dataset))
    return splits


def test_analise_conta_falhas_por_transcricao_e_junta_os_splits(tmp_path):
    splits = _splits(tmp_path, falha_v0={0, 1, 2, 3, 4, 5}, falha_v1=set())

    analise = analisar(splits, "v0", "v1", PROMPTS.__getitem__)

    assert analise.transcricoes == 12
    assert analise.repeticoes == REPETICOES
    assert analise.primaria.falhas_base == [3] * 12
    assert analise.primaria.falhas_candidata == [0] * 12
    assert analise.primaria.sinal.favoraveis_candidata == 12
    assert analise.primaria.sinal.p_valor < 0.001
    assert analise.veredito == MELHORA_CONFIRMADA
    assert analise.rodadas == ["a/a-v0", "a/a-v1", "b/b-v0", "b/b-v1"]
    assert analise.modelos == {"modelo-teste"}


def test_analise_sem_diferenca_vira_equivalencia(tmp_path):
    splits = _splits(tmp_path, falha_v0=set(), falha_v1=set())

    analise = analisar(splits, "v0", "v1", PROMPTS.__getitem__)

    assert analise.primaria.sinal.empates == 12
    assert analise.veredito == SEM_DIFERENCA_RELEVANTE


def test_secundaria_conta_nao_acertos(tmp_path):
    splits = _splits(tmp_path, falha_v0={0, 1}, falha_v1={0})

    analise = analisar(splits, "v0", "v1", PROMPTS.__getitem__)

    # Violação de formato não tem Rótulo válido, então também é "não acerto".
    assert sum(analise.secundaria.falhas_base) == 2 * 2 * REPETICOES
    assert sum(analise.secundaria.falhas_candidata) == 2 * 1 * REPETICOES


def test_recusa_split_sem_rodada_da_versao(tmp_path):
    dataset = _dataset("a")
    _gravar_rodada(tmp_path / "a", dataset, "v0", set(), "a-v0")

    with pytest.raises(RecusaConfirmatorio, match="versão v1: 0 Rodadas"):
        analisar([Split("a", tmp_path / "a", dataset)], "v0", "v1", PROMPTS.__getitem__)


def test_recusa_duas_rodadas_completas_da_mesma_versao(tmp_path):
    dataset = _dataset("a")
    _gravar_rodada(tmp_path / "a", dataset, "v0", set(), "a-v0")
    _gravar_rodada(tmp_path / "a", dataset, "v0", set(), "a-v0-bis")
    _gravar_rodada(tmp_path / "a", dataset, "v1", set(), "a-v1")

    with pytest.raises(RecusaConfirmatorio, match="2 Rodadas"):
        analisar([Split("a", tmp_path / "a", dataset)], "v0", "v1", PROMPTS.__getitem__)


def _sinal(a_favor_candidata, a_favor_base, p):
    return ResultadoSinal(a_favor_candidata, a_favor_base, 0, p)


def _ic(inferior, superior):
    return IntervaloBootstrap((inferior + superior) / 2, inferior, superior, 100, 1)


def test_decidir_cada_ramo_da_regra_preregistrada():
    assert decidir(_sinal(10, 1, 0.01), _ic(-0.3, -0.1)) == MELHORA_CONFIRMADA
    assert decidir(_sinal(1, 10, 0.01), _ic(0.1, 0.3)) == PIORA_CONFIRMADA
    assert decidir(_sinal(3, 2, 0.9), _ic(-0.05, 0.08)) == SEM_DIFERENCA_RELEVANTE
    assert decidir(_sinal(6, 2, 0.29), _ic(-0.2, 0.02)) == INCONCLUSIVO


def test_decidir_p_exatamente_alfa_nao_e_significativo():
    assert decidir(_sinal(10, 2, 0.05), _ic(-0.2, 0.01)) == INCONCLUSIVO


def test_renderizar_traz_numeros_veredito_e_limites(tmp_path):
    splits = _splits(tmp_path, falha_v0={0, 1, 2, 3, 4, 5}, falha_v1=set())
    texto = renderizar(analisar(splits, "v0", "v1", PROMPTS.__getitem__))

    assert "36/36" in texto and "0/36" in texto
    assert "Teste do sinal" in texto
    assert MELHORA_CONFIRMADA in texto
    assert "temperatura efetiva desconhecida" in texto
    assert "Não é validação contra a API oficial" in texto


def _escrever_dataset(caminho: Path, dataset: Dataset) -> None:
    transcricoes = [
        {"id": t.id, "texto": t.texto, "rotulo_esperado": t.rotulo_esperado} for t in dataset.transcricoes
    ]
    transcricoes[0]["intencao_dupla"] = True
    transcricoes[1]["ambiguo"] = True
    caminho.write_text(
        json.dumps(
            {
                "rotulos_validos": dataset.rotulos_validos,
                "regra_desempate": dataset.regra_desempate,
                "transcricoes": transcricoes,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_comando_confirmar_roda_offline_e_imprime_veredito(tmp_path):
    (tmp_path / "prompts").mkdir()
    for versao, texto in PROMPTS.items():
        (tmp_path / "prompts" / f"{versao}.md").write_text(texto, encoding="utf-8")
    dataset = _dataset("a", n=20)  # o Dataset em disco passa na validação (20–30 Transcrições)
    _escrever_dataset(tmp_path / "a.json", dataset)
    _gravar_rodada(tmp_path / "rodadas", dataset, "v0", {f"a{i}" for i in range(15)}, "a-v0")
    _gravar_rodada(tmp_path / "rodadas", dataset, "v1", set(), "a-v1")

    resultado = subprocess.run(
        [sys.executable, "-m", "cx_prompt_lab", "confirmar", "--split", "a", "rodadas", "a.json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.startswith("CONFIRMATÓRIO (offline, nenhum modelo chamado)")
    assert MELHORA_CONFIRMADA in resultado.stdout


def test_comando_confirmar_recusa_sem_rodadas(tmp_path):
    dataset = _dataset("a", n=20)
    _escrever_dataset(tmp_path / "a.json", dataset)

    resultado = subprocess.run(
        [sys.executable, "-m", "cx_prompt_lab", "confirmar", "--split", "a", "rodadas", "a.json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1])},
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert resultado.returncode == 1
    assert "Recusa" in resultado.stderr

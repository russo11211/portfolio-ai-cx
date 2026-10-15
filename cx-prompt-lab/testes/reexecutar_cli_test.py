import json
from pathlib import Path

from cx_prompt_lab import cli
from cx_prompt_lab.provider import ErroProvider, RespostaProvider


DATASET = Path(__file__).parents[1] / "dataset" / "transcricoes.json"


def test_reexecutar_carrega_texto_do_prompt_e_grava_modelo_observado(tmp_path, monkeypatch, capsys):
    class ProviderFalso:
        def __init__(self):
            self.prompts = []

        def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
            self.prompts.append(prompt)
            return RespostaProvider(
                texto='{"rotulo": "cancelamento", "justificativa": "Cliente"}',
                motivo_parada="fim_normal",
                modelo="modelo-devolvido",
                temperatura=None,
            )

    provider = ProviderFalso()
    monkeypatch.setattr(cli, "GatewayProvider", lambda **kwargs: provider, raising=False)
    monkeypatch.setenv("CXLAB_GATEWAY_KEY", "chave-local-de-teste")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "v0.md").write_text("Texto completo do prompt v0.", encoding="utf-8")
    rodadas = tmp_path / "rodadas"

    codigo = cli.main(
        [
            "reexecutar", "--prompt", "v0", "--prompts", str(prompts),
            "--dataset", str(DATASET), "--rodadas", str(rodadas),
            "--modelo", "modelo-pedido", "--max-tokens", "64",
        ]
    )

    assert codigo == 0
    assert capsys.readouterr().out.splitlines()[0] == "REEXECUÇÃO (ao vivo)"
    assert len(provider.prompts) == 72
    assert set(provider.prompts) == {"Texto completo do prompt v0."}
    manifestos = list(rodadas.glob("*/manifest.json"))
    assert len(manifestos) == 1
    manifesto = json.loads(manifestos[0].read_text(encoding="utf-8"))
    assert manifesto["estado"] == "completa"
    assert manifesto["numero_esperado_chamadas"] == 72
    assert manifesto["parametros_efetivos"]["temperature_pedida"] == 0
    chamadas = [json.loads(p.read_text(encoding="utf-8")) for p in manifestos[0].parent.glob("*.json") if p.name != "manifest.json"]
    assert len(chamadas) == 72
    assert {c["modelo"] for c in chamadas} == {"modelo-devolvido"}
    assert {c["temperatura"] for c in chamadas} == {None}
    assert "chave-local-de-teste" not in "".join(p.read_text(encoding="utf-8") for p in manifestos[0].parent.glob("*.json"))


def test_erro_do_gateway_aborta_rodada_e_nao_grava_chamada_sem_resposta(tmp_path, monkeypatch, capsys):
    class ProviderQueFalha:
        def __init__(self):
            self.tentativas = 0

        def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
            self.tentativas += 1
            if self.tentativas == 2:
                raise ErroProvider("Gateway retornou HTTP 500", "Gateway instável")
            return RespostaProvider("{}", "fim_normal", "modelo-devolvido", None)

    provider = ProviderQueFalha()
    monkeypatch.setattr(cli, "GatewayProvider", lambda **kwargs: provider)
    monkeypatch.setenv("CXLAB_GATEWAY_KEY", "chave-local-de-teste")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "v0.md").write_text("Prompt de teste.", encoding="utf-8")
    rodadas = tmp_path / "rodadas"

    codigo = cli.main([
        "reexecutar", "--prompt", "v0", "--prompts", str(prompts),
        "--dataset", str(DATASET), "--rodadas", str(rodadas), "--modelo", "modelo-pedido",
    ])

    assert codigo == 2
    assert provider.tentativas == 2
    assert "HTTP 500" in capsys.readouterr().err
    manifestos = list(rodadas.glob("*/manifest.json"))
    assert len(manifestos) == 1
    assert json.loads(manifestos[0].read_text(encoding="utf-8"))["estado"] == "abortada"
    assert len(list(manifestos[0].parent.glob("*.json"))) == 2  # manifesto + só a Chamada concluída


def test_reexecutar_sem_chave_falha_antes_de_criar_rodada(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CXLAB_GATEWAY_KEY", raising=False)
    rodadas = tmp_path / "rodadas"

    codigo = cli.main([
        "reexecutar", "--prompt", "v0", "--modelo", "modelo-pedido",
        "--rodadas", str(rodadas),
    ])

    assert codigo == 2
    assert "CXLAB_GATEWAY_KEY" in capsys.readouterr().err
    assert not rodadas.exists()


def test_rodada_id_nao_pode_sair_do_diretorio_de_rodadas(tmp_path, monkeypatch, capsys):
    class ProviderFalso:
        def chamar(self, prompt: str, transcricao: str) -> RespostaProvider:
            return RespostaProvider("{}", "fim_normal", "modelo-devolvido", None)

    monkeypatch.setattr(cli, "GatewayProvider", lambda **kwargs: ProviderFalso())
    monkeypatch.setenv("CXLAB_GATEWAY_KEY", "chave-local-de-teste")
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "v0.md").write_text("Prompt de teste.", encoding="utf-8")
    rodadas = tmp_path / "rodadas"

    codigo = cli.main([
        "reexecutar", "--prompt", "v0", "--prompts", str(prompts),
        "--dataset", str(DATASET), "--rodadas", str(rodadas),
        "--rodada-id", "../escape", "--modelo", "modelo-pedido",
    ])

    assert codigo == 2
    assert "Identificador" in capsys.readouterr().err
    assert not (tmp_path / "escape").exists()

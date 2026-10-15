# CX Prompt Lab

Prompts versionados para **classificar a intenção de chamadas de contact center**, medidos
por um eval **determinístico** sobre um Dataset fixo de Transcrições fictícias. Cada chamada
ao modelo é gravada em disco, e o Relatório é recalculado offline a partir dessas gravações
(Replay), sem chamar modelo nenhum.

O resultado das Rodadas reais é **exploratório** e o veredito v0 × v1 é **inconclusivo por
efeito piso** (detalhes abaixo).

## O que tem aqui

| Caminho | O que é |
|---|---|
| `cx_prompt_lab/avaliador.py` | Avaliador: aplica o Contrato de saída e classifica cada resposta |
| `cx_prompt_lab/executor.py` | Executa uma Rodada (Transcrições × Repetições) e conta cada categoria |
| `cx_prompt_lab/conclusao.py` | Regra de melhora: veredito v0 × versão final, só com contagens inteiras |
| `cx_prompt_lab/gravacao.py`, `replay.py` | Gravação das Chamadas + manifesto da Rodada; Replay offline |
| `cx_prompt_lab/provider.py` | Seam do Provider: `GatewayProvider` (usado nas Rodadas) e `AnthropicProvider` |
| `cx_prompt_lab/relatorio.py`, `cli.py` | Relatório e linha de comando (`replay`, `reexecutar`) |
| `dataset/transcricoes.json` | 24 Transcrições fictícias, 6 Rótulos (4 Transcrições por Rótulo), regra de desempate |
| `prompts/v0.md`, `prompts/v1.md` | As duas Versões de prompt medidas |
| `rodadas/car20-v0/`, `rodadas/car20-v1/` | As Chamadas reais gravadas (72 por versão) e o manifesto de cada Rodada |
| `RELATORIO.md` | Relatório gerado pelo Replay, com a conclusão registrada |
| `testes/` | Suíte pytest (offline por padrão) |

O caminho de decisão (ideia, design, spec, ADRs) está em `../docs/`:
[`docs/spec/cx-prompt-lab.md`](../docs/spec/cx-prompt-lab.md),
[`docs/adr/0001-arquitetura-cx-prompt-lab.md`](../docs/adr/0001-arquitetura-cx-prompt-lab.md),
[`docs/adr/0002-gateway-go-no-go.md`](../docs/adr/0002-gateway-go-no-go.md),
[`docs/adr/0002-timestamp-na-chamada.md`](../docs/adr/0002-timestamp-na-chamada.md) e
[`docs/design/cx-prompt-lab-piloto-v0.md`](../docs/design/cx-prompt-lab-piloto-v0.md).
O vocabulário (Transcrição, Rodada, Repetição, Alucinação etc.) está em
[`CONTEXT.md`](../CONTEXT.md).

## Como rodar

Requisitos: Python 3.11+ (o código usa `datetime.UTC`). O pacote só usa a biblioteca padrão;
os testes precisam de `pytest`. Não há `pyproject.toml`: rode tudo a partir deste diretório.

```bash
cd cx-prompt-lab
python3 -m pip install pytest

# suíte completa, offline
python3 -m pytest -q
```

Resultado nesta versão: `147 passed, 2 skipped`. Os 2 *skipped* são os testes de integração
opt-in (Gateway e API Anthropic). O `testes/conftest.py` nega `socket.connect` em todo teste
que não seja de integração habilitado, então a suíte ordinária não sai para a rede, mesmo
com uma chave de API no ambiente.

### Replay (offline, determinístico, sem chave)

```bash
python3 -m cx_prompt_lab replay
```

Lê `rodadas/`, `dataset/transcricoes.json` e `prompts/`, confere os hashes do prompt e do
Dataset contra o manifesto de cada Rodada e reimprime o Relatório. Não chama nenhum modelo.
O Replay recusa Rodada abortada, Chamada duplicada, faltando ou sobrando, e divergência de
hash ou de versão de esquema. O conteúdo de `RELATORIO.md` (até a seção "Conclusão
registrada", que foi escrita à mão) é a saída deste comando.

### Reexecução (ao vivo, chama um modelo de verdade)

```bash
export CXLAB_GATEWAY_KEY=...        # chave do Gateway local (obrigatória)
export CXLAB_MODEL=claude-sonnet-4-5-20250929
export CXLAB_GATEWAY_URL=http://127.0.0.1:8317   # default
python3 -m cx_prompt_lab reexecutar --prompt v1 --rodada-id minha-rodada
```

A Reexecução só está ligada ao `--provider gateway`: um proxy local que fala o formato
`/v1/messages` da Anthropic (nas Rodadas registradas, o CLIProxyAPI; ver ADR 0002). Com
`--provider anthropic` ou `groq` o comando sai com erro "ainda não implementado". Defaults:
3 Repetições (mínimo 3), `--temperatura 0`, `--max-tokens 256`, `--timeout-s 30`. Erro do
provider ou timeout aborta a Rodada sem retentativa; a Rodada fica gravada como `abortada` e
o Replay a recusa.

Testes de integração opt-in:

- Gateway: `CXLAB_TEST_GATEWAY=1`, `CXLAB_GATEWAY_KEY`, `CXLAB_MODEL` (e opcionalmente
  `CXLAB_GATEWAY_URL`).
- API oficial da Anthropic: `CXLAB_TEST_ANTHROPIC=1`, `ANTHROPIC_API_KEY`, `CXLAB_MODEL`.
  Esse teste nunca foi rodado neste projeto; o `AnthropicProvider` só é exercitado offline,
  com transporte falso.

## Metodologia do eval (como está implementada)

Cada Rodada é uma Versão de prompt × 24 Transcrições × 3 Repetições = 72 Chamadas. O prompt
vai no campo `system`, a Transcrição na mensagem do usuário.

**Contrato de saída** (igual para todas as versões): um objeto JSON com `"rotulo"` e
`"justificativa"`, ambos texto. O parser é estrito (`json.loads` na resposta inteira): não
remove bloco de código markdown nem prosa em volta; campos extras são ignorados.

O Avaliador (`avaliador.py`) e o Executor (`executor.py`) classificam cada resposta assim:

| Situação da resposta | Conta como |
|---|---|
| Truncada (`max_tokens`) ou recusa, informada pelo provider | Violação de formato |
| Vazia, JSON inválido (inclui JSON dentro de bloco de código), não-objeto, campo faltando ou de tipo errado, Rótulo ou Justificativa vazios | Violação de formato |
| Rótulo fora da lista de 6 Rótulos válidos | Erro de acerto **e** Alucinação (rótulo inexistente) |
| Rótulo válido, diferente do esperado | Erro de acerto |
| Justificativa que não aparece literalmente na Transcrição (após normalização Unicode NFC e de espaços) | Alucinação (justificativa não ancorada) |
| Rótulo válido e igual ao esperado | Acerto (com ou sem Justificativa ancorada) |

Violação de formato exclui as outras categorias. "Alucinação total" conta a Transcrição uma
vez, mesmo com os dois subtipos. A taxa por versão é o total de ocorrências dividido por
Transcrições × Repetições.

"Ancoragem literal" prova que o trecho existe na Transcrição, não que ele sustenta o Rótulo.

**Regra de melhora** (`conclusao.py`), aplicada só a v0 × versão final, na ordem, parando
na primeira que valer:

1. *Não comparável*: modelo devolvido, `temperature` ou `max_tokens` diferentes.
2. *Piora*: média de Alucinação total da versão final maior que a de v0.
3. *Inconclusivo por efeito piso*: alguma Repetição de v0 teve Alucinação total ≤ 1.
4. *Melhora*: queda de Alucinação total ≥ 2 Transcrições no pior caso entre Repetições,
   Violação de formato que não sobe e acertos que não caem (também no pior caso).
5. Qualquer outro caso: *inconclusivo*.

## Resultados das Rodadas reais

Fonte: Chamadas em `rodadas/car20-v0/` e `rodadas/car20-v1/` (manifestos com
`estado: completa` e `numero_esperado_chamadas: 72`), Relatório em
[`RELATORIO.md`](RELATORIO.md), reproduzível com `python3 -m cx_prompt_lab replay`.

Modelo devolvido pela resposta: `claude-sonnet-4-5-20250929`, via Gateway local.
Parâmetros pedidos: temperatura 0, `max_tokens` 256. Chamadas de 2026-10-01 (UTC).

| Versão | Chamadas | Erro de acerto | Alucinação | Violação de formato | Acertos por Repetição |
|---|---:|---:|---:|---:|---|
| v0 | 72 | 0,0% | 0,0% | 62,5% (45/72) | 10, 7, 10 |
| v1 | 72 | 0,0% | 0,0% | 33,3% (24/72) | 14, 17, 17 |

Violações de formato por Repetição: v0 = 14, 17, 14; v1 = 10, 7, 7 (amplitude de 12,5 pp em
cada versão). Todas as respostas tiveram `stop_reason` normal; todas as Violações de formato
das duas Rodadas são respostas embrulhadas em bloco de código markdown.

O que v1 mudou em relação a v0: só a explicação do Contrato de saída. v1 diz que um
programa rejeita qualquer resposta que não comece com `{` (inclusive bloco de código) e
mostra a forma exata da resposta com valores inventados.

### Veredito

**Exploratório, inconclusivo por efeito piso.** A métrica principal da regra de melhora é a
Alucinação, e ela foi 0 em todas as Repetições das duas versões (o Erro de acerto também).
Com Alucinação de v0 já no piso, não há queda possível para medir, então a regra não
declara melhora. A queda da Violação de formato (62,5% → 33,3%) é uma observação, não um
veredito.

## Limitações

- **Mesmo Dataset para desenvolver e medir.** v1 foi escrita depois de ver as falhas de v0
  nas mesmas 24 Transcrições; não há conjunto de validação separado.
- **Amostra pequena:** 24 Transcrições fictícias, 3 Repetições, um modelo, um prompt de
  cada versão. Sem teste estatístico formal.
- **Temperatura efetiva desconhecida.** O Gateway não repassou o campo `temperature` ao
  upstream no spike (ADR 0002, conferência C5a); a temperatura 0 é a *pedida*.
- **Modelo via Gateway, não via API oficial.** As Rodadas usaram um proxy local autenticado
  pela assinatura Claude do autor. "Compatível com Anthropic" aqui quer dizer o formato do
  pedido e da resposta, não validação contra a API oficial. A ADR 0002 registra como aberto
  o risco de conformidade desse modo de autenticação com os termos do provedor.
- **v1 ainda falha em formato** em 7 a 10 de 24 Transcrições por Repetição. Uma v2 é o
  próximo passo planejado e não foi feita.
- O Dataset é fictício e equilibrado (4 por Rótulo); não representa a distribuição de um
  contact center real.

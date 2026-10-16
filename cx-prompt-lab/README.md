# CX Prompt Lab

Eval determinístico para versões de prompt que **classificam a intenção de chamadas de
contact center** (6 Rótulos, 24 Transcrições fictícias). Cada chamada ao modelo fica
gravada no repositório, e qualquer pessoa recalcula o Relatório offline com um comando
(Replay), sem chave de API.

**Resultado confirmatório (CAR-23, pré-registrado):** num holdout de 60 Transcrições
fictícias nunca usadas para escrever prompt, 300 Chamadas por versão em `claude-sonnet-4-5`,
v1 reduziu a Violação de formato de **75,7% para 55,7%** (−20,0 pp, IC 95% −29,3 a −11,0 pp;
teste do sinal exato por Transcrição, 33 × 9, **p = 0,00027**). Veredito pré-registrado:
**melhora confirmada**. v1 ainda falha em mais da metade das Chamadas: a melhora é real e
mensurável, o problema de formato não está resolvido.

A primeira medição (CAR-20, 24 Transcrições, 72 Chamadas por versão) tinha ficado
*exploratória, inconclusiva por efeito piso*; ela continua publicada abaixo como estava.

> **TL;DR (English).** A small, deterministic eval harness for prompt versions that
> classify contact-center call intent. Every model call is committed to the repo, so the
> report can be recomputed offline with one command and no API key. **Pre-registered
> confirmatory result:** on a 60-transcript held-out set never used for prompt development
> (300 calls per version, `claude-sonnet-4-5`), v1 cut format violations from 75.7% to
> 55.7% (−20.0 pp, 95% cluster-bootstrap CI −29.3 to −11.0 pp; exact sign test over
> transcripts, 33 vs 9, p = 0.00027): *improvement confirmed*, though v1 still fails more
> than half the time. An earlier exploratory run (72 calls per version, same data used to
> develop and measure) was inconclusive due to a floor effect and is kept as published.
> Python 3.11+, standard library only, 178 offline tests. Docs are in Portuguese.

## Conteúdo

- [Resultado confirmatório (holdout, CAR-23)](#resultado-confirmatório-holdout-car-23)
- [Resultado exploratório (CAR-20)](#resultado-exploratório-car-20)
- [Onde olhar: evidência por competência](#onde-olhar-evidência-por-competência)
- [Verifique em 2 minutos](#verifique-em-2-minutos)
- [Como o trabalho foi feito](#como-o-trabalho-foi-feito)
- [Metodologia do eval](#metodologia-do-eval-como-está-implementada)
- [O que cada teste comprova](#o-que-cada-teste-comprova)
- [Limitações](#limitações)
- [Reexecução (ao vivo)](#reexecução-ao-vivo-chama-um-modelo-de-verdade)
- [Mapa do repositório](#mapa-do-repositório)

## Resultado confirmatório (holdout, CAR-23)

Pré-registro: [`docs/spec/cx-prompt-lab-preregistro-holdout.md`](../docs/spec/cx-prompt-lab-preregistro-holdout.md),
commitado e publicado no GitHub **antes** de qualquer Chamada no holdout (hipótese, métrica
primária, holdout congelado por hash, tamanho da amostra com cálculo de poder, α = 0,05 e o que
conta como conclusivo). Chamadas em [`rodadas-holdout/`](rodadas-holdout/), análise reproduzível
com `python3 -m cx_prompt_lab confirmar` (offline).

O que mudou em relação ao CAR-20, só em dados e análise (a arquitetura é a mesma):

- **Contaminação resolvida:** holdout novo, `dataset/holdout_a.json` + `holdout_b.json`
  (60 Transcrições fictícias, 10 por Rótulo, 12 de intenção dupla, 12 ambíguas), escrito depois
  de v0 e v1 congeladas; testes garantem que nenhum texto repete o Dataset de desenvolvimento.
- **Efeito piso resolvido:** a métrica primária passou a ser a Violação de formato (longe do
  piso), em vez da Alucinação (0 em v0).
- **Amostra e estatística:** 60 Transcrições × 5 Repetições × 2 versões = 600 Chamadas; teste do
  sinal exato por Transcrição (as Repetições de uma Transcrição não são independentes) e IC 95%
  por bootstrap de clusters. Poder estimado ≥ 0,91 mesmo para metade do efeito visto no
  desenvolvimento.

Modelo devolvido: `claude-sonnet-4-5-20250929`, via o mesmo Gateway local (ADR 0002).
Parâmetros pedidos: temperatura 0, `max_tokens` 256. Chamadas de 2026-10-16 (UTC), Rodadas na
ordem ABBA (a-v0, a-v1, b-v1, b-v0), nenhuma abortada, todas com `stop_reason` normal.

| Versão | Chamadas | Violação de formato | IC 95% | Não acerto | Erro de acerto | Alucinação |
|---|---:|---:|---|---:|---:|---:|
| v0 | 300 | 75,7% (227) | 66,7% a 83,7% | 76,3% (229) | 2 | 0 |
| v1 | 300 | 55,7% (167) | 46,7% a 64,3% | 56,7% (170) | 3 | 0 |

- **Primária:** diferença v1 − v0 = **−20,0 pp** (IC 95% −29,3 a −11,0 pp). Teste do sinal:
  33 Transcrições a favor de v1, 9 a favor de v0, 18 empates, **p = 2,7 × 10⁻⁴**.
- **Secundária (não acerto):** −19,7 pp (IC 95% −29,0 a −10,7 pp), 32 × 10, p = 9,4 × 10⁻⁴.
- Todas as 394 Violações de formato são o mesmo erro: JSON embrulhado em bloco de código markdown.

### Veredito pré-registrado

**Melhora confirmada** (conclusivo): p < 0,05 a favor de v1 na métrica primária, com o IC da
diferença inteiro abaixo de zero. Leitura honesta do tamanho: v1 corta cerca de um quarto das
Violações, mas ainda falha em 55,7% das Chamadas, então o Contrato de saída continua sendo o
problema a resolver (próximo passo: v2, medida contra um holdout novo). No holdout, v0 falhou
mais que no desenvolvimento (75,7% contra 62,5%).

## Resultado exploratório (CAR-20)

Fonte: Chamadas em [`rodadas/car20-v0/`](rodadas/car20-v0/) e
[`rodadas/car20-v1/`](rodadas/car20-v1/) (manifestos com `estado: completa` e
`numero_esperado_chamadas: 72`), Relatório em [`RELATORIO.md`](RELATORIO.md),
reproduzível com `python3 -m cx_prompt_lab replay`.

Modelo devolvido pela resposta: `claude-sonnet-4-5-20250929`, via Gateway local.
Parâmetros pedidos: temperatura 0, `max_tokens` 256. Chamadas de 2026-10-01 (UTC).

| Versão | Chamadas | Erro de acerto | Alucinação | Violação de formato | Acertos por Repetição (de 24) |
|---|---:|---:|---:|---:|---|
| v0 | 72 | 0,0% | 0,0% | 62,5% (45/72) | 10, 7, 10 |
| v1 | 72 | 0,0% | 0,0% | 33,3% (24/72) | 14, 17, 17 |

Violações de formato por Repetição: v0 = 14, 17, 14; v1 = 10, 7, 7 (amplitude de 12,5 pp em
cada versão). Todas as respostas tiveram `stop_reason` normal; todas as Violações de formato
das duas Rodadas são respostas embrulhadas em bloco de código markdown. Uma Violação de
formato exclui as outras categorias, por isso Erro de acerto 0% convive com 10 de 24 acertos.

O que v1 mudou em relação a v0: só a explicação do Contrato de saída. v1 diz que um
programa rejeita qualquer resposta que não comece com `{` (inclusive bloco de código) e
mostra a forma exata da resposta com valores inventados. Compare
[`prompts/v0.md`](prompts/v0.md) e [`prompts/v1.md`](prompts/v1.md).

### Veredito do CAR-20

**Exploratório, inconclusivo por efeito piso.** A métrica principal da regra de melhora é a
Alucinação, e ela foi 0 em todas as Repetições das duas versões (o Erro de acerto também).
Com Alucinação de v0 já no piso, não há queda possível para medir, então a regra não
declara melhora. A queda da Violação de formato (62,5% → 33,3%) é uma observação, não um
veredito.

## Onde olhar: evidência por competência

Cada linha aponta um arquivo que dá para abrir e conferir. Nada aqui depende de acreditar
no texto deste README.

| Competência | Onde está a evidência | O que conferir |
|---|---|---|
| Desenho de eval com critério verificável por código | [`cx_prompt_lab/avaliador.py`](cx_prompt_lab/avaliador.py), [`testes/avaliador_test.py`](testes/avaliador_test.py) | Parser estrito do Contrato de saída; Alucinação definida como Justificativa que não aparece literalmente na Transcrição, sem juiz LLM |
| Regra de decisão escrita antes dos dados | [`docs/spec/cx-prompt-lab.md`](../docs/spec/cx-prompt-lab.md) ("Regra de melhora"), [`cx_prompt_lab/conclusao.py`](cx_prompt_lab/conclusao.py), [`testes/conclusao_test.py`](testes/conclusao_test.py) | A regra está na spec fechada em 2026-09-25, antes das Rodadas; o código é uma função pura sobre contagens inteiras |
| Reprodutibilidade | [`cx_prompt_lab/replay.py`](cx_prompt_lab/replay.py), [`rodadas/`](rodadas/), [`testes/replay_test.py`](testes/replay_test.py) | Replay confere hash do prompt e do Dataset contra o manifesto e recusa Rodada incompleta, duplicada, corrompida ou de esquema diferente |
| Teste de hipótese pré-registrado | [`docs/spec/cx-prompt-lab-preregistro-holdout.md`](../docs/spec/cx-prompt-lab-preregistro-holdout.md), [`cx_prompt_lab/estatistica.py`](cx_prompt_lab/estatistica.py), [`cx_prompt_lab/confirmatorio.py`](cx_prompt_lab/confirmatorio.py), [`testes/holdout_dataset_test.py`](testes/holdout_dataset_test.py) | Pré-registro commitado antes das Chamadas (`git log`); holdout congelado por hash num teste; teste do sinal e bootstrap em stdlib, testados contra valores calculados à mão |
| Relato honesto de resultado | [`RELATORIO.md`](RELATORIO.md), [`testes/relatorio_test.py`](testes/relatorio_test.py) | Veredito inconclusivo publicado como está; testes que impedem o Relatório de afirmar "validado contra a Anthropic" |
| Dataset com casos difíceis | [`dataset/transcricoes.json`](dataset/transcricoes.json), [`cx_prompt_lab/dataset.py`](cx_prompt_lab/dataset.py) | 24 Transcrições, 4 por Rótulo, regra de desempate escrita; a validação recusa Dataset sem caso ambíguo ou de intenção dupla |
| Iteração de prompt guiada por falha observada | [`docs/design/cx-prompt-lab-piloto-v0.md`](../docs/design/cx-prompt-lab-piloto-v0.md), [`prompts/`](prompts/) | Piloto de v0 (8 Transcrições), causa da falha (bloco de código markdown) e o que v1 mudou por causa disso |
| Integração com API de LLM atrás de uma seam | [`cx_prompt_lab/provider.py`](cx_prompt_lab/provider.py), [`testes/contrato_provider_test.py`](testes/contrato_provider_test.py) | `GatewayProvider` e `AnthropicProvider` contra o mesmo transporte HTTP falso devolvem a mesma resposta normalizada |
| Disciplina de testes | [`testes/`](testes/), [`testes/conftest.py`](testes/conftest.py) | 178 testes offline; `socket.connect` negado em todo teste não opt-in, então a suíte não sai para a rede |
| Decisões de arquitetura registradas | [`docs/adr/`](../docs/adr/) | ADR 0001 (módulos, seams, zero dependências, alternativas descartadas); ADR 0002 do Gateway (conferências C0–C6, incluindo a que falhou) |
| Processo com escopo e gates | [`docs/ideias/`](../docs/ideias/cx-prompt-lab/ideia.md) → [`docs/design/`](../docs/design/cx-prompt-lab-design.md) → [`docs/spec/`](../docs/spec/cx-prompt-lab.md) → [`docs/adr/`](../docs/adr/) → commits `feat(E8)` | Ver [Como o trabalho foi feito](#como-o-trabalho-foi-feito) |
| Linguagem de domínio consistente | [`CONTEXT.md`](../CONTEXT.md) | Glossário (Transcrição, Rodada, Repetição, Alucinação etc.) usado igual no código, nos testes e nos documentos |

## Verifique em 2 minutos

Requisitos: Python 3.11+ (o código usa `datetime.UTC`). O pacote só usa a biblioteca padrão;
os testes precisam de `pytest`. Não há `pyproject.toml`: rode tudo a partir deste diretório.

```bash
git clone https://github.com/russo11211/portfolio-ai-cx.git
cd portfolio-ai-cx/cx-prompt-lab
python3 -m pip install pytest

# 1. suíte completa, offline
python3 -m pytest -q
# esperado: 178 passed, 2 skipped

# 2. Replay: recalcula o Relatório a partir das Chamadas gravadas, sem chave e sem rede
python3 -m cx_prompt_lab replay

# 3. (bash) confere que a saída do Replay é o que está publicado em RELATORIO.md
python3 -m cx_prompt_lab replay | tail -n +2 \
  | diff -B - <(sed '/^## Conclusão registrada/,$d' RELATORIO.md) && echo "Replay idêntico ao RELATORIO.md"

# 4. experimento confirmatório (holdout): teste do sinal + bootstrap, offline
python3 -m cx_prompt_lab confirmar
```

Os 2 *skipped* são os testes de integração opt-in (Gateway e API Anthropic). O
[`testes/conftest.py`](testes/conftest.py) nega `socket.connect` em todo teste que não seja
de integração habilitado, então a suíte ordinária não sai para a rede, mesmo com uma chave
de API no ambiente.

O Replay lê `rodadas/`, `dataset/transcricoes.json` e `prompts/`, confere os hashes do prompt
e do Dataset contra o manifesto de cada Rodada e reimprime o Relatório. Não chama nenhum
modelo. Recusa Rodada abortada, Chamada duplicada, faltando ou sobrando, e divergência de
hash ou de versão de esquema. A primeira linha da saída é o banner
`REPLAY (offline, nenhum modelo chamado)`; o resto é o conteúdo de `RELATORIO.md` até a
seção "Conclusão registrada", que foi escrita à mão.

O Replay prova o cálculo a partir das Chamadas gravadas, não que o modelo responderia igual
hoje. Chamar o modelo de novo é a [Reexecução](#reexecução-ao-vivo-chama-um-modelo-de-verdade).

## Como o trabalho foi feito

O projeto passou por uma esteira de estágios, cada um com um artefato em disco e um gate
antes do próximo (o contrato completo está em [`CLAUDE.md`](../CLAUDE.md)). O que existe no
repositório para cada estágio:

| Estágio | Artefato | Data |
|---|---|---|
| Ideia: o quê, para quem, não-escopo, riscos, critério de sucesso | [`docs/ideias/cx-prompt-lab/ideia.md`](../docs/ideias/cx-prompt-lab/ideia.md) | 2026-09-21 a 23 |
| Design: pressão sobre a ideia, cortes de escopo | [`docs/design/cx-prompt-lab-design.md`](../docs/design/cx-prompt-lab-design.md) | 2026-09-23 |
| Glossário do domínio | [`CONTEXT.md`](../CONTEXT.md) | 2026-09-23 |
| Spec: histórias, fora de escopo (15 itens), revisões e cortes registrados, matriz de cobertura história → ticket | [`docs/spec/cx-prompt-lab.md`](../docs/spec/cx-prompt-lab.md) | fechada em 2026-09-25 |
| Arquitetura antes do código | [`docs/adr/0001-arquitetura-cx-prompt-lab.md`](../docs/adr/0001-arquitetura-cx-prompt-lab.md) | 2026-09-28 |
| Spike do Gateway com go/no-go escrito | [`docs/adr/0002-gateway-go-no-go.md`](../docs/adr/0002-gateway-go-no-go.md) | 2026-09-28 |
| Implementação, commits `feat(E8)` que citam o ticket (`CAR-n`) | `git log --oneline` | 2026-09-28 a 30 |
| Rodadas reais e conclusão | [`rodadas/`](rodadas/), [`RELATORIO.md`](RELATORIO.md) | Chamadas de 2026-10-01 (UTC) |

Os tickets (T1–T14, CAR-9 a CAR-22) ficam num workspace **privado** do Linear, que quem
lê o repositório não acessa. Para a evidência ficar legível aqui, a tabela de tickets, os
bloqueios entre eles e a matriz de cobertura história → ticket estão copiadas na seção
"Cobertura e fechamento (E6)" da [spec](../docs/spec/cx-prompt-lab.md). Cada commit de código do E8 traz o módulo e os testes
juntos (`git show --stat <commit>`).

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

**Margem de variação**: o Relatório imprime a amplitude (maior menos menor) de cada taxa
entre as Repetições, em pontos percentuais. É descritiva e não entra no veredito.

## O que cada teste comprova

`python3 -m pytest -q --co` lista os 180 testes coletados (178 offline + 2 opt-in). Os nomes
dos testes descrevem o comportamento; o resumo por arquivo:

| Arquivo | Testes coletados | Comprova |
|---|---:|---|
| [`avaliador_test.py`](testes/avaliador_test.py) | 16 | Cada linha da tabela de contagem, incluindo JSON em bloco de código e paráfrase como não ancorada |
| [`executor_test.py`](testes/executor_test.py) | 19 | Contagens por Repetição; mínimo de 3 Repetições; erro ou timeout do provider aborta a Rodada sem retentativa |
| [`conclusao_test.py`](testes/conclusao_test.py) | 15 | Cada ramo da regra de melhora, incluindo efeito piso, piora vencendo efeito piso e Repetições em número desigual |
| [`dataset_test.py`](testes/dataset_test.py) | 14 | Validação do Dataset (20–30 Transcrições, lista fechada, regra de desempate, casos ambíguos e de intenção dupla); nenhuma Transcrição aparece como exemplo no prompt |
| [`gravacao_test.py`](testes/gravacao_test.py) | 11 | Um arquivo por Chamada; sem credencial gravada; temperatura pedida ≠ aplicada; Rodada abortada fica marcada e o Replay a recusa |
| [`replay_test.py`](testes/replay_test.py) | 14 | Replay reproduz as contagens sem chamar provider e recusa cada tipo de Rodada inválida |
| [`relatorio_test.py`](testes/relatorio_test.py) | 22 | Tabela, modelo e data das Chamadas, veredito, margem; o texto declara "exploratório" e nunca afirma validação contra a Anthropic |
| [`gateway_provider_test.py`](testes/gateway_provider_test.py), [`anthropic_provider_test.py`](testes/anthropic_provider_test.py) | 11 + 10 | Adapters HTTP com transporte falso: erros viram erro do provider sem expor a chave |
| [`contrato_provider_test.py`](testes/contrato_provider_test.py) | 10 | Os dois adapters normalizam igual sobre o mesmo transporte |
| [`cli_test.py`](testes/cli_test.py), [`reexecutar_cli_test.py`](testes/reexecutar_cli_test.py) | 1 + 4 | `replay` sem rede; `reexecutar` falha antes de criar Rodada se faltar chave |
| [`estatistica_test.py`](testes/estatistica_test.py) | 14 | Binomial exato e teste do sinal contra valores à mão; bootstrap reproduzível pela semente, IC contém a estimativa |
| [`confirmatorio_test.py`](testes/confirmatorio_test.py) | 10 | Contagem por Transcrição via Replay, junção dos splits, cada ramo da regra pré-registrada, recusa de Rodada faltando ou duplicada, comando `confirmar` offline |
| [`holdout_dataset_test.py`](testes/holdout_dataset_test.py) | 7 | Holdout válido e equilibrado, congelado no hash do pré-registro, sem texto repetido do Dataset de desenvolvimento nem nos prompts |
| [`gateway_integracao_test.py`](testes/gateway_integracao_test.py), [`anthropic_integracao_test.py`](testes/anthropic_integracao_test.py) | 1 + 1 | Opt-in, chamam rede de verdade; *skipped* por padrão |

## Limitações

- **Efeito piso e contaminação (CAR-20) foram tratados no CAR-23**, não apagados: o resultado
  do CAR-20 continua exploratório. A regra de melhora original (baseada em Alucinação) segue no
  código e continua sem poder decidir nada enquanto a Alucinação estiver em 0.
- **Holdout escrito pelo mesmo autor do Dataset de desenvolvimento.** É independente dos
  prompts (escrito com v0 e v1 já congeladas), não de quem escreve Transcrições.
- **Escopo do resultado confirmatório:** um modelo, uma tarefa (intenção com saída JSON estrita),
  um idioma, 60 Transcrições fictícias e equilibradas. Vale para Violação de formato; Erro de
  acerto e Alucinação ficaram perto de 0 e não foram testados.
- **Temperatura efetiva desconhecida.** O Gateway não repassou o campo `temperature` ao
  upstream no spike (ADR 0002, conferência C5a); a temperatura 0 é a *pedida*. A análise
  trata as Repetições como amostras do modelo como ele respondeu, mas não dá para afirmar que
  o resultado vale para temperatura 0 de fato.
- **Modelo via Gateway, não via API oficial.** As Rodadas usaram um proxy local autenticado
  pela assinatura Claude do autor. "Compatível com Anthropic" aqui quer dizer o formato do
  pedido e da resposta, não validação contra a API oficial. A ADR 0002 registra como aberto
  o risco de conformidade desse modo de autenticação com os termos do provedor.
- **`AnthropicProvider` nunca chamou a API real**; só é exercitado offline, com transporte
  falso. O Plano B da ADR 0001 (Groq, Llama 3.3 70B) não foi implementado: `reexecutar
  --provider groq` sai com "ainda não implementado".
- **v1 ainda falha em formato** em 55,7% das Chamadas do holdout. Uma v2 é o próximo passo
  planejado e não foi feita; para ser medida, precisa de um holdout novo (este já foi visto).
- O Dataset é fictício e equilibrado (4 por Rótulo); não representa a distribuição de um
  contact center real.
- Não há CI configurado no repositório; a suíte roda localmente.

## Reexecução (ao vivo, chama um modelo de verdade)

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
  Esse teste nunca foi rodado neste projeto.

## Mapa do repositório

| Caminho | O que é |
|---|---|
| `cx_prompt_lab/avaliador.py` | Avaliador: aplica o Contrato de saída e classifica cada resposta |
| `cx_prompt_lab/executor.py` | Executa uma Rodada (Transcrições × Repetições) e conta cada categoria |
| `cx_prompt_lab/conclusao.py` | Regra de melhora: veredito v0 × versão final, só com contagens inteiras |
| `cx_prompt_lab/dataset.py` | Carrega e valida o Dataset |
| `cx_prompt_lab/gravacao.py`, `replay.py` | Gravação das Chamadas + manifesto da Rodada; Replay offline |
| `cx_prompt_lab/provider.py` | Seam do Provider: `GatewayProvider` (usado nas Rodadas) e `AnthropicProvider` |
| `cx_prompt_lab/relatorio.py`, `cli.py` | Relatório e linha de comando (`replay`, `reexecutar`) |
| `dataset/transcricoes.json` | 24 Transcrições fictícias, 6 Rótulos (4 por Rótulo), regra de desempate |
| `prompts/v0.md`, `prompts/v1.md` | As duas Versões de prompt medidas |
| `cx_prompt_lab/estatistica.py`, `confirmatorio.py` | Teste do sinal e bootstrap (stdlib); experimento confirmatório (`confirmar`) |
| `dataset/holdout_a.json`, `holdout_b.json` | Holdout do CAR-23: 60 Transcrições fictícias, congeladas por hash |
| `rodadas-holdout/` | As 600 Chamadas reais do CAR-23 (4 Rodadas de 150) |
| `rodadas/car20-v0/`, `rodadas/car20-v1/` | As Chamadas reais gravadas (72 por versão) e o `manifest.json` de cada Rodada |
| `RELATORIO.md` | Relatório gerado pelo Replay, com a conclusão registrada |
| `testes/` | Suíte pytest (offline por padrão) |
| `../docs/` | Ideia, design, spec e ADRs (ver [Como o trabalho foi feito](#como-o-trabalho-foi-feito)) |
| `../CONTEXT.md` | Glossário do domínio |

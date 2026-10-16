# Pré-registro: experimento confirmatório v0 × v1 no holdout (CAR-23)

Escrito e commitado em 2026-10-16, **antes de qualquer Chamada ao modelo sobre o holdout**.
O commit que adiciona este arquivo é a marca de tempo: as Rodadas do holdout vêm em commits
posteriores. Nada abaixo muda depois de ver os dados; se algo tiver de mudar, a mudança entra
como emenda datada no fim, com o motivo, e o Relatório diz isso.

## Por que este experimento existe

A conclusão do CAR-20 ([`RELATORIO.md`](../../cx-prompt-lab/RELATORIO.md)) foi "exploratório,
inconclusivo por efeito piso", por dois motivos:

1. **Efeito piso.** A métrica principal da regra de melhora era a Alucinação, que já era 0 em v0.
   Não havia queda possível para medir.
2. **Contaminação desenvolvimento/teste.** v1 foi escrita depois de ver as falhas de v0 nas mesmas
   24 Transcrições usadas para medir.

Este experimento ataca os dois sem mudar a arquitetura: troca a métrica primária por uma que não
está no piso e mede num holdout novo que nunca foi usado para desenvolver prompt.

## Hipótese

- **H1:** no holdout, v1 produz menos Violações de formato do que v0 (mesmo modelo, mesmos
  parâmetros pedidos).
- **H0:** v0 e v1 têm a mesma taxa de Violação de formato no holdout.

Teste bicaudal: uma piora de v1 também é detectável e seria relatada como tal.

## Versões comparadas (congeladas)

| Versão | Arquivo | SHA-256 |
|---|---|---|
| v0 (base) | `cx-prompt-lab/prompts/v0.md` | `db30ff2e213224deaf440dc588ea6a0953889fb0ebcaa17da5fd16e47355f4fb` |
| v1 (candidata) | `cx-prompt-lab/prompts/v1.md` | `94ea40f871ac7d45e5896fb9da50e598d9d2c4266ea0af97e0231ca88cfd4419` |

Nenhuma v2 entra neste experimento: v2 seria desenvolvida depois de v1 e precisaria do seu próprio
holdout. Os prompts não são alterados.

## Holdout

- Dois arquivos novos, `cx-prompt-lab/dataset/holdout_a.json` e `holdout_b.json`, **30 Transcrições
  cada (60 no total)**. Dois arquivos porque a validação existente do Dataset aceita 20 a 30
  Transcrições por arquivo, e mudar essa regra seria mudar a spec; a análise junta os dois.
- Fictícios, escritos para este experimento (nenhum dado real de cliente). Mesmos 6 Rótulos e mesma
  regra de desempate do Dataset de desenvolvimento; 5 Transcrições por Rótulo em cada arquivo, das
  quais 1 de intenção dupla e 1 ambígua. Algumas trazem uma fala do Agente antes da do Cliente.
- **Nunca usados para desenvolver prompt**: v0 e v1 já estavam congeladas quando o holdout foi
  escrito, e nenhum dos dois prompts muda depois.
- Congelados por hash (`gravacao.hash_dataset`), conferido por `testes/holdout_dataset_test.py`:
  - `holdout_a`: `775552356466b96063309085e3c902bbcf88f115b636b9ae4052459b37536fa8`
  - `holdout_b`: `e6d64b422e3d5329d9c197aff5a4fa4c91e9a9ed3e1aac2080fca4fde69054c5`
- Os testes também garantem que nenhum texto do holdout repete o Dataset de desenvolvimento nem
  aparece nos prompts.

## Métricas

- **Primária: taxa de Violação de formato**, definida exatamente como já está no Avaliador e no
  Executor (resposta que não é um objeto JSON puro com `rotulo` e `justificativa`, incluindo JSON
  dentro de bloco de código markdown, truncada ou recusa). Por que esta: é a falha que motivou v1
  e, no Dataset de desenvolvimento, v0 ficou em 62,5%, longe do piso e do teto. É também o que
  importa num contact center: uma resposta que o programa não consegue ler é uma classificação
  perdida.
- **Secundária: taxa de não acerto** (Chamada sem Rótulo válido e igual ao esperado). Mesmo teste
  da primária, relatada mas sem decidir o veredito.
- **Descritivas, sem teste:** Erro de acerto e Alucinação (ambas foram 0 no desenvolvimento; podem
  continuar no piso).

## Unidade de análise e testes

A unidade é a **Transcrição**, não a Chamada: as Repetições de uma Transcrição são correlacionadas.
Para cada Transcrição e versão, conta-se em quantas das R Repetições houve Violação de formato.

- **Teste primário: teste do sinal exato, bicaudal**, sobre a diferença pareada por Transcrição
  (falhas de v0 menos falhas de v1). Empates saem. É o McNemar exato com a Transcrição como par.
- **Tamanho de efeito:** diferença de taxas (v1 − v0) com **IC 95% por bootstrap de clusters**
  (reamostra Transcrições com reposição, 10.000 reamostras, semente `20261016`, IC percentil).
  Cada versão também ganha o seu IC da taxa pelo mesmo método.
- **α = 0,05.**
- Implementação: `cx_prompt_lab/estatistica.py` e `cx_prompt_lab/confirmatorio.py`, só stdlib,
  com testes contra valores calculados à mão. Comando: `python3 -m cx_prompt_lab confirmar`.

## Tamanho da amostra (justificativa de poder)

60 Transcrições × **5 Repetições** × 2 versões = **600 Chamadas** (300 por versão).

Justificativa por simulação, usando as taxas por Transcrição observadas no desenvolvimento
(car20-v0 e car20-v1) como distribuição plausível: sorteia-se o holdout com reposição dessas
Transcrições e as Repetições como Bernoulli, e aplica-se o teste do sinal com α = 0,05.

| Transcrições × Repetições | Poder, efeito igual ao do dev | 75% do efeito | 50% do efeito |
|---|---:|---:|---:|
| 24 × 3 (desenho do CAR-20) | 0,62 | 0,54 | 0,40 |
| 30 × 5 | 0,76 | 0,71 | 0,59 |
| **60 × 5 (escolhido)** | **0,98** | **0,97** | **0,91** |

O que limita o poder é o número de Transcrições, não de Repetições; por isso 60 e não 30. O custo é
baixo (prompts de ~300 tokens, respostas de ~60), e todas as Chamadas ficam gravadas para o Replay.

## Regra de decisão (o que conta como conclusivo)

Aplicada à métrica primária, nesta ordem:

1. p < 0,05 e mais Transcrições a favor de v1 → **melhora confirmada** (conclusivo positivo).
2. p < 0,05 e mais Transcrições a favor de v0 → **piora confirmada** (conclusivo negativo).
3. p ≥ 0,05 e o IC 95% da diferença inteiro dentro de ±10 pp → **sem diferença relevante**
   (conclusivo negativo: v1 não melhora o formato de forma que importe).
4. Qualquer outro caso → **inconclusivo** (relatado como tal, sem nova rodada para "desempatar").

A regra de melhora original do CAR-18 (baseada em Alucinação) continua no código e no Relatório do
Replay; ela não é substituída, só deixa de ser a pergunta deste experimento, porque já se sabe que
ela não decide nada com Alucinação no piso.

## Protocolo de execução

- Provider: o mesmo das Rodadas do CAR-20, `--provider gateway` (CLIProxyAPI local, ADR 0002),
  modelo pedido `claude-sonnet-4-5-20250929`, `--temperatura 0` (pedida), `--max-tokens 256`,
  `--timeout-s 30`, `--repeticoes 5`. Sem troca de provider.
- Rodadas, nesta ordem (ABBA, para não confundir versão com deriva no tempo):
  1. `car23-holdout-a-v0` 2. `car23-holdout-a-v1` 3. `car23-holdout-b-v1` 4. `car23-holdout-b-v0`
- Gravadas em `cx-prompt-lab/rodadas-holdout/holdout_a/` e `.../holdout_b/`, separadas de
  `rodadas/` para o Replay do CAR-20 continuar idêntico ao publicado.
- **Aborto de infraestrutura** (erro HTTP, timeout): a Rodada abortada fica gravada como está
  (estado `abortada`, que o Replay recusa) e a mesma Rodada é refeita inteira com o sufixo `-r2`
  (`-r3`...). Aborto não depende da resposta do modelo, então refazer não é escolher resultado.
  Toda Rodada abortada é listada no Relatório.
- **Nada é refeito por causa do resultado.** Uma Rodada completa nunca é descartada nem
  repetida. Nenhum prompt é ajustado olhando o holdout.

## Limitações conhecidas de antemão

- **Temperatura efetiva desconhecida.** O Gateway não repassa `temperature` ao upstream (ADR 0002,
  C5a). A temperatura 0 é a pedida. A análise trata as 5 Repetições como amostras do modelo como
  ele de fato respondeu, o que vale com qualquer temperatura efetiva; o que não dá para afirmar é
  que o resultado vale para temperatura 0 de verdade.
- Um modelo, um provedor (via Gateway, não a API oficial), um idioma, Dataset fictício e equilibrado.
- O holdout foi escrito pela mesma pessoa/agente que escreveu o Dataset de desenvolvimento: é
  independente dos prompts, mas não de quem escreve Transcrições.
- Generalização: a conclusão vale para esta tarefa (classificar intenção com saída JSON estrita),
  não para "prompts em geral".

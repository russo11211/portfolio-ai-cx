# Relatório (Replay)

Resultado declarado como exploratório: as taxas abaixo não são prova estatística formal, servem para julgar a iteração do candidato entre versões de prompt.
Limite do Replay: este comando prova o cálculo a partir das Chamadas já gravadas, não que o modelo responderia igual hoje. Replay recalcula offline, sem chamar nenhum provider; Reexecução chama o provider de novo e pode produzir Chamadas diferentes.

## Tabela por versão

| Versão | Erro de acerto | Alucinação | Violação de formato |
|---|---|---|---|
| v0 | 0.0% | 0.0% | 62.5% |
  modelo: claude-sonnet-4-5-20250929; data das Chamadas: 2026-10-01T01:33:09Z a 2026-10-01T01:34:54Z
| v1 | 0.0% | 0.0% | 33.3% |
  modelo: claude-sonnet-4-5-20250929; data das Chamadas: 2026-10-01T01:38:01Z a 2026-10-01T01:39:57Z

## Resultado de cada Repetição

Versão v0:
  Repetição 1: erro de acerto=0, alucinação=0, violação de formato=14, acertos=10
  Repetição 2: erro de acerto=0, alucinação=0, violação de formato=17, acertos=7
  Repetição 3: erro de acerto=0, alucinação=0, violação de formato=14, acertos=10
Versão v1:
  Repetição 1: erro de acerto=0, alucinação=0, violação de formato=10, acertos=14
  Repetição 2: erro de acerto=0, alucinação=0, violação de formato=7, acertos=17
  Repetição 3: erro de acerto=0, alucinação=0, violação de formato=7, acertos=17

## Veredito (exploratório)

Veredito v0 × v1: inconclusivo por efeito piso
Métrica secundária (Erro de acerto por Repetição): v0 [0, 0, 0], v1 [0, 0, 0]; nenhuma melhora é declarada.
Só v0 × versão final tem veredito; resultado exploratório, sem prova estatística formal.

## Margem de variação da Reexecução

Margem de variação: amplitude (maior menos menor) da taxa entre as Repetições da versão, em pontos percentuais de taxa. A margem vale para a Reexecução: diferença menor que ela entre Rodadas novas pode ser ruído. O Replay não tem ruído, o Replay bate exatamente. A margem é só descritiva e não decide nenhum veredito (o veredito é o da seção acima).

- v0: erro de acerto 0.0 pp, alucinação 0.0 pp, violação de formato 12.5 pp
- v1: erro de acerto 0.0 pp, alucinação 0.0 pp, violação de formato 12.5 pp

## Transcrições que mudaram de Rótulo (ilustrativa)

Lista ilustrativa: compara só a Repetição 1 de cada versão consecutiva; resposta sem Rótulo válido aparece como "sem rótulo válido".

v0 → v1 (Repetição 1):
- t02: cancelamento → sem rótulo válido
- t03: cancelamento → sem rótulo válido
- t05: sem rótulo válido → duvida_fatura
- t09: sem rótulo válido → reclamacao
- t10: sem rótulo válido → reclamacao
- t12: sem rótulo válido → reclamacao
- t16: sem rótulo válido → suporte_tecnico
- t17: sem rótulo válido → elogio

## Todas as Rodadas do repositório

- car20-v0 (versão v0, estado completa): no experimento atual
- car20-v1 (versão v1, estado completa): no experimento atual

Compatível com Anthropic: o formato de pedido/resposta segue o vocabulário da API Anthropic. Isto não é validação contra a API oficial.


## Conclusão registrada (CAR-20, exploratória)

- v0 → v1 (mesmo modelo `claude-sonnet-4-5-20250929`, temperatura pedida 0, `max_tokens` 256, 3 Repetições cada, 24 Transcrições): **inconclusivo por efeito piso**. Erro de acerto e Alucinação foram 0 em todas as Repetições das duas versões, então a regra de melhora não pode declarar melhora.
- O que v1 mudou e por quê: só o Contrato de saída. v0 falhou 100% por formato (45 de 72 respostas vieram em bloco de código markdown, apesar de v0 proibi-lo). v1 explica que um programa rejeita qualquer resposta que não comece com `{` e mostra a forma exata da resposta com valores inventados.
- Observação (não é veredito): a Violação de formato caiu de 62,5% (45/72) para 33,3% (24/72); acertos subiram de 7–10 para 14–17 por Repetição. A temperatura efetiva não foi verificada (ADR 0002).
- Limites: o mesmo Dataset serviu para desenvolver e medir; v1 ainda falha em formato em 7–10 de 24 Transcrições, o que fica como alvo de v2 (CAR-22).


## Experimento confirmatório (CAR-23, pré-registrado)

A saída abaixo é a de `python3 -m cx_prompt_lab confirmar` (offline, a partir de `rodadas-holdout/`), sem o banner e o título da primeira linha, com os subtítulos rebaixados para `####`; o resto é idêntico. Pré-registro: `docs/spec/cx-prompt-lab-preregistro-holdout.md`, commitado antes de qualquer Chamada no holdout. Ele responde às duas limitações do CAR-20 acima: a métrica primária passa a ser a Violação de formato (fora do piso) e a medição usa um holdout de 60 Transcrições nunca usado para desenvolver prompt.


Regras de decisão pré-registradas em docs/spec/cx-prompt-lab-preregistro-holdout.md, commitadas antes de qualquer Chamada no holdout. Calculado offline a partir das Chamadas gravadas.

Transcrições do holdout: 60; Repetições por Transcrição: 5; Chamadas por versão: 300.
Modelo devolvido: claude-sonnet-4-5-20250929.
Rodadas: holdout_a/car23-holdout-a-v0, holdout_a/car23-holdout-a-v1, holdout_b/car23-holdout-b-v0, holdout_b/car23-holdout-b-v1.
Bootstrap: 10000 reamostras de Transcrições, semente 20261016, IC percentil.

#### Métrica primária: Violação de formato

| Versão | Chamadas com falha | Taxa | IC 95% (bootstrap por Transcrição) |
|---|---:|---:|---|
| v0 | 227/300 | 75.7% | 66.7% a 83.7% |
| v1 | 167/300 | 55.7% | 46.7% a 64.3% |

Diferença (v1 − v0): -20.0 pp, IC 95% -29.3 pp a -11.0 pp.
Teste do sinal (por Transcrição): 33 a favor de v1, 9 a favor de v0, 18 empates; p = 2.72e-04 (bicaudal, exato).

#### Métrica secundária: Não acerto (sem Rótulo válido e correto)

| Versão | Chamadas com falha | Taxa | IC 95% (bootstrap por Transcrição) |
|---|---:|---:|---|
| v0 | 229/300 | 76.3% | 67.3% a 84.3% |
| v1 | 170/300 | 56.7% | 47.7% a 65.7% |

Diferença (v1 − v0): -19.7 pp, IC 95% -29.0 pp a -10.7 pp.
Teste do sinal (por Transcrição): 32 a favor de v1, 10 a favor de v0, 18 empates; p = 9.41e-04 (bicaudal, exato).

#### Descritivo (sem teste)

- Erro de acerto: v0 2, v1 3 (Chamadas)
- Alucinação: v0 0, v1 0 (Chamadas)

#### Veredito pré-registrado

Veredito v0 × v1 na métrica primária: **melhora confirmada** (α = 0.05, margem de equivalência ±10 pp).
Escopo: um modelo, via Gateway local, temperatura efetiva desconhecida (ADR 0002); Dataset fictício. Não é validação contra a API oficial da Anthropic.


Leitura: a melhora é estatisticamente clara (IC da diferença inteiro abaixo de zero), mas v1 ainda falha em 55,7% das Chamadas, todas por JSON em bloco de código markdown. Rodadas na ordem ABBA, nenhuma abortada; Chamadas de 2026-10-16T13:03:18Z a 2026-10-16T13:19:52Z. O veredito exploratório do CAR-20 continua valendo para o CAR-20.

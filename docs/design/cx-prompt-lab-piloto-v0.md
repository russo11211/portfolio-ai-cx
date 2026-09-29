# Piloto de v0 e decisão de congelamento (T8, CAR-16)

Data: 2026-09-29

## O que foi rodado

Piloto de 8 Transcrições (t01–t08, subconjunto inicial do Dataset), 1 Repetição de v0,
contra o Gateway local (CLIProxyAPI), modelo devolvido `claude-sonnet-4-5-20250929`
(mesmo modelo confirmado no spike T1/CAR-9). Script efêmero:
`.scratch/piloto_v0.py`, saída completa em `.scratch/piloto_v0_saida.json`
(não commitados — rascunho de execução, não artefato do produto).

O prompt v0 (`cx-prompt-lab/prompts/v0.md`) é ingênuo no conteúdo — nenhum exemplo,
nenhuma estratégia de classificação — mas declara o Contrato de saída de forma
explícita: pede um objeto JSON puro com `rotulo` e `justificativa`, com regras de
formato reforçadas (resposta começa com `{`, termina com `}`, nunca usa bloco de
código markdown). Essa segunda versão do texto de v0 substituiu uma primeira redação
mais branda, testada primeiro (ver "Iteração durante o piloto" abaixo).

## Resultado

| Métrica | Taxa (n=8) |
|---|---|
| Violação de formato | 87,5% (7/8) |
| Alucinação | 0% (0/8) |
| Erro de acerto | 0% (0/8) |

A única resposta interpretável (t07) acertou o rótulo (`duvida_fatura`) com
Justificativa ancorada.

## Causa da Violação de formato

Todas as 7 respostas não interpretáveis vieram com `motivo_parada = fim_normal`
(a Chamada terminou normalmente) mas o corpo veio envolto em bloco de código
markdown (` ```json ... ``` `), apesar da instrução explícita em contrário. O parser
do Avaliador é estrito por decisão da spec (tabela de contagem, linha (f): "JSON
dentro de code fence ou com prosa em volta" é Violação de formato, e o parser "não
remove code fence nem prosa em volta") — o comportamento do parser está correto; o
problema é o hábito do modelo de cercar JSON em bloco de código, que a instrução de
v0 não elimina de forma confiável.

## Iteração durante o piloto

Uma primeira redação de v0 (sem as "Regras de formato" explícitas, só "responda
apenas com um objeto JSON puro... sem bloco de código") teve 100% (8/8) de Violação
de formato pelo mesmo motivo. A segunda redação, com as três regras de formato
reforçadas, reduziu para 87,5%. Essa segunda redação é a que ficou em
`prompts/v0.md`. Reforçar a declaração do Contrato de saída não é "estratégia de
classificação" (v0 continua sem exemplos nem heurística de rótulo) — é a exigência
da própria spec de que v0 "declara o Contrato de saída de forma explícita".

Duas chamadas repetidas para a mesma Transcrição (t01, fora da amostra do piloto,
só para diagnóstico) produziram uma vez com bloco de código e uma vez sem, com
`temperatura=0` — inconsistente com determinismo, e alinhado ao achado já registrado
na ADR 0002 (C5a/C5b: temperatura efetiva não verificada no Gateway).

## Decisão

**Congelar o Dataset e v0 como estão.** A taxa alta de Violação de formato é um
resultado válido e esperado de um prompt v0 deliberadamente ingênuo — é exatamente
o ponto de partida honesto contra o qual medir v1 (história 27 da spec). O Dataset
(8 casos do piloto, todos com Rótulo esperado atribuído corretamente pelo humano)
não mostrou nenhum problema de conteúdo: a única resposta interpretável acertou.
Não há evidência de que o Dataset precise de ajuste.

Não há mais engenharia de prompt a fazer em v0 sem cruzar para "estratégia de
classificação" (few-shot, decomposição, reforço além do contrato de formato), que a
spec reserva para v1. A alta Violação de formato de v0 vira o ponto de partida do
case study de v1: reduzir Violação de formato é um objetivo explícito da próxima
versão.

## Verificação

O teste `test_nenhuma_transcricao_do_dataset_aparece_em_exemplo_de_prompt`
(`cx-prompt-lab/testes/dataset_test.py`, dono: T7) segue verde com
`prompts/v0.md` presente — confirmado rodando a suíte offline depois de escrever o
prompt.

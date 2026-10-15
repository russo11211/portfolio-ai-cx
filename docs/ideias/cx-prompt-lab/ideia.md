---
slug: cx-prompt-lab
titulo: CX Prompt Lab — biblioteca versionada de prompts com evals para contact center
criada: 2026-09-21
atualizada: 2026-09-23
rodadas: 14
status: pronta-para-spec
---

# CX Prompt Lab — biblioteca versionada de prompts com evals para contact center

## 1. O quê        <!-- status: fechado -->

Uma subpasta `cx-prompt-lab/` no monorepo `portfolio-ai-cx` contendo: (1) prompts
versionados (v0 a v3) para **um único problema** — classificação de intenção de chamada
em contact center; (2) um dataset fixo de 20-30 transcrições fictícias de atendimento,
cada uma com o rótulo de intenção correto; (3) um script de eval em Python que roda cada
versão do prompt contra o dataset via API Anthropic e produz métricas de acerto e taxa de
alucinação por versão; (4) um case study em texto documentando o que mudou entre versões
e por quê.

## 2. Para quem    <!-- status: fechado -->

Recrutador/entrevistador técnico nas empresas-alvo (Porto, NCS/GFT, Bain/Caju) avaliando
candidatos para vagas de engenharia de prompt / IA aplicada a contact center.

**Substituto atual:** desafio técnico assíncrono (take-home). Prova execução contra um
problema *que a empresa definiu*, mas não prova que o candidato sabe escopar sozinho nem
que mede a própria iteração ao longo do tempo — é isso que este artefato precisa deixar
explícito para ganhar contra esse substituto.

## 3. Por quê / objetivo    <!-- status: fechado -->

O candidato passa a ter um artefato auditável para apontar durante conversas técnicas e
entrevistas nas empresas-alvo, que substitui a resposta verbal genérica sobre prompt
engineering/evals por evidência específica, versionada e mensurável.

Se não existir: o candidato depende inteiramente de autodeclaração (CV) ou de
performance ao vivo sob pressão (entrevista verbal) para provar essas competências, sem
histórico nem métrica que sustente a afirmação.

## 4. Como (abordagem em alto nível)    <!-- status: fechado -->

O eval roda contra um provedor de LLM trocável: durante o desenvolvimento, contra um
gateway local (para não depender de consumo pago), e, separadamente, contra a API
oficial da Anthropic para gerar a evidência que a issue original pede ("integração com
API Anthropic"). O relatório final distingue explicitamente o que foi validado contra o
gateway (compatibilidade) do que foi validado contra a Anthropic real.

**Decisão difícil de reverter:** a superfície de chamada (formato de mensagem, papéis,
parâmetros) segue o formato da API Anthropic desde o início, mesmo rodando contra o
gateway — para que trocar para a API oficial não exija reescrever a lógica do eval.

*(Detalhe de interface, classes, docker-compose e comandos de teste fica para a ADR do
estágio 7 — ver `arquitetura-llm-provider-notas.md`.)*

## 5. Não é escopo    <!-- status: fechado -->

1. **Triagem de URA e resumo de atendimento** — critério de acerto subjetivo demais para
   o rigor de eval que este primeiro corte quer provar (dimensão 1).
2. **Produto real para agente de contact center (UX, interface operacional)** — o "para
   quem" é o recrutador/entrevistador, não um usuário operacional (dimensão 2).
3. **Framework de orquestração de LLM (LangChain e similares)** — a decisão irreversível
   é usar a superfície de chamada Anthropic diretamente, com uma camada de troca de
   provider própria e mínima, não um framework (dimensão 4).
4. **Múltiplos providers com fallback automático** — complexidade que não serve ao
   objetivo de "artefato auditável em 1 semana" (nota de arquitetura, item 14).
5. **Fine-tuning do modelo** — competência diferente da que está sendo provada (prompt
   engineering, não treino de modelo); contaminaria o "o quê" se entrasse.
6. **Interface web para rodar o eval + CI automatizado** — servem um objetivo diferente
   (visibilidade pública/LinkedIn, não evidência para conversa técnica com recrutador).
   Registrado como ideia futura separada em
   CAR-6,
   com seu próprio ciclo de `/ideacao` quando for retomada.

## 6. Riscos e premissas    <!-- status: fechado -->

1. **Premissa:** o CLIProxyAPI local suporta um modelo compatível o suficiente com
   Anthropic para rodar o eval sem custo durante o dev. **Como testar:** rodar uma
   chamada de teste (Teste B da nota de arquitetura) antes de escrever qualquer prompt
   de produção. **Custo se falsa:** perde-se o motivo de usar o gateway — cai para
   consumo pago direto da API oficial desde o início, ou é preciso achar outro gateway.

2. **Premissa:** 20-30 exemplos fictícios são suficientes para mostrar uma queda
   mensurável e não-ruidosa na taxa de alucinação entre v0 e a versão final. **Como
   testar:** observar a variância dos resultados por rodada — se o mesmo prompt dá
   respostas diferentes em re-execuções, o dataset é pequeno demais para essa conclusão.
   **Custo se falsa:** o case study perde credibilidade (métrica instável); é preciso
   aumentar o dataset ou rodar múltiplas repetições por exemplo.

## 7. Critério de sucesso    <!-- status: fechado -->

**Definições usadas pelo eval (ambas checáveis por script, sem julgamento subjetivo):**
- **Erro de acerto:** o modelo escolhe uma intenção válida da lista de rótulos, mas a errada.
- **Alucinação:** o modelo devolve algo fora do contrato — uma intenção que não existe na lista de rótulos, ou uma justificativa que cita algo que não está na transcrição.

Dentro de **1 semana de trabalho** (a partir do início do estágio de implementação),
existe uma queda **mensurável e documentada** na taxa de alucinação entre a v0 (prompt
ingênuo) e a versão final, medida no mesmo dataset fixo de 20-30 exemplos. "Versão
final" = a última versão concluída; o mínimo aceito é v1 (ver dimensão 8) — se a semana
estourar, v0 → v1 documentado ainda satisfaz o critério. Sem piso
numérico prometido de antemão — o rigor está em medir e documentar honestamente, não em
garantir um percentual de melhora. Esse relatório é o que o candidato leva para
conversas técnicas com o recrutador/entrevistador das empresas-alvo (dimensão 2).

**Reprodutibilidade (liga o sucesso ao "auditável" da dimensão 3):** quem clonar o repo
consegue rodar o eval e chegar aos mesmos números de v0 e v1, dentro de uma margem de
variação declarada. Como o modelo não é determinístico, o relatório registra a variação
observada entre execuções repetidas.

## 8. Primeiro corte entregável    <!-- status: fechado -->

**Corte mínimo aceito: v0 → v1 ponta a ponta.** Dataset fictício pronto (20-30
transcrições rotuladas), eval rodando contra o gateway local, pelo menos uma chamada de
validação real contra a API oficial da Anthropic, e uma queda mensurável de alucinação
documentada entre v0 e v1.

**Alvo:** v0 → v3 completo dentro de 1 semana. Se a semana estourar, o corte v0 → v1 já
conta como primeiro corte entregue — v2/v3 viram iteração seguinte, sem invalidar o
resultado.

**O que prova:** o pipeline inteiro funciona (dataset, eval, os dois providers) e a
iteração de prompt produz efeito medido — que é exatamente a lacuna que o take-home e a
entrevista verbal não cobrem (dimensão 2).

## Registro de decisões
<!-- append-only -->

| data | decisão | o que foi descartado e por quê |
|---|---|---|
| 2026-09-22 | "Para quem" = recrutador/entrevistador técnico das empresas-alvo, não um usuário fictício de contact center | Descartado tratar isso como produto real para um agente de CX — infla escopo com UX que não serve ao objetivo real (demonstrar competência técnica de forma auditável) |
| 2026-09-22 | "O quê" cobre **um único** caso de uso: classificação de intenção de chamada | Descartados triagem de URA e resumo de atendimento no primeiro corte — critério de acerto/alucinação é subjetivo demais nesses dois, diluiria o rigor do eval que é o ponto central a provar |
| 2026-09-22 | Objetivo = ter artefato auditável para conversas técnicas/entrevistas, não métricas de carreira (taxa de resposta, nº de entrevistas) | Descartado medir o objetivo em resultado de carreira — depende de fatores fora do controle do artefato (mercado, ATS, timing); o artefato só controla se a evidência existe e é auditável |
| 2026-09-22 | Sucesso = queda mensurável e documentada na taxa de alucinação v0→final, em 1 semana, sem piso numérico prometido | Descartado prometer um percentual mínimo de melhora antes do experimento rodar — viraria meta artificial que força o prompt a parecer melhor do que é |
| 2026-09-22 | "Como" = provider de LLM trocável (gateway local durante dev, Anthropic oficial para validação), superfície de chamada no formato Anthropic desde o início | Descartado detalhar interfaces/classes/docker/comandos de teste agora — isso é decisão de implementação, fica registrado em `arquitetura-llm-provider-notas.md` para a ADR do estágio 7 |
| 2026-09-22 | Riscos = (1) CLIProxyAPI suportar modelo compatível sem custo, (2) 20-30 exemplos serem suficientes para sinal não-ruidoso | Nenhum item descartado — usuário confirmou as duas premissas propostas sem alteração |
| 2026-09-23 | Primeiro corte = v0→v1 ponta a ponta como mínimo aceito; alvo v0→v3 em 1 semana. Ajusta a dimensão 7: "versão final" passa a ser a última concluída, mínimo v1 | Descartado exigir v0→v3 como condição de sucesso — apertado demais para 1 semana com setup de gateway, validação Anthropic real e dataset do zero; v2/v3 fortalecem o case study mas não são o que prova algo pela primeira vez |
| 2026-09-22 | Não-escopo fechado com 6 itens; interface web + CI automatizado viram ideia futura separada (CAR-6) em vez de v2 desta ideia | Descartado incluir no primeiro corte ou tratar como v2 — contradiz o critério de sucesso de 1 semana e serve um "para quem"/"por quê" diferente (LinkedIn, não recrutador de processo seletivo) |
| 2026-09-23 | Sucesso inclui reprodutibilidade: terceiro que clonar o repo reproduz os números de v0 e v1 dentro de margem de variação declarada | Descartado deixar o sucesso só em "o número existe" — número sem como reproduzir é autodeclaração, a mesma fraqueza do CV que o artefato quer superar |
| 2026-09-23 | Alucinação = saída fora do contrato (intenção inexistente na lista de rótulos, ou justificativa que cita algo ausente da transcrição); erro de acerto = rótulo válido porém errado | Descartado tratar os dois como uma métrica só — misturaria erro comum com invenção e esconderia o que o case study quer mostrar |

## Perguntas em aberto

*(nenhuma)*

## Fontes e anexos

- Issue original: CAR-1 — Fase 1 — CX Prompt Lab (Linear, time Carreira). Conteúdo bruto trazido como ponto de partida, não como decisão fechada — a issue **será atualizada** ao final deste estágio com o que ficar decidido aqui.
- `arquitetura-llm-provider-notas.md`: material bruto de arquitetura (provider abstraction, CLIProxyAPI + Anthropic) colado pelo usuário — insumo para a ADR do estágio 7, não decisão de ideia.

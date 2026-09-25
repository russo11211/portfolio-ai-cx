# portfolio-ai-cx

Este projeto roda na **fábrica agêntica**. Você é o operador da linha de montagem.

## Contrato da fábrica

1. **Trabalho por estágios.** Cada estágio consome um artefato e produz outro.
2. **Não pule estágio.** Se o artefato de entrada não existe em disco, o estágio não
   começou. Pare e diga qual artefato falta.
3. **Um estágio só terminou quando o arquivo dele existe em disco.** Conversa não conta.
   Nunca declare um estágio concluído sem ter escrito o arquivo.
4. **Um gate por estágio.** O gate é checklist verificável, não opinião. Rode o gate
   contra o arquivo e responda PASSA ou NÃO PASSA, item por item.

## Fluxo — 12 estágios

| # | Estágio | Comando | Entrada | Saída | Gate para avançar |
|---:|---|---|---|---|---|
| 1 | Ideação | `/ideacao` | uma frase de ideia | `docs/ideias/<slug>/ideia.md` | `status: pronta-para-spec`; 8 dimensões `fechado`; critério de sucesso com **unidade + valor + prazo**; ≥3 itens em "não é escopo" |
| 2 | Pressão & crítica | `/office-hours` | `ideia.md` | `docs/design/<slug>-design.md` | escopo saiu **menor**; "por que agora" em uma frase |
| 3 | Vocabulário | `/grill-with-docs` | `ideia.md` | `CONTEXT.md` + `docs/adr/` | cada termo repetido tem definição que **exclui** algo |
| 4 | Spec | `/to-spec` | `ideia.md` + `CONTEXT.md` | spec no Linear (cópia em `docs/spec/<slug>.md`) | um estranho lê e sabe: problema, fora de escopo, como verificar. Zero critério não verificável |
| 5 | Revisão de plano | `/autoplan` (roteiro na seção "Estágio 5") | spec | spec revisada + triagem no Review record | nenhum crítico aberto; alguma coisa foi **cortada** com justificativa escrita; nenhuma interpretação `PENDENTE`; triagem registrada; spec commitada |
| 6 | Tickets | `/to-tickets` | spec revisada | **issues no Linear** (time Carreira; um ticket = uma issue) | cada ticket cabe em 1 PR **e** entrega algo observável (tracer bullet, não camada) |
| 7 | Arquitetura | `/codebase-design` | tickets + repo + "Exigências da ADR do E7" (triagem do E5) | ADR em `docs/adr/` | as **seams** estão nomeadas; para cada ticket você sabe qual seam ele toca; cada exigência do E5 foi decidida na ADR ou descartada com motivo |
| 8 | Implementação | `/implement` (dirige `/tdd`) | **um** ticket | commit verificado por testes | teste que falhava antes passa; suíte verde; diff só nos arquivos previstos na ADR |
| 9 | QA | `/qa` | app rodando | bugs corrigidos + `docs/qa/<data>-<slug>.md` | o relatório **nomeia os fluxos percorridos**, e são os do primeiro corte |
| 10 | Code review | `/review` (+ `/cso` se toca auth/input/segredo/endpoint) | diff / PR | veredito + correções | zero achado em aberto; zero achado alto de segurança; **humano leu** |
| 11 | Ship | `/ship` | código revisado | PR + `CHANGELOG.md` + `VERSION` | PR aberto, CI verde, CHANGELOG em linguagem de usuário |
| 12 | Deploy & fechamento | `/setup-deploy` (1ª vez) → `/land-and-deploy` → `/canary` → `/document-release` → `/learn` → `/retro` | PR aprovado | release + `docs/retro/` + lições | janela de canário limpa **verificada por alguém**; um estranho usa o release lendo só o README |

## Tickets e acompanhamento vivem no Linear

O **Linear é o tracker oficial** deste projeto. Ele chega pelo plugin
`linear@claude-plugins-official`, ligado no `.claude/settings.json`, e aparece como as
ferramentas `mcp__plugin:linear:linear__*`.

- **Todo ticket, todo acompanhamento de progresso e todo gerenciamento de projeto vivem
  no Linear.** Issue, status, projeto, ciclo, comentário de andamento: lá.
- **Não crie arquivo de ticket local enquanto o Linear responder.** Nada de
  `.scratch/<feature>/issues/NN-slug.md`, nada de `TODO.md`, nada de lista de tarefas em
  markdown fazendo as vezes de backlog. O `.scratch/` é rascunho efêmero, não tracker.
- **O que fica em disco é a cópia de leitura**, não a fonte da verdade: `docs/spec/<slug>.md`
  (spec), `docs/adr/` (decisão). A issue do Linear é quem manda.
- **Ao criar issue, registre o link.** Toda spec e todo PR citam o identificador da issue
  (`ABC-123`), para a rastreabilidade ideia → spec → ticket → PR → release fechar.
- **`/setup-matt-pocock-skills` não tem o Linear como opção de primeira classe** — as
  nativas dele são GitHub, GitLab e markdown local. Escolha **"Other"** e descreva o
  Linear: ele grava essa descrição em `docs/agents/issue-tracker.md`, que é o arquivo
  que `/to-spec` e `/to-tickets` leem para saber onde publicar.
- **Se o Linear não responder** (MCP fora do ar, não autenticado, sem permissão):
  **pare e avise o humano.** Não invente um tracker local de substituição. Se ele
  autorizar explicitamente um registro provisório, escreva em
  `.scratch/<feature>/issues-pendentes.md`, diga que é provisório e crie as issues no
  Linear assim que ele voltar. Autenticação do MCP é `/mcp` numa sessão interativa.

**Entre estágios: `/clear`.** Entre cada ticket do estágio 8: `/clear` **obrigatório**.
O artefato é a memória; a conversa não precisa sobreviver.

## Skills permitidas neste projeto

Só estas existem aqui. Se algo parece pedir outra skill, é sinal de que o estágio está
errado — pare e pergunte.

**Da esteira**
- `/ideacao` — E1. Loop de uma pergunta por rodada até o `ideia.md` fechar.
- `/office-hours` — E2. Pressiona a ideia formada e corta escopo.
- `/grill-with-docs` — E3. Entrevista que fixa a linguagem ubíqua em `CONTEXT.md`.
- `/setup-matt-pocock-skills` — E3, **uma vez por repositório**: configura o issue
  tracker que `/to-spec` e `/to-tickets` usam. Responda **"Other"** e descreva o Linear.
- `/to-spec` — E4. **Sintetiza**, não entrevista. Se ele quiser te entrevistar, volte ao E1.
- `/autoplan` — E5. As 4 lentes (CEO, design, eng, DX) em sequência, um gate humano só.
  Siga a seção "Estágio 5 — checklist operacional".
- `/to-tickets` — E6. Fatias verticais tracer-bullet com arestas de bloqueio, criadas
  como **issues no Linear**.
- `/codebase-design` — E7. Decide módulos e seams antes da primeira linha de código.
- `/implement` — E8. Um ticket por janela limpa.
- `/tdd` — E8. Vermelho → verde → refatora, restrito à seam acordada.
- `/qa` — E9. Exercita os fluxos no browser e corrige.
- `/browse` — E9 e qualquer navegação web (ver Regras).
- `/review` — E10. Gate pré-landing do PR inteiro.
- `/cso` — E10. Varredura de segurança do código.
- `/ship` — E11. Testes, VERSION, CHANGELOG, commit, push, PR.
- `/setup-deploy` — E12, uma vez: configura o destino do deploy.
- `/land-and-deploy` — E12. **Só com disparo humano explícito.**
- `/canary` — E12. Vigia a versão recém-publicada.
- `/document-release` — E12. Sincroniza README, CHANGELOG e docs.
- `/learn` — E12. Registra a lição nomeando a **classe** do problema.
- `/retro` — E12. Retrospectiva a partir do histórico do repositório.

**Transversais**
- `/guard` — trava escopo de diretório e avisa em comando destrutivo. Rode no começo de
  sessão que vai mexer em código.
- `/investigate` — quando o sintoma é difuso e você precisa de causa raiz.
- `/context-save` / `/context-restore` — quando a janela estoura **no meio** de um
  estágio, antes do `/clear`.

## Onde moram os artefatos

```
CONTEXT.md                          glossário — a linguagem ubíqua (E3). Só glossário.
CHANGELOG.md  VERSION  README.md    produzidos/atualizados pelo /ship e /document-release
docs/ideias/<slug>/ideia.md         E1
docs/design/<slug>-design.md        E2
docs/spec/<slug>.md                 E4 (cópia local da spec do tracker)
docs/adr/NNNN-titulo.md             E3 e E7 — decisões arquiteturais congeladas
docs/qa/<data>-<slug>.md            E9
docs/retro/<data>.md                E12
.scratch/                           rascunho efêmero. NÃO é lugar de ticket — ticket vive no Linear
.claude/                            configuração do harness deste projeto

Tickets (E6) vivem no Linear (time Carreira), não em arquivo local. Ver
`docs/agents/issue-tracker.md`.
```

Não invente outro lugar. Artefato fora da convenção quebra a rastreabilidade
ideia → spec → ticket → PR → release.

## Regras de comportamento

- **Não escreva código antes do estágio 8.** Nos estágios 1–7, nada de arquivo `.py`,
  schema de banco, escolha de biblioteca ou trecho de implementação. Se a pergunta for
  genuinamente executável ("dá para fazer com essa lib?"), diga que é um spike e peça
  autorização antes.
- **Não invente requisito que não está na spec.** Se falta informação, pare e pergunte.
  Preencher lacuna por conta própria contamina todos os estágios seguintes.
- **Pare e pergunte nos pontos de decisão humana:** o que fica fora de escopo (E1),
  seguir ou arquivar a ideia (E2), escopo, critério de sucesso, riscos bloqueantes,
  interpretações e cortes no gate único do E5 (o resto do E5 é triado sem perguntar),
  aceitar o risco do diff (E10), disparar o deploy (E12). Recomende; quem assina é o
  humano.
- **Decisão arquitetural vira ADR.** Se a conversa decidiu uma fronteira de módulo, uma
  seam, um formato de dado persistido ou uma dependência estrutural, escreva
  `docs/adr/NNNN-titulo.md` com: decisão, alternativas descartadas, motivo. Antes de
  escrever o código que a implementa.
- **Ticket é no Linear, sempre.** Nunca crie arquivo de ticket local enquanto o Linear
  responder (ver a seção "Tickets e acompanhamento vivem no Linear").
- **Navegação web é sempre `/browse`.** Nunca use ferramentas `mcp__claude-in-chrome__*`
  (elas estão bloqueadas em `.claude/settings.json`).
- **`/clear` entre estágios e entre tickets.** Lembre o humano quando ele esquecer.
- **Um estágio, uma sessão.** Não encadeie dois estágios na mesma janela.

## Estágio 5 — checklist operacional

Leia esta seção inteira ao abrir o E5. O modelo: revisão completa sem o humano, triagem
automática, **um** gate humano curto, verificação automática. Achado médio ou baixo nunca
segura o E5. Onde este roteiro e o `/autoplan` parecem discordar, vale a lista
"Divergências declaradas" no fim da seção.

**0. Antes de começar**
- [ ] Patches locais do gstack ativos: `git -C ~/.claude/skills/gstack branch --show-current`
  responde `fix/autoplan-native-parent-evidence` e os sinais rápidos de
  `~/GIT/Stack_Engenharia_Agnostica/skills-hub/patches/gstack/README.md` dão positivo para
  0001–0004. Um `/gstack-upgrade` apaga os patches. Se faltar algum, **pare e avise o
  humano**: não rode o `/autoplan` sem eles.
- [ ] Entrada: `docs/spec/<slug>.md` commitada no E4. Anote o commit de partida.

**1. Revisão completa (sem o humano).** `/autoplan` sobre a spec. Cada lente roda uma vez:
CEO → Design (só se houver UI) → DX (só se o escopo for de desenvolvedor) → Eng, sempre por último.
- Use os comandos que o `/autoplan` gera **literalmente**, inclusive o da voz externa (com o
  passo `OUTPUT LANGUAGE CONTRACT`). Não monte comando à mão.
- O checkpoint que o helper pede (`<AMENDMENT_CHECKPOINT>` no `prepare-close`; `CHECKPOINT_PATH`
  na mensagem de uso de `amend-input` e `prepare-close`) é o `snapshotPath` do `create` de
  **checkpoint de emenda**: o primeiro `create` da invocação da fase. Não é o `snapshotPath`
  do `create` que prepara a entrada das vozes (`<CEO_INPUT>`, `<ENG_INPUT>`…). Ele termina em
  `…/<fase>-implementation.md`, nunca em `snapshot.json`, e fica fixo até a fase fechar,
  inclusive depois de compactação.
- Publique cada `**Phase N complete.**` como mensagem visível sua, na hora, antes de qualquer
  chamada da fase seguinte. Esse anúncio fica em **inglês literal**, no começo da linha e fora
  de bloco de código: o hook de publicação procura esse texto.
- Recusa de hook, helper ou validador: **pare** e mostre a mensagem ao humano. Não contorne,
  não tente outro caminho, não edite estado à mão. As recusas conhecidas, com causa e ação,
  estão em "Se algo der errado".
- Blocos `autoplan-*` (`autoplan-accepted:*`, `autoplan-baseline-edits:*`) e a cópia aplicada
  no `## Implementation plan` são do protocolo. **Ninguém edita, remove ou "deduplica" à mão.**
  O registro no Review record e a cópia aplicada são idênticos de propósito.
- O arquivo tem exatamente um `## Implementation plan` e um `## Review record`. O que a fábrica
  acrescenta é `###` dentro do Review record, sem o prefixo `autoplan-`.
- **Interpretação sua não é requisito.** O que você acha que a spec quer dizer onde ela é
  ambígua, e todo acréscimo que você proporia, vai para `### Interpretações pendentes (E5)` no
  Review record, com ID (`I1`, `I2`…) e marcado `PENDENTE`. Nada disso entra no
  `## Implementation plan` antes do gate, **nem em bloco `autoplan-accepted:*`**: um bloco aceito
  nunca muda por baseline-edit (o helper recusa com `Baseline replacements cannot touch prior
  accepted blocks`), só dentro do próprio bloco numa rerun da mesma fase, e bloco de fase
  anterior é imutável; a interpretação ficaria presa na spec mesmo que o humano a recuse. O que as lentes aplicam pelo protocolo é provisório até o gate. A issue do
  Linear só é atualizada no fechamento.
- Revisão interna entre agentes e IAs pode ser em inglês. O que vai para o humano, em português.

**2. Triagem (sem o humano).** Depois da Pre-Gate Verification, classifique cada achado,
decisão de gosto, User Challenge, corte e acréscimo, e grave em `### Triagem da fábrica (E5)`
no Review record: ID, gravidade, destino, origem (fase e linha do Decision Audit Trail) e uma
frase.

| Gravidade | Critério objetivo (basta um) |
|---|---|
| crítico | requisitos que se contradizem; critério de sucesso inverificável ou inatingível como escrito; premissa central falsa; risco de segurança, perda de dado ou obrigação legal; dependência que não existe; escopo que não cabe no prazo do critério |
| alto | muda **o que** se entrega ou **como** se mede o sucesso: corte ou acréscimo de escopo, mudança de critério ou de limiar, risco que impede o E6 ou o E7 de começar sem uma decisão |
| médio | muda **como** se constrói, não o que se entrega: interface pública, forma de erro, esquema, estratégia de teste, observabilidade |
| baixo | polimento, nome, documentação extra, melhoria opcional fora do primeiro corte |

| Destino | O que vai |
|---|---|
| **Gate** | todo crítico; todo alto que toca escopo, critério de sucesso ou risco bloqueante. **E sempre**, qualquer gravidade: todo User Challenge, todo corte proposto, todo acréscimo de escopo, toda interpretação pendente |
| **Exigências da ADR do E7** | o resto que é decisão de implementação ou DX que o E8 teria de tomar sozinho: quickstart, README de primeiro uso, CLI e flags, códigos de saída, forma dos erros e mensagens, formato persistido e compatibilidade de esquema, fronteira de módulo ou seam, dependência externa, estratégia de teste de uma seam |
| **Adiados** | o resto: o primeiro corte é entregue e verificado sem isso. Expansões que o `/autoplan` mandou para o `TODOS.md`, polimento, docs além do quickstart, otimização sem requisito de desempenho, ideia de versão seguinte |

Desempate: na dúvida entre alto e médio, trate como alto. Entre ADR e adiado, ADR.
O que não vai ao gate segue a recomendação do `/autoplan` e **não é perguntado**.

O Spec Review Loop do CEO reprova de forma recorrente (6/10 em 5 de 5 execuções). Essa
reprovação não é veredito da fábrica: cada achado dele passa por esta mesma triagem por
gravidade, e a reprovação sozinha nunca segura o E5.

**3. Gate único (meta: 5 a 10 min do humano).** É o Phase 4 do `/autoplan`, em português,
abrindo com **"Decisões para você"**: só os itens de destino Gate, numerados (`G1`…, `I1`…),
cada um com gravidade, o que muda na spec, recomendação e alternativa. Em seguida, uma linha com
quantos itens foram para a ADR do E7 e quantos ficaram adiados (o detalhe está no Review record).
As demais seções do template do Phase 4 vêm depois, como texto.
- Pergunte com `AskUserQuestion`, **uma pergunta por item** `G`/`I`, no máximo 4 perguntas por
  chamada; com mais itens, faça quantas chamadas precisar. As opções de cada pergunta são do
  tipo "sim (recomendado)", "não" e "alternativa X". As respostas são independentes e
  combináveis ("G1 sim, G2 não, I1 alternativa").
- Não ofereça ao humano as 6 opções do template (A, B, B2, C, D, E): o `AskUserQuestion`
  mostra no máximo 4, e escolher "Approve with overrides" sem conteúdo custa voltas. O humano
  responde aos itens; **você** mapeia as respostas nas opções do protocolo, depois de ter todas:
  - tudo como recomendado e nada a acrescentar ao plano → **A**;
  - só User Challenges → **B2**;
  - qualquer outra decisão que mude o plano (corte recusado, interpretação aceita, acréscimo
    recusado, critério alterado) → **B**, com todas as decisões, inclusive as dos User
    Challenges, numa lista só de overrides escrita por você a partir das respostas;
  - pergunta do humano (em "Other") → **C** (não conta rodada).
- Se a pergunta do template aparecer mesmo assim, B2 e E vão por "Other".

**4. Aplicar.** Registre a decisão ao lado de cada `G`/`I` na triagem. Interpretação aceita vira
texto normativo agora; recusada sai de `PENDENTE` para `recusada`. Em B ou B2 o `/autoplan`
roda de novo as fases afetadas (escopo → CEO; design → Design; DX → DX; arquitetura ou plano
de teste → Eng; Eng sempre por último). Siga **"Starting an affected-phase rerun"** ao pé da
letra: checkpoint novo, o `autoplan-baseline-edits` anterior movido intacto para histórico
cercado no Review record, obrigações aceitas carregadas sem mudança (salvo o que o gate mudou
no bloco da fase corrente, abaixo). Declare o menor conjunto de fases que esse mapeamento
permite.
- Se uma decisão do humano mudar uma obrigação aceita, siga o caminho oficial do `/autoplan`
  (seção "Accepted obligations" e "Starting an affected-phase rerun"):
  - na rerun da fase, o texto que existe só dentro do bloco `autoplan-accepted:<fase corrente>`
    muda **no próprio bloco** do Review record;
  - o registro `autoplan-baseline-edits:<fase>` leva **só** substituições de texto **fora** de
    bloco aceito (o helper recusa as que tocam um bloco com `Baseline replacements cannot touch
    prior accepted blocks`);
  - blocos aceitos de fases anteriores são imutáveis: a substituição é declarada no bloco da
    fase corrente;
  - o `amend-input` copia o bloco revisado do Review record para o `## Implementation plan`;
    não edite a cópia aplicada à mão.
- Se a mudança atingir bloco aceito de **outra** fase (que não está rodando de novo),
  **pare antes da rerun** e peça orientação ao humano.

**5. Verificação (sem o humano).** A rerun do passo 4 é a verificação. Da saída dela só sobem ao
humano **contradição com uma decisão do gate** e **crítico novo**. O resto passa pela triagem
do passo 2 (rodada 2) e vai para a ADR ou para adiados. O `/autoplan` reapresenta o gate:
- sem crítico novo: a mensagem abre com "Verificação limpa, recomendo A" e o humano só confirma;
- com crítico novo (contradição conta como crítico): é a **única** chamada extra, só com aquele
  ponto. Opções, exatamente três: **A**, aceitando o risco por escrito na triagem; **C**,
  pergunta, que não conta rodada; ou **E**, devolvendo a spec ao E4 com o crítico como entrada.
  **Não existe terceira rodada**: B, B2 e D não são oferecidos aqui.

**Retomada.** Depois de limite de API, sessão interrompida ou compactação de contexto, em
qualquer passo:
- não rode de novo nenhuma fase, nem crie checkpoint novo: a retomada continua a invocação e o
  checkpoint de emenda que já existem;
- confira na conversa quais anúncios `**Phase N complete.**` já foram publicados como mensagem
  visível;
- siga a regra de compactação do `phase-close.md` do `/autoplan` (o parágrafo final, depois do
  passo 7 "Return to the driver"): fase verificada sem anúncio publicado retoma no passo 6
  "Publish the parent report" e republica o anúncio; entrada desatualizada volta ao passo 3
  "Prepare this phase's close packet";
- depois, retome no passo deste checklist que estava em aberto.

**6. Fechamento.** O E5 fecha quando todos passam:
- [ ] nenhum crítico aberto (resolvido, ou risco aceito por escrito pelo humano);
- [ ] ao menos um corte com justificativa escrita;
- [ ] nenhuma interpretação ainda `PENDENTE` (toda `I` foi aceita ou recusada no gate);
- [ ] `### Triagem da fábrica (E5)` completa: o que entrou na spec, o que foi para a ADR do E7,
  o que ficou adiado, e a decisão do humano em cada `G`/`I`;
- [ ] spec revisada commitada, **sem push**, e a issue do Linear atualizada com ela, salvo
  instrução do humano em contrário (registre no Review record);
- [ ] a mensagem final ao humano traz a evidência verificável de cada passo (regra de evidência,
  abaixo).

**Regra de evidência.** A mensagem final do E5 ao humano lista a evidência verificável de cada
passo, nunca só afirmações: o horário ou a posição na conversa de cada anúncio
`**Phase N complete.**` publicado, com o pacote e o input sha a que ele se refere; os sha
devolvidos pelo helper (`amend-input`, `prepare-close`); o hash do commit; a lista das decisões
do gate com o lugar onde cada uma foi aplicada. Passo sem evidência conta como não feito, e
afirmar um passo que não aconteceu é falha grave. Antes de afirmar que um passo foi feito,
confira na própria conversa ou no disco. Motivo: na execução de 2026-09-25, a mensagem final
afirmou "publiquei Phase 1 complete" sem ter publicado.

Decisão do gate sem valor concreto (por exemplo, categoria escolhida sem nomear modelo e
provedor) fica marcada `PENDENTE` na triagem, com dono e prazo, e vira exigência da ADR do E7.
Ela não conta como interpretação pendente (o humano já decidiu; falta o valor) e não bloqueia o
fechamento, a menos que seja crítica.

Commits WIP sem push são permitidos e recomendados durante o E5, antes de qualquer operação
arriscada (rerun, investigação de uma recusa, retomada) ou pausa longa. Não deixe centenas de linhas
sem commit de um dia para o outro.

Depois do A, o `/autoplan` sugere `/ship`. Ignore: o próximo é `/clear` e o E6.

**Divergências declaradas (regra da fábrica sobre o protocolo do `/autoplan`)**
- O gate é em português e só pergunta o que a triagem mandou para ele. As escolhas de gosto
  médias ou baixas saem da lista de perguntas e ficam na triagem.
- O gate não usa a pergunta de 6 opções do template: uma pergunta por item `G`/`I`, e o
  mapeamento para A, B, B2 ou C é do agente, não do humano.
- Limite de uma rerun (o protocolo admite 3 ciclos). No gate reapresentado com crítico, só A,
  C ou E, e E significa devolver a spec ao E4.
- Havendo outras decisões que mudam o plano, as resoluções dos User Challenges entram no B,
  em vez de gastar um ciclo próprio no B2.
- Não há rerun restrita ao que mudou: a verificação é a rerun inteira das fases afetadas. A
  fábrica restringe só o que sobe ao humano.
- Mesmo com verificação limpa, o protocolo exige resposta ao gate reapresentado. O humano
  confirma com A.
- `TODOS.md`, onde o `/autoplan` grava o que adia, não é backlog. A lista de adiados que vale é a
  da triagem, e nada vira ticket sem passar pelo E6.

## Se algo der errado

| Sintoma | O que fazer |
|---|---|
| Escrevi código antes da hora | Apague os arquivos, confira se o `ideia.md` foi contaminado com decisão de implementação, volte à dimensão em aberto |
| `/to-spec` começou a me entrevistar | O `ideia.md` não fechou. `/clear` e volte ao `/ideacao` |
| Contexto estourando no meio do estágio | `/context-save` → `/clear` → `/context-restore`. Se o artefato já existe, só `/clear` |
| Entreguei artefato que não era o pedido | Não corrija por cima. `/clear`, reabra o estágio e refaça a partir do artefato **anterior** |
| O Linear não responde | Pare e avise o humano. Não crie tracker local de substituição. Autenticação: `/mcp` numa sessão interativa |
| Skill não apareceu | Ela pode não estar instalada ou não estar na allowlist de `.claude/settings.json`. Não improvise substituta — avise o humano |
| Hook, helper ou validador do `/autoplan` recusou (E5) | Pare e mostre a mensagem inteira ao humano. Confira os patches do gstack (passo 0 do E5). Não contorne nem edite estado à mão. As recusas conhecidas estão nas linhas abaixo |
| E5: `Snapshot identity/content does not match this phase and active plan` | Checkpoint errado. Use o `…/<fase>-implementation.md` do `create` de checkpoint de emenda, não o do `create` das vozes nem o `snapshot.json` (passo 1 do E5) |
| E5: `Missing accepted-obligations record for <fase>` | O registro `autoplan-accepted:*` do Review record foi removido. Não recrie à mão: pare e mostre ao humano |
| E5: `Baseline replacements cannot touch prior accepted blocks` | Uma substituição de texto que está dentro de um bloco `autoplan-accepted:*` foi posta no registro `autoplan-baseline-edits`. Tire-a do registro e faça a mudança no bloco da fase corrente no Review record (passo 4 do E5); se o texto for de bloco de outra fase, pare e peça orientação ao humano |
| E5: `Baseline-edit source SHA does not match immutable input` | Registro `autoplan-baseline-edits` de rodada anterior sem cerca no Review record. Siga "Starting an affected-phase rerun" do `/autoplan` |
| E5: `Methodology source or artifact changed` | Prepare um bundle novo de methodology e leia-o antes de seguir |
| E5: `Native parent evidence has not reached the journal yet` ou `invocation evidence is unavailable` | Confira os patches do gstack (passo 0 do E5) e se o `init` do snapshot rodou literalmente como o `/autoplan` o gerou |
| E5 interrompido (limite de API, sessão caiu, compactação) | Não rode fase de novo. Siga "Retomada" no checklist do E5 |
| Um bloco `autoplan-*` parece duplicado | Não é. Registro e cópia aplicada são idênticos de propósito. Não mexa |

## Agent skills

### Issue tracker

Tickets vivem no Linear (time **Carreira**), via MCP `plugin:linear:linear`. Ver `docs/agents/issue-tracker.md`.

### Domain docs

Layout single-context: `CONTEXT.md` + `docs/adr/` na raiz. Ver `docs/agents/domain.md`.

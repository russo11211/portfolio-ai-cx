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
| 4 | Spec | `/to-spec` | `ideia.md` + `CONTEXT.md` | spec no tracker (cópia em `docs/spec/<slug>.md`) | um estranho lê e sabe: problema, fora de escopo, como verificar. Zero critério não verificável |
| 5 | Revisão de plano | `/autoplan` | spec | spec revisada, cortes justificados | alguma coisa foi **cortada** com justificativa escrita |
| 6 | Tickets | `/to-tickets` | spec revisada | `.scratch/<feature>/issues/NN-slug.md` | cada ticket cabe em 1 PR **e** entrega algo observável (tracer bullet, não camada) |
| 7 | Arquitetura | `/codebase-design` | tickets + repo | ADR em `docs/adr/` | as **seams** estão nomeadas; para cada ticket você sabe qual seam ele toca |
| 8 | Implementação | `/implement` (dirige `/tdd`) | **um** ticket | commit verificado por testes | teste que falhava antes passa; suíte verde; diff só nos arquivos previstos na ADR |
| 9 | QA | `/qa` | app rodando | bugs corrigidos + `docs/qa/<data>-<slug>.md` | o relatório **nomeia os fluxos percorridos**, e são os do primeiro corte |
| 10 | Code review | `/review` (+ `/cso` se toca auth/input/segredo/endpoint) | diff / PR | veredito + correções | zero achado em aberto; zero achado alto de segurança; **humano leu** |
| 11 | Ship | `/ship` | código revisado | PR + `CHANGELOG.md` + `VERSION` | PR aberto, CI verde, CHANGELOG em linguagem de usuário |
| 12 | Deploy & fechamento | `/setup-deploy` (1ª vez) → `/land-and-deploy` → `/canary` → `/document-release` → `/learn` → `/retro` | PR aprovado | release + `docs/retro/` + lições | janela de canário limpa **verificada por alguém**; um estranho usa o release lendo só o README |

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
  tracker que `/to-spec` e `/to-tickets` usam.
- `/to-spec` — E4. **Sintetiza**, não entrevista. Se ele quiser te entrevistar, volte ao E1.
- `/autoplan` — E5. As 4 lentes (CEO, design, eng, DX) em sequência.
- `/to-tickets` — E6. Fatias verticais tracer-bullet com arestas de bloqueio.
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
.scratch/<feature>/issues/NN-slug.md  E6 — tickets (efêmero, versionado mesmo assim)
.claude/                            configuração do harness deste projeto
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
  seguir ou arquivar a ideia (E2), aceitar ou recusar cada corte do `/autoplan` (E5),
  aceitar o risco do diff (E10), disparar o deploy (E12). Recomende; quem assina é o
  humano.
- **Decisão arquitetural vira ADR.** Se a conversa decidiu uma fronteira de módulo, uma
  seam, um formato de dado persistido ou uma dependência estrutural, escreva
  `docs/adr/NNNN-titulo.md` com: decisão, alternativas descartadas, motivo. Antes de
  escrever o código que a implementa.
- **Navegação web é sempre `/browse`.** Nunca use ferramentas `mcp__claude-in-chrome__*`
  (elas estão bloqueadas em `.claude/settings.json`).
- **`/clear` entre estágios e entre tickets.** Lembre o humano quando ele esquecer.
- **Um estágio, uma sessão.** Não encadeie dois estágios na mesma janela.

## Se algo der errado

| Sintoma | O que fazer |
|---|---|
| Escrevi código antes da hora | Apague os arquivos, confira se o `ideia.md` foi contaminado com decisão de implementação, volte à dimensão em aberto |
| `/to-spec` começou a me entrevistar | O `ideia.md` não fechou. `/clear` e volte ao `/ideacao` |
| Contexto estourando no meio do estágio | `/context-save` → `/clear` → `/context-restore`. Se o artefato já existe, só `/clear` |
| Entreguei artefato que não era o pedido | Não corrija por cima. `/clear`, reabra o estágio e refaça a partir do artefato **anterior** |
| Skill não apareceu | Ela pode não estar instalada ou não estar na allowlist de `.claude/settings.json`. Não improvise substituta — avise o humano |

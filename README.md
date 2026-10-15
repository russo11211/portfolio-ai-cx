# portfolio-ai-cx

Monorepo de portfólio: projetos pequenos de IA aplicada a Customer Experience (CX), cada
um numa subpasta, construídos com uma esteira de estágios documentada (ideia → design →
spec → tickets → ADR → implementação com TDD). O plano geral está em
[`plano_portfolio_ai_solutions_consultant.md`](./plano_portfolio_ai_solutions_consultant.md).

## Projetos

| Projeto | Resumo |
|---|---|
| [`cx-prompt-lab/`](./cx-prompt-lab/) | Prompts versionados que classificam a intenção de chamadas de contact center, medidos por um eval determinístico com Replay offline das Chamadas gravadas. Rodadas reais em `claude-sonnet-4-5`: Violação de formato de 62,5% (v0) para 33,3% (v1), 72 Chamadas por versão; resultado exploratório, inconclusivo por efeito piso. |

Os artefatos de cada estágio (ideia, design, spec, ADRs) ficam em [`docs/`](./docs/); o
glossário do domínio, em [`CONTEXT.md`](./CONTEXT.md).

## Como este repositório é trabalhado

> Projeto **adotado** pela fábrica agêntica. O fluxo, as skills permitidas e a
> convenção de artefatos estão em [`CLAUDE.md`](./CLAUDE.md) — leia antes de abrir
> uma sessão.

### Por onde entrar

- **Trabalho novo sobre este código** → Esteira 1, estágio 1: `/ideacao`.
- **Mapear o que já existe contra os artefatos do ciclo** → `/edlc-adequacao`
  (Esteira 3, passo 12 — mapeia e documenta, não reestrutura).
- **Mover fronteira de módulo / modernizar** → Esteira 3, começando por
  `understand-anything:understand`. Ver `ESTEIRAS.md` no skills-hub.

```bash
cd portfolio-ai-cx
claude
```

### Mapa dos artefatos

| Caminho | Estágio | O que é |
|---|---|---|
| `docs/ideias/<slug>/ideia.md` | 1 | A ideia amadurecida, com gate de saída |
| `docs/design/` | 2 | Design doc do `/office-hours` |
| `CONTEXT.md` | 3 | Glossário — a linguagem ubíqua do domínio |
| `docs/spec/` | 4 | Spec executável |
| `docs/adr/` | 3 e 7 | Decisões arquiteturais congeladas |
| `.scratch/<feature>/issues/` | 6 | Tickets tracer-bullet |
| `docs/qa/` | 9 | Relatórios de QA |
| `CHANGELOG.md`, `VERSION` | 11 | Produzidos pelo `/ship` |
| `docs/retro/` | 12 | Retrospectivas |

### Harness

`.claude/settings.json` restringe as skills e os MCP visíveis neste projeto.
O porquê de cada bloco está em `.claude/settings.json.comentado.md`.

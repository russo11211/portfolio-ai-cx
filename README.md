# portfolio-ai-cx

> Projeto **adotado** pela fábrica agêntica. O fluxo, as skills permitidas e a
> convenção de artefatos estão em [`CLAUDE.md`](./CLAUDE.md) — leia antes de abrir
> uma sessão.

## Estado

Repositório que já existia antes da fábrica. O harness e a árvore de artefatos foram
instalados; o que já havia em disco **não** foi alterado.

## O que é isto

<!-- Uma frase do problema e uma do critério de sucesso, com número. -->

## Por onde entrar

- **Trabalho novo sobre este código** → Esteira 1, estágio 1: `/ideacao`.
- **Mapear o que já existe contra os artefatos do ciclo** → `/edlc-adequacao`
  (Esteira 3, passo 12 — mapeia e documenta, não reestrutura).
- **Mover fronteira de módulo / modernizar** → Esteira 3, começando por
  `understand-anything:understand`. Ver `ESTEIRAS.md` no skills-hub.

```bash
cd /home/caueantonacci/GIT/portfolio-ai-cx
claude
```

## Mapa dos artefatos

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

## Harness

`.claude/settings.json` restringe as skills e os MCP visíveis neste projeto.
O porquê de cada bloco está em `.claude/settings.json.comentado.md`.

# /ideacao

Skill de **estágio 1** da fábrica agêntica: o loop conversacional que amadurece uma ideia crua
até ela estar completa e pronta para virar spec.

Não é pesquisa de mercado. É conversa — uma pergunta de cada vez, ao longo de várias sessões,
com o estado persistido em `ideia.md`. Pesquisa de mercado, sondagem de viabilidade no repo e
geração de alternativas são **módulos opcionais** dentro do loop, acionados pelo usuário.

## O que ela entrega

`docs/ideias/<slug>/ideia.md` (ou `~/.claude/ideias/<slug>/ideia.md` fora de repositório) com
oito dimensões fechadas — o quê, para quem, por quê, como, não-escopo, riscos e premissas,
critério de sucesso, primeiro corte — mais um registro append-only de decisões.

A ideia só é declarada pronta quando passa no **gate de saída** (checklist verificável rodado
contra o arquivo, não contra a memória da conversa).

## Instalação

Não está instalada. Escolha uma das duas:

```bash
# cópia (congela a versão atual)
cp -r ~/GIT/Stack_Engenharia_Agnostica/skills-hub/skills/ideacao ~/.claude/skills/ideacao

# symlink (acompanha as edições feitas aqui — recomendado)
ln -s ~/GIT/Stack_Engenharia_Agnostica/skills-hub/skills/ideacao ~/.claude/skills/ideacao
```

Depois, `/ideacao` fica disponível — e o `description` do frontmatter aciona a skill
automaticamente em frases como "tenho uma ideia", "vamos discutir uma ideia",
"me ajuda a amadurecer isso", "retoma aquela ideia".

## Handoff

Com o gate passando, o `ideia.md` alimenta o estágio seguinte sem nova entrevista:
`/to-spec` (mattpocock), `/spec` (gstack) ou `/tlc-plan` (tech-leads-club).
O mapeamento seção-a-seção está na fase F4 do `SKILL.md`.

## Fronteira com as vizinhas

- `/office-hours`, `/grill-me` — **pressionam** uma ideia que já existe. Rodam depois, não antes.
- `/tlc-discover` — decide **se vale construir** e desce para shape técnico em uma sessão só.
- `/ideacao` — decide **o que é a coisa**, em várias sessões, e para antes do shape.

# Issue tracker: Linear

Issues e specs deste repositório vivem no Linear, acessado pelo MCP `plugin:linear:linear`. Todas as ferramentas aparecem como `mcp__plugin_linear_linear__*`.

## Time

- Time padrão: **Carreira** (id `30dd8d87-75c9-4f18-996b-e377e4d74e4e`).
- Confirme o time com o humano antes de criar issues se o trabalho não pertencer claramente a Carreira; `list_teams` mostra os times disponíveis.

## Convenções

- **Criar uma issue**: `save_issue` com `title` = título do ticket e `description` = corpo completo — contexto, critérios de aceite e dependências. Atribuir ao time confirmado.
- **Ler uma issue**: `get_issue`.
- **Listar issues**: `list_issues`, filtrando por time/status conforme necessário.
- **Comentar em uma issue**: `save_comment`.
- **Labels**: `list_issue_labels` / `save_issue_label` se um ticket precisar de label.

## Spec como fonte da verdade

A spec é publicada no Linear (como documento via `save_document`, ou como descrição da issue-pai — confirmar com o humano qual). As issues dos tickets são ligadas à spec. A cópia em `docs/spec/<slug>.md` é **só leitura**: existe para rastreabilidade local, mas o Linear é a fonte da verdade.

## Rastreabilidade

Registre sempre o identificador da issue no Linear (ex.: `CAR-123`) no artefato local correspondente (referência do ticket, mensagem de commit, descrição do PR) para fechar a cadeia ideia → spec → ticket → PR → release.

## Quando uma skill disser "publique no issue tracker"

Crie uma issue no Linear via `save_issue` no time confirmado.

## Quando uma skill disser "busque o ticket correspondente"

Rode `get_issue` com o identificador do Linear.

## Quando o Linear não responder

**Pare e avise o humano.** Não crie arquivos de ticket locais em `.scratch/` como substituto — isso bifurcaria a fonte da verdade.

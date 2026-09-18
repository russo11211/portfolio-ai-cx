# `.claude/settings.json` — por que cada bloco existe

JSON não aceita comentário. Este arquivo é o comentário. Toda afirmação aqui é
rastreável a `../../MECANISMOS.md`, onde está marcada `[TESTE]`, `[SCHEMA]` ou `[DOC]`.

Precedência que faz isso funcionar: `.claude/settings.json` do projeto **vence** o
`~/.claude/settings.json` global (MECANISMOS §1.1). É só por isso que o projeto
consegue enxergar menos que a máquina.

---

## `"disableBundledSkills": true`

Remove as skills embutidas no binário do Claude Code (`code-review`, `simplify`,
`update-config`, `artifact-design`, `security-review`…). `[TESTE]` — MECANISMOS §2.

**Efeito colateral aceito de propósito:** a esteira original cita `security-review` e
`code-review` (built-ins) nos estágios 8 e 10. Com este bloco ligado, eles somem. A
fábrica os substitui por `/cso` (varredura de segurança, gstack) e `/review` (gate
pré-landing do PR inteiro, gstack) — ambos na allowlist.

**Se você quiser os dois built-ins de volta:** troque para `false`. O custo é o resto
das bundled voltando junto, porque não há como escolher uma só.

---

## `"disableClaudeAiConnectors": true`

Derruba os 4 conectores auto-fetch do claude.ai — Gmail, Google Drive, Google Calendar
e Claude Docs. `[TESTE]` — os quatro sumiram de `claude mcp list`.

Uma fábrica de software não lê e-mail nem agenda. Cada conector é superfície de ação
que o agente pode usar por engano, e contexto pago todo turno.

---

## `"enabledPlugins": { ... : false }`

Desliga plugin no projeto — **e leva junto o servidor MCP que o plugin traz**.
`[TESTE]` — `plugin:linear:linear` e `plugin:figma:figma` sumiram do `mcp list`.

| Plugin desligado | Por quê |
|---|---|
| `linear@claude-plugins-official` | Tracker externo; a fábrica usa o tracker configurado por `/setup-matt-pocock-skills`. Traz ~70 ferramentas MCP de contexto |
| `figma@synced` | Design em Figma não é estágio desta esteira. Além disso está `! Needs auth` |
| `codex@openai-codex` | `codex:rescue` é da Esteira 2 (Pit Stop), não da esteira completa. ~449 tok always-on |
| `core-3d-animation@claude-design-skillstack` | 3D/animação não é estágio nenhum. ~762 tok always-on |
| `i-have-adhd@i-have-adhd` | Formatação de resposta; conflita com o contrato de artefatos deste CLAUDE.md. ~424 tok |
| `understand-anything@understand-anything` | Arqueologia de legado — é a **Esteira 3**, não a 1. O mais caro da lista: ~1.146 tok always-on |

**Não existe chave `disabledPlugins`** (MECANISMOS §6.6). É `enabledPlugins` com `false`
e o **id completo com marketplace** — pegue o id exato com `claude plugin list --json`.

**Plugin ausente desta lista fica LIGADO.** É proposital: quando você instalar a suíte
mattpocock (`claude plugins install mattpocock-skills`), ela precisa ficar ligada —
metade da esteira vive nela. Não acrescente o id dela aqui.

---

## `"claudeMdExcludes": ["/home/caueantonacci/.claude/CLAUDE.md"]`

Impede o CLAUDE.md global do usuário de entrar no contexto deste projeto. `[TESTE]` —
`gstack=NAO;projeto=SIM`.

**Consequência que exige atenção:** as diretrizes globais do usuário deixam de valer
aqui. As que continuam valendo foram **re-declaradas** no `CLAUDE.md` do template — a
regra de navegar sempre por `/browse` e nunca pelas ferramentas `mcp__claude-in-chrome__*`
é a principal. Se você editar o CLAUDE.md global, releia o do template.

Caminho absoluto, e é da máquina do `caueantonacci`. Em outra máquina, ajuste.
CLAUDE.md gerenciado por organização **não** pode ser excluído (MECANISMOS §6.7).

---

## `"permissions": { "deny": [...] }`

`mem0-server`, `reicon` e `mcp-server-linkedin` vivem em `~/.claude.json` →
**user scope**. MECANISMOS §6.2 provou que `disabledMcpjsonServers` **não tem efeito
nenhum** sobre eles: aquela chave só alcança servidor vindo de `.mcp.json`.

O que sobra é `deny`, com uma limitação que precisa estar clara:

> **`deny` bloqueia a EXECUÇÃO, não a VISIBILIDADE.** `[TESTE]` — MECANISMOS §5.
> As ferramentas continuam no prompt e continuam custando contexto. O que você ganha é
> a garantia de que o agente não as chama.

`mcp__claude-in-chrome` está na lista por outro motivo: é a **trava** da regra de
navegação re-declarada no CLAUDE.md. A regra diz "use `/browse`"; este `deny` faz com
que desobedecer não funcione.

**Se esses servidores não servem a nenhum projeto seu**, a saída limpa é
`claude mcp remove <nome>` e readicionar com `-s project` onde fizerem falta — mas isso
é decisão **global** do usuário, fora do escopo deste template.

---

## `"skillOverrides": { ... }`

O bloco grande. **Gerado**, nunca escrito à mão:

```bash
skills-hub/bootstrap/gerar-skilloverrides.py \
  --settings .claude/settings.json --in-place
```

`"off"` esconde a skill da listagem — economiza contexto e, mais importante, **limpa o
roteamento**: 25 skills em vez de ~200 significa que o modelo escolhe a certa em vez de
escolher entre descrições truncadas pelo `skillListingBudgetFraction` (MECANISMOS §3).

### A fragilidade que você precisa aceitar

**Não existe curinga.** `{"*": "off"}` é ignorado `[TESTE]` — MECANISMOS §6.1. Não
existe `disableAllSkills` nem `enabledSkills` no schema `[SCHEMA]`. O resultado é uma
allowlist implementada como denylist:

> **Skill nova instalada em `~/.claude/skills/` aparece automaticamente neste projeto**,
> porque não está na lista de `off`.

**Mitigação:** rode `gerar-skilloverrides.py --in-place` toda vez que instalar skill
nova. A allowlist mora dentro do script, na constante `ALLOWLIST`.

### Sobre as chaves `plugin:skill`

O gerador emite também as skills de plugin com o nome qualificado (`codex:rescue`,
`understand-anything:understand`…). **Esse formato de chave não foi verificado por
teste** — MECANISMOS só testou nome curto de skill pessoal. Ele é cinto extra; o
suspensório verificado para plugin é `enabledPlugins: false`, logo acima.

### A allowlist ideal existiria, mas não aqui

`allowedMcpServers`, `strictPluginOnlyCustomization` e companhia são allowlists de
verdade — e só funcionam em **managed settings** (`/etc/claude-code/managed-settings.json`),
fora do alcance de configuração por projeto. MECANISMOS §6.9. É a evolução natural
desta pasta quando o denylist começar a incomodar.

---

## O que NÃO está aqui, e por quê

| Chave | Por que ficou de fora |
|---|---|
| `disabledMcpjsonServers` | Só alcança servidor de `.mcp.json`; este template não tem `.mcp.json`. Sem efeito sobre os user scope `[TESTE]` |
| `enableAllProjectMcpServers` | Não auto-aprovou nos testes, nem em settings.json nem em settings.local.json `[TESTE]` — MECANISMOS §6.3 |
| `syncClaudeAiSkills` / `syncClaudeAiPlugins` | **Não são lidos do settings de projeto** `[SCHEMA]`. Vão no `settings.local.json` — ver `settings.local.json.exemplo` |
| `skillListingMaxDescChars` / `skillListingBudgetFraction` | Com 25 skills a listagem não estoura o orçamento; mexer nos tetos aqui só esconderia um problema que não existe |

---

## Verificação depois de configurar

```bash
cd /caminho/do/projeto

claude mcp list          # só o esperado deve sobrar

claude -p --model haiku 'Responda APENAS uma linha: TOTAL=<numero de skills na sua lista>;\
  gstack=<SIM|NAO se voce ve skills da suite gstack alem das permitidas>' < /dev/null

claude -p --model haiku --output-format json "oi" < /dev/null | \
  python3 -c "import json,sys; u=json.load(sys.stdin)['usage']; \
  print('PROMPT =', u.get('input_tokens',0)+u.get('cache_creation_input_tokens',0)+u.get('cache_read_input_tokens',0))"
```

Referência medida em MECANISMOS §3.2: sessão normal ~16.2k tokens de prompt; com esta
configuração inteira, ~13.0k. **A economia é modesta (~20%); o ganho é roteamento e
superfície de ação.** Restringir se justifica pelo controle, não pela economia.

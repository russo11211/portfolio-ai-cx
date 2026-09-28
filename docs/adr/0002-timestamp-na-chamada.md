# 0002. Timestamp gravado em cada Chamada

Status: aceita (E8/T9, 2026-09-28)

## Contexto

A spec (`docs/spec/cx-prompt-lab.md`) e o ticket T9 (CAR-17) exigem que o Relatório
imprima "o modelo exatamente como devolvido pela resposta e a data das Chamadas". A
ADR 0001 (E7) fixou o esquema da Chamada e do Manifesto (exigência 4) sem incluir nenhum
campo de data — só `versao_prompt`, `hash_prompt`, `transcricao_id`, `repeticao`,
`modelo`, `motivo_parada`, `temperatura`, `max_tokens` e `resposta`. Isso deixa a
exigência de "data das Chamadas" sem fonte: a alternativa que não muda o esquema (usar o
mtime do arquivo no filesystem) não sobrevive a `git clone`/`git checkout` — o mtime vira
a hora do checkout, não a hora da gravação, o que é pior que não mostrar data nenhuma
para um relatório que se declara auditável.

## Decisão

Cada `Chamada` grava `criado_em`: string ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`), obtida no
momento da chamada ao provider por `ProviderGravador.chamar` (não no momento da escrita em
disco — a gravação em si é em lote, no fim da Rodada). O relógio é injetável
(`ProviderGravador(..., relogio=Callable[[], str])`, default `datetime.now(UTC)`), pelo
mesmo motivo que o Provider é injetado: testabilidade sem I/O real.

Isso muda a forma da Chamada gravada (exigência 4 da ADR 0001), então `VERSAO_ESQUEMA`
sobe de 1 para 2 — é exatamente o que esse campo do manifesto existe para sinalizar
(ADR 0001, "Compatibilidade de esquema"). Não há Rodada committada no repositório ainda
(o diretório `rodadas/` só nasce a partir do T11), então não existe dado de produção em
esquema 1 para migrar.

## Alternativas descartadas

- **mtime do arquivo da Chamada ou do manifesto:** descartada — não sobrevive a
  `git clone`/`checkout`, que reescreve o mtime para a hora do checkout. Um Relatório que
  se declara auditável não pode usar um valor que o próprio ato de reproduzi-lo apaga.
- **Um único timestamp no Manifesto (data da Rodada), não por Chamada:** descartada — a
  spec pede "a data das Chamadas" (plural, por Chamada); uma Rodada pode se estender por
  minutos, e T14 (margem de variação da Reexecução) pode precisar da granularidade por
  Chamada no futuro. O Relatório (T9) exibe hoje só o intervalo (mínimo–máximo) por
  Rodada, mas o dado subjacente já está no grão certo.

## Consequências

- `Chamada.de_dict` passa a exigir a chave `criado_em`; qualquer Chamada gravada por uma
  ferramenta em esquema 1 (nunca existiu commitada) seria rejeitada por `KeyError`, o que
  é o comportamento correto para uma mudança de esquema sem dado legado a preservar.
- Os testes que constroem `Chamada(...)` diretamente (fora de `ProviderGravador`) agora
  passam `criado_em` explicitamente.
- Se um ticket futuro precisar do timestamp por Repetição/Transcrição em vez de por
  Rodada no Relatório, o dado já existe; é só o Relatório (T9/T12) que precisa mudar, não
  o esquema de novo.

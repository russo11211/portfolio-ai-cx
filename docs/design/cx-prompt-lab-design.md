# Design: CX Prompt Lab

Gerado por /office-hours em 2026-09-23
Branch: claude/mattpocock-skills-setup-96cf28
Status: APPROVED (humano aprovou em 2026-09-23; seguir com a ideia, abordagem C)
Mode: Builder (objetivo declarado: hackathon/demo, artefato time-boxed de 1 semana)
Entrada: `docs/ideias/cx-prompt-lab/ideia.md` (status: pronta-para-spec)

## Problem Statement

O candidato precisa de evidência auditável de que sabe iterar prompts com medição, para
conversas técnicas na Porto, NCS/GFT e Bain/Caju. O substituto atual (take-home) prova
execução num problema que a empresa define, mas não prova escopo próprio nem iteração
medida ao longo do tempo.

## Por que agora (uma frase)

As vagas nas empresas-alvo estão abertas agora, e o take-home não prova que o candidato
mede a própria iteração.

## Constraints

- Prazo: 1 semana de trabalho a partir do E8.
- **Sem custo de API:** o candidato não pode pagar a API oficial da Anthropic.
- Toda chamada real a LLM e todos os testes rodam pelo **CLIProxyAPI** (gateway local).
- Nenhuma escolha de biblioteca, schema ou código antes do E8 (regra do projeto).

## Premissas (aceitas pelo humano em 2026-09-23)

1. O que pesa para o recrutador é a tabela v0→vN e o case study, não a arquitetura.
2. "Alucinação" precisa ser checável por script. A parte "justificativa cita algo ausente
   da transcrição" só é checável se a justificativa for **citação literal**, verificada
   por substring na transcrição.
3. Um terceiro não tem o gateway. Reproduzir exige **resultados commitados** no repo.
4. O sinal v0→v1 pode ser trivial com lista fechada de rótulos. O dataset precisa ter
   casos ambíguos e de intenção dupla, senão v0 não falha por motivo real.
5. A camada de provider maior que o experimento é escopo a cortar.

## Divergências em relação ao `ideia.md` (a refletir no E4, `ideia.md` não foi editado)

| Item no `ideia.md` | Passa a valer | Motivo |
|---|---|---|
| Dim. 8: "pelo menos uma chamada de validação real contra a API oficial" | **Não haverá chamada real à Anthropic.** O teste real fica *skipped* sem chave | Humano não pode pagar |
| Dim. 4: relatório distingue "validado contra gateway" de "validado contra Anthropic real" | Relatório só afirma **"compatível com Anthropic"**. Nunca "validado contra a Anthropic" | Consequência da linha acima; as notas de arquitetura (item 18) já exigem isso |
| Dim. 7: reprodutibilidade = "quem clonar roda e chega aos mesmos números" | Reprodutibilidade = **modo replay offline** sobre resultados commitados | Terceiro não tem gateway nem chave |
| Dim. 8: alvo v0→v3 | Alvo **v0→v2**, mínimo v1 | Corte de escopo (ver abaixo) |

## Cortes de escopo (o escopo saiu menor)

Cortado do que as notas de arquitetura pediam, ou do `ideia.md`:
- Streaming, `getModelCapabilities`, health check e endpoint `/health/llm`.
- Aliases de modelo (`fast`, `balanced`, `reasoning`).
- Docker compose com o gateway como serviço.
- Fallback entre providers (já estava fora, item 4 do não-escopo).
- v3 como alvo. Vira iteração seguinte.
- Chamada real à API oficial (ver divergências).

Mantido: dataset de 20-30 transcrições rotuladas, eval com métricas por versão, gateway
para dev, uma implementação de provider Anthropic (não exercitada), case study.

## Approaches Considered

- **A: script mínimo com URL base configurável.** Descartada: a integração Anthropic vira
  só configuração, evidência fraca, e não há seam para teste unitário.
- **B: interface de provider + 2 implementações + testes A/B/C.** Descartada como
  isolada: a reprodutibilidade depende de o terceiro ter gateway ou chave.
- **C: B enxuta + record/replay.** **Escolhida.**

## Recommended Approach: C

Interface de provider com **um único método** (gerar), duas implementações (gateway e
Anthropic), formato de request/response interno no vocabulário Anthropic. Cada rodada do
eval grava prompt, transcrição, modelo e resposta em arquivo commitado. Um modo **replay**
recalcula as métricas só a partir desses arquivos, sem chave e sem gateway.

Por quê: o objetivo é evidência auditável para um recrutador, e o replay é o único jeito
de um terceiro conferir os números sem pagar nada.

Limite honesto do replay: prova que o **cálculo da métrica** é reproduzível, não que o
modelo responderia igual hoje. O case study deve dizer isso.

## Open Questions

1. **Termos do CLIProxyAPI.** Ele costuma reaproveitar login de assinatura. Confirmar que o
   modo de autenticação usado é o suportado pelo provedor antes de depender dele. As notas
   de arquitetura proíbem contornar termos. Não respondido na sessão.
2. **Premissa 1 do `ideia.md` não testada:** o gateway serve um modelo compatível. Deve ser
   o primeiro spike do E8, antes de qualquer prompt.
3. **Tamanho do dataset vs. variância** (premissa 2 do `ideia.md`): decidir no E4 se cada
   exemplo roda N repetições.

## Success Criteria

Herdados do `ideia.md` com os ajustes das divergências:
- Queda mensurável e documentada na taxa de alucinação entre v0 e a versão final, no mesmo
  dataset fixo, em 1 semana. Mínimo aceito: v0→v1.
- Um terceiro roda o replay e chega aos mesmos números, sem chave e sem gateway.
- O relatório nunca afirma validação contra a API oficial da Anthropic.

## Distribution Plan

Repositório público (subpasta `cx-prompt-lab/`). Sem CI (fora de escopo, CAR-6). O README
da subpasta traz a matriz do que cada teste comprova e o comando de replay.

## Next Steps

1. E3 `/grill-with-docs`: fixar o vocabulário (intenção, rótulo, alucinação, erro de acerto,
   versão de prompt, rodada, replay). Cada termo com definição que exclui algo.
2. E4 `/to-spec`: incorporar as divergências acima na spec.
3. E7 `/codebase-design`: ADR da seam de provider (uma seam, um método).

## What I noticed about how you think

- Você reconheceu o limite antes de eu pedir: "não posso pagar pelas apis". Isso é
  restrição real, e o design agora a trata como restrição, não como detalhe.
- Você manteve a exigência de "integração com API antropic" mesmo sem poder testá-la. O
  design honra isso com código presente e afirmação limitada a "compatível".
- Você aceitou cortes sem pedir para preservar item nenhum, o que combina com o critério
  "1 semana" que você mesmo escreveu.

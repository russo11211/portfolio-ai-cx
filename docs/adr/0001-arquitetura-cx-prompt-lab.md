# 0001. Arquitetura do cx-prompt-lab: módulos, seams e exigências do E5

Status: aceita (E7, 2026-09-28)

## Contexto

O E5 fechou a spec (`docs/spec/cx-prompt-lab.md`) e o E6 publicou 14 tickets no Linear
(T1–T14, sub-issues de CAR-8). A seção "Exigências para a ADR do E7" e a "Situação dos
achados" do Review record adiaram para esta ADR tudo que é decisão de implementação ou
de DX que o E8 teria de tomar sozinho: runtime, superfície de CLI, formato de
armazenamento, forma dos erros, contrato do Provider, versão do avaliador no manifesto e
a separação do módulo Conclusão. Esta ADR fixa essas decisões antes da primeira linha de
código (E8).

O repositório está vazio de código (greenfield): não há stack prévia a respeitar.

**Decisão do gate deste E7 (Plano B, exigência 7):** o humano nomeou modelo e provedor —
**Groq, modelo Llama 3.3 70B**, camada gratuita. Usado só se o spike (T1) achar o Gateway
(CLIProxyAPI local) incompatível ou instável.

## Decisão: runtime e dependências (exigência 1)

**Python 3.11+, biblioteca padrão apenas — zero dependências de terceiros.**

Motivo: a história DX crítica ("Getting started < 5 min") reprova qualquer atrito de
instalação. Zero dependências elimina lockfile, gerenciador de pacotes e versão de
dependência como fonte de "erro de leitura" logo na primeira tentativa. `hashlib`,
`json`, `argparse`, `dataclasses`, `urllib.request` e `pathlib` cobrem tudo que os
módulos abaixo precisam (hash do manifesto, parsing do contrato de saída, CLI, chamada
HTTP aos providers).

**Alternativa descartada — TypeScript/Node:** exige `npm install` e lockfile mesmo com
poucas dependências; nenhuma vantagem sobre Python para este domínio (parsing de texto,
hashing, HTTP simples) que compense o passo extra no quickstart.

## Módulos e seams

Um seam por módulo, nomeado; ver "Contrato de testabilidade" abaixo para o motivo de
cada um ser deep. Onde há mais de um adapter, o seam é real (Two adapters means a real
one); onde há só um, é seam interno de teste, não de variação.

| Módulo | Interface (resumo) | Seam / adapters | Tickets |
|---|---|---|---|
| **Dataset** | `carregar(caminho) -> Dataset`; valida rótulo fechado, ≥1 Transcrição por Rótulo | arquivo JSON em disco (`dataset/transcricoes.json`) | T7, T8 |
| **Provider** | `chamar(prompt, transcricao) -> RespostaProvider{texto, motivo_parada, modelo, temperatura}` | 3 adapters: `GatewayProvider` (CLIProxyAPI local), `AnthropicProvider` (real, opt-in), `GroqProvider` (Plano B, Llama 3.3 70B) | T1, T5, T6, T11 |
| **Avaliador** | `avaliar(resposta_bruta) -> Resultado{rótulo, veredito_de_forma, justificativa_ancorada?}` — classifica em acerto, Erro de acerto, Alucinação (2 subtipos), Violação de formato | um adapter só (parser do contrato de saída); seam interno para os casos de borda de parsing | T2 |
| **Executor de Rodada** | `rodar(versao_prompt, dataset, provider, repeticoes>=3) -> Rodada` — orquestra Provider + Avaliador, aplica piso de Repetições, aborta com timeout/progresso | compõe os seams Provider e Avaliador; não é seam próprio | T2, T4, T11 |
| **Gravação** | `gravar(rodada) -> Manifesto` — um arquivo por Chamada, escrita atômica (reserva diretório → escreve → valida → publica) | filesystem (`rodadas/<id>/`) | T3 |
| **Replay** | `substituir(caminho_rodada) -> Relatorio` — recalcula sem rede; recusa alto em hash ausente/incompatível | adapter `ReplayProvider`: lê Chamadas gravadas em vez da rede, mesma interface do seam Provider | T3, T9 |
| **Conclusão** | `concluir(contagens_v0, contagens_final) -> Veredito` — função pura sobre contagens, sem I/O | nenhum (módulo puro; seam só para teste, sem adapter alternativo) | T10 |
| **Relatório** | `renderizar(rodadas, veredito) -> texto` — tabela por versão, todas as Rodadas, margem de Reexecução | nenhum adapter alternativo | T9, T12, T14 |
| **CLI** | subcomandos `reexecutar`, `replay`, `rodada --descartar` | fino: só chama os módulos acima | todos, em especial T1, T3, T9 |

T12 e T13 não introduzem módulo novo: reusam Relatório e Executor de Rodada,
respectivamente.

### Contrato de testabilidade (T6)

O teste de contrato de T6 roda `GatewayProvider` e `AnthropicProvider` contra o mesmo
transporte HTTP falso e exige `RespostaProvider` idêntica normalizada. Isso é o que torna
o seam Provider real (não hipotético): dois adapters de produção mais o `GroqProvider` de
plano B, mais o `ReplayProvider` de teste/offline — quatro adapters no mesmo seam.

## Layout do produto

```
cx-prompt-lab/
  README.md                     abre com o comando de Replay + saída de exemplo (exigência 1, item 6)
  cx_prompt_lab/
    cli.py                      seam CLI
    dataset.py
    provider.py                 seam Provider + GatewayProvider/AnthropicProvider/GroqProvider/ReplayProvider
    avaliador.py
    executor.py
    gravacao.py
    replay.py
    conclusao.py                módulo puro (EE12)
    relatorio.py
  testes/
    contrato_provider_test.py   T6: mesmo transporte falso, dois providers reais
    ...
  prompts/v0.md, v1.md, ...
  dataset/transcricoes.json
  rodadas/<id>/manifest.json, <hash-da-chamada>.json
  rodadas/descartadas/<id>/    Rodada descartada, fora do Relatório por padrão
```

Responde à exigência 3 ("onde a suíte, o Replay e a Reexecução moram").

## Exigências do E5 — decisão ou descarte

**1. Quickstart testável.** Decidido acima (Python 3.11+, zero deps). Comando de Replay:
`python -m cx_prompt_lab replay --rodada rodadas/exemplo`. README abre com esse comando e
a tabela de saída de uma Rodada de exemplo commitada; nenhuma chave, Gateway ou rede
necessários depois do clone.

**2. Erros acionáveis.** Toda mensagem segue o formato: problema — causa provável —
próximo passo, citando Rodada, Transcrição ou arquivo; código de saída ≠ 0. Gateway
ausente/incompatível falha rápido citando qual variável de ambiente falta ou qual
endpoint respondeu errado. Todo skip (ex.: Anthropic opt-in desabilitado) nomeia a
variável que o habilitaria.

**3. Superfície de CLI.** Subcomandos em português, espelhando o glossário:
`reexecutar` (nova Rodada, chama o Provider), `replay` (recalcula sem rede), `rodada
--descartar <id>` (descarte sem apagar). Cada um com `--help`. Opções com default e piso
documentados: `--repeticoes` (default e piso 3), `--provider {gateway,anthropic,groq}`,
`--endpoint-url`, `--modelo`, `--timeout-s` (default 30). Seleção de provider/endpoint
nunca exige editar código. Mensagens e nomes de comando em português.

**4. Armazenamento.** **Um arquivo por Chamada** (não JSONL por Rodada). Motivo: o
manifesto referencia cada Chamada pelo hash individual; um arquivo por Chamada permite
detectar e apontar adulteração pontual e permite que uma Rodada abortada mantenha as
Chamadas já gravadas sem reescrever um JSONL parcial. UTF-8, quebra de linha LF. O
Relatório escapa Markdown no texto do modelo antes de renderizar (a Justificativa é
citação literal e pode conter caracteres que quebrariam a tabela). Nome do comando de
Replay: `replay` (subcomando da CLI acima).

**Alternativa descartada — JSONL por Rodada:** dificultaria isolar e revalidar o hash de
uma Chamada específica sem reprocessar o arquivo inteiro; conflita com "descartar Rodada
sem apagar" (exigência 6), que opera por diretório de Rodada, não por linha.

**5. Contrato do Provider.** `RespostaProvider.texto` concatena, na ordem recebida, todos
os blocos de texto da resposta (uma resposta multi-bloco é lida como texto contínuo).
`motivo_parada` usa o vocabulário fechado já fixado na spec (EE5); cada adapter mapeia o
valor nativo do seu provider para esse vocabulário — o teste de contrato (T6) verifica os
dois. Se o Gateway não devolver `temperatura`, o campo é opcional e o Avaliador trata como
"desconhecida" (não bloqueia). O que o Gateway efetivamente devolve para `motivo_parada`,
`modelo` e `temperatura` é confirmado pelo spike (T1); esta ADR fixa apenas a forma do
contrato, não o valor observado.

**6. Do gate de 2026-09-25:**
- **Banner de modo:** toda execução imprime como primeira linha `REPLAY (offline, nenhum
  modelo chamado)` ou `REEXECUÇÃO (ao vivo)`.
- **Saída padrão:** tabela + veredito; detalhe por Repetição só com `--verbose`/`-v`.
- **Override de modelo/parâmetros/URL:** flag com par de variável de ambiente —
  `--provider`/`CXLAB_PROVIDER`, `--modelo`/`CXLAB_MODEL`, `--endpoint-url`/`CXLAB_GATEWAY_URL`;
  flag tem precedência sobre variável.
- **Descartar/superar Rodada ruim:** `rodada --descartar <id>` move o diretório da Rodada
  para `rodadas/descartadas/<id>/` (preservado para auditoria, fora do Relatório por
  padrão; `--todas` reinclui). "Superar" é rodar uma nova Rodada da mesma versão; o
  Relatório mostra a mais recente por padrão.
- **Forma fixa da recusa do Replay:** `Recusa: <Rodada|arquivo> <id/caminho>; hash
  esperado <X>, encontrado <Y>; ação: reexecute com 'reexecutar' ou restaure o commit;
  link: <caminho relativo>`. Códigos de saída distintos: `0` sucesso, `1` recusa de
  integridade, `2` aborto de execução (rede, timeout, credencial).
- **Compatibilidade de esquema:** o manifesto grava `ferramenta_versao` (semver da
  ferramenta). Replay recusa com instrução (`git checkout <tag>`) quando o major da
  versão do manifesto diverge do major instalado.
- **README "Verifique em 2 minutos":** seção com o comando literal e o bloco de saída
  esperado, gerados a partir da Rodada de exemplo commitada; um teste de não-desvio roda
  esse comando exato e compara a saída ao bloco documentado, falhando a suíte se divergir.
- **Timeout por Chamada:** 30s, default documentado, `--timeout-s` sobrescreve.

**7. EE4, EE12 e Plano B:**
- **EE4 — versão do avaliador no manifesto:** campo `avaliador_versao` (semver do módulo
  Avaliador, incrementado sempre que uma regra de classificação muda), gravado junto de
  `ferramenta_versao`.
- **EE12 — Conclusão como módulo separado:** `conclusao.py`, função pura
  `concluir(contagens_v0, contagens_final) -> Veredito`, sem I/O, testável sem Provider
  nem filesystem. O adapter `ReplayProvider` falha alto (código de saída `1`, forma de
  recusa acima) sempre que uma Chamada gravada estiver ausente ou o hash não bater — nunca
  substitui silenciosamente nem inventa resultado.
- **Nota do T10 (CAR-18):** a assinatura real é `concluir(contagens_v0, contagens_final,
  condicoes_v0, condicoes_final) -> Veredito`. As `condicoes_*` (modelo devolvido,
  `temperature`, `max_tokens`) alimentam a pré-condição de comparabilidade da spec e
  mantêm a função pura. O executor passou a expor `acertos` por Repetição e os Rótulos por
  Transcrição (`rotulos_por_repeticao`) para a lista de mudanças.
- **Plano B nomeado:** Groq, Llama 3.3 70B (decisão do humano neste E7). Adapter
  `GroqProvider` no mesmo seam Provider, mapeando o formato de chat completion da Groq
  para `RespostaProvider`. Só instanciado se o spike (T1) declarar o Gateway não-viável.

## Consequências

- Quatro adapters no seam Provider (Gateway, Anthropic, Groq, Replay) tornam esse seam o
  ponto de maior risco de divergência; o teste de contrato (T6) é o que garante que
  `Executor de Rodada`, `Avaliador` e `Conclusão` nunca precisam saber qual adapter está
  por trás.
- Zero dependências externas limita bibliotecas de conveniência (ex.: cliente HTTP mais
  rico); aceito, o volume de chamadas HTTP é pequeno e `urllib.request` cobre o caso.
- Arquivo por Chamada gera mais arquivos por Rodada que JSONL; aceito, é o que permite o
  descarte/adulteração pontual exigidos no gate.

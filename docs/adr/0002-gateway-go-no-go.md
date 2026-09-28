# 0002. Spike do Gateway (CLIProxyAPI local): decisão go/no-go (CAR-9, T1)

Status: decisão técnica GO para o spike, sujeita ao aceite humano deste registro
Ticket: CAR-9 · Relacionada: ADR 0001 (Plano B e contrato do Provider)

## 1. Método de autenticação e gate de termos (decisão registrada em 2026-09-28, antes de instalação e de código do spike)

- **Método escolhido pelo humano:** OAuth da assinatura Claude para uso com o CLIProxyAPI local (`-claude-login`). Nenhuma credencial foi solicitada ou inserida neste registro.
- **Decisão e critério do humano:** escolheu OAuth da própria assinatura Claude e que **não impeça o spike nem cause NO-GO automático**. Para CAR-9, a regra anterior da spec que fazia dos termos uma pré-condição eliminatória é substituída pela emenda explícita ao fim da spec. O gate registra o método e essa decisão antes da instalação; o GO/NO-GO final dependerá das conferências técnicas reais, em especial modelo devolvido, motivo de parada, temperatura e preservação do system prompt.
- **Risco e limites:** o risco aberto 3 da spec permanece **ABERTO**; resultado técnico positivo não é prova de conformidade com termos. A autorização para o método não antecipa o ok específico exigido para cada commit e para a instalação. Os critérios CA1–CA5 continuam pendentes de conferência no ticket e das evidências reais do spike.
- **Plano B já nomeado antes do spike:** Groq, Llama 3.3 70B, camada gratuita, conforme [ADR 0001](0001-arquitetura-cx-prompt-lab.md). Seus limites de taxa ainda estão **NÃO VERIFICADOS**.

## 2. Plano B

**Groq, modelo Llama 3.3 70B, camada gratuita**, nomeados na ADR 0001 antes do spike. Os limites de taxa da camada gratuita permanecem **NÃO VERIFICADOS**. Este spike não acionou nem mediu o Plano B.

## 3. Ambiente e ordem de execução

- Gate de termos: seção 1 commitada em `a3d57d50149515d53272471857c08a076ac9a51e` às 19:31:41 (America/Sao_Paulo), antes do download/instalação do binário. Nenhum código de produção foi escrito neste ticket.
- CLIProxyAPI: binário Linux amd64 da release v8.0.3; SHA-256 do arquivo `CLIProxyAPI_8.0.3_linux_amd64.tar.gz` conferido: `0556446ae0d5941c019252631987cc3b738c6608b855328ece979ab2188ed6dd`. Linha de execução reportada pelo humano: `CLIProxyAPI Version: 8.0.3, Commit: acdace93, BuiltAt: 2026-09-28T00:20:35Z`.
- Instalação e configuração fora do repositório, em `~/cliproxyapi-spike/`; `config.yaml` e `client-key.txt` com permissão `600`. Modo de autenticação upstream: OAuth da assinatura Claude, com login feito pelo humano; credenciais e arquivos de `auths/` não foram lidos aqui.
- Endpoint observado: `http://127.0.0.1:8317`; configuração reportada: `host: "127.0.0.1"`, `request-retry: 0`, `disable-claude-cloak-mode: true`, `logging-to-file: true`, `request-log: true`. Desativar o cloaking foi parte da configuração do teste C4.
- Chamadas reais e evidências locais: 2026-09-28, aproximadamente 19:59–20:30 (America/Sao_Paulo), em `~/cliproxyapi-spike/evidencias/`, fora do repositório. Nenhuma gravação sintética foi usada como prova do Gateway.

## 4. Conferências C0–C6 (CA1 e CA3)

| Check | Observado | Veredito |
|---|---|---|
| C0 — Gateway/modelos | `GET /v1/models` retornou HTTP 200, 17 IDs, incluindo `claude-sonnet-4-5-20250929` (`c0-models.json`). | **PASSA** |
| C1 — formato/modelo/fim normal | `POST /v1/messages` retornou HTTP 200, `type=message`, conteúdo de texto `ok`, `.model=claude-sonnet-4-5-20250929` igual ao solicitado e `stop_reason=end_turn` (`c1.json`). | **PASSA** |
| C2 — truncamento | Com `max_tokens=5`, retornou HTTP 200, `.model=claude-sonnet-4-5-20250929` e `stop_reason=max_tokens` (`c2.json`). | **PASSA** |
| C3 — vocabulário observado | `end_turn` → **fim normal**; `max_tokens` → **truncada**. Todos os valores observados cabem no vocabulário fechado (`c3-stop-reasons.tsv`). `recusa` e `outro` não foram provocados: **NÃO VERIFICADOS** no Gateway. | **PASSA** para os valores observados |
| C4 — system prompt | Pedido com instrução de sistema para responder somente `ABACAXI`; resposta HTTP 200, texto exato `ABACAXI`, `stop_reason=end_turn` (`c4.json`). A preservação literal byte a byte do pedido no upstream não é demonstrada por esse teste comportamental. | **PASSA** no teste obrigatório |
| C5a — temperatura no pedido ao upstream | Pedido de entrada continha `"temperature":0`. Na inspeção humana do trecho `API REQUEST 1` do request-log, o campo `temperature` não apareceu no corpo de saída (`c5a-inspecao.tsv`); o log bruto não foi copiado para o repositório. Isso não prova qual valor foi aplicado pelo upstream. | **FALHA** no critério do guia; aplicação efetiva **NÃO VERIFICADA** |
| C5b — comportamento | 5 chamadas com temperatura pedida 0 e 5 com 1: todas HTTP 200, mesmo `.model`, `stop_reason=end_turn`; 3 textos distintos em cada grupo (`c5b.tsv`, `c5b-t*.json`). Diversidade igual não permite inferir que a temperatura foi respeitada. | **INCONCLUSIVO**; temperatura efetiva **desconhecida** |
| C6 — erro | Modelo inexistente retornou HTTP 400, `invalid_request_error`, mensagem `unknown provider for model modelo-que-nao-existe` (`c6.json`). A requisição foi rejeitada antes do upstream, então este teste não comprova ausência de retentativas upstream. | **PASSA** para erro retornado; retentativa efetiva **NÃO VERIFICADA** |

Evidências: `~/cliproxyapi-spike/evidencias/` (arquivos fora do repositório, sem cabeçalhos de autenticação). O request-log bruto fica em `~/cliproxyapi-spike/logs/` e pode conter dados sensíveis; não integra esta ADR.

## 5. Decisão GO/NO-GO

**GO técnico limitado para usar o Gateway com o método escolhido na seção 1**: C0, C1, C2 e o teste obrigatório C4 demonstraram, em chamadas reais, o formato Anthropic, o ID de modelo devolvido, dois motivos de parada mapeáveis e o comportamento esperado do system prompt. O Plano B continua disponível se a integração futura não sustentar esses resultados.

**Limite do GO:** C5a falhou e C5b foi inconclusivo. A temperatura **solicitada** pode ser registrada como parâmetro do pedido; a temperatura **efetivamente aplicada** permanece **desconhecida** e não deve ser descrita como respeitada. A [ADR 0001](0001-arquitetura-cx-prompt-lab.md) §5 aceita `temperatura=None` no contrato do Provider, sem bloquear o fluxo. O risco aberto 3 da spec permanece **ABERTO** conforme a decisão humana da seção 1; este GO não afirma conformidade com termos.

Critérios de aceite do CAR-9 nesta data:

| Critério | Estado e evidência |
|---|---|
| CA1 — Gateway rodando e configurado | **PASSA**: configuração reportada na seção 3 e C0 HTTP 200. |
| CA2 — gate escrito antes do código do spike | **PASSA**: seção 1 e commit anterior à instalação; regra automática da spec alterada por decisão humana explícita. |
| CA3 — modelo, parada e temperatura efetiva conferidos e registrados | **PARCIAL**: modelo e parada observados; temperatura investigada e registrada, mas o valor efetivo é **NÃO VERIFICADO**. |
| CA4 — Plano B nomeado antes do spike | **PASSA**: ADR 0001 e seção 1 deste registro. |
| CA5 — decisão escrita antes do primeiro prompt de produção | Decisão registrada neste arquivo; **PASSA somente após o commit desta ADR**, se anterior ao primeiro prompt de produção. `cx-prompt-lab/prompts/v0.md` não existia na checagem de 2026-09-28. |

## 6. Consequências para os próximos tickets

- **CAR-13 (T5, GatewayProvider):** manter o escopo via Gateway. Usar `claude-sonnet-4-5-20250929` como ID observado, validar `.model` devolvido, mapear `end_turn` e `max_tokens` como acima e tratar valores ausentes ou não observados sem supor que `refusal` ocorrerá. Enviar o system prompt no campo `system`. Devolver `temperatura=None` quando a resposta não informar o valor efetivo; distinguir parâmetro pedido de parâmetro efetivo na gravação. Não colocar chave nem cabeçalhos nas Chamadas. Tratar HTTP 400 como erro do Provider que aborta a Rodada, sem retentativa no app. A configuração `request-retry: 0` do proxy precisa ser preservada para o piloto; C6 não a comprovou dinamicamente.
- **CAR-20 (T11, Reexecução):** manter o mesmo modelo devolvido e os mesmos parâmetros pedidos entre versões; não apresentar temperatura efetiva como conhecida. Uma mudança de upstream ou modelo exige nova conferência e novas Rodadas comparáveis. Respostas do spike não substituem as Chamadas reais do T11.
- **CAR-16 (T8, piloto):** usar o Gateway real com o modelo acima; reconferir C1 e C4 se a configuração mudar. Registrar explicitamente que o resultado é exploratório e que a temperatura efetiva segue desconhecida.
- **CAR-15 (T6, contrato):** cobrir `end_turn`/`max_tokens`, ausência de `stop_reason`, conteúdo em múltiplos blocos, temperatura ausente e erros HTTP em testes offline. Respostas sintéticas da suíte validam o adapter, mas não servem de evidência sobre o modelo real.

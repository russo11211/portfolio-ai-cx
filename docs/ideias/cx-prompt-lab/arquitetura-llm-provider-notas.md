# Notas de arquitetura — provider abstraction LLM (CLIProxyAPI + Anthropic)

> Material bruto colado pelo usuário durante a sessão de `/ideacao` de 2026-09-22.
> Não é decisão fechada de ideia — é insumo detalhado para a ADR do estágio 7
> (`/codebase-design`) e/ou para a spec do estágio 4 (`/to-spec`). Guardado aqui
> verbatim para não se perder, e linkado em `ideia.md` → Fontes e anexos.

## Motivação (isto sim é ideia-level, já refletido em `ideia.md`)

A aplicação precisa demonstrar capacidade técnica de integração com a API da Anthropic,
mas sem depender obrigatoriamente de consumo pago da API oficial durante o
desenvolvimento. Por isso, usar um gateway local (CLIProxyAPI) durante o dev, com
abstração que permita trocar para a API oficial da Anthropic por configuração, sem
refatorar a aplicação.

## Conteúdo bruto (detalhe de implementação — não decidir agora)

A aplicação precisa demonstrar capacidade técnica de integração com a API da Anthropic.

Durante desenvolvimento, porém, não queremos depender obrigatoriamente de consumo pago da API oficial da Anthropic.

Por isso, utilizaremos o CLIProxyAPI como gateway local/intermediário durante desenvolvimento, permitindo que a aplicação utilize provedores/modelos configurados no gateway.

IMPORTANTE:

O objetivo NÃO é criar uma implementação proprietária presa ao CLIProxyAPI.

A aplicação deve ser arquitetada de forma que:

1. consiga trabalhar atualmente através do CLIProxyAPI;
2. seja compatível com a API da Anthropic;
3. possa posteriormente conectar-se diretamente à API oficial da Anthropic sem refatorar a aplicação;
4. permita comprovar claramente que a integração Anthropic está implementada;
5. diferencie explicitamente:
   - teste de compatibilidade Anthropic;
   - teste real contra a infraestrutura oficial da Anthropic.

Também não implemente mecanismos destinados a contornar autenticação, cobrança, limites, políticas ou termos dos provedores. Utilize somente métodos de autenticação e integração suportados pelas ferramentas/provedores envolvidos.

### Objetivo de arquitetura

```
Application
     │
     ▼
LLM Provider Interface
     │
     ├───────────────┐
     ▼               ▼
AnthropicProvider   GatewayProvider
     │               │
     │               ▼
     │          CLIProxyAPI
     │               │
     │        ┌──────┼────────┐
     │        ▼      ▼        ▼
     │      Claude  Codex   outros
     │
     ▼
Anthropic API oficial
```

A aplicação NÃO deve possuir dependência direta do CLIProxyAPI em sua lógica de negócio.
Crie uma abstração de provider.

### 1. Provider interface

Interface `LLMProvider` com `generate()`, `stream()`, `healthCheck()`, e opcionalmente
`getModelCapabilities()`. A lógica de negócio depende exclusivamente dessa interface.

### 2. AnthropicProvider

Conexão real com a API oficial da Anthropic. Implementa `LLMProvider`, usa endpoints
oficiais, recebe API key só por variável de ambiente/secret manager, nunca armazena
credenciais no código, suporta modelo configurável, timeout, tratamento de erro,
streaming (se necessário) e health check. Config: `LLM_PROVIDER=anthropic`,
`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`. Sem API key, o provider fica desabilitado sem
travar o resto da aplicação.

### 3. GatewayProvider / CLIProxyProvider

Direciona requisições ao CLIProxyAPI. Config: `LLM_PROVIDER=gateway`,
`LLM_GATEWAY_URL=http://localhost:8317`, `LLM_MODEL=reasoning`. Antes de implementar,
consultar a documentação atual do CLIProxyAPI — não assumir endpoints, formatos,
modelos, autenticação ou parâmetros.

### 4. Compatibilidade Anthropic

Preservar os conceitos da API Anthropic (`messages`, `system`, `role`, `content`,
`model`, `max_tokens`, `temperature`, `stream`) na aplicação. Não espalhar estruturas de
outros provedores. Usar adapters quando os formatos divergirem.

### 5. Adapter / normalização

Representação interna independente de provedor:

```
LLMRequest { model, systemPrompt, messages, temperature, maxTokens, stream }
LLMResponse { content, model, provider, usage, finishReason, latency }
```

Cada provider transforma esse formato interno para o protocolo correspondente.

### 6. Troca de provider sem alteração da aplicação

Trocar `LLM_PROVIDER=gateway` → `LLM_PROVIDER=anthropic` sem alterar lógica principal.

### 7. Modelos virtuais

Não espalhar nomes específicos de modelo pelo código. Usar aliases internos (`fast`,
`balanced`, `reasoning`, `default`) mapeados via configuração.

### 8. Testes — três níveis

- **Teste A (unitário):** Application → LLMProvider mock. Sem dependência externa.
- **Teste B (compatibilidade Anthropic):** Application → Provider → CLIProxyAPI.
  Demonstra que a aplicação opera com interface/protocolo compatível com Anthropic.
  Não deve ser descrito como conexão real com a Anthropic.
- **Teste C (Anthropic real):** Application → AnthropicProvider → api.anthropic.com.
  Smoke test opcional (para não gerar custo), só roda quando `ANTHROPIC_API_KEY` existe.

### 9. Matriz de validação (documentar no README)

| Teste | Necessita API Anthropic | O que comprova |
|---|---|---|
| Unit Test | NÃO | lógica da aplicação |
| CLIProxyAPI | NÃO | compatibilidade da integração |
| Anthropic Integration Test | SIM | conexão real com Anthropic |

### 10–11. Smoke tests

`test:anthropic` — verifica `ANTHROPIC_API_KEY`; se ausente, SKIPPED; se presente, envia
requisição mínima, valida sucesso, registra modelo e latência, minimiza custo.

`test:llm-gateway` — valida Application → LLM abstraction → CLIProxyAPI → modelo
configurado.

### 12. Health checks

`/health/llm` retornando `{ provider, status, model }`. Nunca retornar tokens/credenciais.

### 13. Logs e observabilidade

Registrar: provider, model, latency, status, request_id, erro, uso de tokens (quando
disponível). Nunca registrar: API keys, OAuth tokens, cookies, credentials, prompts
sensíveis completos por padrão.

### 14. Fallback

Estruturar para permitir futuramente `primary provider → erro → fallback provider`, mas
não implementar complexidade extra no MVP — configuração explícita de provider basta.

### 15. Segurança

Nunca: API keys no Git, tokens no código-fonte, credenciais em logs, bypass de
autenticação, reuso não suportado de sessões/cookies, contornar limites/cobrança dos
provedores. Usar `.env` local, secret manager ou Docker secrets conforme o ambiente.

### 16. Docker

`docker compose up` sobe `application` + `llm-gateway` (CLIProxyAPI como serviço
separado).

### 17. Documentação

README com seção "LLM Architecture". Criar `docs/llm-architecture.md` com: arquitetura,
providers, configuração, execução local, testes, segurança, troca de provider,
diferença entre compatibilidade Anthropic e conexão Anthropic real.

### 18. Comprovação da integração Anthropic

A documentação deve permitir afirmar: "A aplicação possui integração compatível com a
API Anthropic e possui um AnthropicProvider capaz de se conectar diretamente à API
oficial da Anthropic através de configuração." Enquanto só o CLIProxyAPI estiver em uso,
NÃO afirmar que está usando a API oficial. Só depois de `test:anthropic` passar contra a
infraestrutura oficial, registrar que "a integração foi validada contra a API oficial da
Anthropic."

### 19. Evidência

Ao final: arquitetura utilizada, arquivos criados/modificados, provider utilizado,
comando executado, request/response sanitizados, status do teste, logs sem credenciais.

### 20. Critérios de aceite (nível implementação, não ideia)

1. Abstração `LLMProvider` existe.
2. Existem `GatewayProvider` e `AnthropicProvider`.
3. Aplicação funciona via CLIProxyAPI.
4. Provider trocável por configuração.
5. Lógica principal não muda para usar Anthropic diretamente.
6. Teste de integração do gateway existe.
7. Teste opcional para Anthropic real existe.
8. Credenciais não aparecem em código nem logs.
9. Documentação da arquitetura existe.
10. Documentação distingue compatibilidade vs. conexão real.

### Processo sugerido (para quando chegar ao estágio 7/8)

1. Analisar o repositório atual.
2. Identificar stack e arquitetura existentes.
3. Consultar a documentação atual do CLIProxyAPI e da API Anthropic.
4. Propor as alterações mínimas.
5. Apresentar o plano.
6. Implementar.
7. Executar os testes.
8. Entregar evidências e documentação.

Evitar reescrever partes que já funcionam; preferir alterações pequenas, desacopladas e
testáveis.

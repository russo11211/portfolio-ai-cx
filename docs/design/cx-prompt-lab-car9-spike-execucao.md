# CAR-9 — guia de execução do spike do Gateway local

Registro de 2026-09-28. Gateway: **CLIProxyAPI v8.0.3**, binário Linux amd64, upstream Claude por OAuth da assinatura. Este documento reúne o fluxo realizado, os comandos para reproduzi-lo e os resultados observados. A decisão está na [ADR 0002](../adr/0002-gateway-go-no-go.md); o contrato do app está na [ADR 0001](../adr/0001-arquitetura-cx-prompt-lab.md).

> **Como ler os comandos:** as linhas copiadas da saída enviada pelo humano estão identificadas como *observadas*. Os blocos de instalação, inicialização e `curl` abaixo são a sequência **reproduzível do guia original**; não há um histórico de shell completo que permita afirmar que cada linha foi digitada exatamente assim. Nenhum comando deste documento foi executado ao redigi-lo. Nunca cole no chat `config.yaml`, `client-key.txt`, `auths/` ou request-logs brutos.

## 0. Escopo, decisões e estado

- Diretório do spike: `~/cliproxyapi-spike/` (`~/cliproxyapi-spike/`), **fora do repositório**. Binário, config, token OAuth, logs e respostas reais ficaram ali.
- Método escolhido pelo humano: OAuth da assinatura Claude via `-claude-login`. O humano decidiu que a preocupação com os termos não imporia NO-GO automático. A seção 1 da ADR 0002 e a emenda da spec foram commitadas **antes** da instalação: `a3d57d50149515d53272471857c08a076ac9a51e`, 2026-09-28 19:31:41 −03:00. O risco 3 da spec permanece **ABERTO**; o GO técnico não prova conformidade com termos.
- Plano B nomeado antes do spike: **Groq, Llama 3.3 70B**, camada gratuita. Limites de taxa: **NÃO VERIFICADOS**.
- A decisão final do spike foi commitada em `7a8af9e5b30e8c011b9489ab6ec9844e387c88a2`, 2026-09-28 20:59:08 −03:00, **sem push**. Nenhum arquivo de prompt de produção existia na checagem após esse commit.
- Resultado: **GO técnico limitado** para o Gateway. C5a falhou, C5b foi inconclusivo e a temperatura aplicada permanece **NÃO VERIFICADA**. CA3 do CAR-9 está **PARCIAL**. Os textos para o Linear foram apenas propostos; status Done e comentário **não foram aplicados nem conferidos** nesta sessão porque o conector não estava disponível.
- O desligamento, a revogação OAuth e a remoção **não foram executados** até o fechamento deste registro. Os controles foram apenas preparados e verificados com `bash -n`; seu comportamento destrutivo ainda não foi testado.

## 1. Download, integridade e extração

O caminho escolhido foi o **binário de release**, não Docker nem instalador de serviço. No terminal do humano:

```bash
mkdir -p ~/cliproxyapi-spike
cd ~/cliproxyapi-spike
VER=8.0.3
curl -fLO "https://github.com/router-for-me/CLIProxyAPI/releases/download/v${VER}/CLIProxyAPI_${VER}_linux_amd64.tar.gz"
curl -fLO "https://github.com/router-for-me/CLIProxyAPI/releases/download/v${VER}/checksums.txt"
sha256sum -c --ignore-missing checksums.txt
tar -tzf "CLIProxyAPI_${VER}_linux_amd64.tar.gz"
tar -xzf "CLIProxyAPI_${VER}_linux_amd64.tar.gz"
```

**Observado:** a conferência informou `CLIProxyAPI_8.0.3_linux_amd64.tar.gz: SUCESSO`; SHA-256 registrado na ADR: `0556446ae0d5941c019252631987cc3b738c6608b855328ece979ab2188ed6dd`. A listagem do arquivo mostrou `cli-proxy-api`, `LICENSE`, `README.md`, `README_CN.md`, `config.example.yaml`. O binário extraído usado no spike é `~/cliproxyapi-spike/cli-proxy-api`. A linha de execução reportada pelo humano foi:

```text
CLIProxyAPI Version: 8.0.3, Commit: acdace93, BuiltAt: 2026-09-28T00:20:35Z
```

Fonte da release: <https://github.com/router-for-me/CLIProxyAPI/releases/tag/v8.0.3>.

## 2. Configuração local e login

Foi criada uma chave **do cliente do proxy**, distinta da credencial OAuth upstream. A geração reproduzível é:

```bash
cd ~/cliproxyapi-spike
mkdir -p auths logs evidencias
chmod 700 auths evidencias
openssl rand -hex 24 > client-key.txt
chmod 600 client-key.txt
```

O `config.yaml` ficou no mesmo diretório, fora do repo. O esquema abaixo mostra **somente a estrutura**, sem chave real; não é cópia do arquivo que contém segredos:

```yaml
config-version: 8
server:
  host: "127.0.0.1"
  port: 8317
management:
  allow-remote: false
  secret-key: ""
  disable-control-panel: true
access:
  api-keys:
    - "<valor de client-key.txt, inserido localmente pelo humano>"
routing:
  retry:
    request-retry: 0
oauth:
  auth-dir: "~/cliproxyapi-spike/auths"
  providers:
    claude:
      disable-claude-cloak-mode: true
observability:
  logs:
    logging-to-file: true
    request-log: true
```

**Observado pelo comando do humano:** `config.yaml` e `client-key.txt` tinham permissão `600`. O `grep` de campos não secretos mostrou `host: "127.0.0.1"`, `request-retry: 0`, `auth-dir` absoluto, `disable-claude-cloak-mode: true`, `logging-to-file: true` e `request-log: true`. O arquivo completo não foi lido por este agente. A estrutura acima serve para localizar campos; valide contra o `config.example.yaml` da versão instalada antes de recriar a configuração.

Comandos de verificação segura usados pelo humano:

```bash
cd ~/cliproxyapi-spike
stat -c '%a %n' config.yaml client-key.txt
grep -E '^[[:space:]]*(host:|request-retry:|auth-dir:|disable-claude-cloak-mode:|logging-to-file:|request-log:)' config.yaml
```

O login foi concluído **pelo humano** no fluxo do provedor. O comando de entrada do guia foi:

```bash
cd ~/cliproxyapi-spike
./cli-proxy-api -config config.yaml -claude-login -no-browser
```

O navegador abriu o fluxo OAuth da Claude com callback local. O humano concluiu o login. Nenhum token, código de autorização, conteúdo de `auths/` ou chave foi solicitado no chat ou lido pelo agente.

## 3. Subida e acesso

O comando de subida indicado para um terminal dedicado foi:

```bash
cd ~/cliproxyapi-spike
./cli-proxy-api -config config.yaml 2>&1 | tee run.log
```

O humano confirmou que o Gateway estava rodando e enviou a linha de versão acima. A API local usada nos testes foi `http://127.0.0.1:8317`; a porta não foi publicada por Docker.

O comando **efetivamente enviado pelo humano** para localizar a versão no log foi:

```bash
grep -E 'CLIProxyAPI Version:' ~/cliproxyapi-spike/logs/main.log | tail -1
```

Para chamar o Gateway a partir de **outro terminal**, sem expor o valor da chave no chat:

```bash
cd ~/cliproxyapi-spike
export CPA_KEY="$(cat client-key.txt)"
export CPA='http://127.0.0.1:8317'
export MODELO='claude-sonnet-4-5-20250929'
```

`CPA_KEY` protege o acesso local ao proxy. A credencial upstream permanece somente no mecanismo OAuth do CLIProxyAPI.

## 4. Conferências reais C0–C6

As chamadas abaixo usam o formato `/v1/messages` e `x-api-key`. Os arquivos existentes em `~/cliproxyapi-spike/evidencias/` vieram das chamadas reais do spike. Os exemplos a seguir servem para **reproduzir o teste**; se forem rodados de novo, são uma nova execução, com novas respostas. Os códigos HTTP informados abaixo foram os reportados pelo humano e conferidos nas respostas onde havia arquivo JSON.

### C0 — modelos servidos: PASSA

```bash
curl -sS -o evidencias/c0-models.json -w 'HTTP %{http_code}\n' \
  "$CPA/v1/models" -H "x-api-key: $CPA_KEY"
jq -r '.data[].id' evidencias/c0-models.json
```

**Observado:** HTTP 200, 17 IDs, inclusive `claude-sonnet-4-5-20250929`. Este ID datado foi escolhido para as chamadas seguintes. Evidência: `evidencias/c0-models.json`.

### C1 — formato Anthropic, modelo e fim normal: PASSA

```bash
curl -sS -o evidencias/c1.json -w 'HTTP %{http_code}\n' \
  "$CPA/v1/messages" \
  -H "x-api-key: $CPA_KEY" -H 'anthropic-version: 2023-06-01' \
  -H 'content-type: application/json' \
  -d "{\"model\":\"$MODELO\",\"max_tokens\":256,\"temperature\":0,\"messages\":[{\"role\":\"user\",\"content\":\"Responda só com a palavra: ok\"}]}"
jq '{type,model,stop_reason,texto:[.content[]|select(.type=="text").text]|join("")}' evidencias/c1.json
```

**Observado:** HTTP 200, `type=message`, `.model=claude-sonnet-4-5-20250929`, `stop_reason=end_turn`, texto `ok`. Mapeamento: `end_turn` → **fim normal**.

### C2 — truncamento: PASSA

```bash
curl -sS -o evidencias/c2.json -w 'HTTP %{http_code}\n' \
  "$CPA/v1/messages" \
  -H "x-api-key: $CPA_KEY" -H 'anthropic-version: 2023-06-01' \
  -H 'content-type: application/json' \
  -d "{\"model\":\"$MODELO\",\"max_tokens\":5,\"temperature\":0,\"messages\":[{\"role\":\"user\",\"content\":\"Conte de 1 a 50 por extenso, separados por vírgula.\"}]}"
jq '{model,stop_reason,usage}' evidencias/c2.json
```

**Observado:** HTTP 200, `stop_reason=max_tokens`, 5 tokens de saída. Mapeamento: `max_tokens` → **truncada**. Evidência: `evidencias/c2.json`.

### C3 — vocabulário observado: PASSA no que foi visto

Os valores reais de C1, C2, C4 e C5b foram registrados em `evidencias/c3-stop-reasons.tsv`: `end_turn` → fim normal; `max_tokens` → truncada. Nenhum `stop_reason` observado ficou fora do vocabulário fechado. **Recusa** e **outro** não foram provocados nem verificados no Gateway; os respectivos mapeamentos permanecem para os testes de contrato de CAR-15.

### C4 — preservação comportamental do system prompt: PASSA

```bash
curl -sS -o evidencias/c4.json -w 'HTTP %{http_code}\n' \
  "$CPA/v1/messages" \
  -H "x-api-key: $CPA_KEY" -H 'anthropic-version: 2023-06-01' \
  -H 'content-type: application/json' \
  -d "{\"model\":\"$MODELO\",\"max_tokens\":20,\"temperature\":0,\"system\":\"Responda sempre, a qualquer mensagem, só com a palavra ABACAXI.\",\"messages\":[{\"role\":\"user\",\"content\":\"Qual é a capital da França?\"}]}"
jq -r '[.content[]|select(.type=="text").text]|join("")' evidencias/c4.json
```

**Observado:** HTTP 200, texto exato `ABACAXI`, `stop_reason=end_turn`. Evidência: `evidencias/c4.json`. Este é um teste de comportamento; não comprova identidade byte a byte do pedido que chegou ao upstream.

### C5a — temperatura no request-log de saída: FALHA

O pedido de entrada de C1 continha `"temperature":0`. O humano inspecionou localmente o request-log `logs/v1-messages-2026-09-28T201602-00000002.log`: havia `REQUEST BODY` com esse campo e a seção `API REQUEST 1` para `https://api.anthropic.com/v1/messages?beta=true`. Depois de examinar a saída, informou que **não havia a variável `temperature`** na requisição ao upstream. A observação foi resumida em `evidencias/c5a-inspecao.tsv`; o log bruto não foi copiado para o repo nem para o chat porque pode conter cabeçalhos sensíveis.

Pelo critério do guia original, C5a é **FALHA**. O teste **não determina** qual temperatura o upstream aplicou. A temperatura efetiva é **NÃO VERIFICADA**.

### C5b — comportamento em T=0 e T=1: INCONCLUSIVO

Foram feitas **5 chamadas reais** com temperatura pedida 0 e **5** com temperatura pedida 1, usando o pedido abaixo com `T` e `i` variáveis. Cada resposta ficou em `evidencias/c5b-t${T}-${i}.json`; o resumo ficou em `evidencias/c5b.tsv`.

```bash
for T in 0 1; do
  for i in 1 2 3 4 5; do
    arquivo="evidencias/c5b-t${T}-${i}.json"
    curl -sS -o "$arquivo" -w "T=$T repetição=$i HTTP %{http_code}\n" \
      "$CPA/v1/messages" \
      -H "x-api-key: $CPA_KEY" -H 'anthropic-version: 2023-06-01' \
      -H 'content-type: application/json' \
      -d "{\"model\":\"$MODELO\",\"max_tokens\":30,\"temperature\":$T,\"messages\":[{\"role\":\"user\",\"content\":\"Invente um nome de planeta que não existe. Responda só o nome.\"}]}"
  done
done
```

Para reconstruir o resumo TSV **a partir das respostas salvas**, sem chamar o Gateway novamente:

```bash
: > evidencias/c5b.tsv
for T in 0 1; do
  for i in 1 2 3 4 5; do
    jq -r --arg t "$T" '[ $t, .model, .stop_reason, ([.content[]|select(.type=="text").text]|join("")) ] | @tsv' \
      "evidencias/c5b-t${T}-${i}.json" >> evidencias/c5b.tsv
  done
  printf 'T=%s textos distintos: ' "$T"
  jq -r '[.content[]|select(.type=="text").text]|join("")' \
    evidencias/c5b-t${T}-*.json | sort -u | wc -l
done
```

**Observado:** todas as 10 chamadas HTTP 200, mesmo `.model`, `stop_reason=end_turn`; **3 textos distintos** em cada grupo. A diversidade igual torna o teste **INCONCLUSIVO**; nem T=0 implica determinismo, nem a diferença entre T=0 e T=1 foi demonstrada. Temperatura aplicada: **desconhecida**. A ADR 0001 §5 admite `temperatura=None` no contrato do Provider.

### C6 — erro para modelo inexistente: PASSA para retorno do erro

```bash
curl -sS -o evidencias/c6.json -w 'HTTP %{http_code}\n' \
  "$CPA/v1/messages" \
  -H "x-api-key: $CPA_KEY" -H 'anthropic-version: 2023-06-01' \
  -H 'content-type: application/json' \
  -d '{"model":"modelo-que-nao-existe","max_tokens":5,"messages":[{"role":"user","content":"oi"}]}'
jq . evidencias/c6.json
```

**Observado:** HTTP 400, `error_type=invalid_request_error`, mensagem `unknown provider for model modelo-que-nao-existe`. Evidência: `evidencias/c6.json`. A rejeição ocorreu antes de uma chamada upstream; por isso C6 não comprova dinamicamente o comportamento de retentativa, embora a configuração reportada fosse `request-retry: 0`.

## 5. Decisão e efeito nos tickets

A ADR 0002 registrou **GO técnico limitado** para este Gateway e esse upstream, com C4 obrigatório aprovado e com temperatura efetiva desconhecida. CAR-13 mantém o escopo `GatewayProvider`: usar o ID devolvido, mapear `end_turn`/`max_tokens`, tratar erros sem retentativa e deixar `temperatura=None` se não houver valor efetivo. CAR-20 deve comparar Rodadas com o mesmo modelo devolvido e mesmos parâmetros **pedidos**, sem afirmar que a temperatura foi respeitada. CAR-16 precisa usar chamadas reais do Gateway. CAR-15 cobre o contrato em testes offline, sem confundir respostas sintéticas com evidência do modelo.

**Rastreabilidade:** a ADR é um registro local commitado, não uma atualização automática do Linear. O conector Linear não estava disponível; CAR-9 → Done e o comentário opcional em CAR-13 foram apenas **propostos**, não aplicados. CA1, CA2, CA4 e CA5 têm evidência; CA3 permanece **PARCIAL**. O risco aberto 3 da spec segue **ABERTO**.

## 6. Controles preparados: onde ficam e como acessar

Os controles estão **fora do repositório**, nestes caminhos absolutos:

| Controle | Caminho | Efeito quando acionado |
|---|---|---|
| Desligar/inibir esta instalação | `~/cliproxyapi-spike/desligar.sh` | Tira a permissão de execução do binário deste diretório (`chmod 600`), envia `TERM` aos processos cujo `/proc/<pid>/exe` aponta para ele, espera e mostra a porta 8317. |
| Remover esta instalação | `~/cliproxyapi-spike/remover.sh` | Chama `desligar.sh`, pede confirmação de revogação OAuth e solicita `APAGAR` **para cada** arquivo ou pasta conhecido, inclusive `auths/`, config, chave, logs, evidências, binário e os próprios controles. |

Ambos tinham permissão `700` na conferência deste registro. Para localizá-los e ler o código **sem executá-los**:

```bash
ls -l ~/cliproxyapi-spike/desligar.sh ~/cliproxyapi-spike/remover.sh
sed -n '1,220p' ~/cliproxyapi-spike/desligar.sh
sed -n '1,260p' ~/cliproxyapi-spike/remover.sh
bash -n ~/cliproxyapi-spike/desligar.sh ~/cliproxyapi-spike/remover.sh
```

### 6.1 Desligar e inibir esta cópia (somente quando o humano decidir)

```bash
~/cliproxyapi-spike/desligar.sh
```

O script atua **somente** sobre o binário em `~/cliproxyapi-spike/cli-proxy-api` e processos iniciados dessa cópia; não é um bloqueio global de outras cópias, containers ou serviços. O dono do arquivo pode restaurar a permissão de execução mais tarde, então o bloqueio é reversível. Após executá-lo, o humano deve conferir que não há processo residual e que a porta 8317 não está em `LISTEN`; se a porta seguir ocupada, investigar outra instância. O script não foi executado ainda, portanto o estado atual da porta/processo é **NÃO VERIFICADO** neste registro.

### 6.2 Revogar OAuth e remover arquivos (cada confirmação é humana)

Antes de remover, copiar `evidencias/` para outro local **se quiser preservá-las**; `remover.sh` também as apaga. A remoção local **não revoga** o token no provedor: o humano deve revogar a autorização correspondente no painel Claude (o script orienta procurar `Settings > Claude Code`; o caminho exato no painel pode mudar).

```bash
~/cliproxyapi-spike/remover.sh
```

O script pede `REVOQUEI` antes das exclusões e depois `APAGAR` item por item. Se uma resposta não corresponder, ele para e preserva os itens restantes; arquivos já confirmados antes desse ponto podem ter sido removidos. Ao final, tenta remover o diretório **apenas se vazio**. O script não inspeciona nem remove `~/.cli-proxy-api`; se esse caminho existir, apenas avisa, pois pode pertencer a outro uso. A remoção ainda depende da autorização e da execução do humano; **não aconteceu** nesta documentação.

## 7. Limites do que foi demonstrado

- A resposta de C4 sustenta que o system prompt funcionou naquele pedido; não demonstra o pedido upstream byte a byte.
- C5a e C5b não demonstram temperatura efetiva nem que T=0 é determinístico. A distinção entre parâmetro **pedido** e **aplicado** deve permanecer nas próximas Rodadas e no relatório.
- `request-retry: 0` foi observado na configuração reportada; C6 não mede chamadas upstream repetidas.
- Os arquivos `evidencias/` são respostas de chamadas reais deste spike. Testes com transporte falso podem verificar o código de CAR-13/CAR-15, mas **não** substituem evidência de um modelo real.
- Nenhuma credencial upstream, chave do cliente, `auths/` ou log bruto foi copiado para o repositório.

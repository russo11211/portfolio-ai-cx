# CX Prompt Lab

Biblioteca versionada de prompts que classificam a intenção de chamadas de contact center, medida por um eval sobre um dataset fixo. Existe para dar ao candidato evidência auditável de iteração de prompt com medição.

## Language

### Dado

**Transcrição**:
Texto fictício de uma chamada de atendimento. Cada transcrição pertence ao dataset e tem exatamente um rótulo esperado.
_Avoid_: exemplo, caso, amostra, ligação

**Dataset**:
O conjunto fixo de 20-30 transcrições rotuladas. Não muda entre versões de prompt, e é isso que torna as taxas comparáveis.
_Avoid_: base, corpus

**Intenção**:
O que o cliente quer resolver na chamada. É um conceito do mundo, não um valor da lista.
_Avoid_: motivo, assunto

**Rótulo**:
Um valor da lista fechada de intenções. O rótulo esperado é o da intenção principal; numa chamada de intenção dupla, vale a regra de desempate escrita no dataset. Não existe conjunto de rótulos válidos por transcrição.
_Avoid_: classe, categoria, intenção (quando se fala do valor devolvido)

### Contrato de saída

**Justificativa**:
Trecho copiado literalmente da transcrição que sustenta o rótulo escolhido. Paráfrase não é justificativa.
_Avoid_: explicação, raciocínio

**Justificativa ancorada**:
Justificativa cujo trecho aparece como substring da transcrição.
_Avoid_: justificativa correta, justificativa plausível

**Contrato de saída**:
Rótulo da lista mais justificativa literal. Vale igual para todas as versões de prompt, v0 inclusive; o que muda entre versões é a instrução, nunca a definição de erro.

### Métricas

**Erro de acerto**:
O modelo devolve um rótulo válido, mas diferente do rótulo esperado. Independe da justificativa.
_Avoid_: erro de classificação, alucinação (quando o rótulo existe)

**Alucinação**:
Saída que inventa algo: rótulo fora da lista, ou justificativa não ancorada. É taxa independente do erro de acerto; uma resposta pode contar nas duas. Reportada em dois subtipos: rótulo inexistente e justificativa não ancorada.
_Avoid_: erro, resposta errada, invenção

**Violação de formato**:
Saída que não dá para interpretar (estrutura quebrada, campo faltando). Categoria própria, fora da alucinação, para não inflar a queda entre versões com erro de parsing.
_Avoid_: alucinação de formato, erro de parsing

### Execução

**Versão de prompt**:
Uma instrução numerada (v0, v1, …) para a classificação. v0 é o prompt ingênuo. "Versão final" é a última concluída, com mínimo v1.
_Avoid_: iteração, variante, release

**Chamada**:
Um pedido e uma resposta para (versão de prompt, transcrição, modelo). É a unidade gravada em arquivo.
_Avoid_: request, execução, rodada (quando é uma só)

**Rodada**:
Uma passada de uma versão de prompt por todo o dataset, que produz uma taxa por métrica. Nunca designa uma chamada isolada.
_Avoid_: run, execução, batch

**Repetição**:
Refazer uma rodada com a mesma versão e o mesmo dataset para medir variação.
_Avoid_: retry, nova rodada

### Reprodução

**Gateway**:
O CLIProxyAPI local, usado no desenvolvimento para não gerar custo. Só afirma compatibilidade, nunca validação contra a API oficial.
_Avoid_: proxy, provider, servidor

**Compatível com Anthropic**:
Único enunciado permitido sobre o lado Anthropic: o formato de pedido e resposta segue a API Anthropic e o gateway o aceitou. Nunca "validado contra a Anthropic".
_Avoid_: validado, testado na Anthropic, integrado (sem qualificar)

**Replay**:
Recalcular as métricas a partir das chamadas gravadas e commitadas, sem chamar modelo. Prova que o cálculo é reproduzível, não que o modelo responderia igual hoje.
_Avoid_: reprodução, rerun

**Reexecução**:
Fazer novas chamadas ao gateway. Depende do gateway e produz números novos.
_Avoid_: replay, reprodução

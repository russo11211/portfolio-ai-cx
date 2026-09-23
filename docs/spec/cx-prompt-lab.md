<!-- /autoplan restore point: "~/.gstack/projects/russo11211-portfolio-ai-cx/claude-mattpocock-skills-setup-96cf28-autoplan-restore-20260923-133952.md" -->
## Implementation plan
<!-- Cópia somente leitura. Fonte da verdade: https://linear.app/1bitpios/issue/CAR-8 (time Carreira) -->

## Problem Statement

O candidato precisa de evidência auditável de que sabe iterar prompts **com medição**, para conversas técnicas na Porto, NCS/GFT e Bain/Caju. O substituto atual, o take-home, prova execução num problema que a empresa define, mas não prova que o candidato escopa sozinho nem que mede a própria iteração. Hoje a resposta é verbal ou autodeclarada (CV). O leitor real é um recrutador/entrevistador técnico que precisa conferir os números sem pagar nada e sem ter acesso ao gateway do candidato.

Restrições: 1 semana de trabalho a partir da implementação; o candidato **não pode pagar** a API oficial da Anthropic; toda chamada real a modelo passa pelo **Gateway** (CLIProxyAPI local).

## Solution

O **CX Prompt Lab**: uma biblioteca versionada de **Versões de prompt** que classificam a **Intenção** de chamadas de contact center, medida por um eval sobre um **Dataset** fixo de 20-30 **Transcrições** fictícias rotuladas.

Para quem lê: uma tabela por versão (v0, v1, …) com **Erro de acerto**, **Alucinação** (nos dois subtipos) e **Violação de formato**, mais um case study que explica o que mudou entre versões e por quê. Qualquer pessoa que clone o repositório roda o **Replay** offline e chega aos mesmos números, sem chave e sem Gateway. O candidato, com o Gateway, faz **Rodadas** novas (**Reexecução**) e grava as **Chamadas**. Cada Chamada gravada é commitada.

O relatório só afirma que o lado Anthropic é **Compatível com Anthropic**. Nunca afirma validação contra a API oficial.

## User Stories

1. Como recrutador técnico, quero ver uma tabela v0→vN com Erro de acerto, Alucinação e Violação de formato por versão de prompt, para julgar em minutos se o candidato mede a própria iteração.
2. Como recrutador técnico, quero ler um case study que explica o que mudou de uma versão para a próxima e por que, para entender o raciocínio e não só o número.
3. Como recrutador técnico ou terceiro que clonou o repositório, quero rodar um único comando de Replay, sem chave e sem Gateway, e ver a tabela, para conferir que os números saem das Chamadas gravadas sem instalar nada além do necessário para o cálculo.
4. Como recrutador técnico, quero que o README diga exatamente o que cada teste comprova e qual é o comando de Replay, para não ter de adivinhar.
5. Como recrutador técnico, quero que o relatório declare o limite do Replay (prova o cálculo, não que o modelo responderia igual hoje) e distinga Replay de Reexecução, para confiar na honestidade do candidato e não confundir "recalculei" com "o modelo respondeu de novo".
6. Como recrutador técnico, quero que o relatório nunca diga "validado contra a Anthropic", para não ser induzido a erro sobre o que foi testado.
7. Como recrutador técnico, quero ver a variação observada entre Repetições, para saber se a queda entre v0 e a versão final é maior que o ruído.
8. Como recrutador técnico, quero abrir o Dataset e ver casos ambíguos e de intenção dupla com a regra de desempate escrita, para saber que v0 falha por motivo real e não por um problema trivial.
9. Como candidato, quero um Dataset fixo de 20-30 Transcrições fictícias, cada uma com exatamente um Rótulo esperado, para que as taxas sejam comparáveis entre Versões de prompt.
10. Como candidato, quero que a lista de Rótulos seja fechada e igual para todas as versões, para que "rótulo inexistente" seja checável por script.
11. Como candidato, quero que o Contrato de saída (Rótulo + Justificativa literal) valha igual para v0 e para as versões seguintes, para que só a instrução mude entre versões e nunca a definição de erro.
12. Como candidato, quero que a Justificativa seja um trecho copiado literalmente da Transcrição, para que "Justificativa ancorada" seja verificável por substring, sem julgamento subjetivo.
13. Como candidato, quero que uma saída com Rótulo válido porém errado conte como Erro de acerto, independentemente da Justificativa.
14. Como candidato, quero que uma saída com Rótulo fora da lista conte como Alucinação do subtipo "rótulo inexistente".
15. Como candidato, quero que uma saída com Justificativa não ancorada conte como Alucinação do subtipo "justificativa não ancorada".
16. Como candidato, quero que uma mesma resposta possa contar em Erro de acerto e em Alucinação, para que as taxas sejam independentes.
17. Como candidato, quero que saída não interpretável (estrutura quebrada, campo faltando) conte como Violação de formato e **não** como Alucinação, para não inflar a queda entre versões com erro de parsing.
18. Como candidato, quero rodar uma versão de prompt sobre todo o Dataset e obter uma taxa por métrica (uma Rodada), para comparar versões.
19. Como candidato, quero repetir uma Rodada com a mesma versão e o mesmo Dataset (Repetição), para medir a variação do modelo.
20. Como candidato, quero que cada Chamada (versão de prompt, Transcrição, modelo → resposta) seja gravada em arquivo commitado, para que o Replay exista.
21. Como candidato, quero que o Replay recalcule as métricas só a partir das Chamadas gravadas, sem chamar modelo, para que qualquer pessoa reproduza o cálculo.
22. Como candidato, quero rodar a Reexecução contra o Gateway durante o desenvolvimento, para iterar sem custo.
23. Como candidato, quero que o formato de pedido e resposta siga o da API Anthropic desde o início, mesmo rodando contra o Gateway, para que trocar de provider não exija reescrever a lógica do eval.
24. Como candidato, quero uma implementação de provider Anthropic presente no código, mesmo sem poder exercitá-la, para honrar o requisito de "integração com API Anthropic" com afirmação limitada a "compatível".
25. Como candidato, quero que o teste contra a API real fique *skipped* quando não há chave, para que a suíte fique verde sem custo e sem fingir cobertura.
26. Como candidato, quero validar primeiro, antes de escrever qualquer prompt, que o Gateway serve um modelo compatível, para descobrir cedo se a premissa central é falsa.
27. Como candidato, quero que v0 seja um prompt ingênuo, para ter um ponto de partida honesto contra o qual medir.
28. Como candidato, quero que v1 seja uma melhoria documentada sobre v0, para ter o mínimo aceito (v0→v1) mesmo se a semana estourar.
29. Como candidato, quero tentar v2 se sobrar tempo, para fortalecer o case study sem invalidar o resultado se ela não sair.
30. Como candidato, quero um relatório que nomeie a "versão final" como a última versão concluída, para que o critério de sucesso seja inequívoco.
31. Como terceiro que clonou o repositório, quero saber a margem de variação declarada da Reexecução (em pontos percentuais de taxa), para saber quanto diferença entre Rodadas novas é ruído; o Replay bate exatamente.
32. Como candidato, quero que o uso do Gateway respeite os termos do provedor, para não depender de um modo de autenticação que os viole.

## Implementation Decisions

- **Uma seam de teste: a Rodada.** Entrada: versão de prompt + Dataset + provider. Saída: Chamadas gravadas + taxas por métrica. O Replay usa a mesma seam, com o provider substituído por "ler Chamadas gravadas". O provider é dependência injetada.
- **Módulos (nomes de conceito, não de arquivo):**
  - *Dataset*: Transcrições fictícias, cada uma com exatamente um Rótulo esperado, lista fechada de Rótulos e regra de desempate para intenção dupla escrita no próprio Dataset. Contém casos ambíguos e de intenção dupla.
  - *Versões de prompt*: v0 (ingênuo), v1 obrigatória, v2 alvo. v3 fora.
  - *Provider*: interface com **um único método** ("gerar"). Duas implementações: Gateway e Anthropic. O formato interno de pedido/resposta usa o vocabulário da API Anthropic (mensagens, papéis, parâmetros). Esta é a decisão difícil de reverter.
  - *Avaliador*: aplica o Contrato de saída a cada resposta e classifica em Erro de acerto, Alucinação (rótulo inexistente / justificativa não ancorada) e Violação de formato. As categorias são independentes, exceto que Violação de formato é excludente com Alucinação.
  - *Gravação e Replay*: cada Chamada grava versão de prompt, Transcrição, modelo e resposta. O Replay lê só esses registros.
  - *Relatório*: tabela por versão, variação entre Repetições, comparação queda vs variação, lista de Transcrições que mudaram, case study e a matriz "o que cada teste comprova".
- **Contrato de saída:** Rótulo da lista + Justificativa literal. Igual para todas as versões, v0 incluída.
- **Regra do enunciado sobre Anthropic:** o relatório só usa "Compatível com Anthropic". Não haverá chamada real à API oficial. O teste real existe e fica *skipped* sem chave.
- **Reprodutibilidade = Replay sobre resultados commitados.** Não "rodar de novo e obter o mesmo número".
- **Repetições (decisão do E4, fechando a pergunta em aberto do design):** v0 e a versão final são executadas em mais de uma Repetição, e o relatório registra a variação observada. O piso é 3 Repetições por versão (configurável; 3 é o padrão, porque com 2 a amplitude é frágil e a Reexecução no Gateway é gratuita). Se a queda não for maior que a variação, a conclusão é declarada inconclusiva e o Dataset ou as Repetições aumentam (premissa 2 da ideia).
- **Pré-condição, primeiro spike:** confirmar que o Gateway serve um modelo compatível com o formato Anthropic (premissa 1) e que o modo de autenticação usado respeita os termos do provedor. Nenhum prompt de produção é escrito antes disso.
- **Divergências em relação ao `ideia.md`, agora valendo nesta spec:** (a) sem chamada real à API oficial; (b) relatório afirma só "compatível com Anthropic"; (c) reprodutibilidade por Replay offline; (d) alvo v0→v2, mínimo v1.
- **Sem framework de orquestração de LLM.** Chamada direta no formato Anthropic.

## Testing Decisions

- **O que é um bom teste aqui:** exercita a Rodada e o Replay por fora e verifica o resultado observável (Chamadas gravadas e taxas por métrica), nunca funções internas do Avaliador. Cada teste nomeia a métrica ou o comportamento que comprova, para alimentar a matriz do README.
- **Seam testada:** a Rodada, com provider injetado. Os testes usam um provider falso com respostas roteirizadas, cobrindo: Rótulo válido e correto; Rótulo válido e errado (Erro de acerto); Rótulo fora da lista; Justificativa não ancorada; resposta que conta em Erro de acerto e Alucinação ao mesmo tempo; Violação de formato (e que ela **não** conta como Alucinação); Justificativa parafraseada (não ancorada).
- **Replay:** a partir de Chamadas gravadas de exemplo, produz exatamente as mesmas taxas que a Rodada que as gerou, e não chama nenhum provider.
- **Integração local com o Gateway:** roda só onde há Gateway; marcada para pular quando ausente. Comprova compatibilidade de formato, não validação da Anthropic.
- **Teste Anthropic real:** existe e é *skipped* sem chave, com o motivo visível na saída.
- **Prior art:** nenhum no repositório (não há código de aplicação ainda; só docs). O padrão de teste nasce nesta spec e segue o `/tdd` da esteira.

## Out of Scope

1. Triagem de URA e resumo de atendimento (critério de acerto subjetivo demais).
2. Produto real para agente de contact center (UX, interface operacional).
3. Framework de orquestração de LLM (LangChain e similares).
4. Múltiplos providers com fallback automático.
5. Fine-tuning do modelo.
6. Interface web para rodar o eval e CI automatizado do eval (o CI do repositório exigido no /ship não é afetado) (ideia futura separada, CAR-6).
7. Chamada real à API oficial da Anthropic (o candidato não pode pagar).
8. Streaming, consulta de capacidades do modelo, health check e endpoint de saúde do provider.
9. Aliases de modelo (`fast`, `balanced`, `reasoning`).
10. Gateway como serviço em compose/contêiner.
11. v3 como alvo (vira iteração seguinte).
12. Prometer piso numérico de melhora antes do experimento rodar.
13. Intervalos de confiança/bootstrap nas taxas (adiado para depois do primeiro corte).
14. Matriz de confusão por Rótulo (adiado para depois do primeiro corte).
15. Página HTML estática do relatório (pertence à ideia futura CAR-6).

## Further Notes

- **Critério de sucesso:** em até 1 semana a partir do início da implementação, existe queda **mensurável e documentada** na taxa de Alucinação entre v0 e a versão final (a última concluída; mínimo v1), medida no mesmo Dataset fixo. Sem percentual prometido. Um terceiro roda o Replay e chega aos mesmos números, sem chave e sem Gateway, e os números batem exatamente (o Replay é determinístico). A margem de variação declarada aplica-se apenas à Reexecução. O relatório nunca afirma validação contra a API oficial.
- **Primeiro corte:** v0→v1 ponta a ponta (Dataset pronto, eval rodando contra o Gateway, queda documentada). v2 é alvo. O teste Anthropic real, em vez de uma chamada real, fica presente e *skipped*.
- **Riscos abertos herdados:** (1) o Gateway pode não servir um modelo compatível, e o custo se falsa é perder o motivo de usá-lo; (2) 20-30 exemplos podem dar sinal ruidoso, e o custo se falsa é aumentar Dataset ou Repetições; (3) os termos do CLIProxyAPI sobre autenticação não foram confirmados.
- **Limite honesto do Replay:** prova que o cálculo da métrica é reproduzível, não que o modelo responderia igual hoje. O case study deve dizer isso.
- Detalhes de interface, classes e comandos de teste ficam para a ADR do E7 (a seam de provider: uma seam, um método), a partir das notas de arquitetura da ideia.
- Rastreabilidade: ideia original CAR-1; ideia futura separada CAR-6.

<!-- autoplan-accepted:ceo -->
- Lista de Transcrições que mudaram: o Relatório lista, por par de versões consecutivas, as Transcrições cujo Rótulo mudou, comparando a Repetição de índice 1 de cada versão. Uma resposta sem Rótulo válido (Violação de formato ou rótulo inexistente) é o estado "sem rótulo válido"; mudar de ou para ele conta como mudança. Verificação: o Replay imprime a lista a partir das Chamadas gravadas, e um teste da Rodada com provider falso confirma que uma Transcrição que muda de Rótulo (inclusive para "sem rótulo válido") aparece e uma que não muda não aparece.
- Regra de decisão da queda: queda = taxa média de Alucinação total nas Repetições de v0 menos a taxa média nas Repetições da versão final, em pontos percentuais. Variação = max(amplitude da Alucinação total entre as Repetições de v0, amplitude entre as Repetições da versão final); escolha conservadora, a maior das duas. A queda é "mensurável" somente se estritamente maior que a variação; caso contrário o resultado é inconclusivo, inclusive com variação zero e queda zero. "Alucinação total" conta uma resposta uma vez se ela tiver ao menos um subtipo; os subtipos aparecem separados na tabela. Verificação: o Replay calcula queda, variação e a comparação a partir das Chamadas gravadas e o Relatório as imprime; teste com Chamadas de exemplo cobre queda maior, igual e menor que a variação.
- Cada Chamada gravada registra também o índice da Repetição, o identificador da Rodada, o modelo e os parâmetros de geração (temperature e max_tokens), para o Replay agrupar por Repetição e o Relatório declarar as condições. Verificação: o Replay a partir de Chamadas de exemplo com 3 Repetições reproduz a variação calculada pela Rodada que as gerou.
- Piso de 3 Repetições por versão (configurável), para v0 e para a versão final; ver a edição de Implementation Decisions.
- Tabela de contagem por resposta, denominador sempre todas as Transcrições do Dataset: (a) Rótulo válido e correto, Justificativa ancorada: nenhuma métrica; (b) Rótulo válido e errado: Erro de acerto; (c) Rótulo válido e correto, Justificativa não ancorada: Alucinação (justificativa não ancorada); (d) Rótulo válido e errado, Justificativa não ancorada: Erro de acerto e Alucinação; (e) Rótulo fora da lista: Erro de acerto e Alucinação (rótulo inexistente); (f) saída não interpretável: apenas Violação de formato, sem Erro de acerto nem Alucinação. Justificativa ancorada = substring exata da Transcrição após normalizar espaços em branco consecutivos para um espaço e remover espaços nas pontas; maiúsculas e minúsculas contam como diferença. Verificação: um teste da Rodada por linha (a) a (f), com provider falso.
- Falhas: erro do provider (timeout, limite de taxa, erro HTTP) não vira Chamada nem resposta; a Rodada aborta com mensagem visível e não fica marcada como completa. O Replay recusa, com mensagem, uma Rodada com Chamadas faltando, corrompidas ou de Transcrição fora do Dataset. Verificação: testes com provider falso que falha e com Chamadas de exemplo truncadas.
- Honestidade do relatório: o Relatório gerado contém o texto do limite do Replay (prova o cálculo, não que o modelo responderia igual hoje) e nunca contém "validado contra a Anthropic". Verificação: teste sobre o texto do Relatório gerado.
- Edições de baseline aplicadas (ver o registro de edições abaixo): módulo Relatório passa a listar comparação queda vs variação e a lista de Transcrições que mudaram; a decisão de Repetições passa a fixar o piso de 3 e a regra "inconclusivo" (substitui "decidida no E5/E7" e "comparável"); o critério de sucesso e a história 33 passam a dizer que o Replay bate exatamente e a margem vale só para a Reexecução; o Fora de escopo ganha os itens 13 a 15 (bootstrap, matriz de confusão, página HTML) e o item 6 esclarece que o CI do repositório no /ship não é afetado.
<!-- /autoplan-accepted:ceo -->
## Review record

### CEO review (E5) — decisões provisórias

| ID | Contrato e evidência | Atual | Proposto | Status | Aprovação e escopo |
|---|---|---|---|---|---|
| C1 | v2 como alvo (história 29; Implementation Decisions "v2 alvo"; Further Notes) | v2 é alvo | v2 sai da spec, vira TODO; v0→v1 é o único entregável | RECUSADO pelo humano | v2 permanece como alvo; mínimo aceito continua v1. Motivo: decisão do humano, sem justificativa adicional registrada |
| C2 | Matriz "o que cada teste comprova" aparece no módulo *Relatório* e no README (história 4) | nos dois | só no README | RECUSADO pelo humano | a matriz permanece no módulo Relatório (e no README). Motivo: decisão do humano, sem justificativa adicional registrada |
| C3 | História 34 (vocabulário segue glossário) | é história | sai: não verificável, já é regra do CLAUDE.md/CONTEXT.md | ACEITO pelo humano; aplicado | História 34 removida da spec. Justificativa: não há como verificar por teste ou checklist que "o vocabulário segue o glossário"; a regra já vale para o projeto inteiro via CLAUDE.md e CONTEXT.md, então mantê-la como história só duplicava uma regra e deixava um critério não verificável, o que o gate do E4 proíbe |
| C4 | Histórias 3/32 e 5/31 duplicadas | 35 histórias | fundir duplicadas, sem mudar comportamento | ACEITO pelo humano; aplicado | 3 fundida com 32 e 5 fundida com 31; a spec passa de 35 para 32 histórias (as antigas 33 e 35 viram 31 e 32). Justificativa: 3 e 32 descreviam o mesmo comportamento (rodar um comando de Replay sem chave e sem Gateway e ver a tabela) e 5 e 31 o mesmo (o relatório separa o que o Replay prova do que a Reexecução mostra); duas histórias para um comportamento geravam dois testes/critérios para uma coisa só |
| A1 | História 2 (case study explica o que mudou) | sem lista de itens que mudaram | Relatório lista as Transcrições cuja classificação mudou entre versões | aprovado (auto-decisão P2, taste) | bloco `autoplan-accepted:ceo` |
| A2 | Critério "queda mensurável" sem regra de decisão (Further Notes; linha "inconclusiva" em Implementation Decisions) | ambíguo | queda só conta se maior que a variação observada entre Repetições | aprovado (auto-decisão P1, taste; deriva do texto existente) | bloco `autoplan-accepted:ceo` |
| Q1 | Efeito piso: se v0 quase não alucina, não há queda a medir. A spec não diz o que fazer | sem resposta | decisão humana: definir o que vale como sucesso nesse caso | ABERTA: o humano decide no gate final | nenhuma |

<!-- autoplan-baseline-edits:ceo {"sourceSha256":"a6c0a7da494367d4b524825663d62aa6592204b945f946b7c2b5e6665bd21ee9","replacements":[{"oldText":"tabela por versão, variação entre Repetições, case study e a matriz \"o que cada teste comprova\".","newText":"tabela por versão, variação entre Repetições, comparação queda vs variação, lista de Transcrições que mudaram, case study e a matriz \"o que cada teste comprova\"."},{"oldText":"A quantidade exata de Repetições é decidida no E5/E7 com base no que a Reexecução mostrar sobre a variância. Se as Repetições mostrarem variação comparável à queda entre versões, a conclusão é declarada como inconclusiva e o Dataset ou as Repetições aumentam (premissa 2 da ideia).","newText":"O piso é 3 Repetições por versão (configurável; 3 é o padrão, porque com 2 a amplitude é frágil e a Reexecução no Gateway é gratuita). Se a queda não for maior que a variação, a conclusão é declarada inconclusiva e o Dataset ou as Repetições aumentam (premissa 2 da ideia)."},{"oldText":"dentro da margem de variação declarada.","newText":"e os números batem exatamente (o Replay é determinístico). A margem de variação declarada aplica-se apenas à Reexecução."},{"oldText":"quero saber a margem de variação declarada, para saber quanto diferença entre números é ruído.","newText":"quero saber a margem de variação declarada da Reexecução (em pontos percentuais de taxa), para saber quanto diferença entre Rodadas novas é ruído; o Replay bate exatamente."},{"oldText":"Interface web para rodar o eval e CI automatizado (ideia futura separada, CAR-6).","newText":"Interface web para rodar o eval e CI automatizado do eval (o CI do repositório exigido no /ship não é afetado) (ideia futura separada, CAR-6)."},{"oldText":"12. Prometer piso numérico de melhora antes do experimento rodar.","newText":"12. Prometer piso numérico de melhora antes do experimento rodar.\n13. Intervalos de confiança/bootstrap nas taxas (adiado para depois do primeiro corte).\n14. Matriz de confusão por Rótulo (adiado para depois do primeiro corte).\n15. Página HTML estática do relatório (pertence à ideia futura CAR-6)."}]} -->

### Adições feitas por auto-decisão do /autoplan, sem aval prévio do humano (aprovar ou recusar cada uma no gate)

Nenhuma foi revertida. Todas já estão no texto da spec (seções indicadas). Status de todas: PENDENTE DE APROVAÇÃO.

| # | Adição | Onde está na spec |
|---|---|---|
| 1 | **A1:** o Relatório lista as Transcrições cujo Rótulo mudou entre versões consecutivas, comparando a Repetição de índice 1 de cada uma; resposta sem Rótulo válido é o estado "sem rótulo válido" | módulo Relatório (Implementation Decisions); bullet "Lista de Transcrições que mudaram" no fim de Further Notes |
| 2 | **A2:** regra de decisão da queda: queda = média das taxas de Alucinação total de v0 menos a média da versão final, em pontos percentuais; variação = max das amplitudes entre Repetições de v0 e da versão final; "mensurável" só se a queda for estritamente maior que a variação, senão inconclusivo (inclui variação e queda zero) | bullet "Regra de decisão da queda" no fim de Further Notes; parágrafo Repetições em Implementation Decisions |
| 3 | **P6:** piso de 3 Repetições por versão (configurável), no lugar de "decidida no E5/E7" | parágrafo Repetições em Implementation Decisions; bullet "Piso de 3 Repetições" |
| 4 | **Tabela de contagem a–f** por resposta (denominador = todas as Transcrições; regra de normalização da Justificativa ancorada; Violação de formato conta só nela mesma, nem Erro de acerto nem Alucinação) e um teste da Rodada por linha | bullet "Tabela de contagem por resposta" no fim de Further Notes |
| 5 | **Política de falha do provider:** erro do provider não vira Chamada; a Rodada aborta com mensagem e não fica completa; o Replay recusa Rodada com Chamadas faltando, corrompidas ou fora do Dataset | bullet "Falhas" no fim de Further Notes |
| 6 | **Campos novos da Chamada:** índice da Repetição, identificador da Rodada, modelo e parâmetros de geração (temperature, max_tokens) | bullet "Cada Chamada gravada registra também..." no fim de Further Notes |
| 7 | **Itens 13 a 15 do Fora de escopo:** bootstrap/intervalos de confiança, matriz de confusão por Rótulo, página HTML estática | seção Out of Scope, itens 13-15 |
| 8 | Teste do texto do Relatório: contém o limite do Replay e nunca contém "validado contra a Anthropic" | bullet "Honestidade do relatório" no fim de Further Notes |
| 9 | Esclarecimentos de texto: margem de variação vale só para a Reexecução (Replay bate exatamente), no critério de sucesso e na história 31 (antiga 33); item 6 do Fora de escopo esclarece que o CI do repositório no /ship não é afetado; módulo Relatório passa a listar comparação queda vs variação e a lista de mudanças | Further Notes (Critério de sucesso), User Stories, Out of Scope item 6, módulo Relatório |

Observação: os bullets "no fim de Further Notes" formam o registro de obrigações aceitas (bloco `autoplan-accepted:ceo`) e estão duplicados no texto onde a spec original já dizia algo parecido; a remoção de qualquer item recusado deve apagar as duas ocorrências.


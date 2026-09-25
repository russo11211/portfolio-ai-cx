<!-- /autoplan restore point: "~/.gstack/projects/russo11211-portfolio-ai-cx/claude-mattpocock-skills-setup-96cf28-autoplan-restore-20260923-204713.md" -->
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
7. Como recrutador técnico, quero ver o resultado de cada Repetição e a conclusão que a regra de melhora produz (piora, inconclusivo por efeito piso, melhora, inconclusivo ou não comparável), para julgar se a queda é confiável ou ruído.
8. Como recrutador técnico, quero abrir o Dataset e ver casos ambíguos e de intenção dupla com a regra de desempate escrita, para saber que v0 falha por motivo real e não por um problema trivial.
9. Como candidato, quero um Dataset fixo de 20-30 Transcrições fictícias, cada uma com exatamente um Rótulo esperado, para que as taxas sejam comparáveis entre Versões de prompt.
10. Como candidato, quero que a lista de Rótulos seja fechada e igual para todas as versões, para que "rótulo inexistente" seja checável por script.
11. Como candidato, quero que o Contrato de saída (Rótulo + Justificativa literal) valha igual para v0 e para as versões seguintes, para que só a instrução mude entre versões e nunca a definição de erro.
12. Como candidato, quero que a Justificativa seja um trecho copiado literalmente da Transcrição, para que "Justificativa ancorada" seja verificável por substring, sem julgamento subjetivo.
13. Como candidato, quero que uma saída com Rótulo válido porém errado conte como Erro de acerto, independentemente da Justificativa.
14. Como candidato, quero que uma saída com Rótulo fora da lista conte como Alucinação do subtipo "rótulo inexistente".
15. Como candidato, quero que uma saída com Justificativa não ancorada conte como Alucinação do subtipo "justificativa não ancorada".
16. Como candidato, quero que uma mesma resposta possa contar em Erro de acerto e em Alucinação, para que as taxas sejam independentes.
17. Como candidato, quero que saída não interpretável (estrutura quebrada, campo faltando) conte como Violação de formato e **não** como Alucinação, para não inflar a queda entre versões com erro de parsing. [Nota de 2026-09-25, texto anterior mantido: a linha (f) da tabela de contagem e o módulo Avaliador estabelecem que Violação de formato também não conta como Erro de acerto.]
18. Como candidato, quero rodar uma versão de prompt sobre todo o Dataset e obter uma taxa por métrica (uma Rodada), para comparar versões. [Nota de 2026-09-25, texto anterior mantido: definição fechada: uma Rodada é uma versão de prompt sobre o Dataset inteiro com N Repetições (passagens completas pelo Dataset), e o manifesto é da Rodada; um experimento é o conjunto de Rodadas (v0 até a versão final) sobre o mesmo Dataset e que o Relatório identifica.]
19. Como candidato, quero repetir uma Rodada com a mesma versão e o mesmo Dataset (Repetição), para medir a variação do modelo. [Nota de 2026-09-25, texto anterior mantido: toda versão tem no mínimo 3 Repetições; a Repetição é uma passagem completa pelo Dataset dentro da mesma Rodada (ver a nota da história 18).]
20. Como candidato, quero que cada Chamada (versão de prompt, Transcrição, modelo → resposta) seja gravada em arquivo commitado, para que o Replay exista.
21. Como candidato, quero que o Replay recalcule as métricas só a partir das Chamadas gravadas, sem chamar modelo, para que qualquer pessoa reproduza o cálculo.
22. Como candidato, quero rodar a Reexecução contra o Gateway durante o desenvolvimento, para iterar sem custo.
23. Como candidato, quero que o formato de pedido e resposta siga o da API Anthropic desde o início, mesmo rodando contra o Gateway, para que trocar de provider não exija reescrever a lógica do eval.
24. Como candidato, quero uma implementação de provider Anthropic presente no código, mesmo sem poder exercitá-la, para honrar o requisito de "integração com API Anthropic" com afirmação limitada a "compatível".
25. Como candidato, quero que o teste contra a API real só rode com habilitação explícita além da chave e fique *skipped* sem ela, para que a suíte ordinária fique verde, offline e sem custo, mesmo com uma chave no ambiente, e sem fingir cobertura.
26. Como candidato, quero validar primeiro, antes de escrever qualquer prompt, que o Gateway serve um modelo compatível, para descobrir cedo se a premissa central é falsa.
27. Como candidato, quero que v0 seja um prompt ingênuo, para ter um ponto de partida honesto contra o qual medir.
28. Como candidato, quero que v1 seja uma tentativa documentada de melhoria sobre v0, para ter o mínimo aceito (v0→v1) mesmo se a semana estourar, qualquer que seja o resultado.
29. Como candidato, quero tentar v2 se sobrar tempo, para fortalecer o case study sem invalidar o resultado se ela não sair.
30. Como candidato, quero um relatório que nomeie a "versão final" como a última versão concluída, para que o critério de sucesso seja inequívoco.
31. Como terceiro que clonou o repositório, quero saber a margem de variação declarada da Reexecução (em pontos percentuais de taxa), para saber quanto diferença entre Rodadas novas é ruído; o Replay bate exatamente. [Nota de 2026-09-25, texto anterior mantido: a margem é apenas descritiva da Reexecução e não decide nenhum veredito do Relatório.]
32. Como candidato, quero que o uso do Gateway respeite os termos do provedor, para não depender de um modo de autenticação que os viole.

## Implementation Decisions

- **Uma seam de teste: a Rodada.** Entrada: versão de prompt + Dataset + provider. Saída: Chamadas gravadas + taxas por métrica. O Replay usa a mesma seam, com o provider substituído por "ler Chamadas gravadas". O provider é dependência injetada.
- **Módulos (nomes de conceito, não de arquivo):**
  - *Dataset*: Transcrições fictícias, cada uma com exatamente um Rótulo esperado, lista fechada de Rótulos e regra de desempate para intenção dupla escrita no próprio Dataset. Contém casos ambíguos e de intenção dupla.
  - *Versões de prompt*: v0 (ingênuo), v1 obrigatória, v2 alvo. v3 fora. v0 é ingênuo no conteúdo (sem exemplos nem estratégia), mas declara o Contrato de saída de forma explícita: pede um objeto JSON puro com Rótulo e Justificativa. Antes de congelar o Dataset, um piloto de 5 a 10 Transcrições do rascunho, com 1 Repetição de v0, registra a taxa de Violação de formato e de Alucinação, e a decisão de congelar ou de ajustar o Dataset ou v0 fica por escrito.
  - *Provider*: interface com **um único método** ("gerar"). Duas implementações: Gateway e Anthropic. O formato interno de pedido/resposta usa o vocabulário da API Anthropic (mensagens, papéis, parâmetros). Esta é a decisão difícil de reverter. O resultado do método é normalizado (texto, motivo de parada e o modelo devolvido pela resposta). Não há retentativa automática: erro do provider aborta a Rodada.
  - *Avaliador*: aplica o Contrato de saída a cada resposta e classifica em Erro de acerto, Alucinação (rótulo inexistente / justificativa não ancorada) e Violação de formato. Erro de acerto e Alucinação são independentes; Violação de formato é excludente com as duas (linha (f) da tabela de contagem e história 17).
  - *Gravação e Replay*: cada Chamada grava versão de prompt, Transcrição, modelo e resposta, sem credenciais nem cabeçalhos de autenticação. Cada Rodada tem um manifesto versionado (versão do esquema) com o hash do texto do prompt, o hash do Dataset, os parâmetros efetivos, o número esperado de Chamadas (Transcrições × Repetições) e o estado (iniciada, completa ou abortada). A identidade de uma Chamada é (Rodada, hash do prompt, Transcrição, Repetição) e é única. A escrita é atômica: a Rodada só passa a existir para o Replay quando o manifesto é gravado como completo, e uma Rodada existente nunca é sobrescrita. O Replay lê só esses registros e recusa, com mensagem, divergência de hash ou de versão de esquema, Chamada duplicada, extra ou faltando, e Rodada não completa.
  - *Relatório*: tabela por versão, resultado de cada Repetição, lista de TODAS as Rodadas do repositório (com identificador e estado, inclusive abortadas e de experimentos anteriores), veredito pela regra de melhora só para v0 × versão final (piora, inconclusivo por efeito piso, melhora, inconclusivo ou não comparável) com os pares intermediários como informativos e sem veredito, lista ilustrativa de Transcrições que mudaram, modelo (como devolvido pela resposta) e data das Chamadas, o resultado declarado como exploratório, case study com um memo curto de decisão (por que este problema, o que foi cortado, o que as métricas não afirmam) e a matriz "o que cada teste comprova".
- **Contrato de saída:** um objeto JSON com dois campos de texto, Rótulo (da lista) e Justificativa (literal). Igual para todas as versões, v0 incluída. O parser é estrito: não remove code fence nem prosa em volta, e campos extras são ignorados. O Rótulo é comparado depois de aparar espaços nas pontas, e maiúsculas e minúsculas contam como diferença. Resposta vazia, truncada (o Provider informa o motivo de parada), recusa, JSON inválido, campo faltando ou de tipo errado, e Justificativa vazia ou só de espaços são saída não interpretável (Violação de formato). "Ancoragem literal" é o nome da métrica: ela prova que o trecho existe na Transcrição, não que sustenta o Rótulo. O motivo de parada normalizado é um vocabulário fechado (fim normal, truncada, recusa, outro), mapeado dentro de cada provider e nunca no Avaliador; os dois providers passam pelo mesmo teste de contrato com um transporte falso.
- **Regra do enunciado sobre Anthropic:** o relatório só usa "Compatível com Anthropic". Não haverá chamada real à API oficial. O teste real existe, exige habilitação explícita além da chave e fica *skipped* sem ela.
- **Reprodutibilidade = Replay sobre resultados commitados.** Não "rodar de novo e obter o mesmo número".
- **Repetições (decisão do E4, fechando a pergunta em aberto do design):** toda versão, inclusive as intermediárias, é executada em pelo menos 3 Repetições, e o relatório registra as contagens de cada uma. O mínimo é 3 (configurável para cima; 3 é o padrão, porque com 2 a amplitude é frágil e a Reexecução no Gateway é gratuita), e a Rodada e o Replay recusam menos de 3. A conclusão segue a regra de melhora de Further Notes; aumentar o Dataset ou as Repetições depois de ver o resultado cria um novo experimento identificado e exige rodar de novo v0 e a versão final (premissa 2 da ideia).
- **Pré-condição, primeiro spike:** confirmar que o Gateway serve um modelo compatível com o formato Anthropic (premissa 1) e que o modo de autenticação usado respeita os termos do provedor. Nenhum prompt de produção é escrito antes disso. O primeiro passo do spike é o gate de termos de uso, decidido por escrito antes de qualquer código do spike: se o modo de autenticação do Gateway violar os termos do provedor, é no-go. O spike tem prazo de 1 dia de trabalho e confere o nome do modelo devolvido, o motivo de parada e a temperatura efetiva. O plano B, com modelo e provedor nomeados na própria decisão go/no-go antes de o spike começar, é outro provider sob a mesma seam e é uma exceção declarada à restrição de passar pelo Gateway; Plano B PENDENTE: o humano escolheu em 2026-09-25 só a categoria (modelo open-weights hospedado com camada gratuita); o modelo e o provedor específicos são decisão do humano, com prazo antes do início do spike, no E7, e são exigência da ADR do E7; os limites de taxa dessa camada, que podem abortar Rodadas (não há retentativa), entram nessa decisão. Se o Gateway falhar (modelo incompatível ou termos violados), a decisão go/no-go é escrita e o trabalho de prompts só começa com o plano B aceito por escrito; gravações sintéticas nunca contam como evidência de modelo e o case study passa a falar do método, não do modelo.
- **Divergências em relação ao `ideia.md`, agora valendo nesta spec:** (a) sem chamada real à API oficial; (b) relatório afirma só "compatível com Anthropic"; (c) reprodutibilidade por Replay offline; (d) alvo v0→v2, mínimo v1.
- **Sem framework de orquestração de LLM.** Chamada direta no formato Anthropic.

## Testing Decisions

- **O que é um bom teste aqui:** exercita a Rodada e o Replay por fora e verifica o resultado observável (Chamadas gravadas e taxas por métrica), nunca funções internas do Avaliador. Cada teste nomeia a métrica ou o comportamento que comprova, para alimentar a matriz do README.
- **Seam testada:** a Rodada, com provider injetado. Os testes usam um provider falso com respostas roteirizadas, cobrindo: Rótulo válido e correto; Rótulo válido e errado (Erro de acerto); Rótulo fora da lista; Justificativa não ancorada; resposta que conta em Erro de acerto e Alucinação ao mesmo tempo; Violação de formato (e que ela **não** conta como Alucinação nem como Erro de acerto); Justificativa parafraseada (não ancorada). Cada teste compara com contagens calculadas à mão, não com a saída de outro cálculo do próprio código.
- **Replay:** a partir de Chamadas gravadas de exemplo, produz exatamente as mesmas taxas que a Rodada que as gerou, e não chama nenhum provider.
- **Integração local com o Gateway:** só roda com habilitação explícita; sem habilitação é marcada para pular, e habilitada sem Gateway falha com a causa e o passo de correção. Comprova compatibilidade de formato, não validação da Anthropic.
- **Teste Anthropic real:** existe, exige habilitação explícita além da chave e é *skipped* sem ela, com o motivo visível na saída; neste plano fica desabilitado. A suíte ordinária e o Replay rodam sempre offline, mesmo com uma chave no ambiente. O código do provider Anthropic tem teste de montagem do pedido com transporte falso.
- **Dataset:** um teste valida IDs únicos, um Rótulo esperado por Transcrição, Rótulo dentro da lista fechada, 20 a 30 Transcrições, ao menos uma Transcrição por Rótulo, regra de desempate presente, e que nenhuma Transcrição do Dataset aparece nos exemplos dos prompts.
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

- **Critério de sucesso:** em até 1 semana a partir do início da implementação, existe o ciclo medir, iterar e concluir documentado: v0 medida e ao menos v1 (a versão final é a última concluída), no mesmo Dataset fixo, com a conclusão registrada no Relatório. Resultado nulo, inconclusivo ou piora é válido e cumpre o critério. Sem percentual prometido. Um terceiro roda o Replay e chega aos mesmos números, sem chave e sem Gateway, e os números batem exatamente (o Replay é determinístico). A margem de variação declarada aplica-se apenas à Reexecução. O relatório nunca afirma validação contra a API oficial e declara o resultado como exploratório (o mesmo Dataset serve para desenvolver e para medir).
- **Primeiro corte:** v0→v1 ponta a ponta (Dataset pronto, eval rodando contra o Gateway, conclusão documentada). v2 é alvo. O teste Anthropic real, em vez de uma chamada real, fica presente e *skipped*.
- **Riscos abertos herdados:** (1) o Gateway pode não servir um modelo compatível, e o custo se falsa é perder o motivo de usá-lo; (2) 20-30 exemplos podem dar sinal ruidoso, e o custo se falsa é aumentar Dataset ou Repetições; (3) os termos do CLIProxyAPI sobre autenticação não foram confirmados.
- **Limite honesto do Replay:** prova que o cálculo da métrica é reproduzível, não que o modelo responderia igual hoje. O case study deve dizer isso.
- Detalhes de interface, classes e comandos de teste ficam para a ADR do E7 (a seam de provider: uma seam, um método), a partir das notas de arquitetura da ideia.
- Rastreabilidade: ideia original CAR-1; ideia futura separada CAR-6.

<!-- autoplan-accepted:ceo -->
- Lista de Transcrições que mudaram (ilustrativa): o Relatório lista, por par de versões consecutivas, as Transcrições cujo Rótulo mudou, comparando a Repetição de índice 1 de cada versão, e a rotula como ilustrativa, pois não explica a conclusão, que usa todas as Repetições. Uma resposta sem Rótulo válido (Violação de formato ou rótulo inexistente) é o estado "sem rótulo válido"; mudar de ou para ele conta como mudança. Verificação: o Replay imprime a lista a partir das Chamadas gravadas, e um teste da Rodada com provider falso confirma que uma Transcrição que muda de Rótulo (inclusive para "sem rótulo válido") aparece e uma que não muda não aparece, e que o rótulo "ilustrativa" está no texto.
- Regra de melhora (substitui a regra de decisão da queda contra a variação): o veredito vale só para v0 × versão final; os pares intermediários (por exemplo v0→v1 e v1→v2) aparecem no Relatório como informativos, com as contagens de cada Repetição e sem veredito. Toda versão tem no mínimo 3 Repetições. "Alucinação total" conta uma Transcrição uma vez se a resposta tiver ao menos um subtipo (os subtipos aparecem separados na tabela); "acertos" são as Transcrições com Rótulo válido e correto (linhas (a) e (c) da tabela de contagem). Pré-condição de comparabilidade: v0 e a versão final foram executadas com o mesmo modelo devolvido pela resposta e os mesmos parâmetros de geração (temperature e max_tokens); se diferirem, o veredito é "não comparável" e o Relatório mostra a diferença, sem aplicar as condições abaixo. O veredito segue esta ordem de precedência e para na primeira condição que valer: (1) piora: se a soma da Alucinação total ao longo das Repetições da versão final, multiplicada pelo número de Repetições de v0, for maior que a soma da Alucinação total ao longo das Repetições de v0, multiplicada pelo número de Repetições da versão final (comparação das médias só com contagens inteiras, sem divisão), o veredito é "piora"; (2) efeito piso, só se não houve piora: se em qualquer Repetição de v0 a Alucinação total for de no máximo 1 Transcrição, o veredito é "inconclusivo por efeito piso", o Relatório mostra o Erro de acerto como métrica secundária e não declara melhora; (3) melhora: só se, ao mesmo tempo, (a) em todas as Repetições a queda da Alucinação total for de pelo menos 2 Transcrições, lida no pior caso: (menor Alucinação total entre as Repetições de v0) menos (maior Alucinação total entre as Repetições da versão final) maior ou igual a 2, (b) a Violação de formato não aumentar, lida no pior caso: (maior Violação de formato entre as Repetições da versão final) menor ou igual a (menor Violação de formato entre as Repetições de v0), e (c) a guarda de acurácia: (menor total de acertos entre as Repetições da versão final) maior ou igual a (maior total de acertos entre as Repetições de v0); (4) qualquer outro caso é "inconclusivo". Todas as comparações usam contagens inteiras de Transcrições, e o Relatório imprime as contagens de cada Repetição e o veredito. Verificação: o Replay calcula o veredito a partir das Chamadas gravadas e o Relatório o imprime; testes com Chamadas de exemplo e contagens calculadas à mão cobrem modelo ou parâmetros diferentes entre v0 e a versão final ("não comparável"), melhora, queda de 1 Transcrição, queda de 2 em uma só Repetição, Violação de formato que aumenta, guarda de acurácia que falha (a Alucinação cai e os acertos caem), efeito piso, piora, efeito piso e piora ao mesmo tempo (vence a piora), Repetições com variação zero, Repetições em número desigual entre v0 e a versão final, e a recusa de uma versão com menos de 3 Repetições.
- Critério de sucesso e conclusão: cumprir o critério é ter o ciclo medir, iterar e concluir documentado no Relatório; resultado nulo, inconclusivo, inconclusivo por efeito piso ou piora é válido. O Relatório declara o resultado como exploratório. O veredito vale só para v0 × versão final. Verificação: teste sobre o texto do Relatório gerado confirma a conclusão impressa e a palavra "exploratório".
- Cada Chamada gravada registra também o índice da Repetição, o identificador da Rodada, o modelo devolvido pela resposta, o motivo de parada e os parâmetros de geração (temperature e max_tokens), sem credenciais nem cabeçalhos de autenticação, para o Replay agrupar por Repetição e o Relatório declarar as condições. Verificação: o Replay a partir de Chamadas de exemplo com 3 Repetições reproduz a contagem por Repetição calculada pela Rodada que as gerou, e um teste confirma que nenhuma Chamada gravada contém credencial ou cabeçalho de autenticação.
- Mínimo de 3 Repetições para toda versão, inclusive as intermediárias (configurável para cima; 3 é o padrão); a Rodada e o Replay recusam, com mensagem, uma versão com menos de 3 Repetições; ver a edição de Implementation Decisions. Verificação: teste que recusa 2 Repetições em v0, na versão final e numa versão intermediária.
- Manifesto e integridade da Rodada: cada Rodada tem manifesto versionado com versão do esquema, hash do texto do prompt, hash do Dataset, parâmetros efetivos, número esperado de Chamadas e estado (iniciada, completa, abortada); a identidade de uma Chamada é (Rodada, hash do prompt, Transcrição, Repetição) e é única; a escrita é atômica e uma Rodada existente nunca é sobrescrita. O Replay só aceita Rodada completa e recusa, com mensagem, divergência de hash ou de esquema, Chamada duplicada, extra ou faltando. Verificação: testes de adulteração (prompt ou Dataset alterado depois da gravação), de Chamada duplicada, extra e faltando, de versão de esquema desconhecida e de tentativa de sobrescrever uma Rodada.
- Tabela de contagem por resposta, denominador sempre todas as Transcrições do Dataset: (a) Rótulo válido e correto, Justificativa ancorada: nenhuma métrica; (b) Rótulo válido e errado: Erro de acerto; (c) Rótulo válido e correto, Justificativa não ancorada: Alucinação (justificativa não ancorada); (d) Rótulo válido e errado, Justificativa não ancorada: Erro de acerto e Alucinação; (e) Rótulo fora da lista: Erro de acerto e Alucinação (rótulo inexistente); (f) saída não interpretável (resposta vazia, truncada, recusa, JSON inválido, campo faltando ou de tipo errado, Justificativa vazia ou só de espaços, ou JSON dentro de code fence ou com prosa em volta): apenas Violação de formato, sem Erro de acerto nem Alucinação. Justificativa ancorada (comparada sobre o texto já decodificado do JSON, isto é, com escapes como \n e \" convertidos nos caracteres que representam) = substring exata da Transcrição após normalização Unicode NFC, troca de espaço não separável por espaço, normalização de espaços em branco consecutivos para um espaço e remoção de espaços nas pontas; maiúsculas e minúsculas contam como diferença. Verificação: um teste da Rodada por linha (a) a (f) e um por caso listado em (f), com provider falso e contagens calculadas à mão.
- Falhas e Rodada parcial: erro do provider (timeout, limite de taxa, erro HTTP) não vira Chamada nem resposta; a Rodada aborta com mensagem visível (problema, causa provável e próximo passo, com a Rodada e a Transcrição), é registrada como abortada e não é retomável: os arquivos dela nunca são aceitos pelo Replay e recomeçar cria uma nova Rodada. Não há retentativa automática. O Replay recusa, com mensagem, uma Rodada com Chamadas faltando, corrompidas, duplicadas ou de Transcrição fora do Dataset. A Rodada tem timeout por chamada (o valor fica na ADR do E7) e reporta o progresso (Chamada N de M); a mensagem de aborto traz o comando exato para começar uma Rodada nova e avisa que as Chamadas já concluídas serão repetidas. Verificação: testes com provider falso que falha e com Chamadas de exemplo truncadas, um teste em que uma Rodada abortada não deixa nada que o Replay aceite, e um teste da mensagem de aborto (comando de reinício e aviso) e do texto de progresso.
- Plano B do spike do Gateway: o primeiro passo é o gate de termos de uso, decidido por escrito antes de qualquer código do spike: se o modo de autenticação do Gateway violar os termos do provedor, é no-go. O spike tem prazo de 1 dia de trabalho, termina com uma decisão go/no-go escrita antes do primeiro prompt e confere o nome do modelo devolvido, o motivo de parada e a temperatura efetiva. O plano B, com modelo e provedor nomeados na própria decisão go/no-go antes de o spike começar, é outro provider sob a mesma seam e é uma exceção declarada à restrição de passar pelo Gateway; Plano B PENDENTE: o humano escolheu em 2026-09-25 só a categoria (modelo open-weights hospedado com camada gratuita); o modelo e o provedor específicos são decisão do humano, com prazo antes do início do spike, no E7, e são exigência da ADR do E7; os limites de taxa dessa camada, que podem abortar Rodadas (não há retentativa), entram nessa decisão. Se o Gateway não servir modelo compatível ou violar os termos, o trabalho de prompts só começa com o plano B aceito por escrito; gravações sintéticas nunca contam como evidência de modelo. Verificação (manual): a decisão go/no-go, com o gate de termos, o plano B nomeado e as três conferências do spike, existe por escrito antes do primeiro arquivo de prompt de produção.
- Testes offline e opt-in: a suíte ordinária e o Replay rodam sempre offline, com a chave de API presente ou não e sem rede; o teste da API real e a integração com o Gateway só rodam com habilitação explícita, e habilitados sem condição de rodar falham com a causa e o passo de correção. O provider Anthropic tem teste de montagem do pedido com transporte falso. Verificação: suíte verde com uma chave no ambiente e com a rede negada.
- Validação do Dataset: um teste valida IDs únicos, um Rótulo esperado por Transcrição, Rótulo dentro da lista fechada, 20 a 30 Transcrições, ao menos uma Transcrição por Rótulo, regra de desempate presente, e que nenhuma Transcrição do Dataset aparece nos exemplos dos prompts.
- Honestidade do relatório: o Relatório gerado, o README do produto e o case study contêm o texto do limite do Replay (prova o cálculo, não que o modelo responderia igual hoje) e nunca contêm "validado contra a Anthropic". Verificação: teste sobre o texto inteiro dos três arquivos commitados.
- Modelo, data e memo: o Relatório declara o modelo exatamente como devolvido pela resposta e a data das Chamadas, e o case study traz um memo curto de decisão (por que este problema, o que foi cortado, o que as métricas não afirmam). Verificação (manual): o Relatório e o case study contêm o modelo devolvido, a data e o memo.
- Contrato explícito em v0 e piloto: v0 é ingênuo no conteúdo (sem exemplos nem estratégia de classificação), mas declara o Contrato de saída de forma explícita, pedindo um objeto JSON puro com Rótulo e Justificativa; o parser estrito e a linha (f) não mudam. Antes de congelar o Dataset, um piloto de 5 a 10 Transcrições do rascunho, com 1 Repetição de v0, registra a taxa de Violação de formato e de Alucinação, e a decisão de congelar ou de ajustar o Dataset ou v0 fica por escrito. Verificação (manual): o prompt de v0 pede JSON puro e o registro do piloto com a decisão existe antes de o Dataset ser congelado.
- Relatório com todas as Rodadas: o Relatório lista todas as Rodadas do repositório, com identificador e estado (completa, abortada, iniciada), inclusive as de experimentos anteriores; o veredito usa somente as Rodadas do experimento identificado, e os pares intermediários aparecem como informativos. Descartar uma Rodada ruim não a apaga nem a sobrescreve: o experimento identificado lista explicitamente as Rodadas que entram, e as demais aparecem no Relatório como "fora do experimento" com o motivo escrito. Verificação: teste do Relatório com Rodadas completas, abortada, de experimento anterior e uma completa descartada com motivo, confirmando que todas aparecem, que só as do experimento entram no veredito e que a descartada aparece como "fora do experimento" com o motivo.
- Motivo de parada normalizado: vocabulário fechado (fim normal, truncada, recusa, outro), mapeado dentro de cada provider e nunca no Avaliador; truncada e recusa são Violação de formato pela linha (f). Verificação: teste de contrato que roda o provider do Gateway e o Anthropic sobre o mesmo transporte falso e exige o mesmo resultado normalizado.
- Edições de baseline aplicadas (ver os registros de edições no Review record; rodada 4 de 2026-09-25: precedência piora, piso, melhora, inconclusivo; plano B pendente, só a categoria escolhida; comparabilidade de modelo e parâmetros; decodificação do JSON na ancoragem; definição de Rodada, Repetição e experimento; descarte de Rodada): módulo Relatório com todas as Rodadas e veredito só para v0 × versão final; história 28 como tentativa documentada; notas de 2026-09-25 nas histórias 17, 18, 19 e 31; Regra do enunciado sobre Anthropic alinhada ao opt-in; v0 com contrato JSON explícito e piloto; mínimo de 3 Repetições para toda versão; gate de termos e plano B nomeado no spike; vocabulário fechado de motivo de parada.
<!-- /autoplan-accepted:ceo -->
## Review record

<!-- autoplan-accepted:ceo -->
- Lista de Transcrições que mudaram (ilustrativa): o Relatório lista, por par de versões consecutivas, as Transcrições cujo Rótulo mudou, comparando a Repetição de índice 1 de cada versão, e a rotula como ilustrativa, pois não explica a conclusão, que usa todas as Repetições. Uma resposta sem Rótulo válido (Violação de formato ou rótulo inexistente) é o estado "sem rótulo válido"; mudar de ou para ele conta como mudança. Verificação: o Replay imprime a lista a partir das Chamadas gravadas, e um teste da Rodada com provider falso confirma que uma Transcrição que muda de Rótulo (inclusive para "sem rótulo válido") aparece e uma que não muda não aparece, e que o rótulo "ilustrativa" está no texto.
- Regra de melhora (substitui a regra de decisão da queda contra a variação): o veredito vale só para v0 × versão final; os pares intermediários (por exemplo v0→v1 e v1→v2) aparecem no Relatório como informativos, com as contagens de cada Repetição e sem veredito. Toda versão tem no mínimo 3 Repetições. "Alucinação total" conta uma Transcrição uma vez se a resposta tiver ao menos um subtipo (os subtipos aparecem separados na tabela); "acertos" são as Transcrições com Rótulo válido e correto (linhas (a) e (c) da tabela de contagem). Pré-condição de comparabilidade: v0 e a versão final foram executadas com o mesmo modelo devolvido pela resposta e os mesmos parâmetros de geração (temperature e max_tokens); se diferirem, o veredito é "não comparável" e o Relatório mostra a diferença, sem aplicar as condições abaixo. O veredito segue esta ordem de precedência e para na primeira condição que valer: (1) piora: se a soma da Alucinação total ao longo das Repetições da versão final, multiplicada pelo número de Repetições de v0, for maior que a soma da Alucinação total ao longo das Repetições de v0, multiplicada pelo número de Repetições da versão final (comparação das médias só com contagens inteiras, sem divisão), o veredito é "piora"; (2) efeito piso, só se não houve piora: se em qualquer Repetição de v0 a Alucinação total for de no máximo 1 Transcrição, o veredito é "inconclusivo por efeito piso", o Relatório mostra o Erro de acerto como métrica secundária e não declara melhora; (3) melhora: só se, ao mesmo tempo, (a) em todas as Repetições a queda da Alucinação total for de pelo menos 2 Transcrições, lida no pior caso: (menor Alucinação total entre as Repetições de v0) menos (maior Alucinação total entre as Repetições da versão final) maior ou igual a 2, (b) a Violação de formato não aumentar, lida no pior caso: (maior Violação de formato entre as Repetições da versão final) menor ou igual a (menor Violação de formato entre as Repetições de v0), e (c) a guarda de acurácia: (menor total de acertos entre as Repetições da versão final) maior ou igual a (maior total de acertos entre as Repetições de v0); (4) qualquer outro caso é "inconclusivo". Todas as comparações usam contagens inteiras de Transcrições, e o Relatório imprime as contagens de cada Repetição e o veredito. Verificação: o Replay calcula o veredito a partir das Chamadas gravadas e o Relatório o imprime; testes com Chamadas de exemplo e contagens calculadas à mão cobrem modelo ou parâmetros diferentes entre v0 e a versão final ("não comparável"), melhora, queda de 1 Transcrição, queda de 2 em uma só Repetição, Violação de formato que aumenta, guarda de acurácia que falha (a Alucinação cai e os acertos caem), efeito piso, piora, efeito piso e piora ao mesmo tempo (vence a piora), Repetições com variação zero, Repetições em número desigual entre v0 e a versão final, e a recusa de uma versão com menos de 3 Repetições.
- Critério de sucesso e conclusão: cumprir o critério é ter o ciclo medir, iterar e concluir documentado no Relatório; resultado nulo, inconclusivo, inconclusivo por efeito piso ou piora é válido. O Relatório declara o resultado como exploratório. O veredito vale só para v0 × versão final. Verificação: teste sobre o texto do Relatório gerado confirma a conclusão impressa e a palavra "exploratório".
- Cada Chamada gravada registra também o índice da Repetição, o identificador da Rodada, o modelo devolvido pela resposta, o motivo de parada e os parâmetros de geração (temperature e max_tokens), sem credenciais nem cabeçalhos de autenticação, para o Replay agrupar por Repetição e o Relatório declarar as condições. Verificação: o Replay a partir de Chamadas de exemplo com 3 Repetições reproduz a contagem por Repetição calculada pela Rodada que as gerou, e um teste confirma que nenhuma Chamada gravada contém credencial ou cabeçalho de autenticação.
- Mínimo de 3 Repetições para toda versão, inclusive as intermediárias (configurável para cima; 3 é o padrão); a Rodada e o Replay recusam, com mensagem, uma versão com menos de 3 Repetições; ver a edição de Implementation Decisions. Verificação: teste que recusa 2 Repetições em v0, na versão final e numa versão intermediária.
- Manifesto e integridade da Rodada: cada Rodada tem manifesto versionado com versão do esquema, hash do texto do prompt, hash do Dataset, parâmetros efetivos, número esperado de Chamadas e estado (iniciada, completa, abortada); a identidade de uma Chamada é (Rodada, hash do prompt, Transcrição, Repetição) e é única; a escrita é atômica e uma Rodada existente nunca é sobrescrita. O Replay só aceita Rodada completa e recusa, com mensagem, divergência de hash ou de esquema, Chamada duplicada, extra ou faltando. Verificação: testes de adulteração (prompt ou Dataset alterado depois da gravação), de Chamada duplicada, extra e faltando, de versão de esquema desconhecida e de tentativa de sobrescrever uma Rodada.
- Tabela de contagem por resposta, denominador sempre todas as Transcrições do Dataset: (a) Rótulo válido e correto, Justificativa ancorada: nenhuma métrica; (b) Rótulo válido e errado: Erro de acerto; (c) Rótulo válido e correto, Justificativa não ancorada: Alucinação (justificativa não ancorada); (d) Rótulo válido e errado, Justificativa não ancorada: Erro de acerto e Alucinação; (e) Rótulo fora da lista: Erro de acerto e Alucinação (rótulo inexistente); (f) saída não interpretável (resposta vazia, truncada, recusa, JSON inválido, campo faltando ou de tipo errado, Justificativa vazia ou só de espaços, ou JSON dentro de code fence ou com prosa em volta): apenas Violação de formato, sem Erro de acerto nem Alucinação. Justificativa ancorada (comparada sobre o texto já decodificado do JSON, isto é, com escapes como \n e \" convertidos nos caracteres que representam) = substring exata da Transcrição após normalização Unicode NFC, troca de espaço não separável por espaço, normalização de espaços em branco consecutivos para um espaço e remoção de espaços nas pontas; maiúsculas e minúsculas contam como diferença. Verificação: um teste da Rodada por linha (a) a (f) e um por caso listado em (f), com provider falso e contagens calculadas à mão.
- Falhas e Rodada parcial: erro do provider (timeout, limite de taxa, erro HTTP) não vira Chamada nem resposta; a Rodada aborta com mensagem visível (problema, causa provável e próximo passo, com a Rodada e a Transcrição), é registrada como abortada e não é retomável: os arquivos dela nunca são aceitos pelo Replay e recomeçar cria uma nova Rodada. Não há retentativa automática. O Replay recusa, com mensagem, uma Rodada com Chamadas faltando, corrompidas, duplicadas ou de Transcrição fora do Dataset. A Rodada tem timeout por chamada (o valor fica na ADR do E7) e reporta o progresso (Chamada N de M); a mensagem de aborto traz o comando exato para começar uma Rodada nova e avisa que as Chamadas já concluídas serão repetidas. Verificação: testes com provider falso que falha e com Chamadas de exemplo truncadas, um teste em que uma Rodada abortada não deixa nada que o Replay aceite, e um teste da mensagem de aborto (comando de reinício e aviso) e do texto de progresso.
- Plano B do spike do Gateway: o primeiro passo é o gate de termos de uso, decidido por escrito antes de qualquer código do spike: se o modo de autenticação do Gateway violar os termos do provedor, é no-go. O spike tem prazo de 1 dia de trabalho, termina com uma decisão go/no-go escrita antes do primeiro prompt e confere o nome do modelo devolvido, o motivo de parada e a temperatura efetiva. O plano B, com modelo e provedor nomeados na própria decisão go/no-go antes de o spike começar, é outro provider sob a mesma seam e é uma exceção declarada à restrição de passar pelo Gateway; Plano B PENDENTE: o humano escolheu em 2026-09-25 só a categoria (modelo open-weights hospedado com camada gratuita); o modelo e o provedor específicos são decisão do humano, com prazo antes do início do spike, no E7, e são exigência da ADR do E7; os limites de taxa dessa camada, que podem abortar Rodadas (não há retentativa), entram nessa decisão. Se o Gateway não servir modelo compatível ou violar os termos, o trabalho de prompts só começa com o plano B aceito por escrito; gravações sintéticas nunca contam como evidência de modelo. Verificação (manual): a decisão go/no-go, com o gate de termos, o plano B nomeado e as três conferências do spike, existe por escrito antes do primeiro arquivo de prompt de produção.
- Testes offline e opt-in: a suíte ordinária e o Replay rodam sempre offline, com a chave de API presente ou não e sem rede; o teste da API real e a integração com o Gateway só rodam com habilitação explícita, e habilitados sem condição de rodar falham com a causa e o passo de correção. O provider Anthropic tem teste de montagem do pedido com transporte falso. Verificação: suíte verde com uma chave no ambiente e com a rede negada.
- Validação do Dataset: um teste valida IDs únicos, um Rótulo esperado por Transcrição, Rótulo dentro da lista fechada, 20 a 30 Transcrições, ao menos uma Transcrição por Rótulo, regra de desempate presente, e que nenhuma Transcrição do Dataset aparece nos exemplos dos prompts.
- Honestidade do relatório: o Relatório gerado, o README do produto e o case study contêm o texto do limite do Replay (prova o cálculo, não que o modelo responderia igual hoje) e nunca contêm "validado contra a Anthropic". Verificação: teste sobre o texto inteiro dos três arquivos commitados.
- Modelo, data e memo: o Relatório declara o modelo exatamente como devolvido pela resposta e a data das Chamadas, e o case study traz um memo curto de decisão (por que este problema, o que foi cortado, o que as métricas não afirmam). Verificação (manual): o Relatório e o case study contêm o modelo devolvido, a data e o memo.
- Contrato explícito em v0 e piloto: v0 é ingênuo no conteúdo (sem exemplos nem estratégia de classificação), mas declara o Contrato de saída de forma explícita, pedindo um objeto JSON puro com Rótulo e Justificativa; o parser estrito e a linha (f) não mudam. Antes de congelar o Dataset, um piloto de 5 a 10 Transcrições do rascunho, com 1 Repetição de v0, registra a taxa de Violação de formato e de Alucinação, e a decisão de congelar ou de ajustar o Dataset ou v0 fica por escrito. Verificação (manual): o prompt de v0 pede JSON puro e o registro do piloto com a decisão existe antes de o Dataset ser congelado.
- Relatório com todas as Rodadas: o Relatório lista todas as Rodadas do repositório, com identificador e estado (completa, abortada, iniciada), inclusive as de experimentos anteriores; o veredito usa somente as Rodadas do experimento identificado, e os pares intermediários aparecem como informativos. Descartar uma Rodada ruim não a apaga nem a sobrescreve: o experimento identificado lista explicitamente as Rodadas que entram, e as demais aparecem no Relatório como "fora do experimento" com o motivo escrito. Verificação: teste do Relatório com Rodadas completas, abortada, de experimento anterior e uma completa descartada com motivo, confirmando que todas aparecem, que só as do experimento entram no veredito e que a descartada aparece como "fora do experimento" com o motivo.
- Motivo de parada normalizado: vocabulário fechado (fim normal, truncada, recusa, outro), mapeado dentro de cada provider e nunca no Avaliador; truncada e recusa são Violação de formato pela linha (f). Verificação: teste de contrato que roda o provider do Gateway e o Anthropic sobre o mesmo transporte falso e exige o mesmo resultado normalizado.
- Edições de baseline aplicadas (ver os registros de edições no Review record; rodada 4 de 2026-09-25: precedência piora, piso, melhora, inconclusivo; plano B pendente, só a categoria escolhida; comparabilidade de modelo e parâmetros; decodificação do JSON na ancoragem; definição de Rodada, Repetição e experimento; descarte de Rodada): módulo Relatório com todas as Rodadas e veredito só para v0 × versão final; história 28 como tentativa documentada; notas de 2026-09-25 nas histórias 17, 18, 19 e 31; Regra do enunciado sobre Anthropic alinhada ao opt-in; v0 com contrato JSON explícito e piloto; mínimo de 3 Repetições para toda versão; gate de termos e plano B nomeado no spike; vocabulário fechado de motivo de parada.
<!-- /autoplan-accepted:ceo -->

<!-- autoplan-accepted:dx -->
None: nenhum achado de DX (X1 a X7) foi aprovado pelo humano; todos são taste pendente e a implementação da spec permanece inalterada por esta fase.
<!-- /autoplan-accepted:dx -->

<!-- autoplan-accepted:eng -->
None: nenhum achado de Eng (E1 a E11) foi aprovado pelo humano; todos são taste pendente e a implementação da spec permanece inalterada por esta fase.
<!-- /autoplan-accepted:eng -->

### CEO review (E5) — decisões provisórias [SUPERADO em 2026-09-25: as decisões finais estão nas seções de rerun e de "Situação dos achados" abaixo; a tabela é mantida como histórico]

| ID | Contrato e evidência | Atual | Proposto | Status | Aprovação e escopo |
|---|---|---|---|---|---|
| C1 | v2 como alvo (história 29; Implementation Decisions "v2 alvo"; Further Notes) | v2 é alvo | v2 sai da spec, vira TODO; v0→v1 é o único entregável | RECUSADO pelo humano | v2 permanece como alvo; mínimo aceito continua v1. Motivo: decisão do humano, sem justificativa adicional registrada |
| C2 | Matriz "o que cada teste comprova" aparece no módulo *Relatório* e no README (história 4) | nos dois | só no README | RECUSADO pelo humano | a matriz permanece no módulo Relatório (e no README). Motivo: decisão do humano, sem justificativa adicional registrada |
| C3 | História 34 (vocabulário segue glossário) | é história | sai: não verificável, já é regra do CLAUDE.md/CONTEXT.md | ACEITO pelo humano; aplicado | História 34 removida da spec. Justificativa: não há como verificar por teste ou checklist que "o vocabulário segue o glossário"; a regra já vale para o projeto inteiro via CLAUDE.md e CONTEXT.md, então mantê-la como história só duplicava uma regra e deixava um critério não verificável, o que o gate do E4 proíbe |
| C4 | Histórias 3/32 e 5/31 duplicadas | 35 histórias | fundir duplicadas, sem mudar comportamento | ACEITO pelo humano; aplicado | 3 fundida com 32 e 5 fundida com 31; a spec passa de 35 para 32 histórias (as antigas 33 e 35 viram 31 e 32). Justificativa: 3 e 32 descreviam o mesmo comportamento (rodar um comando de Replay sem chave e sem Gateway e ver a tabela) e 5 e 31 o mesmo (o relatório separa o que o Replay prova do que a Reexecução mostra); duas histórias para um comportamento geravam dois testes/critérios para uma coisa só |
| A1 | História 2 (case study explica o que mudou) | sem lista de itens que mudaram | Relatório lista as Transcrições cuja classificação mudou entre versões | APROVADO pelo humano no gate de 2026-09-24, rotulado "ilustrativo" | bloco `autoplan-accepted:ceo` (primeiro item) |
| A2 | Critério "queda mensurável" sem regra de decisão (Further Notes; linha "inconclusiva" em Implementation Decisions) | ambíguo | queda só conta se maior que a variação observada entre Repetições | RECUSADO pelo humano no gate de 2026-09-24; SUBSTITUÍDO pela regra de melhora do item 1 do gate (queda >= 2 Transcrições em todas as Repetições e sem aumento de Violação de formato) | bloco `autoplan-accepted:ceo` ("Regra de melhora") |
| Q1 | Efeito piso: se v0 quase não alucina, não há queda a medir. A spec não diz o que fazer | sem resposta | decisão humana: definir o que vale como sucesso nesse caso | DECIDIDA pelo humano em 2026-09-24: v0 com Alucinação <= 1 Transcrição => "inconclusivo por efeito piso", Erro de acerto como métrica secundária, sem declarar melhora | bloco `autoplan-accepted:ceo` ("Regra de melhora") |

Histórico: baseline-edits da execução CEO anterior, já aplicado

```md
<!-- autoplan-baseline-edits:ceo {"sourceSha256":"a6c0a7da494367d4b524825663d62aa6592204b945f946b7c2b5e6665bd21ee9","replacements":[{"oldText":"tabela por versão, variação entre Repetições, case study e a matriz \"o que cada teste comprova\".","newText":"tabela por versão, variação entre Repetições, comparação queda vs variação, lista de Transcrições que mudaram, case study e a matriz \"o que cada teste comprova\"."},{"oldText":"A quantidade exata de Repetições é decidida no E5/E7 com base no que a Reexecução mostrar sobre a variância. Se as Repetições mostrarem variação comparável à queda entre versões, a conclusão é declarada como inconclusiva e o Dataset ou as Repetições aumentam (premissa 2 da ideia).","newText":"O piso é 3 Repetições por versão (configurável; 3 é o padrão, porque com 2 a amplitude é frágil e a Reexecução no Gateway é gratuita). Se a queda não for maior que a variação, a conclusão é declarada inconclusiva e o Dataset ou as Repetições aumentam (premissa 2 da ideia)."},{"oldText":"dentro da margem de variação declarada.","newText":"e os números batem exatamente (o Replay é determinístico). A margem de variação declarada aplica-se apenas à Reexecução."},{"oldText":"quero saber a margem de variação declarada, para saber quanto diferença entre números é ruído.","newText":"quero saber a margem de variação declarada da Reexecução (em pontos percentuais de taxa), para saber quanto diferença entre Rodadas novas é ruído; o Replay bate exatamente."},{"oldText":"Interface web para rodar o eval e CI automatizado (ideia futura separada, CAR-6).","newText":"Interface web para rodar o eval e CI automatizado do eval (o CI do repositório exigido no /ship não é afetado) (ideia futura separada, CAR-6)."},{"oldText":"12. Prometer piso numérico de melhora antes do experimento rodar.","newText":"12. Prometer piso numérico de melhora antes do experimento rodar.\n13. Intervalos de confiança/bootstrap nas taxas (adiado para depois do primeiro corte).\n14. Matriz de confusão por Rótulo (adiado para depois do primeiro corte).\n15. Página HTML estática do relatório (pertence à ideia futura CAR-6)."}]} -->
```

Histórico: baseline-edits da rodada 2 do CEO (2026-09-24), já aplicado

```md
<!-- autoplan-baseline-edits:ceo {"sourceSha256":"6a40b4bbedf17ccee641a12e0a851e545b26ffa6db421954494357b11d43033d","replacements":[{"oldText":"7. Como recrutador técnico, quero ver a variação observada entre Repetições, para saber se a queda entre v0 e a versão final é maior que o ruído.","newText":"7. Como recrutador técnico, quero ver o resultado de cada Repetição e a conclusão que a regra de melhora produz (melhora, inconclusivo, inconclusivo por efeito piso ou piora), para julgar se a queda é confiável ou ruído."},{"oldText":"25. Como candidato, quero que o teste contra a API real fique *skipped* quando não há chave, para que a suíte fique verde sem custo e sem fingir cobertura.","newText":"25. Como candidato, quero que o teste contra a API real só rode com habilitação explícita além da chave e fique *skipped* sem ela, para que a suíte ordinária fique verde, offline e sem custo, mesmo com uma chave no ambiente, e sem fingir cobertura."},{"oldText":"Esta é a decisão difícil de reverter.","newText":"Esta é a decisão difícil de reverter. O resultado do método é normalizado (texto, motivo de parada e o modelo devolvido pela resposta). Não há retentativa automática: erro do provider aborta a Rodada."},{"oldText":"As categorias são independentes, exceto que Violação de formato é excludente com Alucinação.","newText":"Erro de acerto e Alucinação são independentes; Violação de formato é excludente com as duas (linha (f) da tabela de contagem e história 17)."},{"oldText":"*Gravação e Replay*: cada Chamada grava versão de prompt, Transcrição, modelo e resposta. O Replay lê só esses registros.","newText":"*Gravação e Replay*: cada Chamada grava versão de prompt, Transcrição, modelo e resposta, sem credenciais nem cabeçalhos de autenticação. Cada Rodada tem um manifesto versionado (versão do esquema) com o hash do texto do prompt, o hash do Dataset, os parâmetros efetivos, o número esperado de Chamadas (Transcrições × Repetições) e o estado (iniciada, completa ou abortada). A identidade de uma Chamada é (Rodada, hash do prompt, Transcrição, Repetição) e é única. A escrita é atômica: a Rodada só passa a existir para o Replay quando o manifesto é gravado como completo, e uma Rodada existente nunca é sobrescrita. O Replay lê só esses registros e recusa, com mensagem, divergência de hash ou de versão de esquema, Chamada duplicada, extra ou faltando, e Rodada não completa."},{"oldText":"*Relatório*: tabela por versão, variação entre Repetições, comparação queda vs variação, lista de Transcrições que mudaram, case study e a matriz \"o que cada teste comprova\".","newText":"*Relatório*: tabela por versão, resultado de cada Repetição, conclusão pela regra de melhora (melhora, inconclusivo, inconclusivo por efeito piso ou piora), lista ilustrativa de Transcrições que mudaram, modelo (como devolvido pela resposta) e data das Chamadas, o resultado declarado como exploratório, case study com um memo curto de decisão (por que este problema, o que foi cortado, o que as métricas não afirmam) e a matriz \"o que cada teste comprova\"."},{"oldText":"- **Contrato de saída:** Rótulo da lista + Justificativa literal. Igual para todas as versões, v0 incluída.","newText":"- **Contrato de saída:** um objeto JSON com dois campos de texto, Rótulo (da lista) e Justificativa (literal). Igual para todas as versões, v0 incluída. O parser é estrito: não remove code fence nem prosa em volta, e campos extras são ignorados. O Rótulo é comparado depois de aparar espaços nas pontas, e maiúsculas e minúsculas contam como diferença. Resposta vazia, truncada (o Provider informa o motivo de parada), recusa, JSON inválido, campo faltando ou de tipo errado, e Justificativa vazia ou só de espaços são saída não interpretável (Violação de formato). \"Ancoragem literal\" é o nome da métrica: ela prova que o trecho existe na Transcrição, não que sustenta o Rótulo."},{"oldText":"Se a queda não for maior que a variação, a conclusão é declarada inconclusiva e o Dataset ou as Repetições aumentam (premissa 2 da ideia).","newText":"A conclusão segue a regra de melhora de Further Notes; aumentar o Dataset ou as Repetições depois de ver o resultado cria um novo experimento identificado e exige rodar de novo v0 e a versão final (premissa 2 da ideia)."},{"oldText":"Nenhum prompt de produção é escrito antes disso.","newText":"Nenhum prompt de produção é escrito antes disso. O spike tem prazo de 1 dia de trabalho. Se falhar (modelo incompatível ou termos violados), a decisão go/no-go é escrita, o trabalho de prompts não começa, e a alternativa é outro provider sob a mesma seam (por exemplo um modelo aberto local ou gratuito de terceiros, no formato Anthropic); gravações sintéticas nunca contam como evidência de modelo e o case study passa a falar do método, não do modelo."},{"oldText":"Violação de formato (e que ela **não** conta como Alucinação)","newText":"Violação de formato (e que ela **não** conta como Alucinação nem como Erro de acerto)"},{"oldText":"Justificativa parafraseada (não ancorada).","newText":"Justificativa parafraseada (não ancorada). Cada teste compara com contagens calculadas à mão, não com a saída de outro cálculo do próprio código."},{"oldText":"- **Integração local com o Gateway:** roda só onde há Gateway; marcada para pular quando ausente. Comprova compatibilidade de formato, não validação da Anthropic.","newText":"- **Integração local com o Gateway:** só roda com habilitação explícita; sem habilitação é marcada para pular, e habilitada sem Gateway falha com a causa e o passo de correção. Comprova compatibilidade de formato, não validação da Anthropic."},{"oldText":"- **Teste Anthropic real:** existe e é *skipped* sem chave, com o motivo visível na saída.","newText":"- **Teste Anthropic real:** existe, exige habilitação explícita além da chave e é *skipped* sem ela, com o motivo visível na saída; neste plano fica desabilitado. A suíte ordinária e o Replay rodam sempre offline, mesmo com uma chave no ambiente. O código do provider Anthropic tem teste de montagem do pedido com transporte falso.\n- **Dataset:** um teste valida IDs únicos, um Rótulo esperado por Transcrição, Rótulo dentro da lista fechada, 20 a 30 Transcrições, ao menos uma Transcrição por Rótulo, regra de desempate presente, e que nenhuma Transcrição do Dataset aparece nos exemplos dos prompts."},{"oldText":"existe queda **mensurável e documentada** na taxa de Alucinação entre v0 e a versão final (a última concluída; mínimo v1), medida no mesmo Dataset fixo. Sem percentual prometido.","newText":"existe o ciclo medir, iterar e concluir documentado: v0 medida e ao menos v1 (a versão final é a última concluída), no mesmo Dataset fixo, com a conclusão registrada no Relatório. Resultado nulo, inconclusivo ou piora é válido e cumpre o critério. Sem percentual prometido."},{"oldText":"O relatório nunca afirma validação contra a API oficial.\n- **Primeiro corte:**","newText":"O relatório nunca afirma validação contra a API oficial e declara o resultado como exploratório (o mesmo Dataset serve para desenvolver e para medir).\n- **Primeiro corte:**"},{"oldText":"eval rodando contra o Gateway, queda documentada)","newText":"eval rodando contra o Gateway, conclusão documentada)"}]} -->
```

Histórico: baseline-edits da rodada 3 do CEO (2026-09-25), já aplicado

```md
<!-- autoplan-baseline-edits:ceo {"sourceSha256":"5cd0a51feb00a95acd71d8f3e64cc0bcc1608172f18c7b2d7735a35609b67569","replacements":[{"oldText":"28. Como candidato, quero que v1 seja uma melhoria documentada sobre v0, para ter o mínimo aceito (v0→v1) mesmo se a semana estourar.","newText":"28. Como candidato, quero que v1 seja uma tentativa documentada de melhoria sobre v0, para ter o mínimo aceito (v0→v1) mesmo se a semana estourar, qualquer que seja o resultado."},{"oldText":"para não inflar a queda entre versões com erro de parsing.","newText":"para não inflar a queda entre versões com erro de parsing. [Nota de 2026-09-25, texto anterior mantido: a linha (f) da tabela de contagem e o módulo Avaliador estabelecem que Violação de formato também não conta como Erro de acerto.]"},{"oldText":"18. Como candidato, quero rodar uma versão de prompt sobre todo o Dataset e obter uma taxa por métrica (uma Rodada), para comparar versões.","newText":"18. Como candidato, quero rodar uma versão de prompt sobre todo o Dataset e obter uma taxa por métrica (uma Rodada), para comparar versões. [Nota de 2026-09-25, texto anterior mantido: a hierarquia entre Rodada e Repetição está pendente (achado EE3, adiado); o manifesto trata as Repetições como parte da Rodada.]"},{"oldText":"19. Como candidato, quero repetir uma Rodada com a mesma versão e o mesmo Dataset (Repetição), para medir a variação do modelo.","newText":"19. Como candidato, quero repetir uma Rodada com a mesma versão e o mesmo Dataset (Repetição), para medir a variação do modelo. [Nota de 2026-09-25, texto anterior mantido: toda versão tem no mínimo 3 Repetições; a hierarquia Rodada e Repetição está pendente (achado EE3, adiado).]"},{"oldText":"para saber quanto diferença entre Rodadas novas é ruído; o Replay bate exatamente.","newText":"para saber quanto diferença entre Rodadas novas é ruído; o Replay bate exatamente. [Nota de 2026-09-25, texto anterior mantido: a margem é apenas descritiva da Reexecução e não decide nenhum veredito do Relatório.]"},{"oldText":"O teste real existe e fica *skipped* sem chave.","newText":"O teste real existe, exige habilitação explícita além da chave e fica *skipped* sem ela."},{"oldText":"*Versões de prompt*: v0 (ingênuo), v1 obrigatória, v2 alvo. v3 fora.","newText":"*Versões de prompt*: v0 (ingênuo), v1 obrigatória, v2 alvo. v3 fora. v0 é ingênuo no conteúdo (sem exemplos nem estratégia), mas declara o Contrato de saída de forma explícita: pede um objeto JSON puro com Rótulo e Justificativa. Antes de congelar o Dataset, um piloto de 5 a 10 Transcrições do rascunho, com 1 Repetição de v0, registra a taxa de Violação de formato e de Alucinação, e a decisão de congelar ou de ajustar o Dataset ou v0 fica por escrito."},{"oldText":"*Relatório*: tabela por versão, resultado de cada Repetição, conclusão pela regra de melhora (melhora, inconclusivo, inconclusivo por efeito piso ou piora), lista ilustrativa de Transcrições que mudaram,","newText":"*Relatório*: tabela por versão, resultado de cada Repetição, lista de TODAS as Rodadas do repositório (com identificador e estado, inclusive abortadas e de experimentos anteriores), veredito pela regra de melhora só para v0 × versão final (melhora, inconclusivo, inconclusivo por efeito piso ou piora) com os pares intermediários como informativos e sem veredito, lista ilustrativa de Transcrições que mudaram,"},{"oldText":"\"Ancoragem literal\" é o nome da métrica: ela prova que o trecho existe na Transcrição, não que sustenta o Rótulo.","newText":"\"Ancoragem literal\" é o nome da métrica: ela prova que o trecho existe na Transcrição, não que sustenta o Rótulo. O motivo de parada normalizado é um vocabulário fechado (fim normal, truncada, recusa, outro), mapeado dentro de cada provider e nunca no Avaliador; os dois providers passam pelo mesmo teste de contrato com um transporte falso."},{"oldText":"v0 e a versão final são executadas em mais de uma Repetição, e o relatório registra a variação observada. O piso é 3 Repetições por versão (configurável; 3 é o padrão, porque com 2 a amplitude é frágil e a Reexecução no Gateway é gratuita).","newText":"toda versão, inclusive as intermediárias, é executada em pelo menos 3 Repetições, e o relatório registra as contagens de cada uma. O mínimo é 3 (configurável para cima; 3 é o padrão, porque com 2 a amplitude é frágil e a Reexecução no Gateway é gratuita), e a Rodada e o Replay recusam menos de 3."},{"oldText":"O spike tem prazo de 1 dia de trabalho. Se falhar (modelo incompatível ou termos violados), a decisão go/no-go é escrita, o trabalho de prompts não começa, e a alternativa é outro provider sob a mesma seam (por exemplo um modelo aberto local ou gratuito de terceiros, no formato Anthropic); gravações sintéticas nunca contam como evidência de modelo e o case study passa a falar do método, não do modelo.","newText":"O primeiro passo do spike é o gate de termos de uso, decidido por escrito antes de qualquer código do spike: se o modo de autenticação do Gateway violar os termos do provedor, é no-go. O spike tem prazo de 1 dia de trabalho e confere o nome do modelo devolvido, o motivo de parada e a temperatura efetiva. O plano B, com modelo e provedor nomeados na própria decisão go/no-go antes de o spike começar, é outro provider sob a mesma seam e é uma exceção declarada à restrição de passar pelo Gateway; se o Gateway falhar (modelo incompatível ou termos violados), a decisão go/no-go é escrita e o trabalho de prompts só começa com o plano B aceito por escrito; gravações sintéticas nunca contam como evidência de modelo e o case study passa a falar do método, não do modelo."}]} -->
```

Baseline-edits da rodada 4 do CEO (2026-09-25), aprovados pelo humano no último gate (só texto fora do bloco aceito; o texto do bloco muda no próprio bloco `autoplan-accepted:ceo` acima):

<!-- autoplan-baseline-edits:ceo {"sourceSha256":"59478217b69b74c21593963013fc7b3bc398521a06d26b2d4f193787c92d0731","replacements":[{"oldText":"é uma exceção declarada à restrição de passar pelo Gateway; se o Gateway falhar","newText":"é uma exceção declarada à restrição de passar pelo Gateway; Plano B PENDENTE: o humano escolheu em 2026-09-25 só a categoria (modelo open-weights hospedado com camada gratuita); o modelo e o provedor específicos são decisão do humano, com prazo antes do início do spike, no E7, e são exigência da ADR do E7; os limites de taxa dessa camada, que podem abortar Rodadas (não há retentativa), entram nessa decisão. Se o Gateway falhar"},{"oldText":"(melhora, inconclusivo, inconclusivo por efeito piso ou piora), para julgar","newText":"(piora, inconclusivo por efeito piso, melhora, inconclusivo ou não comparável), para julgar"},{"oldText":"só para v0 × versão final (melhora, inconclusivo, inconclusivo por efeito piso ou piora)","newText":"só para v0 × versão final (piora, inconclusivo por efeito piso, melhora, inconclusivo ou não comparável)"},{"oldText":"[Nota de 2026-09-25, texto anterior mantido: a hierarquia entre Rodada e Repetição está pendente (achado EE3, adiado); o manifesto trata as Repetições como parte da Rodada.]","newText":"[Nota de 2026-09-25, texto anterior mantido: definição fechada: uma Rodada é uma versão de prompt sobre o Dataset inteiro com N Repetições (passagens completas pelo Dataset), e o manifesto é da Rodada; um experimento é o conjunto de Rodadas (v0 até a versão final) sobre o mesmo Dataset e que o Relatório identifica.]"},{"oldText":"[Nota de 2026-09-25, texto anterior mantido: toda versão tem no mínimo 3 Repetições; a hierarquia Rodada e Repetição está pendente (achado EE3, adiado).]","newText":"[Nota de 2026-09-25, texto anterior mantido: toda versão tem no mínimo 3 Repetições; a Repetição é uma passagem completa pelo Dataset dentro da mesma Rodada (ver a nota da história 18).]"}]} -->

### Adições feitas por auto-decisão do /autoplan, sem aval prévio do humano (aprovar ou recusar cada uma no gate)

Status atualizado no gate de 2026-09-24: aprovados 1 (rotulado "ilustrativo"), 3, 4 (módulo Avaliador alinhado à linha f), 5 (Rodada abortada e não retomável), 6, 7, 8 (estendido ao README e ao case study) e 9 ("história 33" corrigida para 31). Recusado 2 (A2), substituído pela regra de melhora.

| # | Adição | Onde está na spec |
|---|---|---|
| 1 [APROVADO (ilustrativo)] | **A1:** o Relatório lista as Transcrições cujo Rótulo mudou entre versões consecutivas, comparando a Repetição de índice 1 de cada uma; resposta sem Rótulo válido é o estado "sem rótulo válido" | módulo Relatório (Implementation Decisions); bullet "Lista de Transcrições que mudaram" no fim de Further Notes |
| 2 [RECUSADO; substituído pela regra de melhora] | **A2:** regra de decisão da queda: queda = média das taxas de Alucinação total de v0 menos a média da versão final, em pontos percentuais; variação = max das amplitudes entre Repetições de v0 e da versão final; "mensurável" só se a queda for estritamente maior que a variação, senão inconclusivo (inclui variação e queda zero) | bullet "Regra de decisão da queda" no fim de Further Notes; parágrafo Repetições em Implementation Decisions |
| 3 [APROVADO] | **P6:** piso de 3 Repetições por versão (configurável), no lugar de "decidida no E5/E7" | parágrafo Repetições em Implementation Decisions; bullet "Piso de 3 Repetições" |
| 4 [APROVADO (Avaliador alinhado à linha f)] | **Tabela de contagem a–f** por resposta (denominador = todas as Transcrições; regra de normalização da Justificativa ancorada; Violação de formato conta só nela mesma, nem Erro de acerto nem Alucinação) e um teste da Rodada por linha | bullet "Tabela de contagem por resposta" no fim de Further Notes |
| 5 [APROVADO (Rodada abortada e não retomável)] | **Política de falha do provider:** erro do provider não vira Chamada; a Rodada aborta com mensagem e não fica completa; o Replay recusa Rodada com Chamadas faltando, corrompidas ou fora do Dataset | bullet "Falhas" no fim de Further Notes |
| 6 [APROVADO] | **Campos novos da Chamada:** índice da Repetição, identificador da Rodada, modelo e parâmetros de geração (temperature, max_tokens) | bullet "Cada Chamada gravada registra também..." no fim de Further Notes |
| 7 [APROVADO] | **Itens 13 a 15 do Fora de escopo:** bootstrap/intervalos de confiança, matriz de confusão por Rótulo, página HTML estática | seção Out of Scope, itens 13-15 |
| 8 [APROVADO (estendido ao README e ao case study)] | Teste do texto do Relatório: contém o limite do Replay e nunca contém "validado contra a Anthropic" | bullet "Honestidade do relatório" no fim de Further Notes |
| 9 [APROVADO (história 33 para 31)] | Esclarecimentos de texto: margem de variação vale só para a Reexecução (Replay bate exatamente), no critério de sucesso e na história 31 (antiga 33); item 6 do Fora de escopo esclarece que o CI do repositório no /ship não é afetado; módulo Relatório passa a listar comparação queda vs variação e a lista de mudanças | Further Notes (Critério de sucesso), User Stories, Out of Scope item 6, módulo Relatório |

[SUPERADO em 2026-09-25: as obrigações aceitas do CEO vivem no bloco `autoplan-accepted:ceo` acima; esta observação descreve a duplicação da rodada anterior e fica só como histórico.] Observação: os bullets "no fim de Further Notes" formam o registro de obrigações aceitas (bloco `autoplan-accepted:ceo`) e estão duplicados no texto onde a spec original já dizia algo parecido; a remoção de qualquer item recusado deve apagar as duas ocorrências.


### CEO review (E5), rodada 2, 2026-09-24 (SELECTIVE EXPANSION) [SUPERADO PARCIALMENTE em 2026-09-25]

> Status em 2026-09-25: D1 (critério de sucesso) foi resolvido pelo Challenge 1 do humano (o critério mudou); D3 foi aplicado em parte (regra de melhora com guarda de acurácia, parser e bordas de (f)); R1 e R2 desta rodada seguem como User Challenges já decididos (D1 e D2 do gate de 2026-09-25). A tabela abaixo é histórico; o estado atual está em "Situação dos achados".

Ponto de partida: spec de 775f853. Nenhuma expansão nova aceita; o bloco `autoplan-accepted:ceo` acima foi carregado sem alteração e continua PENDENTE DE APROVAÇÃO humana (lista de acréscimos acima). C1 e C2 recusados e C3 e C4 aceitos pelo humano: não reabertos.

**Vozes.** Spec Review Loop: 1 lançamento, nota 6/10, 20 achados, 0 corrigidos (ver "Reviewer Concerns" no CEO plan). Claude CEO (nativo): completo, 7 achados. Codex CEO (externo, provider codex, gpt-6-astra): completo, 8 achados (1ª tentativa falhou sem causa determinada; 2ª validada, exit 0).

```
CEO DUAL VOICES — CONSENSUS TABLE:
  Dimension                             Claude  Codex  Consensus
  1. Premises valid?                    NAO     NAO    CONFIRMED (Gateway/ToS sem fallback; premissa de contratação não validada)
  2. Right problem to solve?            PARCIAL PARCIAL CONFIRMED (ambos pedem reenquadrar para o laço medir-iterar-concluir/decisão)
  3. Scope calibration correct?         NAO     NAO    CONFIRMED (pesado para 1 semana; provider Anthropic e validação de Replay)
  4. Alternatives sufficiently explored? NAO    NAO    CONFIRMED (dataset público / sem baseline não-LLM / sem "pular provider Anthropic")
  5. Competitive/market risks covered?  PARCIAL —      single-voice (Claude: baixo peso; Codex não comentou)
  6. 6-month trajectory sound?          NAO     NAO    CONFIRMED (prova autoavaliada; reporte seletivo; modelo do Gateway pode sumir)
CONFIRMED 5 de 6; 1 single-voice.
```

**Decisões e achados (ledger).**

| ID | Achado | Vozes | Classe | Disposição (nada aplicado à spec) |
|---|---|---|---|---|
| D1 | Critério de sucesso "queda mensurável" pode reprovar um resultado honesto (v0 quase sem alucinar, ou queda inconclusiva) e premia "obter queda". Ambos pedem: sucesso = laço medir-iterar-concluir documentado e reproduzível; resultado nulo ou inconclusivo vale; a queda vira alvo, não portão. Liga à Q1 | Claude + Codex | **USER CHALLENGE** | Direção original preservada (queda é o critério). Vai ao gate |
| D2 | Falta ramo "spike do Gateway falha" (modelo incompatível ou ToS violado): sem fallback nem regra de parada | Claude + Codex | TASTE | Recomendo: regra "spike falha → parar e replanejar; alternativa sob a mesma seam de Provider; o case study é sobre método". Vai ao gate |
| D3 | Regressão invisível: saída não interpretável conta 0 em Erro de acerto e em Alucinação, então uma versão que só quebra formato "melhora". Justificativa literal não prova que sustenta o Rótulo. Contradição adicional: módulo Avaliador diz que Violação de formato exclui só Alucinação; tabela (f) e história 17 dizem que exclui também Erro de acerto | Codex + Revisor de spec | TASTE | Recomendo: o Relatório mostra taxa de respostas utilizáveis e corretas ao lado das três métricas, e o texto do Avaliador é alinhado à linha (f). Vai ao gate |
| D4 | Mesmo Dataset serve para desenvolver e para provar: mede adaptação, não generalização; Repetições medem só variação de geração | Codex (+ Claude: dataset pequeno) | TASTE | Recomendo: declarar o resultado como exploratório no Relatório (custo zero) e, se sobrar tempo, reservar um subconjunto congelado. Vai ao gate |
| D5 | Provider Anthropic e teste *skipped* como segundo corte | Claude (cortar); Codex (questionar retorno, sem pedir corte) | TASTE | Recomendo manter: é a exigência declarada (história 24). Vai ao gate |
| D6 | Provas de "escopa sozinho": falta memo curto de decisão (por que este problema, o que cortei, o que as métricas não afirmam) | Claude | TASTE | Recomendo incluir no case study, custo S. Vai ao gate |
| D7 | Sem baseline não-LLM (regras simples) nem v0 competente | Codex | TASTE (P3) | Adiado. Não decido pelo humano |
| D8 | Matriz de confusão deveria vir antes de v2 | Codex | TASTE (P3) | Continua adiada (Fora de escopo 14); voz única |
| D9 | Reporte seletivo: falta hash imutável do prompt e do Dataset, registro de Rodadas abortadas ou excluídas, manifesto da Rodada, e lista de mudanças só na Repetição 1 | Codex + Revisor de spec | TASTE | Recomendo manifesto com hash do prompt e registro de abortadas; lista de mudanças resumida por todas as Repetições. Vai ao gate |
| D10 | Fixar nome do modelo e data no Relatório (Gateway pode renomear) | Claude | TASTE | Vai ao gate |
| D11 | Premissa de que o recrutador pede isso não tem evidência | Claude + Codex | Observação | Sem ação na spec; risco aceito pelo humano no E2 |
| Q1 | Efeito piso | — | ABERTA (humano) | D1 é a mesma família |

**Seção 1, Arquitetura.** Uma seam (a Rodada), Provider com um método, Replay pela mesma seam.
```
 Dataset ─┐
 Versão ──┼─> Rodada ─> Provider(injetado) ─> Chamadas gravadas ─> Avaliador ─> taxas ─> Relatório
 Replay:   └────────────  (Provider = ler Chamadas gravadas)  ───────────────┘
```
Achado: manifesto da Rodada ausente (D9); acoplamento ao vocabulário Anthropic é a decisão difícil de reverter e está declarada. Ponto único de falha: o Gateway (D2). Rollback: sem produção, reverter commits.

**Seção 2, Erros e resgate.** 6 linhas, 4 GAPS (ver registro abaixo). Nenhum catch-all descrito. Chamadas a LLM: malformado e recusa tratados como Violação de formato apenas em parte (truncada, vazia e recusa não classificadas).

**Seção 3, Segurança.** Superfície pequena: sem endpoint, sem dado real (Transcrições fictícias). Riscos: (a) segredo/chave nunca deve entrar em Chamada gravada (o Replay é commitado em repositório público): não há requisito, GAP baixo, vai ao gate; (b) ToS do CLIProxyAPI (história 32, D2); (c) injeção de prompt via Transcrição: irrelevante, dado fictício controlado. Severidade alta: nenhuma.

**Seção 4, Fluxo de dados e bordas.** INPUT(Transcrição) → prompt → Provider → resposta → Avaliador → taxa. Sombras: resposta vazia, truncada, com code fence ou prosa extra, Rótulo com caixa ou espaço diferente, Justificativa vazia (substring trivial), Chamada duplicada ou extra no Replay: nenhuma tem regra (GAPS). Sem async compartilhado.

**Seção 5, Qualidade de código.** Sem código ainda. A regra de normalização e a tabela a–f estão bem definidas. Sinal: Avaliador com 6 caminhos, aceitável. Repetições "configuráveis" é YAGNI leve.

**Seção 6, Testes.** Diagrama: Rodada (provider falso) cobre a–f, falha de provider, Replay idêntico, lista de mudanças, regra da queda (maior, igual, menor), honestidade do texto. Faltam testes para as bordas da Seção 4. Prompt/LLM: sem CLAUDE.md com padrões de eval; o próprio projeto é o eval. Flakiness: só a Reexecução (isolada, skipped sem Gateway).

**Seção 7, Performance.** ~120 a 270 chamadas por experimento no Gateway; abortar a Rodada inteira num erro pode custar a Rodada (retomar por identificador de Rodada seria opcional). Memória e latência irrelevantes.

**Seção 8, Observabilidade.** Sem produção. Debuggabilidade em 3 semanas: as Chamadas gravadas reconstroem tudo, exceto o texto do prompt (D9) e a versão do Dataset.

**Seção 9, Deploy.** Sem deploy de serviço; distribuição = repositório público. Verificação pós-publicação: um terceiro roda o Replay do zero em clone limpo (vira critério do E12).

**Seção 10, Trajetória.** Dívida: doc e teste. Reversibilidade 2/5 (vocabulário Anthropic no formato interno). Depois deste: CAR-6 (demo pública) e novos problemas de eval sob o mesmo Provider. Retrospectiva SELECTIVE: as adiadas (bootstrap, matriz de confusão) seguem não carregantes; a lista de mudanças e a regra da queda são carregantes para o argumento.

**Seção 11, Design.** SKIPPED (sem escopo de UI).

**NOT in scope.** Adiadas (também no CEO plan; não há TODOS.md no repositório): bootstrap/IC; matriz de confusão; subconjunto "casos difíceis"; baseline não-LLM (D7). Rejeitada: hash do Dataset por Chamada (o Replay já recusa Transcrição fora do Dataset).

**What already exists.** Nada de código. Reusa: glossário `CONTEXT.md`, notas de arquitetura (209 linhas), design doc E2.

**Dream state delta.** Da resposta verbal para uma tabela reproduzível por Replay. Falta para o ideal de 12 meses: baseline não-LLM, conjunto reservado e evidência de que o problema pesa na contratação (D4, D7, D11).

**Error & Rescue Registry.**

| Capacidade | Falha | Resgatada? | Ação | Usuário vê |
|---|---|---|---|---|
| Spike do Gateway | modelo incompatível ou ToS | NAO (GAP) | nenhuma definida | bloqueio sem regra |
| Provider | timeout, 429, HTTP | SIM (abortar) | Rodada não completa | mensagem visível; sem retomar |
| Avaliador | resposta vazia, truncada, recusa | NAO (GAP) | não classificada | silêncio ou contagem errada |
| Avaliador | Justificativa vazia | NAO (GAP) | substring trivial | Alucinação some |
| Replay | Chamadas faltando, corrompidas, fora do Dataset | PARCIAL | recusa com mensagem; "faltando" sem manifesto | mensagem |
| Chamada | prompt editado após gravar | NAO (GAP) | sem hash | silêncio |

**Failure Modes Registry.**

| Codepath | Falha | RESCUED | TEST | USER SEES | LOGGED |
|---|---|---|---|---|---|
| Spike | Gateway incompatível | N | N | Bloqueio | N |
| Avaliador | resposta truncada/vazia/recusa | N | N | Silent | N |
| Avaliador | Justificativa vazia | N | N | Silent | N |
| Chamada | prompt mudou após gravar | N | N | Silent | N |
| Provider | erro HTTP | Y | Y | Mensagem | Y |
| Replay | Chamada truncada | Y | Y | Mensagem | Y |

CRITICAL GAPS: 3 (truncada/vazia/recusa, Justificativa vazia, prompt mudou), mais o spike sem regra (bloqueio visível, contado como GAP).

**Diagramas.** Arquitetura e fluxo (acima). Estado: Rodada = {iniciada, completa, abortada}; transição inválida: abortada → completa (a spec exige que não fique marcada completa). Diagramas de deploy e de rollback: N/A (biblioteca de repositório, sem serviço). Diagramas obsoletos: nenhum (não há código).

**Accepted obligations (CEO).** Nenhuma nova. O bloco `autoplan-accepted:ceo` já registrado acima é carregado sem alteração; permanece provisório (taste, pendente do humano). Nenhum item de D1 a D10 foi incorporado à spec.

**Decision Audit Trail.**

| # | Fase | Decisão | Classe | Princípio | Motivo | Rejeitado |
|---|---|---|---|---|---|---|
| 1 | CEO | Modo SELECTIVE EXPANSION | mecânica | override do autoplan | capacidade nova | HOLD, REDUCTION |
| 2 | CEO | Abordagem A (plano atual) | mecânica | P1, P5 | B já recusada em C1 | B, C |
| 3 | CEO | Expansões E1 a E4 adiadas, E5 rejeitada | taste | P3, P4 | fora da semana ou duplicada | aceitar |
| 4 | CEO | Loop de spec review encerrado após 1 lançamento sem emendar | taste | P6, CLAUDE.md (não inventar requisito) | emendas criam requisitos; ficam para o humano | emendar por conta própria |
| 5 | CEO | Aprovar as versões dos documentos (0H) | mecânica | autoauto | só aprova as versões, não as pendências | pausar |
| 6 | CEO | D1 marcado User Challenge | challenge | regra do skill | ambas as vozes pedem mudar o critério do humano | aplicar |
| 7 | CEO | D2 a D6, D9, D10 marcados taste | taste | P1, P5 | viáveis com trocas; vão ao gate | aplicar |
| 8 | CEO | D7, D8 adiados | taste | P3 | voz única ou fora do primeiro corte | aplicar |

**CEO Completion Summary.**
```
  | Mode selected        | SELECTIVE EXPANSION                        |
  | Step 0               | 0 expansões aceitas; 4 adiadas; 1 rejeitada |
  | Section 1  (Arch)    | 1 issue (manifesto)                        |
  | Section 2  (Errors)  | 6 caminhos mapeados, 4 GAPS                |
  | Section 3  (Security)| 1 issue, 0 High (segredo em Chamada)       |
  | Section 4  (Data/UX) | 6 bordas mapeadas, 6 sem tratamento        |
  | Section 5  (Quality) | 1 issue (Repetições configuráveis)         |
  | Section 6  (Tests)   | diagrama produzido, 6 gaps                 |
  | Section 7  (Perf)    | 1 issue (abortar Rodada inteira)           |
  | Section 8  (Observ)  | 2 gaps (prompt, Dataset)                   |
  | Section 9  (Deploy)  | 1 risco (clone limpo)                      |
  | Section 10 (Future)  | Reversibility 2/5, 3 itens de dívida       |
  | Section 11 (Design)  | SKIPPED (no UI scope)                      |
  | Outside voice        | codex completed, 8 achados                 |
  | Unresolved decisions | D1 (challenge), D2-D6, D9, D10 (taste), Q1 |
```

### Design review (E5), rodada 2, 2026-09-24: SKIPPED (no UI scope)

Skip registrado, não é revisão concluída. Motivo: a spec não tem tela, componente nem interação de UI (Fora de escopo 2, 6 e 15 excluem interface web e página HTML). A própria metodologia do plan-design-review manda sair cedo sem escopo de UI. Zero achados, zero decisões, sem vozes externas, sem nota. A superfície legível pelo recrutador (Relatório e README) é coberta pelas lentes CEO e DX. O humano pode pedir a lente de Design forçada no gate.

### DX review (E5), rodada 2, 2026-09-24 (modo DX POLISH) [SUPERADO pela rerun; classificação atual em "Situação dos achados"]

Vozes: Claude DX (nativo) completo, 17 achados; Codex DX (externo, provider codex, gpt-6-astra) completo, 6 achados (validador exit 0). Nada foi aplicado à spec; todos os achados abaixo ficam pendentes do humano. Evidência: o produto ainda não existe (só docs); os achados são lacunas de plano, não falhas observadas. O README da raiz descreve a fábrica; o README do produto viverá em `cx-prompt-lab/` (design doc, Distribution Plan) e ainda não existe.

**Tipo de produto:** biblioteca/CLI com documentação (Replay como comando). **Persona alvo (auto, P6):** terceiro técnico que clonou o repositório (recrutador técnico ou desenvolvedor avaliador). Contexto: 5 a 15 minutos de atenção numa conversa de seleção. Tolerância: abandona se não vê a tabela em poucos passos. Espera: um comando, sem chave, sem conta.

**Narrativa de empatia (prevista, não observada).** "Abro o link do repositório antes da entrevista. Procuro uma frase que diga o que é e um comando para rodar. Vejo a tabela v0→v1? Se o README da subpasta abrir com o comando de Replay e a tabela de exemplo, em dois minutos eu sei se isso é sério. Se em vez disso eu preciso descobrir a versão da linguagem, instalar dependências sem lockfile e adivinhar o nome do comando, eu fecho a aba e confio só no que o candidato disser. Se o comando falha com 'erro de leitura', eu não sei se o problema é meu ambiente ou o projeto. Se a saída afirma 'queda mensurável' sem eu saber se a versão nova só parou de responder direito, eu desconfio da conclusão inteira."

**Consenso DX (vozes nativa e externa):**
```
DX DUAL VOICES — CONSENSUS TABLE:
  Dimension                           Claude  Codex  Consensus
  1. Getting started < 5 min?          NAO     NAO    CONFIRMED gap (sem comando, runtime, dependências ou saída esperada)
  2. API/CLI naming guessable?         NAO     NAO    CONFIRMED gap (superfície de CLI indefinida; defaults sem lista)
  3. Error messages actionable?        NAO     NAO    CONFIRMED gap (mensagem sem causa, correção nem identificador)
  4. Docs findable & complete?         NAO     NAO    CONFIRMED gap (README sem estrutura; produto e Gateway misturados)
  5. Upgrade path safe?                —       NAO    single-voice (Codex: Chamada sem versão de esquema nem hash do prompt)
  6. Dev environment friction-free?    PARCIAL PARCIAL CONFIRMED gap (seleção de provider e Gateway sem mecanismo; teste ordinário pode usar chave ambiente)
CONFIRMED 5 de 6; 1 single-voice, tratado como achado crítico de uma voz.
```

**Achados e disposição (todos taste, nenhum aplicado):**

| ID | Achado | Vozes | Recomendação (não aplicada) |
|---|---|---|---|
| X1 | Quickstart não testável: sem critério de tempo, comando, pré-requisito, saída esperada; README sem esqueleto | Claude F1, F11 + Codex 1, 4 | Critério: de um clone limpo até a tabela impressa em no máximo 5 minutos e poucos comandos, sem chave, sem Gateway e sem rede após instalar; README do produto abre com o comando e a saída de exemplo gerada pelo Replay |
| X2 | Mensagens de erro sem causa, correção e identificador; Gateway ausente ou incompatível sem falha rápida | Claude F7, F8, F9 + Codex 2 | Modelo problema + causa + próximo passo, com Rodada e Transcrição ou arquivo, saída com código diferente de zero; falha rápida de Gateway; motivo do skip com a variável que habilita |
| X3 | Superfície de CLI, defaults, seleção de provider e piso de Repetições indefinidos | Claude F4, F5, F15 + Codex 3 | Exigir que a ADR do E7 congele comandos que espelham o glossário, `--help`, lista de opções com default e piso, e a língua dos comandos e mensagens |
| X4 | Chamada sem versão de esquema, hash do prompt, identidade do Dataset ou estado de completude; política de Rodada abortada indefinida | Codex 5 + Claude F10 (+ CEO D9) | Manifesto versionado da Rodada; Replay recusa versão não suportada com instrução; regra escrita para Rodada parcial |
| X5 | Teste ordinário pode acionar a API oficial se houver chave no ambiente | Codex 3 | Suíte ordinária sempre offline; teste real só com habilitação explícita e desativado neste plano |
| X6 | Sucesso do Replay não é sucesso do experimento; conclusão positiva só com condições de qualidade | Codex 6 (+ CEO D1, D3) | Mesma família de D1 e D3; decide o humano |
| X7 | Receita "adicionar versão", casos difíceis no topo do Dataset, números do case study ligados à saída do Replay, defaults fixos declarados, inspeção de uma Transcrição | Claude F12, F13, F14, F16, F17 | Opcionais. Sugiro X7a (números do case study vindos do Replay) e X7b (defaults fixos declarados); o resto adiado |

**Developer Journey Map:**
```
ESTÁGIO        | O DEV FAZ                          | FRICÇÃO                                   | STATUS
1 Discover     | abre o repositório                 | README do produto inexiste (fábrica na raiz)| pendente (X1)
2 Evaluate     | lê a tabela e o limite do Replay   | sem tabela de exemplo no README            | pendente (X1)
3 Install      | instala runtime e dependências     | sem versão nem lockfile especificados      | pendente (X1)
4 Hello World  | roda o Replay                      | comando e saída esperada indefinidos       | pendente (X1, X3)
5 Integrate    | injeta outro provider              | seleção de provider indefinida             | pendente (X3)
6 Debug        | lê um erro de Replay ou Reexecução | mensagem sem causa e correção              | pendente (X2)
7 Upgrade      | puxa novas Chamadas                | sem versão de esquema nem hash do prompt   | pendente (X4)
8 Scale        | roda mais Repetições ou versões    | piso e faixas indefinidos                  | pendente (X3)
9 Migrate      | troca Gateway por Anthropic        | seam existe; seleção indefinida            | pendente (X3)
```

**Relatório de confusão do primeiro uso (previsto):** T+0:00 abre o repositório, vê a fábrica agêntica na raiz. T+0:30 procura `cx-prompt-lab/`, não existe ainda. T+1:00 sem comando, tenta adivinhar. T+3:00 desiste e confia na fala do candidato. Nada disso foi observado: o produto não existe.

**TTHW:** atual: não mensurável (sem produto); estimativa de um estranho hoje: acima de 10 min (Red Flag) se depender de instalar runtime e descobrir comandos. Alvo proposto: Competitivo, até 5 min com quatro ações no máximo. O alvo vem à mercê da decisão do humano.

**DX Scorecard (antes = depois, pois nada foi aplicado):**
```
| Getting Started   | 3/10 |  | API/CLI/SDK    | 4/10 |  | Error Messages | 3/10 |  | Documentation | 3/10 |
| Upgrade Path      | 2/10 |  | Dev Environment| 3/10 |  | Community      | 5/10 |  | DX Measurement| 4/10 |
| TTHW: indefinido (estimativa > 10 min) | Competitive Rank: Red Flag | Magical Moment: definido (tabela por Replay, sem chave) |
| Product Type: biblioteca/CLI + docs | Mode: DX POLISH | Overall DX: 3.4/10 |
| Princípios: Zero Friction gap; Learn by Doing gap; Fight Uncertainty gap; Escape Hatches covered (seam); Code in Context gap; Magical Moments covered |
```

**DX Implementation Checklist (proposto, pendente):**
```
[ ] Clone limpo até a tabela impressa em <= 5 min, poucas ações, sem chave, sem Gateway
[ ] README do produto abre com o comando de Replay e a saída de exemplo gerada pelo Replay
[ ] Cada erro: problema + causa + próximo passo + identificador, código de saída diferente de zero
[ ] Gateway ausente ou incompatível falha rápido, com instrução
[ ] Comandos, opções e defaults congelados na ADR do E7, espelhando o glossário
[ ] Suíte ordinária sempre offline; teste real da API desativado, com habilitação explícita
[ ] Manifesto versionado da Rodada; versão não suportada é recusada com instrução
```

**NOT in scope (DX):** SDK em outras linguagens; playground online; codemods; canal de comunidade; telemetria de TTHW; documentação de versão (o produto não tem consumidores externos).
**What already exists (DX):** glossário `CONTEXT.md`; seam de provider de um método (ótimo escape hatch); caminho padrão sem chave (Replay); honestidade sobre o limite do Replay.

**Unresolved (DX):** X1 a X7 pendentes de aprovação humana; alvo de TTHW pendente.

### Eng review (E5), rodada 2, 2026-09-24 [SUPERADO pela rerun; E1 a E11 seguem como histórico, EE1 a EE13 valem]

Vozes: Claude Eng (nativo) completo, 17 achados; Codex Eng (externo, provider codex, gpt-6-astra) completo, 10 achados. A 1ª saída do Codex, em português, foi rejeitada pelo validador ("missing review completion recommendation") e descartada; a 2ª, em inglês, passou (exit 0). Nada foi aplicado à spec. Sem código nem framework de testes no repositório: o diagrama abaixo é de cobertura **planejada**, não observada.

**Step 0, Scope Challenge.** Sem código a reaproveitar. Gate de complexidade disparou (8 ou mais arquivos estimados); auto-decisão: manter lista de funcionalidades e arrumação original (uma seam, um método), pois nenhuma arrumação menor preserva os contratos aprovados; escopo nunca reduzido (P2). Pesquisa web indisponível. Distribuição por clone de repositório público; sem CI de release (CAR-6, NOT in scope).

```
ENG DUAL VOICES — CONSENSUS TABLE:
  Dimension                        Claude   Codex    Consensus
  1. Architecture sound?           PARCIAL  PARCIAL  CONFIRMED (seam e Provider de um método ok; contratos de resposta, manifesto e estados de Rodada indefinidos)
  2. Test coverage sufficient?     NAO      NAO      CONFIRMED gap (bordas, integridade, testes independentes, opt-in da API real)
  3. Performance risks addressed?  PARCIAL  —        single-voice (Claude: abortar Rodada inteira em 429, ~90 a 270 chamadas, sem retomada)
  4. Security threats covered?     NAO      PARCIAL  CONFIRMED gap (credenciais fora das Chamadas; integridade do Replay; sanear texto do modelo no Relatório: Claude)
  5. Error paths handled?          NAO      NAO      CONFIRMED gap (truncada, vazia, recusa, Rodada parcial, duplicadas)
  6. Deployment risk manageable?   PARCIAL  PARCIAL  CONFIRMED manageable com lacunas (clone limpo sem comando definido; 270 arquivos vs JSONL)
CONFIRMED 5 de 6; 1 single-voice.
```

**Temas que aparecem em 2 ou mais fases:** (1) critério de sucesso pode premiar regressão e a regra "queda > variação" é frágil (CEO D1, D3; DX X6; Eng E1, E8); (2) integridade e completude do Replay: hash do prompt, esquema, manifesto, estados da Rodada (CEO D9; DX X4; Eng E2, E3); (3) sem plano B se o spike do Gateway falhar (CEO D2; Eng E10); (4) fronteiras do Contrato de saída (CEO D3; Eng E4, E5); (5) teste da API real e suíte offline (DX X5; Eng E7); (6) quickstart e CLI indefinidos (DX X1, X3; Eng E10).

**Ledger Eng (todos taste, nenhum aplicado; severidade e confiança como reportadas):**

| ID | Achado | Vozes | Sev/Conf | Recomendação (não aplicada) |
|---|---|---|---|---|
| E1 | Critério pode premiar regressão; com variação zero, queda de 1 Transcrição (3 a 5 pp) vira "mensurável"; média vs amplitude não é teste | Claude 1 + Codex 1, 8 | P1 / 9 | Queda mínima absoluta (contagens) além de "> variação", ou contagem pareada de Transcrições que mudaram; guarda-corpos de regressão; declarar a regra como heurística predeclarada; definir queda negativa ("pior") e variação não estimável |
| E2 | Replay sem integridade: sem hash do prompt, da Transcrição, do Dataset, sem versão de esquema; prompt editado depois ainda "bate exato" | Claude 2 + Codex 3 | P1 / 9 | Manifesto versionado com hashes e configurações efetivas; Replay recusa divergência; teste de adulteração; sem credenciais nas Chamadas |
| E3 | Completude sem modelo de dados: Rodada parcial no disco, sem chave de identidade da Chamada, duplicadas escondem omissões | Claude 3, 7 + Codex 4 | P1 / 9 | Registrar a Rodada antes da 1ª chamada; estados iniciada/completa/abortada; chave (rodada, hash do prompt, Transcrição, repetição); escrita atômica; recusar sobrescrita; teste "Rodada abortada não deixa nada aceito" |
| E4 | Fronteira formato vs alucinação sem regra: fence, prosa extra, campo extra, caixa e espaço do Rótulo, vários Rótulos, blocos múltiplos | Claude 4 + Codex 5 | P1 / 8 | Especificar parser (JSON estrito ou extração definida) e casamento do Rótulo; linhas novas na tabela a–f; mostrar Violação de formato ao lado de Alucinação |
| E5 | Ancoragem: Justificativa vazia é substring de tudo; Unicode NFC/NFD, aspas tipográficas, NBSP; citar tudo passa; ancoragem não prova suporte semântico | Claude 5 + Codex 5 | P2 / 8 | Vazia = Violação de formato ou tamanho mínimo; normalização Unicode; nomear a métrica "ancoragem literal" e declarar o que ela não prova |
| E6 | Interface do Provider: retorno indefinido (cru, envelope ou texto), truncamento (stop_reason), erro 429/529, sem política de retry ou retomada; nome do modelo pedido vs devolvido | Claude 6, 14 + Codex 6 | P2 / 8 | Resultado normalizado {texto, stop_reason, modelo devolvido}; truncamento como caso explícito; política de retry decidida e retomada por chave de Chamada, ou excluída do primeiro corte |
| E7 | Teste da API real "skipped sem chave" roda se houver chave ambiente; skips de Gateway podem esconder falha de configuração | Codex 7 + Claude 12 (+ DX X5) | P1 / 8 | Habilitação explícita para integração; suíte ordinária e Replay sempre offline; falha com causa quando habilitada e inviável; teste do payload do provider Anthropic com transporte falso |
| E8 | Lista de mudanças só na Repetição 1 é amostra única; aquisição sequencial confunde prompt com deriva do Gateway | Claude 8 + Codex 8 | P2 / 7 | Rotular como ilustrativa ou resumir por todas as Repetições; congelar e intercalar a aquisição dos extremos |
| E9 | Testes de ida e volta reproduzem o mesmo bug duas vezes; falta validação do Dataset (IDs únicos, Rótulo por Transcrição, mínimo por Rótulo, regra de desempate) e checagem de vazamento de exemplos few-shot para o Dataset | Claude 9 + Codex 9 | P2 / 7 | Contagens calculadas à mão nos testes externos; teste de validação do Dataset; proibir Transcrições do Dataset em exemplos de prompt |
| E10 | Spike sem prazo nem resultado de parada; sem plano B se o ToS for violado; Codex: sintético não é evidência de modelo | Claude 10 + Codex 10 (+ CEO D2) | P1 / 8 | Prazo curto, decisão go/no-go por escrito, alternativa sob a mesma seam; gravações sintéticas nunca contam como evidência de modelo |
| E11 | Higiene: texto do Relatório e do README inteiros contra a frase proibida (não só a tabela); sanear caracteres de controle do modelo no Relatório; UTF-8 e LF; um JSONL por Rodada em vez de ~270 arquivos | Claude 11, 13, 15, 16, 17 | P3 / 7 | Critérios de aceite dos tickets |
| Q1 | Efeito piso | — | — | ABERTA (humano) |

**Seção 1, Arquitetura.**
```
 Dataset(hash) ─┐
 Versão(hash) ──┼─> Rodada(id, estado) ─> Provider.gerar() ─> {texto, stop_reason, modelo}
 Config(params)─┘        │                                          │
                         ▼                                          ▼
            Manifesto da Rodada  <── grava ──  Chamadas (chave única)  ──> Avaliador ─> taxas ─> Relatório
                         ▲                                          │
   Replay: mesmo caminho, Provider = ler Chamadas; recusa se manifesto, hash, versão ou contagem divergirem
```
Estado da Rodada: iniciada → completa; iniciada → abortada; transição inválida: abortada → completa e completa → sobrescrita (proposta E3). Ponto único de falha: Gateway. Falha realista: 429 na chamada 61 de 90 aborta a Rodada sem retomada.

**Seção 2, Qualidade de código.** Sem código. Riscos de desenho: Avaliador com muitos casos de borda, mitigado por tabela; regra da queda e Replay compartilham o cálculo (útil, desde que os testes tenham valores calculados à mão, E9). Repetições configuráveis é YAGNI leve. Sem diagramas obsoletos.

**Seção 3, Diagrama de testes (planejado, não observado; framework desconhecido).**
```
CODE PATHS                                              USER FLOWS
[+] Rodada (provider falso)                             [+] Clone limpo -> tabela
  ├── [★★ PLANNED] linhas (a) a (f)                       └── [GAP] [→E2E] offline, sem chave/Gateway/rede
  ├── [★★ PLANNED] erro de provider aborta              [+] Reexecução com Gateway
  ├── [GAP] resposta truncada/vazia/recusa                  └── [★ PLANNED] skipped sem Gateway (falha com causa se habilitado: GAP)
  ├── [GAP] Justificativa vazia / Unicode                [+] Adicionar uma versão de prompt
  └── [GAP] fence, prosa extra, caixa do Rótulo             └── [GAP] receita testada (DX X7, opcional)
[+] Replay
  ├── [★★ PLANNED] mesmas taxas da Rodada
  ├── [★★ PLANNED] Chamadas truncadas/corrompidas
  ├── [GAP] duplicadas/extras; hash/esquema divergente
  └── [GAP] Rodada abortada não deixa nada aceito
[+] Regra da queda e lista de mudanças
  ├── [★★ PLANNED] maior, igual, menor; lista de mudanças
  └── [GAP] queda negativa, variação zero, Repetições desiguais
[+] Relatório e README
  ├── [★★ PLANNED] frase proibida ausente e limite presente (tabela gerada)
  └── [GAP] texto inteiro do Relatório e README
[+] Providers
  ├── [★ PLANNED] Gateway (skipped sem Gateway); Anthropic real (skipped)
  └── [GAP] payload Anthropic com transporte falso; opt-in; suíte offline com chave ambiente
[+] Dataset
  └── [GAP] validação (IDs, Rótulo único, mínimo por Rótulo, desempate, vazamento few-shot)

COVERAGE (planejada): 10/24 caminhos (42%) | Code paths: 9/21 | User flows: 1/3
QUALITY: ★★:8 ★:2 | GAPS: 14 (1 E2E). LLM/eval: o projeto é o próprio eval; a suíte de eval deve rodar em qualquer mudança de prompt.
```
Regressão (IRON RULE): não há comportamento existente em risco (sem código); nada a proteger. Artefato de plano de testes gravado em `~/.gstack/projects/russo11211-portfolio-ai-cx/<usuario>-claude-mattpocock-skills-setup-96cf28-eng-review-test-plan-20260924-124154.md`.

**Seção 4, Performance.** ~90 a 270 chamadas por experimento (30 Transcrições × 3 Repetições × 1 a 3 versões); latência do Gateway domina; Replay é linear e trivial. Risco: abortar a Rodada inteira num erro (E6). Sem cache nem índice.

**NOT in scope (Eng).** Publicação de pacote, CI de release e distribuição (CAR-6); framework de testes escolhido agora (fica para o spike do E8); teste estatístico formal e bootstrap (Fora de escopo 13); autenticação da origem do modelo (hashes provam consistência, não origem); retomada de Rodada se o humano excluir do primeiro corte.

**What already exists (Eng).** Nada de código. Reusa o glossário e a seam decididas na spec; o Replay pela mesma seam já evita um segundo caminho de cálculo.

**Failure Modes Registry (Eng).**

| Codepath | Falha | RESCUED | TEST | USER SEES | LOGGED |
|---|---|---|---|---|---|
| Rodada | Rodada parcial commitada | N | N | Silent | N |
| Chamada | prompt editado depois de gravar | N | N | Silent | N |
| Avaliador | resposta truncada, vazia ou recusa | N | N | Silent | N |
| Avaliador | Justificativa vazia | N | N | Silent | N |
| Replay | Chamada duplicada ou extra | N | N | Silent | N |
| Gravação | credencial ou cabeçalho dentro da Chamada | N | N | Silent | N |
| Regra da queda | variação zero, queda de 1 Transcrição | N | N | Silent (declara "mensurável") | N |
| Provider | erro HTTP | Y | Y | Mensagem | Y |
| Replay | Chamada truncada | Y | Y | Mensagem | Y |

CRITICAL GAPS: 7.

**Worktree parallelization.** Depende do spike do Gateway. Depois dele:

| Passo | Módulos | Depende de |
|---|---|---|
| Spike do Gateway | provider | nenhum |
| Dataset | dataset | nenhum (pode andar em paralelo ao spike) |
| Avaliador + Gravação/Replay + Relatório | núcleo | contratos de saída e manifesto |
| Providers (Gateway, Anthropic) | provider | spike |

Lane A: Dataset (independente). Lane B: Avaliador → Gravação/Replay → Relatório (sequencial, módulos compartilhados). Lane C: Providers (após o spike). Executar A e C em paralelo, depois B integra. Conflito: B e C compartilham o contrato de resposta do Provider (E6); fixar antes.

**TODOS.md (coleta de todas as fases).** O repositório não tem `TODOS.md` e o CLAUDE.md não prevê esse arquivo, então **não foi criado**. Deferidos: bootstrap/IC; matriz de confusão; subconjunto "casos difíceis"; baseline não-LLM (CEO D7); receita "adicionar versão", casos difíceis no topo do Dataset, inspeção de uma Transcrição (DX X7). Decisão sobre onde registrá-los é sua.

**Decision Audit Trail (Eng).**

| # | Fase | Decisão | Classe | Princípio | Motivo | Rejeitado |
|---|---|---|---|---|---|---|
| 9 | Eng | Escopo mantido, arrumação original | mecânica | P2, P5 | contratos aprovados exigem a seam única | arrumação menor |
| 10 | Eng | E1 a E11 marcados taste e não aplicados | taste | P5, CLAUDE.md | criam requisitos; o humano decide | aplicar por conta própria |
| 11 | Eng | Não criar TODOS.md | mecânica | CLAUDE.md (não inventar lugar de artefato) | fora da convenção | auto-escrever |
| 12 | Eng | Descartar a 1ª saída do Codex (português, validador rejeitou) e refazer em inglês | mecânica | regra de validação | sem marcador válido não há crédito | usar a saída rejeitada |

**Eng Completion Summary.**
```
| Step 0: Scope Challenge | scope accepted as-is (arrumação original) |
| Architecture Review     | 3 issues (integridade, estados da Rodada, contrato do Provider) |
| Code Quality Review     | 2 issues (Repetições configuráveis; testes de ida e volta) |
| Test Review             | diagram produced, 14 gaps identified |
| Performance Review      | 1 issue (abortar tudo, sem retomada) |
| NOT in scope / What exists | written / written |
| TODOS.md updates        | 0 propostas ao humano como pergunta; lista consolidada acima, arquivo não criado |
| Failure modes           | 7 critical gaps flagged |
| Unresolved decisions    | E1 a E11 + Q1 (taste, pendentes) |
| Outside voice           | codex completed (1 tentativa rejeitada pelo validador, 2ª ok), 10 concerns |
| Parallelization         | 3 lanes, 2 parallel / 1 sequential |
| Lake Score              | N/A (nenhuma pergunta de cobertura respondida pelo humano) |
```

**Implementation Tasks (Eng), propostas pendentes de aprovação:**
- [ ] **T1 (P1, human: ~2h / CC: ~15min)** — Critério de sucesso — endurecer a regra da queda (queda mínima ou contagem pareada, guarda-corpos, "pior", variação não estimável). Surfaced by: Eng E1. Files: `docs/spec/cx-prompt-lab.md`. Verify: teste da regra com casos de variação zero, queda de 1, queda negativa.
- [ ] **T2 (P1, human: ~3h / CC: ~20min)** — Gravação/Replay — manifesto versionado, estados e chave de Chamada, escrita atômica. Surfaced by: Eng E2, E3. Files: a determinar (ADR do E7). Verify: testes de adulteração, duplicadas e "Rodada abortada não deixa nada aceito".
- [ ] **T3 (P1, human: ~2h / CC: ~15min)** — Avaliador — especificar parser, casamento do Rótulo e bordas. Surfaced by: Eng E4, E5. Files: `docs/spec/cx-prompt-lab.md`. Verify: uma linha de tabela e um teste por caso.
- [ ] **T4 (P2, human: ~2h / CC: ~15min)** — Provider — resultado normalizado, truncamento, política de retry ou retomada. Surfaced by: Eng E6. Files: a determinar (ADR do E7). Verify: teste com provider falso que trunca e que falha em 429.
- [ ] **T5 (P1, human: ~1h / CC: ~10min)** — Testes — API real só com opt-in; suíte offline com chave ambiente; payload Anthropic com transporte falso. Surfaced by: Eng E7. Files: a determinar. Verify: suíte verde com chave definida e rede negada.
- [ ] **T6 (P2, human: ~2h / CC: ~15min)** — Dataset — teste de validação e proibição de vazamento few-shot; testes com contagens à mão. Surfaced by: Eng E9. Files: a determinar. Verify: teste de validação falha com Dataset inválido.
- [ ] **T7 (P1, human: ~1h / CC: ~10min)** — Spike — prazo, decisão go/no-go escrita e alternativa sob a mesma seam. Surfaced by: Eng E10. Files: `docs/spec/cx-prompt-lab.md`. Verify: decisão registrada antes do primeiro prompt.


### Exigências para a ADR do E7 (tema F, decisão do humano em 2026-09-24; não fazem parte da spec)

A ADR do E7 (`docs/adr/NNNN-...`) deve fixar, antes do E8:
1. **Quickstart testável:** de um clone limpo até a tabela impressa em no máximo 5 minutos e poucas ações, sem chave, sem Gateway e sem rede depois de instalar; o README do produto (`cx-prompt-lab/`) abre com o comando de Replay e uma saída de exemplo gerada pelo próprio Replay; runtime e dependências fixados.
2. **Erros acionáveis:** toda mensagem de erro traz problema, causa provável e próximo passo, com Rodada, Transcrição ou arquivo, e sai com código diferente de zero; Gateway ausente ou incompatível falha rápido com instrução; o motivo de cada skip diz que variável o habilita.
3. **Superfície de CLI:** comandos que espelham o glossário (Replay, Reexecução, Rodada, Repetição, Chamada), `--help`, lista de opções com default e piso (incluindo o piso de 3 Repetições), seleção do provider e do endpoint sem editar código, língua dos comandos e mensagens, e onde a suíte, o Replay e a Reexecução moram.
4. **Armazenamento:** arquivo por Chamada ou JSONL por Rodada, codificação UTF-8 e LF, saneamento do texto do modelo no Relatório, e o nome do comando de Replay (dependência das histórias 3 e 4).
5. **Contrato do Provider:** extração do texto quando a resposta vem em vários blocos, política de parada e o que o Gateway devolve de motivo de parada, modelo e temperatura (o spike confirma).
Origem: achados DX X1 a X3 do /autoplan (E5). Rastreio: CEO plan `2026-09-23-cx-prompt-lab-rerun.md`.
6. **Do gate de 2026-09-25 (critério do humano: quickstart, README verificado, CLI, códigos de saída, forma das recusas e compatibilidade de esquema vão para a ADR):** banner de modo em toda execução (`REPLAY (offline, nenhum modelo chamado)` ou `REEXECUÇÃO (ao vivo)`); saída padrão do Replay = tabela mais veredito, com opção verbosa por Repetição; caminho de override de modelo, parâmetros e URL do Gateway (flag com variável de ambiente); como descartar ou superar uma Rodada ruim sem poluir o repositório; forma fixa das recusas do Replay (Rodada ou arquivo, hash esperado e encontrado, ação, link) e códigos de saída distintos (sucesso, recusa, aborto); política de compatibilidade de esquema (versão da ferramenta na Rodada e comando de checkout); README com bloco "Verifique em 2 minutos" gerado pelo Replay, teste de não desvio e Rodada de exemplo commitada; valor do timeout por chamada.
7. **Do último gate de 2026-09-25:** EE4 (versão do avaliador no manifesto da Rodada) e EE12 (seam da Conclusão e Replay que falha alto) ficam para esta ADR. **Plano B PENDENTE:** a ADR nomeia o modelo e o provedor (categoria já escolhida pelo humano: open-weights hospedado com camada gratuita), com os limites de taxa da camada; dono: o humano; prazo: antes do início do spike, no E7.

### CEO review (E5), rerun 2026-09-24 (SELECTIVE EXPANSION; checkpoint autoplan-ceo-60Y4MF)

Entrada: spec com os overrides do gate aplicados (sha da revisão `fa798631…`). Spec Review Loop: 1 lançamento, nota 6/10, 25 achados, 0 corrigidos (ver "Reviewer Concerns" no CEO plan). Vozes: Claude CEO (nativo) completo, 11 achados; Codex CEO (externo, comando gerado literal com o contrato de idioma) completo, 7 achados, validador ok.

```
CEO DUAL VOICES — CONSENSUS TABLE (rerun):
  Dimension                             Claude  Codex  Consensus
  1. Premises valid?                    NAO     NAO    CONFIRMED (ToS do Gateway sem plano nomeado; premissa de contratação sem evidência)
  2. Right problem to solve?            PARCIAL PARCIAL CONFIRMED (ambos: reenquadrar para a história e a decisão, não para a máquina)
  3. Scope calibration correct?         NAO     NAO    CONFIRMED (maquinaria de integridade e provider Anthropic pesam mais que a evidência legível)
  4. Alternatives sufficiently explored? NAO    NAO    CONFIRMED (held-out ou ordem de commit; baseline não-LLM; ferramenta de eval pronta)
  5. Competitive/market risks covered?  PARCIAL —      single-voice (Claude: eval de LLM virou commodity; o diferencial é a história)
  6. 6-month trajectory sound?          NAO     NAO    CONFIRMED (resultado nulo em repositório grande; versão pior parecendo recomendada)
CONFIRMED 5 de 6; 1 single-voice.
```

**Achados novos da rerun (todos pendentes do humano; nada aplicado além dos overrides):**

| ID | Achado | Vozes | Classe |
|---|---|---|---|
| R1 | **Regra de melhora ignora acerto**: pode declarar "melhora" com Erro de acerto subindo muito; formato conta contra o sucesso. Relacionado ao 1.3 (parser estrito x efeito piso) | Codex 2 + Claude F6 (Erro de acerto co-primário) + Revisor 1.3 | USER CHALLENGE (as duas vozes pedem mudar a regra que o humano aprovou) |
| R2 | Cortar maquinaria de integridade (matriz de recusa de esquema, testes de aborto) e o provider Anthropic do primeiro corte; verificar se a integração real é requisito | Claude F1, F4 + Codex 6 | USER CHALLENGE (contraria o tema B e a história 24) |
| R3 | Gate de termos primeiro, plano B nomeado (modelo e provedor) em vez de "por exemplo" | Claude F3 (crítico) + Codex (indireto) | taste |
| R4 | Held-out congelado ou prova pela ordem de commit (v0 e sua medição antes de v1) | Claude F5 + Codex 4 | taste |
| R5 | Piloto de 5 a 10 Transcrições para ver se v0 falha de verdade antes de congelar o Dataset; baseline não-LLM e prompt curto competente | Claude F6, F7 + Codex 5 | taste |
| R6 | História primeiro: case study e resumo de uma página como entregável principal; separar "última testada" de "recomendada" | Claude F2 + Codex 6, 7 | taste |
| R7 | Ferramenta de eval pronta (promptfoo, inspect): justificar no memo por que construir | Claude F10 | taste (voz única) |
| R8 | Métrica de "Alucinação" estreita e manipulável; matriz de confusão | Codex 3, 4 | taste; matriz continua adiada |

**Seções 1 a 11 (rerun, resumo do que mudou):** 1 Arquitetura: manifesto, hashes, chave única e escrita atômica agora estão na spec; falta decidir o armazenamento (ADR). 2 Erros: fechados truncada, vazia, recusa, Justificativa vazia, Rodada abortada e credencial; aberto: o spike não confirma stop_reason, modelo e temperatura. 3 Segurança: credenciais fora das Chamadas (teste); ToS do Gateway segue como risco crítico sem plano nomeado (R3). 4 Fluxo: bordas de parsing agora têm regra; a interação parser x piso é a lacuna real (R1). 5 Qualidade: definição de Rodada x Repetição ainda solta. 6 Testes: tabela a a f, opt-in, adulteração e validação do Dataset planejados; falta teste da conclusão em conflito (piso x piora). 7 Performance: Rodada de 60 a 90 Chamadas abortada sem retomada é frágil, decisão do humano. 8 Observabilidade: manifesto e modelo devolvido resolvem a reconstrução. 9 Deploy: sem serviço; clone limpo vira critério do E12. 10 Trajetória: reversibilidade 2/5; risco de resultado nulo. 11 Design: SKIPPED (sem UI).

**Failure Modes (rerun):** Regra de melhora degenera (v0 vira Violação de formato): RESCUED N, TEST N, Silent: CRITICAL. Gateway sem stop_reason, modelo ou temperatura (não verificado): RESCUED N, TEST N: CRITICAL até o spike. Demais linhas da rodada anterior estão fechadas pelos overrides. CRITICAL GAPS: 2.

**Interpretações minhas que entraram na spec sem seu aval (a decidir no gate):** ver seção "Interpretações tomadas pelo agente" do CEO plan.

**Decision Audit Trail (rerun):** 13: aplicar só os overrides e registrar os achados novos como pendentes (CLAUDE.md: não inventar requisito); 14: R1 e R2 como User Challenge; 15: a spec e o bloco ceo não mudam nesta rerun, então sem novo amend-input.

### DX review (E5), rerun 2026-09-24 (DX POLISH; checkpoint autoplan-dx-Jo1DXc)

Entrada: spec com os overrides aplicados (sha da revisão `fa798631…`). Vozes: Claude DX (nativo) completo, 11 achados (2 altos); Codex DX (externo, comando gerado com o contrato de idioma) completo, 6 achados, validador ok. O tema E e o acréscimo 8 tocam o DX, por isso a lente foi reaberta. Nada foi aplicado à spec nesta fase (bloco `autoplan-accepted:dx` continua `None`).

```
DX DUAL VOICES — CONSENSUS TABLE (rerun):
  Dimension                           Claude  Codex  Consensus
  1. Getting started < 5 min?          NAO     NAO    CONFIRMED gap (sem critério mensurável nem Rodada de exemplo commitada; vira exigência da ADR do E7)
  2. API/CLI naming guessable?         NAO     NAO    CONFIRMED gap (mapa conceito para comando fica para a ADR; banner de modo Replay vs Reexecução sugerido)
  3. Error messages actionable?        PARCIAL PARCIAL CONFIRMED partial (erros do provider e do Replay agora têm forma; faltam código de saída, hash esperado vs encontrado, comando de reinício)
  4. Docs findable & complete?         NAO     NAO    CONFIRMED gap (README com exemplo verificado contra a saída real; link a partir da raiz)
  5. Upgrade path safe?                —       NAO    single-voice (Codex: versão de esquema sem política de compatibilidade)
  6. Dev environment friction-free?    PARCIAL SIM    DISAGREE (Claude: caminho de override de modelo, parâmetros e URL não dito; Codex: offline e opt-in adequados) -> taste
CONFIRMED 4 de 6 (com o item 3 parcial); 1 disagree; 1 single-voice.
```

**Achados novos (pendentes do humano; nada aplicado):**

| ID | Achado | Vozes | Recomendação |
|---|---|---|---|
| X8 | README "Verifique em 2 minutos" com o comando e a tabela esperada, gerado pelo Replay (teste de que não desvia); Rodada de exemplo commitada; link a partir do README da raiz (que hoje descreve a fábrica; o do produto ainda não existe) | Claude 1.1, 4.1 + Codex 1, 2 | Exigência da ADR do E7 já registrada (item 1); acrescentar a Rodada de exemplo e o teste de não desvio |
| X9 | Recusas do Replay sem forma fixa: falta nomear Rodada ou arquivo, hash esperado vs encontrado, ação, link para "Troubleshooting", códigos de saída distintos (sucesso, recusa, aborto); Rodada abortada: prazo do provider, progresso e o comando exato para começar outra, avisando que as Chamadas concluídas serão repetidas | Claude 3.1, 3.2 + Codex 4 | Exigência da ADR do E7 (item 2); testes que asseguram conteúdo da mensagem |
| X10 | Rejeitar esquema não é estratégia de atualização: registrar a versão da ferramenta que produziu a Rodada e publicar política de compatibilidade (releases e comando de checkout) | Codex 5 | Voz única; vira item da ADR |
| X11 | Banner de modo em toda execução (`REPLAY (offline, nenhum modelo chamado)` ou `REEXECUÇÃO (ao vivo via Gateway)`); saída padrão = tabela + conclusão; opção verbosa para detalhe por Repetição | Claude 2.1, 2.2 | Exigência da ADR do E7 |
| X12 | Caminho de override de modelo, parâmetros e URL do Gateway (flag com variável de ambiente), o parser estrito documentado como não-configurável de propósito, e como descartar uma Rodada ruim ou supersedida sem poluir o repositório | Claude 5.1, 5.2 | Exigência da ADR do E7 |
| X13 | Teste da frase proibida com lista de variantes (inglês, "validated", "validado na") além do texto exato | Claude 4.2 | Ampliar o teste já aprovado (acréscimo 8) |
| X14 | O rótulo de melhora pode endossar um classificador pior (queda de Alucinação com Erro de acerto subindo) | Codex 6 (+ CEO R1) | Mesma decisão do R1; humano decide |

**Scorecard (rerun):** Getting Started 3/10 (antes 3), API/CLI 4 (4), Error Messages 6 (3), Documentation 4 (3), Upgrade Path 3 (2), Dev Environment 5 (3), Community 5 (5), DX Measurement 4 (4). Overall DX 4,3/10 (antes 3,4). TTHW: continua não mensurável (produto inexiste), estimativa acima de 10 min, alvo de 5 min registrado como exigência da ADR do E7. Competitive Rank: Red Flag até a ADR fechar o quickstart. Mode: DX POLISH. Persona e narrativa: inalteradas da rodada anterior.

### Eng review (E5), rerun 2026-09-24 (checkpoint autoplan-eng-WdjMKC)

Entrada: spec com os overrides aplicados (sha da revisão `fa798631…`). Vozes: Claude Eng (nativo) completo, 21 achados (3 altos); Codex Eng (externo, comando gerado com o contrato de idioma) completo, 8 achados (4 altos), validador ok. Nenhum achado foi aplicado; o bloco `autoplan-accepted:eng` continua `None`. Scope Challenge: escopo mantido, arrumação original (uma seam, um método).

```
ENG DUAL VOICES — CONSENSUS TABLE (rerun):
  Dimension                        Claude   Codex    Consensus
  1. Architecture sound?           PARCIAL  PARCIAL  CONFIRMED partial (seam e Provider ok; vocabulário de motivo de parada, hierarquia Rodada x Repetição e versão do avaliador indefinidos)
  2. Test coverage sufficient?     NAO      NAO      CONFIRMED gap (precedência da conclusão, Unicode, normalização de resposta nos dois providers, mecanismo de rede negada)
  3. Performance risks addressed?  PARCIAL  PARCIAL  CONFIRMED partial (abortar Rodada inteira sem retomada; custo aceito precisa ser dito)
  4. Security threats covered?     NAO      —        single-voice (Claude: corpo bruto, token, Markdown, caminho; Codex: hashes provam consistência, não autenticidade)
  5. Error paths handled?          PARCIAL  PARCIAL  CONFIRMED partial (ciclo de vida da publicação atômica sem exigir que o registro de aborto consiga gravar)
  6. Deployment risk manageable?   SIM      PARCIAL  DISAGREE (Claude: sem bloqueio; Codex: plano B conflita com "toda chamada pelo Gateway" e runtime, comando e código de saída não fixados) -> taste
CONFIRMED 4 de 6; 1 disagree; 1 single-voice.
```

**Achados novos da rerun (pendentes do humano):**

| ID | Achado | Vozes | Recomendação (não aplicada) |
|---|---|---|---|
| EE1 | Melhora pode certificar classificador pior (a taxa de Erro de acerto exclui respostas malformadas e não é o complemento da acurácia); nomear "redução de alucinação" ou exigir não regressão de acurácia sobre todas as Transcrições | Codex 1 (+ CEO R1, DX X14) | USER CHALLENGE R1 (quatro fases concordam); humano decide |
| EE2 | Comparabilidade: gravar modelo e parâmetros não exige que combinem entre versões nem dentro do experimento; ligar Dataset, política de Rótulo, pedido renderizado, modelo pedido e devolvido, parâmetros e política de Repetição; rejeitar ou rotular "confundido"; avisar se o modelo devolvido varia dentro da Rodada; checar cache do Gateway | Codex 2 + Claude T6, H3 | taste |
| EE3 | Completude por produto cartesiano exato (par Transcrição x Repetição), com uma hierarquia única (experimento, execução da versão, Repetição, Chamada); e qual conjunto de Rodadas entra no Relatório | Codex 3 + Revisor 2.5 | taste |
| EE4 | Versão da semântica de medição: registrar versão do avaliador e da regra de conclusão no manifesto; commit chronology é evidência separada | Codex 4 | taste (voz única) |
| EE5 | Vocabulário fechado de motivo de parada, mapeado dentro de cada provider, e teste de contrato rodando os dois com o mesmo transporte falso; regras para vários blocos de texto | Claude A1 + Codex 6 | taste |
| EE6 | Precedência da conclusão (efeito piso, piora, melhora, inconclusivo), comparação por pares consecutivos e Repetições mínimas por versão; a média não é inteira e conflita com "contagens inteiras" | Claude E1, E2 + Codex 5 + Revisor 1.1, 1.2 | Decisão do humano: sugiro ordem piso, piora, melhora, inconclusivo, comparação sobre somas cruzadas |
| EE7 | Ciclo de vida da publicação: reservar diretório único, escrever, validar, publicar; diretório interrompido conta como incompleto sem exigir que o registro de aborto consiga gravar; ID de Rodada único e caracteres validados | Codex 7 + Claude E3, S4 | taste |
| EE8 | Plano B conflita com "toda chamada real passa pelo Gateway"; nomear um provider viável e emendar a restrição antes do spike | Codex 8 + CEO R3 | taste |
| EE9 | Testes: casos Unicode, mecanismo de rede negada, controle positivo de credencial, definição de "aparece" nos exemplos few-shot, contagem esperada divergente e modelo divergente na integridade | Claude T1 a T5, T2 | taste (voz única) |
| EE10 | Segurança: gravar só campos normalizados (nunca o corpo HTTP bruto), token do Gateway no gitignore com varredura, escapar Markdown no Relatório, validar caracteres de caminho | Claude S1 a S4 | taste (voz única) |
| EE11 | Ancoragem literal x escape JSON e aspas tipográficas: pode dominar a Alucinação de v0; registrar como limitação no case study e fazer verificação rápida no Dataset durante o spike | Claude H1, H2 | taste (voz única); liga ao 1.3 |
| EE12 | Nomear a Conclusão como módulo separado (função pura sobre contagens) e fazer o provider de Replay falhar alto quando faltar chave | Claude A2, A3 | taste (voz única) |
| EE13 | História 31 (margem da Reexecução) sem consumidor; confirmar que é só descritiva | Claude H4 (+ Revisor 2.3) | decisão do humano |

**Diagrama de testes (planejado, framework desconhecido):** 27 caminhos, 11 planejados (★★:9, ★:2), 16 lacunas (1 E2E): as 14 anteriores mais precedência da conclusão e normalização do stop_reason nos dois providers. Cobertura planejada 41% (11/27). Plano de testes atualizado em `~/.gstack/projects/russo11211-portfolio-ai-cx/<usuario>-claude-mattpocock-skills-setup-96cf28-eng-review-test-plan-*.md` (arquivo mais recente).

**Failure Modes (rerun):** fechados pelos overrides: Rodada parcial, prompt editado, resposta truncada ou vazia, Justificativa vazia, duplicadas, credencial. Abertos: regra de melhora degenera com parser estrito (R1/1.3); conclusão com precedência indefinida (EE6); comparação entre versões com modelo devolvido diferente (EE2); Gateway sem stop_reason, modelo ou temperatura (spike). CRITICAL GAPS: 4. Nova linha: ciclo de vida da publicação sem recuperação (Y parcial, N teste, visível). 

**Failure Modes Registry (rerun):**

| Codepath | Falha | RESCUED | TEST | USER SEES | LOGGED |
|---|---|---|---|---|---|
| Conclusão | melhora com Erro de acerto subindo | N | N | Silent | N |
| Conclusão | piso, piora e melhora ao mesmo tempo | N | N | Silent | N |
| Comparação | modelo devolvido diferente entre versões | N | N | Silent | N |
| Spike | Gateway sem stop_reason, modelo ou temperatura | N | N | Bloqueio | N |
| Publicação | crash antes do manifesto | Y (Replay recusa) | N | Mensagem | N |
| Provider | erro HTTP | Y | Y | Mensagem | Y |

**Paralelização (rerun):** 3 lanes, 2 em paralelo e 1 sequencial; nova dependência: o contrato do Provider (EE5) e o da Conclusão (EE6) devem fechar antes das lanes B e C.

**NOT in scope (Eng, rerun):** verificação independente da origem do modelo; publicação de pacote e CI de release (CAR-6); teste estatístico formal; JSONL por Repetição vs arquivo por Chamada (ADR do E7).

**TODOS.md:** não criado (instrução do humano em 2026-09-24). Adiadas ficam no CEO plan.

**Decision Audit Trail (Eng, rerun):** 16: escopo mantido, arrumação original (P2, P5); 17: EE1 a EE13 pendentes, EE1 como User Challenge junto com R1 (cross-fase); 18: aplicar só os overrides (CLAUDE.md, não inventar requisito); 19: vozes externas com o comando gerado e contrato de idioma, validadas na 1ª tentativa.

**Eng Completion Summary (rerun):**
```
| Step 0: Scope Challenge | scope accepted as-is (arrumação original) |
| Architecture Review     | 5 issues (stop_reason, hierarquia, versão do avaliador, seam Conclusão, provider de Replay) |
| Code Quality Review     | 2 issues (precedência da conclusão; média x contagens inteiras) |
| Test Review             | diagram produced, 16 gaps identified |
| Performance Review      | 1 issue (abortar sem retomada; custo aceito precisa ser dito) |
| NOT in scope / What exists | written / written (sem código) |
| TODOS.md updates        | 0 propostas como pergunta; arquivo não criado |
| Failure modes           | 4 critical gaps flagged |
| Unresolved decisions    | EE1 a EE13 (EE1 = User Challenge), R1 a R8, X8 a X14, Q1 resolvida |
| Outside voice           | codex completed, 8 concerns |
| Parallelization         | 3 lanes, 2 parallel / 1 sequential |
| Lake Score              | N/A |
```


### Decisões do humano no gate final, 2026-09-25 (aplicadas nesta rodada)

- **D1:** e + f. Guarda de acurácia na regra de melhora, v0 com contrato JSON explícito e piloto de 5 a 10 Transcrições antes de congelar o Dataset. Parser estrito mantido.
- **D2:** a. Manter a maquinaria de integridade e o provider Anthropic.
- **D3 aprovadas:** precedência piso, piora, melhora, inconclusivo; piora por somas cruzadas; veredito só para v0 × versão final, com pares intermediários informativos; mínimo de 3 Repetições para toda versão; spike de 1 dia com gate de termos primeiro, plano B com modelo e provedor nomeados e conferência de modelo, motivo de parada e temperatura; sem retentativa, com timeout, progresso e reinício documentados; pelo menos 1 Transcrição por Rótulo; regra de novo experimento com o Relatório mostrando todas as Rodadas.
- **D3 não citadas (nada aplicado além do que já estava; listadas de novo no próximo gate com recomendação):** queda de 2 Transcrições e Violação de formato lidas no pior caso; efeito piso por qualquer Repetição de v0; parser estrito (Rótulo aparado e com caixa, campos extras ignorados); Justificativa vazia como Violação de formato; provider Anthropic desabilitado neste plano.
- **D4:** restos marcados como "superado" sem apagar (histórias 17, 18, 19 e 31 com nota; 28 reescrita; enunciado Anthropic alinhado ao opt-in; títulos e tabelas do Review record marcados).
- **D5:** critério de classificação abaixo.
- **Nomes do plano B:** a spec exige modelo e provedor nomeados na decisão go/no-go antes do spike, mas os nomes não foram fornecidos e não foram inventados: preencher.

### Situação dos achados R3–R8, X8–X14 e EE2–EE13 (classificação por critério do humano, 2026-09-25)

| Achado | Resumo | Destino |
|---|---|---|
| R1 (= EE1 = X14) | melhora com acerto pior; parser estrito x efeito piso | SPEC (D1 e+f: guarda de acurácia, contrato explícito em v0, piloto) |
| R2 | cortar maquinaria e provider Anthropic | MANTIDO (D2 a) |
| R3 | gate de termos primeiro e plano B nomeado | SPEC (spike) |
| R4 | held-out ou prova pela ordem de commit | ADIADO |
| R5 | piloto de v0 | SPEC (piloto); baseline não-LLM e prompt curto competente: ADIADO |
| R6 | história primeiro; separar "última testada" de "recomendada" | ADIADO |
| R7 | ferramenta de eval pronta | ADIADO |
| R8 | métrica de alucinação estreita; matriz de confusão | ADIADO |
| X8 | README verificado e Rodada de exemplo | ADR do E7 |
| X9 | forma das recusas e códigos de saída | ADR do E7; timeout, progresso e reinício de Rodada abortada: SPEC |
| X10 | compatibilidade de esquema | ADR do E7 |
| X11 | banner de modo e saída padrão | ADR do E7 (CLI) |
| X12 | overrides e descarte de Rodada | overrides: ADR do E7; descarte de Rodada: SPEC (rodada 4, gate de 2026-09-25) |
| X13 | variantes da frase proibida | ADIADO |
| EE2 | comparabilidade entre versões (modelo e parâmetros) | SPEC (rodada 4, gate de 2026-09-25) |
| EE3 | hierarquia Rodada e Repetição; membership exato | SPEC (rodada 4, gate de 2026-09-25) |
| EE4 | versão do avaliador no manifesto | ADR do E7 (gate de 2026-09-25) |
| EE5 | vocabulário fechado de motivo de parada | SPEC (contrato de saída) |
| EE6 | precedência e pares | SPEC |
| EE7 | ciclo de vida da publicação | ADIADO (Rodada abortada e não retomável já na spec) |
| EE8 | plano B vs restrição do Gateway | SPEC (exceção declarada e plano B nomeado) |
| EE9 | testes extras (Unicode, rede negada, controle de credencial, few-shot) | ADIADO |
| EE10 | segurança (corpo bruto, token, Markdown, caminho) | ADIADO |
| EE11 | ancoragem literal x escape JSON | SPEC (rodada 4, gate de 2026-09-25); conferências do spike: SPEC |
| EE12 | seam Conclusão e Replay que falha alto | ADR do E7 (gate de 2026-09-25) |
| EE13 | margem da história 31 | SPEC (nota na história 31) |

Adiados sem arquivo próprio (`TODOS.md` não criado): a lista acima e o CEO plan são o registro; o humano leva ao Linear.

### Decisões do último gate do E5, 2026-09-25 (rodada 4 do CEO, checkpoint autoplan-ceo-uCJMlC)

- **(a)** Precedência do veredito v0 × versão final: piora → efeito piso → melhora → inconclusivo (substitui a ordem aprovada em D3). Aplicada no bloco `autoplan-accepted:ceo`.
- **(b)** Plano B: categoria "modelo open-weights hospedado com camada gratuita". Modelo e provedor: PENDENTES; dono: o humano; prazo: antes do início do spike, no E7; exigência 7 da ADR do E7. Substitui a pendência "Nomes do plano B" acima.
- **(c)** Aprovadas as interpretações 1, 2, 3, 8 e 11 e os acréscimos do ciclo 3 (guarda de acurácia c; contrato JSON explícito em v0 e piloto; piso de 3 Repetições para toda versão; Relatório com todas as Rodadas; vocabulário fechado de motivo de parada; timeout, progresso e reinício; gate de termos primeiro). Nenhuma mudança de texto.
- **(d)** Reclassificação do D5: EE11, EE2, EE3 e o descarte de Rodada (X12) entram na SPEC nesta rodada; EE4 e EE12 vão para a ADR do E7 (exigência 7). Achados novos das vozes do ciclo 3: adiados ou ADR do E7, sem discussão.
- Encerramento sem reabrir DX/Eng por decisão do humano em 2026-09-25. O protocolo do /autoplan pede Eng depois de qualquer rerun do CEO; esta rodada não roda Eng nem novas vozes do CEO, por decisão do humano.
- Vozes da rodada 4: N/A, dispensadas pelo humano em 2026-09-25 (sem novo revisor nativo nem Codex sobre a spec desta rodada; as vozes do ciclo 3 rodaram sobre a versão anterior).
- Linear/CAR-8 não foi tocado. O E6 não começou.

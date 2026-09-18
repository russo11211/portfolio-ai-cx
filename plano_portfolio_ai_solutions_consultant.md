# Plano de Fechamento de Gap — AI Solutions Consultant / Prompt Engineer

**Criado em:** 2026-09-16
**Status:** Fase 0 concluída (2026-09-16). Fases 1-4 ainda serão refinadas individualmente antes da execução de cada uma. Monorepo do portfólio: [github.com/russo11211/portfolio-ai-cx](https://github.com/russo11211/portfolio-ai-cx).
**Baseado em:** diagnóstico honesto de prontidão cruzando 15 vagas-alvo (`trilha2_ai_engineer_vagas.md`), inventário real de commits em repositórios git, e consulta ao vault Obsidian.

## Por que este alvo (e não "Engenheiro de IA Sênior" full-stack)

O diagnóstico mostrou que as vagas de Engenheiro de IA pleno/sênior (Capgemini, IBM, Bain, NCS, GFT, Mercado Libre) exigem um histórico de engenharia de software/ML em produção que não existe na trajetória de carreira (consultoria técnica CX/CRM, não desenvolvimento). Perseguir essas vagas diretamente hoje tem alta chance de reprovação técnica.

O combo real e comprovável é: (a) 8 anos de consultoria técnica em contact center/CRM/IVR, domínio genuíno de jornadas de atendimento, troubleshooting N2/N3, integração de sistemas; (b) fluência operacional real e verificada com Claude Code e ferramentas agentic (não fabricada — confirmada por auditoria de commits e investigação do vault). Isso mapeia diretamente para papéis de **AI Solutions Consultant** e **Prompt Engineer** — que valorizam ponte entre negócio/CX e IA aplicada, mais do que profundidade de ML engineering em produção.

Vagas da trilha 2 mais alinhadas a este reposicionamento: Porto (Engenheiro de IA Sênior — na prática produto/EX), e a postura consultiva valorizada por EY e Bain.

## Gaps identificados (o que este plano fecha)

| Gap | Status atual |
|---|---|
| Prompt engineering sistemático | Só intenção registrada, nunca praticado |
| Integração real com API de LLM (Anthropic/OpenAI) | Zero evidência |
| RAG | Zero implementação |
| Bancos vetoriais | Zero |
| Evals aplicados a saídas de LLM | Só evidência adjacente (checker do vault, não sobre LLM) |
| Agentes de IA / tool-calling | Só uso operacional de terceiros, nunca construído |
| MCP | Só teórico (bookmarks) |
| Python aplicado a IA (portfólio) | Fraco — nenhum projeto próprio substancial |
| Narrativa/case studies provando a fluência real com Claude Code | Existe a prática, falta a documentação pública |

## Estrutura do plano — 4 fases, ~8-10 semanas, projetos pequenos e sequenciais

Cada projeto deve virar um repositório público próprio (não dentro do CLTech), com README bom, e — quando fizer sentido — um case study curto (post de LinkedIn ou artigo) conectando o projeto ao domínio de CX/consultoria. Todo projeto deve mencionar explicitamente o uso de Claude Code no processo de construção (isso é, em si, parte da prova de habilidade visada pelas vagas que citam Claude Code/Copilot).

### Fase 0 — Higiene (antes de começar, ~1-2 dias)
- [x] Reescrever a seção "Formação Complementar" do `CLAUDE.md` para refletir só o que é verificável hoje (fluência Claude Code, disciplina de avaliação determinística) e marcar RAG/API de LLM/MCP como "em construção — ver portfólio".
- [x] Criar uma organização/pasta única no GitHub pessoal para os projetos de portfólio de IA — decidido: monorepo único em [github.com/russo11211/portfolio-ai-cx](https://github.com/russo11211/portfolio-ai-cx), com uma subpasta por projeto (Fase 1: `cx-prompt-lab/`, Fase 2: `portfolio-rag-assistant/`, Fase 3: `contact-center-agent-toolkit/`).

### Fase 1 — Prompt Engineering + Evals (semanas 1-2)
**Projeto: "CX Prompt Lab"**
- Objetivo: construir uma biblioteca versionada de prompts para um caso de uso real de contact center (ex: classificação de intenção de chamada, triagem de URA, resumo de atendimento) usando a API da Anthropic diretamente.
- Skills comprovadas: prompt engineering, integração com API Anthropic, evals aplicados a LLM.
- Requisito de vaga endereçado: Porto ("engenharia de prompt avançada", "identificação de vieses e alucinações"), NCS/GFT (Anthropic API), Bain/Caju (evals).
- Entregável concreto: repo com `prompts/v0..v3`, script de eval em Python rodando um dataset de 20-30 exemplos de teste (ex: transcrições fictícias de atendimento) e métricas de acerto/alucinação por versão — mesmo padrão do "vault-fine-tuning-playbook" que você já validou, agora aplicado a saídas de LLM de verdade.
- Case study: "Como medi e reduzi alucinação em classificação de intenção de atendimento com engenharia de prompt iterativa".

### Fase 2 — Integração de LLM + RAG (semanas 3-4)
**Projeto: "Portfolio RAG Assistant"**
- Objetivo: chatbot que responde perguntas sobre sua própria carreira/portfólio usando RAG sobre seus documentos reais (CV, cases, este repo CLTech como fonte).
- Skills comprovadas: LLM API integration, RAG, banco vetorial.
- Requisito de vaga endereçado: praticamente todas as 15 vagas citam RAG; Caju/NCS citam vector DB nominalmente (Pgvector/Pinecone/Qdrant).
- Entregável concreto: app pequeno (CLI ou interface web simples) usando Claude API + Chroma ou pgvector, com README explicando arquitetura de retrieval.
- Case study: "RAG aplicado a um caso de auto-atendimento" (ponte direta com domínio de IVR/URA).

### Fase 3 — Agentes + MCP (semanas 5-6)
**Projeto: "Contact Center Agent Toolkit"**
- Objetivo: agente simples com tool-calling que resolve uma tarefa de atendimento (ex: consultar status de chamado, decidir escalonamento) + um servidor MCP mínimo expondo essa ferramenta.
- Skills comprovadas: agentes de IA, tool-calling, MCP (hands-on, não teórico).
- Requisito de vaga endereçado: EY Sênior e Solutis exigem MCP como obrigatório; quase todas exigem agentes.
- Entregável concreto: repo com servidor MCP + agente cliente, README com diagrama de arquitetura, gif/demo curto.
- Case study: "De URA a agente de IA: aplicando 8 anos de roteamento de atendimento a arquiteturas agentic modernas" — esta é a narrativa mais forte de todo o plano, veste seu domínio real por cima da técnica nova.

### Fase 4 — Consolidação de portfólio (semanas 7-8)
- [ ] Reunir os 3 projetos + o CLTech (como "opero e customizo sistemas agentic de produção", não como autoria) em uma página/README de portfólio único.
- [ ] Escrever 2-3 case studies em formato STAR conectando projetos à experiência de consultoria.
- [ ] Atualizar CV e LinkedIn com a nova narrativa "AI Solutions Consultant" / "Prompt Engineer" apoiada em evidência real.
- [ ] Recandidatar-se à vaga da Porto com o portfólio pronto; reavaliar EY/Bain com a narrativa consultiva reforçada.

## Regras do plano
- Nenhum projeto deve ficar só documentado — cada fase termina com código funcional publicado.
- Nenhuma alegação nova entra no CV sem um repo público que a sustente.
- Cada projeto usa Claude Code explicitamente no processo (e isso é citado no README) — reforça o pilar mais forte já comprovado.
- Revisitar este plano a cada fase concluída para reavaliar prontidão contra as 15 vagas.

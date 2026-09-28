# 0002. Spike do Gateway (CLIProxyAPI local): decisão go/no-go (CAR-9, T1)

Status: método de autenticação decidido; decisão técnica pendente
Ticket: CAR-9 · Relacionada: ADR 0001 (Plano B e contrato do Provider)

## 1. Método de autenticação e gate de termos (decisão registrada em 2026-09-28, antes de instalação e de código do spike)

- **Método escolhido pelo humano:** OAuth da assinatura Claude para uso com o CLIProxyAPI local (`-claude-login`). Nenhuma credencial foi solicitada ou inserida neste registro.
- **Decisão e critério do humano:** escolheu OAuth da própria assinatura Claude e que **não impeça o spike nem cause NO-GO automático**. Para CAR-9, a regra anterior da spec que fazia dos termos uma pré-condição eliminatória é substituída pela emenda explícita ao fim da spec. O gate registra o método e essa decisão antes da instalação; o GO/NO-GO final dependerá das conferências técnicas reais, em especial modelo devolvido, motivo de parada, temperatura e preservação do system prompt.
- **Risco e limites:** o risco aberto 3 da spec permanece **ABERTO**; resultado técnico positivo não é prova de conformidade com termos. A autorização para o método não antecipa o ok específico exigido para cada commit e para a instalação. Os critérios CA1–CA5 continuam pendentes de conferência no ticket e das evidências reais do spike.
- **Plano B já nomeado antes do spike:** Groq, Llama 3.3 70B, camada gratuita, conforme [ADR 0001](0001-arquitetura-cx-prompt-lab.md). Seus limites de taxa ainda estão **NÃO VERIFICADOS**.

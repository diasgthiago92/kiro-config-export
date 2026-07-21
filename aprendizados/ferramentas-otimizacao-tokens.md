# Ferramentas de Otimização de Tokens

**Data:** 20/07/2026

## Contexto

Avaliação de 3 projetos open source para reduzir consumo de tokens no uso do Claude/Kiro CLI.

## Ferramentas Avaliadas

### 1. Caveman
- **O que faz:** System prompt que força respostas mais diretas, sem filler e markdown desnecessário.
- **Redução alegada:** ~65% nos tokens de saída.
- **Veredicto:** ❌ Redundante — o Kiro CLI já opera com instruções de concisão no system prompt. Aplicar por cima pode prejudicar outputs que precisam ser completos (código, specs, relatórios).

### 2. RTK — Rust Token Killer
- **O que faz:** Proxy que filtra e comprime outputs de terminal (git, npm, builds, Docker, logs) antes de entrar no contexto.
- **Veredicto:** ✅ Já usamos — instalado em `/opt/homebrew/bin/rtk`. Garantir que intercepta 100% dos outputs relevantes.

### 3. Context Mode
- **O que faz:** Camada MCP que processa outputs extensos em ambientes isolados. Apenas resultados relevantes entram no contexto; histórico de sessão ajuda na recuperação pós-compactação.
- **Veredicto:** 🔍 Investigar — potencialmente útil para nossos bridges (postgres, trino, atlassian, google) que retornam dados volumosos. Risco: filtro pode descartar informação relevante sem aviso.

## Resumo

| Ferramenta | Decisão | Motivo |
|------------|---------|--------|
| Caveman | Não usar | Já temos isso nativo |
| RTK | Já usamos | Garantir cobertura total |
| Context Mode | Investigar | Pode ajudar com outputs volumosos dos bridges |

## Aprendizado-chave

O maior gargalo de tokens no nosso setup não é a verbosidade das respostas (já controlada), mas sim os **inputs volumosos** vindos dos bridges MCP (queries SQL, listagens Confluence/Drive, outputs de rotinas). A otimização mais efetiva atua na camada de entrada, não na saída.

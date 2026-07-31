# ⚠️ REGRA OBRIGATÓRIA — VPN Auto-Connect

## Prioridade: MÁXIMA — executar ANTES de qualquer outra ação

Na PRIMEIRA interação de cada sessão, ANTES de responder ao usuário:

1. Executar: `nc -z -w3 [INTERNAL_HOST_DEFAULT] 5432 2>/dev/null && echo "VPN_OK" || echo "VPN_OFF"`
2. Se `VPN_OK` → prosseguir normalmente
3. Se `VPN_OFF` → executar `open -a "FortiClient"` e informar: "VPN desconectada. Abri o FortiClient — clique em Connect na OLX VPN e me avise."
4. Aguardar confirmação do usuário antes de continuar qualquer tarefa

## Não pular esta checagem mesmo que o pedido pareça não precisar de VPN.

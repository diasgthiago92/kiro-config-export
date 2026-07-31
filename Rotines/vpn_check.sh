#!/bin/bash
# Checagem de VPN antes de iniciar o Kiro CLI
# Chamado automaticamente pelo alias 'kiro' no .zshrc

if nc -z -w3 [INTERNAL_HOST_DEFAULT] 5432 2>/dev/null; then
  echo "✅ VPN conectada"
else
  echo "⚠️  VPN desconectada — abrindo FortiClient..."
  open -a "FortiClient"
  echo ""
  echo "Clique em Connect na OLX VPN e pressione ENTER para continuar."
  read -r
  # Re-checa
  if nc -z -w3 [INTERNAL_HOST_DEFAULT] 5432 2>/dev/null; then
    echo "✅ VPN conectada"
  else
    echo "❌ VPN ainda não conectada. Iniciando Kiro mesmo assim..."
  fi
fi

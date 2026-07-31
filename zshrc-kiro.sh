# Kiro CLI pre block. Keep at the top of this file.
[[ -f "${HOME}/Library/Application Support/kiro-cli/shell/zshrc.pre.zsh" ]] && builtin source "${HOME}/Library/Application Support/kiro-cli/shell/zshrc.pre.zsh"

# RTK wrappers — must come before system bins
export PATH="$HOME/bin/rtk-wrappers:$HOME/.local/bin:$PATH"


# Kiro CLI post block. Keep at the bottom of this file.
[[ -f "${HOME}/Library/Application Support/kiro-cli/shell/zshrc.post.zsh" ]] && builtin source "${HOME}/Library/Application Support/kiro-cli/shell/zshrc.post.zsh"

# Kiro environments
alias kiro-training='KIRO_HOME=/tmp/kiro-training kiro chat'
alias kiro-prod='kiro chat'

# VPN auto-check antes do kiro chat
kiro() {
  if [[ "$1" == "chat" || -z "$1" ]]; then
    source ~/Brain-KIRO/vpn_check.sh
  fi
  command kiro-cli "$@"
}


# Added by Antigravity CLI installer
export PATH="/Users/[YOUR_USER]/.local/bin:$PATH"

# GitHub Token
export GITHUB_TOKEN="<YOUR_GITHUB_TOKEN>"

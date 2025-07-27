#!/bin/bash

# Alias bash
alias sb="source ~/.bashrc ; echo '~/.bashrc sourced!'"

# Alias config : ls
export LS_OPTIONS='--color=auto'
eval "$(dircolors)"
alias ls='ls $LS_OPTIONS'
alias ll='ls -lh $LS_OPTIONS'
alias l='ls -lah $LS_OPTIONS'

# Alias config: File manipulation
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Alias config: editor
alias v='vim'
alias vi='vim'

# Alias config: netstat
alias ns='sudo netstat -tulpn |sort -k 4 -n'
alias nso='sudo netstat -tulpano |sort -k 4 -n'

# Alias config: networking
alias sifa='sudo ifconfig -a'
alias sbs='sudo brctl show'
alias srn='sudo route -n'

# Alias config: iptables
alias siptl='sudo iptables -L -v -n'
alias siptln='sudo iptables -L -v -n -t nat'


# Alias config: ip info
alias whoamip='echo $(curl -s ifconfig.me)'

# Alias config: disksize
alias sdf='sudo df -h | pee "head -n 1" "tail -n +2" | sort'
alias sdfa='sudo df -ah | pee "head -n 1" "tail -n +2" | sort'

# cat
alias bcat='batcat'
alias scat='sudo cat'
alias sbcat='sudo batcat'

# exa
alias e='exa'
alias et='exa --long --tree'
alias ee='exa -abghHlS'
alias eet='exa --long --tree -abghHlS'
alias see='sudo exa -abghHlS'
alias stree='sudo exa --long --tree'

# apt
alias pq='apt search'
alias pi='sudo apt install'
alias pd='sudo apt remove'
alias puu='sudo apt update && sudo apt upgrade'


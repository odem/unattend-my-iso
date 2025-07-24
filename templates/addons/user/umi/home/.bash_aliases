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

# Alias config: Networking
alias ns='sudo netstat -tulpano'
alias sifa='sudo ifconfig -a'
alias sbs='sudo brctl show'
alias srn='sudo route -n'
alias siptl='sudo iptables -L -v -n'
alias siptln='sudo iptables -L -v -n -t nat'



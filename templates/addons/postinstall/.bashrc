#!/bin/bash

if ! shopt -oq posix; then
        if [ -f /usr/share/bash-completion/bash_completion ]; then
                . /usr/share/bash-completion/bash_completion
        elif [ -f /etc/bash_completion ]; then
                . /etc/bash_completion
        fi
fi
#--- Environment Variable -----------------------------------------------------
export PATH=$PATH:~/.local/bin
export EDITOR=vim 
export SHELL=/bin/bash
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export DISPLAY=:0

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

# Alias config: Networking
alias ns='sudo netstat -tulpano'
alias sifa='sudo ifconfig -a'
alias sbs='sudo brctl show'
alias srn='sudo route -n'
alias siptl='sudo iptables -L -v -n'
alias siptln='sudo iptables -L -v -n -t nat'

# Alias config: umi
alias umi-post='cd /opt/umi/postinstall'
alias umi-env='source /opt/umi/config/env.bash'

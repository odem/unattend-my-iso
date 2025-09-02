#!/bin/bash

# Alias bash
alias sb="source ~/.bashrc ; echo '~/.bashrc sourced!'"

# Alias config : ls
export LS_OPTIONS='--color=auto'
eval "$(dircolors)"
alias ls='ls $LS_OPTIONS'
alias ll='ls -lah $LS_OPTIONS'
alias l='ls -lh $LS_OPTIONS'

# Alias config: File manipulation
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Alias config: editor
alias v='vim'
alias vi='vim'

# Alias config: netstat
alias ns='sudo netstat -tulpn |sort -k 4 -n'
alias nsao='sudo netstat -tulpano |sort -k 4 -n'

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
alias sdf='sudo df -h | head -n 1 ; sudo df -h | tail -n +2 | sort -k 6'

# Alias config: cfg helpers
alias cfg-hosts='sudo vim /etc/hosts'
alias cfg-fstab='sudo vim /etc/fstab'
alias cfg-aptsrc='sudo vim /etc/apt/sources.list'
alias cfg-net='sudo vim /etc/network/interfaces'
alias cfg-ssh='sudo vim ~/.ssh/config'

# cat
alias bat='batcat'
alias sbat='sudo batcat'
alias scat='sudo cat'

# systemctl 
alias sdr='systemctl daemon-reload'
alias syss='systemctl status'
alias sysup='systemctl start'
alias sysdown='systemctl stop'
alias sysre='systemctl restart'

# exa
alias e='eza'
alias et='eza --long --tree'
alias ee='eza -abghHlS'
alias eet='eza --long --tree -abghHlS'
alias see='sudo eza -abghHlS'
alias stree='sudo eza --long --tree'

# apt
alias pq='apt search'
alias pi='sudo apt install'
alias pd='sudo apt remove'
alias puu='sudo apt update && sudo apt upgrade'

# docker
alias dps="docker ps -a"
alias dcexec="docker exec -ti "
alias dcstop="docker container stop "
alias dckill="docker container kill "
alias dcrm="docker container rm"
alias dnls="docker network ls"
alias dvls="docker volume ls"
alias dirm="docker image rm"
alias dia="docker images -a"
alias dlogs="docker logs -f"
alias dexe="docker exec -it"
alias diatagged='docker images -a | grep -v "<none>"'
function dbash() { docker exec -it "$1" bash ;}
function dsh() { docker exec -it "$1" sh ;}
function dip() { docker exec "$1" cat /etc/hosts | grep "$1" | cut -f 1; }
function dips() {
  if [ -z "$1" ]; then
    docker ps -q | xargs -n1 docker inspect --format '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' | sed 's|^/||'
  else
    docker inspect --format '{{.Name}} - {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' "$1" | sed 's|^/||'
  fi
}

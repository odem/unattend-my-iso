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

# Alias config: Networking
alias ns='sudo netstat -tulpano'
alias sifa='sudo ifconfig -a'
alias sbs='sudo brctl show'
alias srn='sudo route -n'
alias siptl='sudo iptables -L -v -n'
alias siptln='sudo iptables -L -v -n -t nat'

# Ceph stuff
MANAGE_CEPH="/opt/umi/postinstall/manage/manage_ceph_pools.bash"
alias c-manage="$MANAGE_CEPH"
alias c-bootstrap-cluster="$MANAGE_CEPH -a bootstrap-cluster"
alias c-bootstrap-crush="$MANAGE_CEPH -a recreate-all-crush"
alias c-bootstrap-fs="$MANAGE_CEPH -a del-all-fs ; $MANAGE_CEPH -a add-all-fs"
alias c-bootstrap-pools="$MANAGE_CEPH -a recreate-all-pools"
alias c-bootstrap-all="c-bootstrap-cluster ; c-bootstrap-crush ; c-bootstrap-pools"
alias c-clean-fs="$MANAGE_CEPH -a del-all-fs"
alias c-clean-pools="$MANAGE_CEPH -a del-all-pools"
alias c-clean-crush="$MANAGE_CEPH -a del-all-crush"
alias c-clean-all="c-clean-fs ; c-clean-pools ; c-clean-crush"
alias c-s='ceph -s'
alias c-mgr='ceph mgr services'
alias c-df='ceph df detail'
alias c-tree='ceph osd tree'
alias c-poolstat='ceph osd pool stats'
alias c-pools='ceph osd pool ls'
alias c-poolsd='ceph osd pool ls detail'
alias c-rules='ceph osd crush rule ls'
alias c-pg='ceph pg dump pools'
alias c-stats='ceph report'
alias c-stats-pools='ceph osd dump -f json-pretty | jq ".pools[]"'

# Ceph functions
c-rule-export() {
    [[ -z "$1" ]] && echo "Filename required!" && return 1
    echo "Rule export:"
    c-manage -a export-crush -n "$1"
}
c-rule-import() {
    [[ -z "$1" ]] && echo "Filename required!" && return 1
    echo "Rule import:"
    c-manage -a import-crush -n "$1"
}
c-rule-edit() {
    [[ -z "$1" ]] && echo "Filename required!" && return 1
    c-rule-export "$1"
    "$EDITOR" "$1"
    c-rule-import "$1"
}
c-cfg() {
    [[ -z "$1" ]] && echo "Poolname required!" && return 1
    ceph osd pool get "$1" all
}
c-bench() {
    [[ -z "$1" ]] && echo "OSD name required!" && return 1
    ceph tell "$1" bench
}

# Alias config: umi
alias umi-post='cd /opt/umi/postinstall'
alias umi-env='source /opt/umi/config/env.bash'
alias umi-envcat='cat /opt/umi/config/env.bash'

# Alias cfg
alias cfg-bash="$EDITOR ~/.bashrc ; sb"

each_line() {
  local cmd_prefix="$1"
  local cmd_trail="$2"
  
  while IFS= read -r line; do
    if [[ -z "$cmd_trail" ]]; then
      eval "$cmd_prefix \"$line\""
    else
      eval "$cmd_prefix \"$line\" $cmd_trail"
  fi
  done
}


#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL VIM"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# update and install essentials
apt-get update -y
apt-get install -y exuberant-ctags fonts-powerline vim vim-addon-manager \
    vim-airline vim-gruvbox vim-ale vim-autopep8 vim-ctrlp vim-fugitive vim-gitgutter \
    vim-julia vim-lastplace vim-latexsuite vim-pathogen vim-puppet \
    vim-python-jedi vim-scripts vim-snippets vim-syntastic vim-syntax-gtk \
    vim-tabular vim-tlib vim-youcompleteme xclip
apt-get autoremove

cat <<EOF > /root/.vimrc
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Syntax / Highlight / Visual / Audio / etc. 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
syntax on
set number
set relativenumber
colorscheme gruvbox
set background=dark
set signcolumn=yes
set colorcolumn=80
set cursorline
set noeb vb t_vb=
set noerrorbells
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Tabs / Indent / Wrap
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
set tabstop=4 softtabstop=4
set shiftwidth=4
set expandtab
set smartindent
set wrap
set nohlsearch
set noincsearch
set ignorecase
set smartcase
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Splits / Buffers 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
set splitbelow
set splitright
set hidden
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Status bar 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
set laststatus=2
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Some type specific configs
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
let mapleader = " "
filetype on
filetype plugin on
filetype indent on " file type based indentation
augroup filetype
  autocmd BufNewFile,BufRead *.txt set filetype=human
augroup END
autocmd FileType human set formatoptions-=t textwidth=0 
autocmd FileType html,xhtml,css,xml,xslt set shiftwidth=2 softtabstop=2 
autocmd FileType make set noexpandtab shiftwidth=4 softtabstop=0
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Navigate files
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Harpoon Link: https://github.com/ThePrimeagen/harpoon 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Motions 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Window
nnoremap <C-j> <C-W>j    " Window up
nnoremap <C-k> <C-W>k    " Window down
nnoremap <C-h> <C-W>h    " Window left
nnoremap <C-l> <C-W>l    " Window right
" Resize
nnoremap <C-A-j> :resize +3<CR>
nnoremap <C-A-k> :resize -3<CR>
nnoremap <C-A-h> :vertical resize +3<CR>
nnoremap <C-A-l> :vertical resize -3<CR>
" 1/2 Page jump
nnoremap <C-d> <C-d>zz          " Cursor half page down (centered)
nnoremap <C-u> <C-u>zz          " Cursor half page up (centered)
" Other
nnoremap <n> nzzzv              " Cursor half page down (centered)
nnoremap <N> Nzzzv              " Cursor half page up (centered)
nnoremap "<leader>p" "\"_dP     " Keep copy
tnoremap <Esc> <C-\><C-n>       " Escape terminal 
EOF
# Remove Job From Jobfile
echo "Sucessfully invoked all actions"
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed -i "/$filename/d" "$SERVICE"
    echo "Removed job from firstboot script: $(basename "$0")"
fi
echo ""
sleep 1
exit 0

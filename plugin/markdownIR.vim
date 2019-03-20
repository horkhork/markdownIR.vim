let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

python3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import markdownIR
EOF

function! Foo()
        python3 markdownIR.foo()
endfunction
command! -nargs=0 Foo call Foo()

function! NewEntry()
        python3 markdownIR.NewEntry()
endfunction
command! -nargs=0 NewEntry call NewEntry()

function! IndexData()
        python3 markdownIR.IndexData()
endfunction
command! -nargs=0 IndexData call IndexData()

function! ShowIndex()
        python3 markdownIR.Query()
endfunction
command! -nargs=0 ShowIndex call ShowIndex()

function! SearchByDate()
        python3 markdownIR.SearchByDate()
endfunction
command! -nargs=0 SearchByDate call SearchByDate()

function! SearchByRelevance()
        python3 markdownIR.SearchByRelevance()
endfunction
command! -nargs=0 SearchByRelevance call SearchByRelevance()

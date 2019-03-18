let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

python3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import wikitime
EOF

function! Foo()
        python3 wikitime.foo()
endfunction
command! -nargs=0 Foo call Foo()

function! NewEntry()
        python3 wikitime.NewEntry()
endfunction
command! -nargs=0 NewEntry call NewEntry()

function! IndexData()
        python3 wikitime.IndexData()
endfunction
command! -nargs=0 IndexData call IndexData()

function! ShowIndex()
        python3 wikitime.Query()
endfunction
command! -nargs=0 ShowIndex call ShowIndex()

function! SearchByDate()
        python3 wikitime.SearchByDate()
endfunction
command! -nargs=0 SearchByDate call SearchByDate()

function! SearchByRelevance()
        python3 wikitime.SearchByRelevance()
endfunction
command! -nargs=0 SearchByRelevance call SearchByRelevance()

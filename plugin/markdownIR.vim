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

" Time-sorted Search variants

function! SearchByDate()
        python3 markdownIR.SearchByDate()
endfunction
command! -nargs=0 SearchByDate call SearchByDate()

function! SearchCatByDate()
        python3 markdownIR.SearchCatByDate()
endfunction
command! -nargs=0 SearchCatByDate call SearchCatByDate()

function! SearchTagByDate()
        python3 markdownIR.SearchTagByDate()
endfunction
command! -nargs=0 SearchTagByDate call SearchTagByDate()

function! SearchAllByDate()
        python3 markdownIR.SearchAllByDate()
endfunction
command! -nargs=0 SearchAllByDate call SearchAllByDate()

" Relevance-sorted Search variants

function! SearchByRelevance()
        python3 markdownIR.SearchByRelevance()
endfunction
command! -nargs=0 SearchByRelevance call SearchByRelevance()

function! SearchCatByRelevance()
        python3 markdownIR.SearchCatByRelevance()
endfunction
command! -nargs=0 SearchCatByRelevance call SearchCatByRelevance()

function! SearchTagByRelevance()
        python3 markdownIR.SearchTagByRelevance()
endfunction
command! -nargs=0 SearchTagByRelevance call SearchTagByRelevance()

function! SearchAllByRelevance()
        python3 markdownIR.SearchAllByRelevance()
endfunction
command! -nargs=0 SearchAllByRelevance call SearchAllByRelevance()

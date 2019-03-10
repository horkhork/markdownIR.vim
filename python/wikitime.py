# Implement Markdown handling tools similar to what Vimwiki offers. This follows
# the example written here:
#    http://candidtim.github.io/vim/2017/08/11/write-vim-plugin-in-python.html

import datetime
import os
import vim

# Config parameters
#  - Markdown root path
#  - Filename template string ('%Y-%m-%d_%H:%M')
#  - File suffix
#  - 

def foo():
    print("FOO BAR")

def NewEntry():
    # Create a new Markdown file
    suffix = vim.eval('g:wikitime_file_suffix')
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M") + "." + suffix
    filepath = vim.eval('g:wikitime_root')
    print(os.path.join(filepath, filename))

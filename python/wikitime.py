# Implement Markdown handling tools similar to what Vimwiki offers. This follows
# the example written here:
#    http://candidtim.github.io/vim/2017/08/11/write-vim-plugin-in-python.html
#
# Use a template file to define initial Markdown doc. Set up default template
# for new files in .vimrc like:
#     autocmd BufNewFile  *.md  0r ~/.vim/templates/skeleton.md
#
# Sample template file:
#    ---
#    author: {author}
#    excerpt:
#    cover:
#    date: {date}
#    name: {name}
#    tags:
#    title:
#    subtitle:
#    ...

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
    # Create a new Markdown file prepopulated from a template
    suffix = vim.eval('g:wikitime_file_suffix')
    file_pattern = vim.eval('g:wikitime_file_pattern')
    filepath = vim.eval('g:wikitime_root')
    author = vim.eval('g:wikitime_default_author')

    now = datetime.datetime.now().strftime(file_pattern)
    filename = now + "." + suffix

    args = {
        "author": author,
        "date": now,
        "name": filename,
    }

    # Open the new file according to filename template
    vim.command(":edit {}".format(os.path.join(filepath, filename)))

    # Substitute parameters into the template
    for k, v in args.items():
        vim.command(":%s/{{{key}}}/{val}/".format(key=k, val=v))


def GenerateIndexListing():
    # Given the root directory, scan all the markdown files there and build an
    # index page ordered by date DESC, listing each document title, with links
    # to each file
    pass

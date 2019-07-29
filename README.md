# markdownIR.vim

A Markdown Information Retrieval index/query vim plugin for helping to author
and curate Markdown content.

Intended to be used in conjunction with other vim markdown plugins to enable
desired features.

This uses Xapian 1.4 to index and query your markdown data files.

## Requirements

### Install python-dateutils and pytz

`pip3 install -r path/to/requirements.txt`

### Install Xapian library

Following <https://xapian.org/download>

```
# On Mac
brew install --build-from-source xapian -- --with-python
brew upgrade xapian
```

### Instal pandoc

`brew install pandoc`

## Installation

Use Plug

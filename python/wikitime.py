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
#    tags:
#    title:
#    subtitle:
#    ...

import datetime
import dateutil.parser
import json
import os
import re
import subprocess
import vim
import xapian
import yaml
from os.path import normpath, join
from collections import OrderedDict

# Config parameters
#  - Markdown root path
#  - Filename template string ('%Y-%m-%d_%H:%M')
#  - File suffix
#  -

PANDOC = '/usr/bin/pandoc'
PLUGIN_ROOT_DIR = vim.eval('s:plugin_root_dir')
TEMPLATE_DIR = normpath(join(PLUGIN_ROOT_DIR, '..', 'template'))
METADATA_TMPL = join(TEMPLATE_DIR, 'metadata_template.pandoc')
BODY_TMPL = join(TEMPLATE_DIR, 'body_template.pandoc')

def foo():
    print("FOO BAR")

def NewEntry():
    # Create a new Markdown file prepopulated from a template
    suffix = vim.eval('g:wikitime_file_suffix')
    file_pattern = vim.eval('g:wikitime_file_pattern')
    filepath = vim.eval('g:wikitime_content_root')
    author = vim.eval('g:wikitime_default_author')

    now = datetime.datetime.now().strftime(file_pattern)
    filename = now + "." + suffix

    args = {
        "author": author,
        "date": datetime.datetime.now().isoformat(),
    }

    # Open the new file according to filename template
    vim.command(":edit {}".format(os.path.join(filepath, filename)))

    # Substitute parameters into the template
    for k, v in args.items():
        vim.command(":%s/{{{key}}}/{val}/".format(key=k, val=v))

class DisplayItem(object):
    def __init__(self, date, rank, docid, title, fname, tags):
        self.date = date
        self.rank = rank
        self.docid = docid
        self.title = title
        self.fname = fname
        self.tags = tags

    def __lt__(self, other):
        return self.date < other.date

    def __repr__(self):
        return "[{} {:<10} {} {} {}]({})".format(
            self.date.strftime("%d"),
            self.date.strftime("%A"),
            self.date.strftime("%H:%M"),
            self.title,
            ','.join(self.tags),
            self.fname)

def Search():
    vim.command('call inputsave()')
    vim.command("let query = input('Query string: ')")
    vim.command('call inputrestore()')
    query = vim.eval('query')
    vim.command('call inputsave()')
    vim.command("let tags = input('Tags: ')")
    vim.command('call inputrestore()')
    tags = vim.eval('tags')
    Query(query, tags)

def Query(queryStr='', tags='', order_by_date=True):
    tags = list(filter(None, re.split('[ ,]', tags)))

    # Query the Xapian DB and generate an Index page for navigation
    dbPath = vim.eval('g:wikitime_db')
    root = vim.eval('g:wikitime_content_root')

    # Open the database we're going to search.
    db = xapian.Database(dbPath)

    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

    queryparser.add_prefix("filename", "F")

    # Enable querying date ranges
    queryparser.add_rangeprocessor(
            xapian.DateRangeProcessor(1,
                xapian.RP_DATE_PREFER_MDY)
    )

    # Parse the query
    query = xapian.Query.MatchAll
    if queryStr:
        query = queryparser.parse_query(queryStr)

    if tags:
        tag_query = xapian.Query(xapian.Query.OP_OR, ['XT{}'.format(t) for t in tags])
        query = xapian.Query(xapian.Query.OP_FILTER, query, tag_query)

    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    if order_by_date:
        # Sort by date DESC
        enquire.set_sort_by_value_then_relevance(1, True)

    vim.command(":new")
    vim.command(":setlocal buftype=nofile")
    vim.command(":setlocal filetype=markdown")
    vim.command(":setlocal bufhidden=hide")
    vim.command(":setlocal noswapfile")
    vim.current.buffer[:] = None
    vim.command(":only")

    data = OrderedDict()

    for match in enquire.get_mset(0, 10000):
        fields = json.loads(match.document.get_data().decode('utf-8'))

        date = fields.get('date')
        if date is None:
            print("No date field in %s" % fields)
        date = dateutil.parser.parse(date)
        year = date.strftime("%Y")
        month = date.strftime("%B")
        daynum = date.strftime("%d")
        day = date.strftime("%A")

        if year not in data:
            data[year] = OrderedDict()

        if month not in data[year]:
            data[year][month] = OrderedDict()

        if daynum not in data[year][month]:
            data[year][month][daynum] = list()

        rank = match.rank + 1
        docid = match.docid
        title = fields.get('title', u'')
        tags = fields.get('tags', u'')
        filename = fields.get('filename')

        entry = DisplayItem(date, rank, docid, title, filename, tags)
        data[year][month][daynum].append(entry)

    for y in data:
        vim.current.buffer.append(str(y))
        for m in data[y]:
            vim.current.buffer.append("  " + str(m))
            for d in data[y][m]:
                for i in sorted(data[y][m][d], reverse=True):
                    vim.current.buffer.append("    " + str(i))

def IndexData(fname=None):
    # Given the root directory, scan all the markdown files there and build an
    # index page ordered by date DESC, listing each document title, with links
    # to each file

    dbPath = vim.eval('g:wikitime_db')

    db = xapian.WritableDatabase(dbPath, xapian.DB_CREATE_OR_OPEN)
    termgenerator = xapian.TermGenerator()
    termgenerator.set_stemmer(xapian.Stem("en"))

    if fname is not None:
        index_md_file(fname, termgenerator)

    else:
        root = vim.eval('g:wikitime_content_root')
        for fname in os.listdir(root):
            try:
                index_md_file(join(root, fname), termgenerator, db)
            except Exception as e:
                print("Exception processing %s: %s" % (fname, e))

def index_md_file(fname, termgenerator, db):
    cmd = [PANDOC, '--standalone', '--from', 'markdown+yaml_metadata_block', '--to',
            'markdown+yaml_metadata_block', '--atx-headers', '--template',
            METADATA_TMPL, fname]
    mdata = subprocess.check_output(cmd)
    metadata = yaml.load(mdata.strip().strip(b"---"))

    cmd = [PANDOC, '--standalone', '--from', 'markdown+yaml_metadata_block', '--to',
            'markdown+yaml_metadata_block', '--atx-headers', '--template',
            BODY_TMPL, fname]
    body = subprocess.check_output(cmd)

    # Metadata fields
    #author: steve
    #category: programming
    #cover:
    #excerpt:
    #date: '2019-02-23T00:00:00-05:00'
    #tags:
    #- xapian
    #- python
    #title: Initial exploration into Xapian
    #subtitle: Install Xapian and go through examples

    author = metadata.get("author", u"")
    category = metadata.get("category", u"")
    cover = metadata.get("cover", u"")
    date = metadata.get("date", u"")
    xdate = dateutil.parser.parse(date).strftime('%Y%m%d')
    tags = metadata.get("tags", u"")
    title = metadata.get("title", u"")
    subtitle = metadata.get("subtitle", u"")
    # Explicitly set the filename as part of the indexed metadata
    metadata["filename"] = fname

    doc = xapian.Document()
    termgenerator.set_document(doc)

    termgenerator.index_text(author, 1, 'A')
    termgenerator.index_text(category, 1, 'B')
    termgenerator.index_text(xdate, 1, 'D')
    termgenerator.index_text(fname, 1, 'F')
    termgenerator.index_text(title, 1, 'S')
    termgenerator.index_text(subtitle, 1, 'XS')

    # Allow for sorting by date
    doc.add_value(1, xdate)

    # Index fields without prefixes for general search.
    termgenerator.index_text(title)
    termgenerator.increase_termpos()
    termgenerator.index_text(subtitle)
    termgenerator.increase_termpos()
    termgenerator.index_text(category)
    termgenerator.increase_termpos()
    for tag in tags:
        termgenerator.index_text(tag)
        termgenerator.increase_termpos()

    termgenerator.index_text(body)

    for tag in tags:
        doc.add_boolean_term('XT' + tag)

    # Store all the fields for display purposes.
    doc.set_data(json.dumps(metadata))

    # We use the identifier to ensure each object ends up in the database only
    # once no matter how many times we run the indexer.
    idterm = u"Q" + date
    doc.add_boolean_term(idterm)
    db.replace_document(idterm, doc)

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
import glob
import json
import os
import re
import pytz
import subprocess
import vim
import xapian
import yaml
from os.path import normpath, join
from collections import OrderedDict, Counter

# Config parameters
#  - Markdown root path
#  - Filename template string ('%Y-%m-%d_%H:%M')
#  - File suffix
#  -

PANDOC = vim.eval('g:markdownIR_pandoc_bin')
PLUGIN_ROOT_DIR = vim.eval('s:plugin_root_dir')
TEMPLATE_DIR = normpath(join(PLUGIN_ROOT_DIR, '..', 'template'))
METADATA_TMPL = join(TEMPLATE_DIR, 'metadata_template.pandoc')
BODY_TMPL = join(TEMPLATE_DIR, 'body_template.pandoc')

def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)[:50]

def NewEntry():
    ''' Create a new Markdown file prepopulated from a template '''

    timezone = pytz.timezone(vim.eval('g:markdownIR_timezone'))
    now = timezone.localize(datetime.datetime.now())
    nowStr = now.strftime(vim.eval('g:markdownIR_file_pattern'))

    vim.command('call inputsave()')
    vim.command("let title = input('Title: ')")
    vim.command('call inputrestore()')
    title = vim.eval('title')
    filename = get_valid_filename(title) + "." + vim.eval('g:markdownIR_file_suffix')
    args = {
        "author": vim.eval('g:markdownIR_default_author'),
        "date": nowStr,
        "title": title,
    }

    # Open the new file according to filename template
    vim.command(":edit {}".format(os.path.join(vim.eval('g:markdownIR_content_root'), filename)))

    # Substitute parameters into the template
    for k, v in args.items():
        vim.command(":%s/{{{key}}}/{val}/".format(key=k, val=v))

class DisplayItem(object):
    def __init__(self, date, rank, docid, title, fname, tags):
        if date.tzinfo is None:
            date = pytz.utc.localize(date)
        self.date = date
        self.rank = rank
        self.docid = docid
        self.title = title
        self.fname = fname
        self.tags = tags

    def __lt__(self, other):
        return self.date < other.date

    def __repr__(self):
        ret = "[{} {} <{}>]({})".format(
            self.date.strftime("%H:%M"),
            self.title,
            ','.join(self.tags),
            self.fname)
        return ret.replace('\n', ' ')

class DisplayItemDetailedTime(DisplayItem):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

    def __repr__(self):
        ret = "[{} {} <{}>]({})".format(
            self.date.strftime("%c"),
            self.title,
            ','.join(self.tags),
            self.fname)
        return ret.replace('\n', ' ')

def SearchByRelevance():
    _search(False)

def SearchByDate():
    _search(True)

def _search(order_by_date=True):
    vim.command('call inputsave()')
    vim.command("let query = input('Query string: ')")
    vim.command('call inputrestore()')
    query = vim.eval('query')
    Query(query, order_by_date)

def Query(queryStr=None, order_by_date=True):
    # Query the Xapian DB and generate an Index page for navigation
    dbPath = vim.eval('g:markdownIR_db')

    # Open the database we're going to search.
    db = xapian.Database(dbPath)

    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)

    # Start of prefix configuration.
    queryparser.add_prefix("author", "A")
    queryparser.add_prefix("filename", "XF")
    queryparser.add_prefix("description", "XD")
    queryparser.add_prefix("title", "S")
    queryparser.add_prefix("subtitle", "XS")
    queryparser.add_prefix("tag", "K")
    # End of prefix configuration.

    # Enable querying date ranges
    queryparser.add_rangeprocessor(xapian.DateRangeProcessor(1, xapian.RP_DATE_PREFER_MDY))

    # Parse the query
    query = xapian.Query.MatchAll
    if queryStr is not None:
        query = queryparser.parse_query(queryStr)

    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    #vim.command(":setlocal splitright")
    vim.command(":new")
    #vim.command(":vnew")
    #vim.command(":30vnew  MarkdownIndex")
    vim.command(":setlocal noswapfile")
    vim.command(":setlocal buftype=nofile")
    vim.command(":setlocal nobuflisted")
    vim.command(":setlocal cursorline")
    vim.command(":setlocal filetype=markdown")
    vim.command(":setlocal bufhidden=hide")
    vim.command(":only")

    header_line = '#'
    if queryStr != '':
        header_line += ' Query: {}'.format(queryStr)
    if order_by_date:
        header_line += ' Ordered By Date'
    else:
        header_line += ' Ordered By Relevance'

    vim.current.buffer[:] = None
    vim.current.buffer[0] = (header_line)
    vim.current.buffer.append('')

    if order_by_date:
        DisplayResultsByDate(enquire)

    else:
        DisplayResults(enquire)

def DisplayResultsByDate(enquire):
    # Sort by date DESC
    enquire.set_sort_by_value_then_relevance(1, True)

    data = OrderedDict()

    count = 0
    for match in enquire.get_mset(0, 100000):
        count += 1
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
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        filename = fields.get('filename')

        entry = DisplayItem(date, rank, docid, title, filename, tags)
        data[year][month][daynum].append(entry)

    for y in data:
        vim.current.buffer.append(str(y))
        for m in data[y]:
            vim.current.buffer.append(str(m))
            for d in data[y][m]:
                vim.current.buffer.append(dateutil.parser.parse("{} {} {}".format(y, m, d)).strftime("%A %d"))
                for i in sorted(data[y][m][d], reverse=True):
                    try:
                        vim.current.buffer.append(str(i))
                    except:
                        print("Exception handling %s", str(i))

    vim.current.buffer.append("")
    vim.current.buffer.append("Found {} matches".format(count))

def DisplayResults(enquire):
    count = 0
    for match in enquire.get_mset(0, 100000):
        count += 1
        fields = json.loads(match.document.get_data().decode('utf-8'))

        date = fields.get('date')
        if date is None:
            print("No date field in %s" % fields)
        date = dateutil.parser.parse(date)

        rank = match.rank + 1
        docid = match.docid
        title = fields.get('title', u'')
        tags = fields.get('tags', u'')
        if not isinstance(tags, (list, tuple)):
            tags = [tags]
        filename = fields.get('filename')

        entry = DisplayItemDetailedTime(date, rank, docid, title, filename, tags)
        vim.current.buffer.append(str(entry))

    vim.current.buffer.append("")
    vim.current.buffer.append("Found {} matches".format(count))

def IndexData(fname=None):
    # Given the root directory, scan all the markdown files there and build an
    # index page ordered by date DESC, listing each document title, with links
    # to each file

    dbPath = vim.eval('g:markdownIR_db')

    db = xapian.WritableDatabase(dbPath, xapian.DB_CREATE_OR_OPEN)
    termgenerator = xapian.TermGenerator()
    termgenerator.set_stemmer(xapian.Stem("en"))

    if fname is not None:
        index_md_file(fname, termgenerator)

    else:
        root = vim.eval('g:markdownIR_content_root')
        globPattern = '{}/**/*.{}'.format(root, vim.eval('g:markdownIR_file_suffix'))
        for fname in glob.iglob(globPattern, recursive=True):
            try:
                index_md_file(join(root, fname), termgenerator, db)
            except Exception as e:
                print("Exception processing %s: %s" % (fname, e))

def index_md_file(fname, termgenerator, db):
    cmd = [PANDOC, '--standalone', '--from', 'markdown+yaml_metadata_block', '--to',
            'markdown+yaml_metadata_block', '--atx-headers', '--template',
            METADATA_TMPL, fname]
    mdata = subprocess.check_output(cmd)
    metadata = yaml.load(mdata.strip().strip(b"---"), Loader=yaml.SafeLoader)

    cmd = [PANDOC, '--standalone', '--from', 'markdown+yaml_metadata_block', '--to',
            'markdown+yaml_metadata_block', '--atx-headers', '--template',
            BODY_TMPL, fname]
    body = subprocess.check_output(cmd)

    # Metadata fields
    #author: steve
    #cover:
    #excerpt:
    #date: '2019-02-23T00:00:00-05:00'
    #tags:
    #- xapian
    #- python
    #title: Initial exploration into Xapian
    #subtitle: Install Xapian and go through examples

    author = metadata.get("author", u"")
    cover = metadata.get("cover", u"")
    date = metadata.get("date", u"")
    xdate = dateutil.parser.parse(date).strftime('%Y%m%d')
    tags = metadata.get("tags", u"")
    if not isinstance(tags, (list, tuple)):
        tags = [tags]
    title = metadata.get("title", u"")
    subtitle = metadata.get("subtitle", u"")
    # Explicitly set the filename as part of the indexed metadata
    metadata["filename"] = fname

    doc = xapian.Document()
    termgenerator.set_document(doc)

    termgenerator.index_text(author, 1, 'A')
    termgenerator.index_text(xdate, 1, 'D')
    termgenerator.index_text(fname, 1, 'F')
    termgenerator.index_text(title, 1, 'S')
    termgenerator.index_text(subtitle, 1, 'XS')
    for tag in tags:
        termgenerator.index_text(tag, 1, 'K')

    # Allow for sorting by date
    doc.add_value(1, xdate)

    # Index fields without prefixes for general search.
    termgenerator.index_text(title)
    termgenerator.increase_termpos()
    termgenerator.index_text(subtitle)
    termgenerator.increase_termpos()
    termgenerator.increase_termpos()
    for tag in tags:
        termgenerator.index_text(tag)
        termgenerator.increase_termpos()

    termgenerator.index_text(body)

    # Store all the fields for display purposes.
    doc.set_data(json.dumps(metadata))

    # We use the identifier to ensure each object ends up in the database only
    # once no matter how many times we run the indexer.
    idterm = u"Q" + date
    doc.add_boolean_term(idterm)
    db.replace_document(idterm, doc)

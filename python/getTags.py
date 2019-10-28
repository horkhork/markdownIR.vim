#!/usr/bin/python3

import json
import vim
import xapian
from pdb import set_trace

# parser = argparse.ArgumentParser(description='Index markdown files including FrontMatter Metadata')
# parser.add_argument('--db', type=str, help='Path to Xapian DB file')
# parser.add_argument('--query', type=str, default=None, help='Query to run')
# parser.add_argument('--tags', type=str, nargs='*', help='Document tags to match')
# parser.add_argument('--offset', type=int, default=0, help='search offset')
# parser.add_argument('--pagesize', type=int, default=100000, help='num results')
# args = parser.parse_args()
# 
# # Open the database we're going to search.
# db = xapian.Database(args.db)
# 
# # Set up a QueryParser with a stemmer and suitable prefixes
# queryparser = xapian.QueryParser()
# queryparser.set_stemmer(xapian.Stem("en"))
# queryparser.set_stemming_strategy(queryparser.STEM_SOME)
# 
# # Start of prefix configuration.
# queryparser.add_prefix("title", "S")
# queryparser.add_prefix("description", "XD")
# # End of prefix configuration.
# 
# query = xapian.Query.MatchAll
# # And parse the query
# if args.query is not None:
#     query = queryparser.parse_query(args.query)
# 
# if args.tags:
#     tag_query = xapian.Query(xapian.Query.OP_OR, ['XM{}'.format(t) for t in args.tags])
#     query = xapian.Query(xapian.Query.OP_FILTER, query, tag_query)
# 
# # Use an Enquire object on the database to run the query
# enquire = xapian.Enquire(db)
# enquire.set_query(query)
# 
# tags = set()
# for match in enquire.get_mset(args.offset, args.pagesize):
#     fields = json.loads(match.document.get_data().decode('utf-8'))
#     for tag in fields.get('tags', []):
#         tags.add(tag)
# 
# print(tags)

def GetTags(): #query=None, tags=[], offset=0, pagesize=100000):
    vim.command('call inputsave()')
    vim.command("let query = input('Query string: ')")
    vim.command('call inputrestore()')
    query = vim.eval('query')

    # Query the Xapian DB and generate an Index page for navigation
    dbPath = vim.eval('g:markdownIR_db')

    # Open the database we're going to search.
    db = xapian.Database(dbPath)
    
    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("en"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)
    
    # Start of prefix configuration.
    queryparser.add_prefix("title", "S")
    queryparser.add_prefix("description", "XD")
    # End of prefix configuration.
    
    q = xapian.Query.MatchAll
    # And parse the query
    if query is not None:
        q = queryparser.parse_query(query)
    
    if tags:
        tag_query = xapian.Query(xapian.Query.OP_OR, ['XM{}'.format(t) for t in tags])
        q = xapian.Query(xapian.Query.OP_FILTER, q, tag_query)
    
    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(q)
    
    vim.current.buffer[:] = None
    vim.current.buffer[0] = (header_line)
    vim.current.buffer.append('')

    for match in enquire.get_mset(offset, pagesize):
        fields = json.loads(match.document.get_data().decode('utf-8'))
        for tag in fields.get('tags', []):
            vim.current.buffer.append(tag)

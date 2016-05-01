#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import subprocess
import dateutil.parser

# https://github.com/juanre/dashify
import dashify
from docmeta import guess_meta

def reasonable_length(title):
    """
    >>> reasonable_length('how-children-succeed-grit-curiosity-and-the-hidden-power-of-character')
    'how-children-succeed-grit-curiosity'
    >>> reasonable_length('influence')
    'influence'
    """
    words = title.split('-')
    dont_end =['the', 'and', 'but', 'or', 'yet', 'for', 'with',
               'no', 'nor', 'not', 'so', 'a', 's', 'that']
    length = 7
    if length < len(words):
        while words[length-1] in dont_end and length > 1:
            length -= 1
    return '-'.join(words[:length])

def dashed_title(title):
    """
    >>> dashed_title(u'This Very Long and Unwieldy Title That Never Ends')
    u'this-very-long-and-unwieldy-title'
    >>> dashed_title(u'This Title: With a Subtitle')
    u'this-title'
    >>> dashed_title('this title (with paren)')
    u'this-title'
    """
    title = title.split(u':')[0]
    title = re.sub(u'\(.*\)', '', title).strip()
    return reasonable_length(dashify.dash_name(title))

def dashed_author(author):
    """
    >>> dashed_author('Cialdini, Robert B.')
    'cialdini'
    >>> dashed_author('Robert B. Cialdini')
    'cialdini'
    >>> dashed_author('Robert B.Cialdini')
    'cialdini'
    >>> dashed_author('Cialdini')
    'cialdini'
    >>> dashed_author("C{}\'ialdi\~ni")
    'cialdini'
    """
    if not isinstance(author, basestring):
        author = author[0]

    author = re.sub(u"[{}\\\\\\'~]", '', author)

    if ',' in author:
        last, first = author.split(',')
        return dashify.dash_name(last)
    else:
        return dashify.dash_name(re.split(r'[\s\.]', author)[-1])

def bibid(title, author, year=''):
    author = dashed_author(author)
    if author:
        author = author + '-'
    if year:
        year = str(year) + '-'
    title = dashed_title(title)
    if year or author:
        title = '--' + title
    return (author + year + title)

def bibstr(docfile, doctype='book', add_isbn=False):
    required = ['title', 'author', 'date']
    if add_isbn:
        required.append('isbn')
    if doctype == 'article':
        required.append('url')

    meta = guess_meta(docfile, required)
    if 'year' in meta:
        year = meta['year']
    elif 'date' in meta:
        year = meta['date'].year
    else:
        year = ''
    bid = bibid(meta['title'], meta['author'], year)
    meta['bibid'] = bid

    if 'bibstr' in meta:
        return re.sub(u'\{.+,', u'{%s,' % bid, meta['bibstr'], count=1), meta

    bib = [bid,
           'title = {%s}' % meta['title'],
           'author = {%s}' % ' and '.join(meta['author']),
           'year = {%s}' % str(year)]
    for field in ['isbn', 'publisher', 'url']:
        if field in meta:
            bib.append('%s = {%s}' % (field, meta[field]))
    return "@%s {%s\n}" % (doctype, ',\n  '.join(bib)), meta

def _test():
    import doctest
    doctest.testmod()

def as_main():
    import sys
    if len(sys.argv) > 1:
        for book in sys.argv[1:]:
            print bibstr(book)[0]
    else:
        _test()

if __name__ == '__main__':
    as_main()

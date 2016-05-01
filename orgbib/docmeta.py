# -*- coding: utf-8 -*-
"""docmeta
By %s
%s

Interactive wrapper around some parts of ebook-meta, one of the apps
that come with calibre.

Usage: docmeta book_file[s]
"""
__date__ = "2013-05-02"
__author__ = "Juan Reyero, http://juanreyero.com"

import sys, os, codecs
import re
import webbrowser, urllib
import collections
import subprocess
import dateutil.parser

from getch import getch

def ensure_comma(author):
    if not u',' in author:
        author = author.split(' ')
        if len(author) > 1:
            return author[-1] + u', ' + u' '.join(author[:-1])
        else:
            return u'' + author[0]
    return author

def parse_author(info):
    """Try to preserve information on what's the last name:
 http://tex.stackexchange.com/questions/557/how-should-i-type-author-names-in-a-bib-file

    >>> parse_author('Stuckey, Maggie & McGee, Rose Marie Nichols [Stuckey, Maggie]')
    [u'Stuckey, Maggie', u'McGee, Rose Marie Nichols']
    >>> parse_author('Cialdini, Robert B. [Cialdini, Robert B.]')
    [u'Cialdini, Robert B.']
    >>> parse_author('Robert B. Cialdini')
    [u'Cialdini, Robert B.']
    >>> parse_author(u'Cialdini')
    [u'Cialdini']
    """
    info = re.sub(u'\[.+\]', u'', info)
    if u'&' in info:
        out = [s.strip() for s in info.split(u'&')]
    elif u' and ' in info:
        out = [s.strip() for s in info.split(u' and ')]
    else:
        out = [info.strip()]
    return [ensure_comma(a) for a in out]

def guess_meta(book, required=None):
    """Tries to figure out the metadata of the book (title, author and
    publishing year) using the ebook-meta command line tool from
    calibre.  Install calibre from http://calibre-ebook.com/, then
    Preferences -> Miscelaneous -> Install command line tools.

    It requires dateutil-parser.

    If interactive is True and not all data can be read with ebook-meta
    it will ask for the missing parts.
    """
    meta = {}
    for line in [re.split(r'\s+:\s+', l) for l in
                 subprocess.check_output(['ebook-meta', book]).splitlines()]:
        if len(line) != 2:
            continue
        what, info = line[0].lower(), line[1]
        if 'author' in what:
            meta['author'] = parse_author(info.decode('utf8'))
        if 'language' in what:
            meta['language'] = info.decode('utf8')
        elif 'identifier' in what:
            identified = False
            for identifier in [ii.strip() for ii in info.split(',')]:
                if ':' in identifier:
                    idtype, idcontent = identifier.split(':')
                    meta[idtype] = idcontent
                    identified = True
            if not identified:
                meta['identifier'] = info
        elif 'published' in what:
            published = dateutil.parser.parse(info)
            meta['date'] = published
        else:
            meta[what] = u'' + info.decode('utf8')
    if required:
        for r in required:
            if not r in meta:
                print 'Missing', r
                meta, key = interactive_meta(book)
                if key == 'q':
                    import sys
                    sys.exit(1)
                return meta
    return meta

def print_meta(meta, fields, new_meta=None):
    if new_meta is None:
        new_meta = {}
    new_meta = dict(meta.items() + new_meta.items())
    for field in fields:
        value = new_meta.get(field, '')
        if not isinstance(value, basestring) and hasattr(value, '__iter__'):
            value = u' and '.join(value)
        if not field in meta and value:
            value = '(%s)' % value
        print "%15s [%s]: %s" % (field, field[0], value)

def userinput(valuestr, multiline):
    if valuestr:
        valuestr = ' (%s)' % valuestr
    print u'Value%s: ' % valuestr,
    if multiline:
        print
        value = u''
        line = raw_input('').decode(sys.stdin.encoding)
        while line:
            value += (line + '\n')
            line = raw_input('').decode(sys.stdin.encoding)
        return value
    else:
        return raw_input('').decode(sys.stdin.encoding)

def cl_option(fname, val):
    if fname == u'author':
        fname = u'authors'
        val = u' & '.join(val)
    elif fname == u'url' or fname == u'bibstr':
        return ''
    elif fname == u'date':
        val = str(val.year)
    return u'--' + fname + u'=' + val

def field_to_file(field, value, bookfile):
    option = cl_option(field, value)
    if option:
        devnull = codecs.open(os.devnull, 'w', encoding='utf-8')
        if subprocess.call(['ebook-meta', option, bookfile],
                           stdout=devnull, stderr=devnull):
            print "** Error calling ebook-meta on", bookfile, \
              "(maybe DRMed book?)"

def interactive_meta(bookfile):
    meta = guess_meta(bookfile)

    fields = ['author', 'date', 'isbn', 'language', 'publisher',
              'title', 'url', 'bibstr', 'Open file',
              'google scholar', 'Books at google', 'open library', 'wikipedia']
    formatters = collections.defaultdict(lambda: lambda v: v)
    formatters['author'] = lambda a: a.split(u' and ')
    formatters['date'] = lambda a: dateutil.parser.parse(a)
    formatters['isbn'] = lambda a: a.replace('-', '')

    print '\n', bookfile
    print_meta(meta, fields)

    def open_google(search):
        if not search and 'title' in meta:
            search = meta['title']
        if search:
            webbrowser.open('http://scholar.google.com/scholar?' +
                            urllib.urlencode({'q': search.encode('utf-8')}))
    formatters['google scholar'] = lambda v: open_google(v)

    def open_file(search):
        if sys.platform.startswith('darwin'):
            os.system('open \"' + bookfile + '\"')
        elif sys.platform.startswith('linux'):
            os.system('xdg-open \"' + bookfile + '\"')
        else:
            # Assume windows
            os.system('start ' + bookfile)
    formatters['Open file'] = lambda v: open_file(v)

    def open_google_books(search):
        if not search and 'title' in meta:
            search = meta['title']
        if search:
            webbrowser.open('http://books.google.com/books?' +
                            urllib.urlencode({'q': search.encode('utf-8')}))
    formatters['Books at google'] = lambda v: open_google_books(v)

    def open_open_library(search):
        if not search and 'isbn' in meta:
            search = meta['isbn']
        if search:
            webbrowser.open('http://openlibrary.org/search?' +
                            urllib.urlencode({'isbn': search}))
    formatters['open library'] = lambda v: open_open_library(v)

    def open_wikipedia(search):
        if not search and 'isbn' in meta:
            search = meta['isbn']
        if search:
            webbrowser.open('http://en.wikipedia.org/wiki/' +
                            'Special:BookSources/' + search)
    formatters['wikipedia'] = lambda v: open_wikipedia(v)

    newmeta = {}

    def meta_from_bibstr(bs):
        translate = {'date': 'year'}
        for f in fields:
            fb = f
            if f in translate:
                fb = translate[f]
            m = re.search(u'' + fb + '=\{(.+)\}', bs)
            if m:
                val = formatters[f](m.group(1))
                field_to_file(f, val, bookfile)
                newmeta[f] = val
        return bs
    formatters['bibstr'] = lambda v: meta_from_bibstr(v)


    multiline = ['bibstr']
    index = {}
    for field in fields:
        index[field[0]] = field
    while True:
        print 'Option (enter to next book, q to exit): ',
        option = getch()
        if option == 'q' or not option.strip():
            print
            return dict(meta.items() + newmeta.items()), option

        field = index.get(option, '')
        if not field:
            print
            continue
        print field
        value = userinput(meta.get(field, u''),
                          multiline=field in multiline)
        formatted_value = formatters[field](value)
        if formatted_value:
            field_to_file(field, formatted_value, bookfile)
            ##option = cl_option(field, formatted_value)
            ##if option:
            ##    devnull = codecs.open(os.devnull, 'w', encoding='utf-8')
            ##    if subprocess.call(['ebook-meta', option, bookfile],
            ##                       stdout=devnull, stderr=devnull):
            ##        print "** Error calling ebook-meta on", bookfile, \
            ##          "(maybe DRMed book?)"
            newmeta[field] = formatted_value
            meta = guess_meta(bookfile)
            print_meta(meta, fields, newmeta)


def as_main():
    import os, sys
    def help():
        print __doc__ % (__author__, __date__)

    from getopt import getopt
    opts, files = getopt(sys.argv[1:], 'h',
                         ['help'])
    for (opt, val) in opts:
        if   opt == '-h' or opt == '--help':
            help()
            sys.exit(1)

    for fname in files:
        meta, key = interactive_meta(fname)
        print meta
        if key == 'q':
            return

if __name__ == '__main__':
    as_main()

# -*- coding: utf-8 -*-
"""bookmeta
By %s
%s

Interactive wrapper around some parts of ebook-meta, one of the apps
that come with calibre.

Usage: bookmeta book_file[s]
"""
__date__ = "2013-05-02"
__author__ = "Juan Reyero, http://juanreyero.com"

import sys, os, codecs
import webbrowser, urllib
import orgklip.bookid as bookid
import collections
import subprocess

#sys.stdout = codecs.getwriter('utf8')(sys.stdout)

class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()


def print_meta(meta, fields):
    for field in fields:
        value = meta.get(field, '')
        if not isinstance(value, basestring) and hasattr(value, '__iter__'):
            value = u' and '.join(value)
        print "%12s [%s]: %s" % (field, field[0], value)

def interactive_meta(bookfile):
    meta = bookid.guess_meta(bookfile)

    fields = ['author', 'date', 'isbn', 'language', 'publisher',
              'title', 'google']
    index = {}
    for field in fields:
        index[field[0]] = field
    formatters = collections.defaultdict(lambda: lambda v: v)
    formatters['author'] = lambda a: u' & '.join(a.split(u' and '))

    print '\n', bookfile
    print_meta(meta, fields)
    meta['google'] = meta.get('title', '')

    def open_google(search):
        if not search and 'title' in meta:
            search = meta['title']
        if search:
            webbrowser.open('http://books.google.com/books?' +
                            urllib.urlencode({'q': search.encode('utf-8')}))

    formatters['google'] = lambda v: open_google(v)

    def cl_option(fname, val):
        if fname == u'author':
            fname = u'authors'
        return u'--' + fname + u'=' + val

    while True:
        print 'Option (enter to next book, q to exit): ',
        option = getch()
        if option == 'q':
            sys.exit(1)
        if not option.strip():
            print
            return
        field = index.get(option, '')
        if not field:
            continue
        print field
        #print u'' % meta.get(field, u'')
        #value = raw_input(u'Value : ').decode(sys.stdin.encoding)
        print u'Value (%s): ' % meta.get(field, u''),
        value = raw_input('').decode(sys.stdin.encoding)
        value = formatters[field](value)
        if value:
            devnull = codecs.open(os.devnull, 'w', encoding='utf-8')
            subprocess.call(['ebook-meta', cl_option(field, value), bookfile],
                             stdout=devnull, stderr=devnull)
            meta = bookid.guess_meta(bookfile)
            print_meta(meta, fields)


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
        interactive_meta(fname)

if __name__ == '__main__':
    as_main()

# -*- coding: utf-8 -*-
"""refstore
By %s
%s

Import books, possibly cleaning them.  For each book: build a bibid
based on the metadata, add an entry to a bib file, copy the book to a
centralized location with a name built from the bibid, and add the
clippings to an org-mode file assuming that the kindle clipping file
is present (either as /Volumes/Kindle/documents/My Clippings.txt or
as kindle-clippings.txt in the current directory.)

If no book files are specified it will import all the books in the
source directory.

Usage: refstore [options] [book_file[s]]

Options:

-m dir, --master=dir  Directory to which book files will be copied.
-s dir, --source=dir  Directory in which to look for books.
-b fname, --bib=fname Bib file, by default 'ref.bib'
-o fname, --org=fname Org-mode file, by default 'ref.org', to which
                      clippings will be appended.
-a, --also-repeated   Process books that already appear on the bib file
                      (by default they are ignored)
-k str, --kindle=str  Serial of the kindle for which the books have been
                      downloaded, in case you want to de-drm them.
-d str, --dedrm=str   Directory where the k4mobidedrm.py file of the
                      de-drm distribution (search for apprenticealf)
                      resides.
-h, --help            This help.
"""
__date__ = "2013-04-29"
__author__ = "Juan Reyero, http://juanreyero.com"

import os
import re
import codecs
import subprocess

from cleanup import Cleanup
import docid
from clipper import KindleBook


class ImportBooks(object):
    def __init__(self, sourcedir, masterdir, bibfile, orgfile,
                 serial=None, alfdir=None, also_repeated=False):
        self.sourcedir = os.path.expanduser(sourcedir)
        self.masterdir = os.path.expanduser(masterdir)
        if serial and alfdir:
            self.cleanup = Cleanup(serial, alfdir)
        else:
            self.cleanup = None
        self.bibfile = os.path.expanduser(bibfile)
        self.orgfile = os.path.expanduser(orgfile)
        self.also_repeated = also_repeated

    def add_to_bib(self, bibstr, bibid):
        if os.path.exists(self.bibfile):
            bib = codecs.open(self.bibfile,
                              encoding='utf-8').read()
        else:
            bib = ''
        if not bibid in bib:
            with codecs.open(self.bibfile, 'a', encoding='utf-8') as f:
                f.write(u'\n' + bibstr + u'\n')
            return True
        return False

    def clippings_to_org(self, bookfile):
        kc = KindleBook(bookfile, org_path='.', text_path='text')
        kc.print_clippings(self.orgfile)

    def convert(self, book):
        if not os.path.exists(book):
            book = os.path.join(self.sourcedir, book)
        print book
        ext = os.path.splitext(book)[1]
        if ext == '.azw':
            if self.cleanup:
                book = self.cleanup.decrypt(book)
            else:
                print ("** Won't be able to clean up " + book +
                       ", need a kindle serial")
                return

        bibstr, meta = docid.bibstr(book, interactive=True)
        bidid = meta['bibid']

        new = self.add_to_bib(bibstr, bibid)
        if new or self.also_repeated:
            newbook = os.path.join(self.masterdir, bibid)
            if ext in ('.mobi', '.pdf'):
                os.rename(book, newbook + ext)
            else:
                newbook = newbook + '.mobi'
                devnull = codecs.open(os.devnull, 'w', encoding='utf-8')
                if subprocess.call(['ebook-convert', book,
                                    newbook],
                                    stdout=devnull, stderr=devnull):
                    print ("** Error converting to " + newbook +
                           " (maybe DRMed book?)")
                    return None

            self.clippings_to_org(newbook)
            print ' ->', newbook
            return newbook

    def convert_all(self):
        for book in os.listdir(self.sourcedir):
            ext = os.path.splitext(book)[1]
            if ext in ('.azw', '.epub', '.mobi', '.pdf'):
                self.convert(book)


def as_main():
    import os, sys
    def help():
        print __doc__ % (__author__, __date__)

    from getopt import getopt
    opts, files = getopt(sys.argv[1:], 'hm:s:b:o:ak:d:',
                         ['help', 'master=', 'source=', 'bib=', 'org=',
                          'also-repeated', 'kindle=', 'dedrm='])
    master = ''
    source = ''
    also_repeated = False
    serial = None
    alfdir = None
    bibfile = 'ref.bib'
    orgfile = 'ref.org'
    for (opt, val) in opts:
        if   opt == '-h' or opt == '--help':
            help()
            sys.exit(1)
        elif opt == '-m' or opt == '--master':
            master = val
        elif opt == '-s' or opt == '--source':
            source = val
        elif opt == '-b' or opt == '--bib':
            bibfile = val
        elif opt == '-o' or opt == '--org':
            orgfile = val
        elif opt == '-a' or opt == '--also-repeated':
            also_repeated = True
        elif opt == '-k' or opt == '--kindle':
            serial = val
        elif opt == '-d' or opt == '--dedrm':
            alfdir = val

    fr = ImportBooks(source, master, bibfile, orgfile,
                     serial, alfdir, also_repeated)

    if files:
        for fname in files:
            fr.convert(fname)
    else:
        fr.convert_all()

if __name__ == '__main__':
    as_main()

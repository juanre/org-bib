# -*- coding: utf-8 -*-
"""bookclips
By %s
%s

Extracts clippings associated to books from the Kindle clippings file
(to be found in the kindle as "documents/My Clippings.txt") and
produces, for all the books in the command line,

- a unique id, usable by bibtex and as the canonical file name for the
  different formats;
- a text version;
- an org-mode formatted entry including all the metadata and all the
  book's clippings, with links to the position in the text version of
  the book where they appear.

If a new file is created the books will be written under an * Inbox
heading.

Requirements:

- dashify (https://github.com/juanre/dashify)
- dateutil.parser (http://labix.org/python-dateutil)
- ebook-meta and ebook-convert, command line tools from calibre.
  Install calibre from http://calibre-ebook.com/, then Preferences ->
  Miscelaneous -> Install command line tools.

Usage: bookclips [options] book_file[s]

Options:

-o fname, --org-file=fname  File to which the org-mode file will be saved.
-t dir, --text-path=dir Directory to which the text version of the book (and
                        target of the links) will be saved.
-c file, --clips=file   File where the clips are to be found.  Defaults to
                        /Volumes/Kindle/documents/My Clippings.txt or
                        the clippings backup file (see next option).
-b file, --backup-file=file  The file to which clippings will be backed up.
                             If the main clippings file is not found this
                             one will be used, unless the next option is set.
-n, --no-backup         Do not backup the clippings file.
-h, --help              This help.

"""
__date__ = "2013-04-29"
__author__ = "Juan Reyero, http://juanreyero.com"


import os, codecs, sys, subprocess
import re
import datetime
import orgbib.parse
import orgbib.docid

def extract_quotes(orgfile):
    return set(re.findall(r'\#\+begin_quote\n(.+?)\n\#\+end_quote',
                          codecs.open(orgfile,
                                      encoding='utf-8').read(),
                          re.DOTALL|re.IGNORECASE))

def extract_ids(orgfile):
    return set(re.findall(r':custom_id: (.+?)\n',
                          codecs.open(orgfile,
                                      encoding='utf-8').read(),
                          re.DOTALL|re.IGNORECASE))

#:Custom_ID: harford-2011---adapt

class KindleBook(object):
    """Associated to a mobi book file, it knows how to extract the
    clippings from the clips_file and print them in org-mode format
    with all the metadata.  It can also produce the bib entry for the
    book.
    """
    def __init__(self, book_file, text_path='',
                 clips_file='/Volumes/Kindle/documents/My Clippings.txt',
                 bu_clips_file='kindle-clippings.txt', meta=None):
        self.clips_file = clips_file
        self.bu_clips_file = bu_clips_file
        self.book_file = book_file
        if meta is None:
            self.meta = orgbib.docid.bibstr(book_file)[1]
        else:
            self.meta = meta
        self.bibid = self.meta['bibid']
        self.title = self.meta['title']

        self.txtbook_file = os.path.join(text_path, self.bibid + '.txt')
        if not os.path.exists(self.txtbook_file) and \
               os.path.splitext(book_file)[1] != '.pdf':
            if not os.path.exists(text_path):
                os.makedirs(text_path)
            try:
                devnull = codecs.open(os.devnull, 'w', encoding='utf-8')
                if subprocess.call(['ebook-convert', book_file,
                                    self.txtbook_file],
                                    stdout=devnull, stderr=devnull):
                    print "** Error converting to", self.txtbook_file, \
                      "(maybe DRMed book?)"
                else:
                    print ' ->', self.txtbook_file
            except:
                print "** Error converting to", self.txtbook_file, \
                  "(maybe calibre's ebook-convert not installed?)"

        if os.path.exists(self.txtbook_file):
            self.txtbook = codecs.open(self.txtbook_file,
                                       encoding='utf-8').read()
        else:
            self.txtbook = None
            print '** Warning: No txt book file, no links will be produced.'

    def bibstr(self):
        return self.bibstr, self.bibid

    def find_clipping(self, clipping):
        """The clipping might not be identical to the text in the book.  This
        function attempts to find the closest match.  If it finds it, it
        should be usable as an org-mode link.
        """
        import difflib
        book = self.txtbook
        if book is None:
            return None
        s = difflib.SequenceMatcher(None, book, clipping, autojunk=False)
        loc = s.find_longest_match(0, len(book), 0, len(clipping))
        if loc:
            return book[loc.a : loc.a+loc.size]
        return None

    def print_clippings(self, outfile, doctype='book'):
        def upcase_first(s):
            return s[0].upper() + s[1:]

        kc = orgbib.parse.Clippings(self.clips_file, self.bu_clips_file)

        skip = set([])
        present_ids = set([])
        if os.path.exists(outfile):
            skip = extract_quotes(outfile)
            present_ids = extract_ids(outfile)

        clippings = [(clip, meta, note)
                     for clip, meta, note in kc.list_book(self.title)
                     if not (upcase_first(clip) in skip)]

        ext = os.path.splitext(self.book_file)[1]
        if not clippings:
            return

        if self.bibid in present_ids:
            print '*** duplicating entry', self.bibid

        if not os.path.exists(outfile):
            with codecs.open(outfile, 'w', encoding='utf-8') as f:
                f.write(u'# -*- coding: utf-8 -*-\n\n')
                f.write(u'* Inbox\n\n')

        with codecs.open(outfile, 'a', encoding='utf-8') as f:
            f.write(u'\n** ' + kc.book_full_name(self.title) + '\n')

            f.write(u':PROPERTIES:\n:on: [%s]\n' %
                    datetime.date.today().isoformat())
            f.write(u':Custom_ID: %s\n' % self.bibid)
            f.write(u':author: %s\n' % ' and '.join(self.meta['author']))
            for k, v in self.meta.iteritems():
                if (not k in ('tags', 'comments', 'author', 'author(s)',
                              'book producer', 'bibstr')
                    and not ' ' in k):
                    f.write(u':%s: %s\n' % (k, v))
            f.write(u':END:\n')

            if doctype == 'book':
                f.write(u'\n[[file:%s][Master]].\n' % self.book_file)
                f.write(u'[[bib:%s][Bib entry]].\n' % self.bibid)
            else:
                f.write(u'\n[[paper:%s][Master]].\n' % self.bibid)
                f.write(u'[[bib:%s][Bib entry]].\n' % self.bibid)

            for clip, meta, note in clippings:
                if meta.kind != 'bookmark':
                    f.write(u'\n*** ' +
                            upcase_first(u' '.join(clip.split(' ')[:10]))
                            + '\n')
                    props = ''
                    if meta.when:
                        props = ':added: [%s]\n' % meta.when.isoformat(' ')
                    if meta.loc:
                        props += ':loc: %s\n' % str(meta.loc)
                    if meta.page:
                        props += ':page: %s\n' % str(meta.page)
                    f.write(u':PROPERTIES:\n%s:END:\n' % props)
                    if note:
                        f.write(upcase_first(note) + u'\n\n')
                    #!!link = self.find_clipping(clip)
                    link = ''
                    if link:
                        f.write(u'[[file:%s::%s][Read more]].\n' %
                                (self.txtbook_file, link))
                    f.write(u'\n#+begin_quote\n' + upcase_first(clip) +
                            u'\n#+end_quote\n')


def as_main():
    import os, sys
    def help():
        print __doc__ % (__author__, __date__)

    from getopt import getopt
    opts, files = getopt(sys.argv[1:], 'hc:b:no:t:',
                         ['help', 'clips=', 'backup-file=', 'no-backup',
                          'org-file=', 'text-path='])


    clips_file = '/Volumes/Kindle/documents/My Clippings.txt'
    bu_clips_file = 'kindle-clippings.txt'
    backup = True
    org_file = None
    text_path = ''
    for (opt, val) in opts:
        if   opt == '-h' or opt == '--help':
            help()
            sys.exit(1)
        elif opt == '-c' or opt == '--clips':
            clips_file = val
        elif opt == '-b' or opt == '--backup-file':
            bu_clips_file = val
        elif opt == '-n' or opt == '--no-backup':
            backup = False
        elif opt == '-o' or opt == '--org-file':
            org_file = val
        elif opt == '-t' or opt == '--text-path':
            text_path = val

    if not backup:
        bu_clips_file = None

    for fname in files:
        KindleBook(fname, text_path,
                   clips_file, bu_clips_file).print_clippings(org_file)


if __name__ == '__main__':
    as_main()

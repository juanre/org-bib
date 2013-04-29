# -*- coding: utf-8 -*-
"""azwclean
By %s
%s

Ugly hack to clean up drm without too much noise and with dashified names.

Usage: azwclean [options] book_file[s]

Options:

-k str, --kindle=str  Serial of the kindle for which the books have been
                      downloaded, in case you want to de-drm them.
-d str, --dedrm=str   Directory where the k4mobidedrm.py file of the
                      de-drm distribution (search for apprenticealf)
                      resides.
-h, --help            This help.
"""
__date__ = "2013-04-29"
__author__ = "Juan Reyero, http://juanreyero.com"

import sys, os, codecs
import dashify

class Cleanup(object):
    def __init__(self, serial, alfdir, outdir='tmp'):
        self.serial = serial
        self.alfdir = alfdir
        self.outdir = outdir

    def decrypt(self, book):
        """Decrypts the book and returns the name of the output file.
        """
        if self.outdir and not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        drmdir = os.path.join(self.outdir, 'drm')
        os.mkdir(drmdir)
        cleanbook = None
        mobi = None
        try:
            temp = sys.stdout
            sys.stdout = codecs.open(os.devnull, 'w', encoding='utf-8')
            if self.alfdir:
                sys.path.append(self.alfdir)
            from k4mobidedrm import decryptBook
            decryptBook(os.path.expanduser(book), drmdir,
                        [], [self.serial], [])
            sys.stdout = temp
            cleanbook = os.listdir(drmdir)[0]
            mobi = os.path.join(self.outdir,
                                dashify.dash_name(cleanbook.replace('_nodrm', '')))

            os.rename(os.path.join(drmdir, cleanbook), mobi)
        finally:
            os.rmdir(drmdir)

        return mobi

def as_main():
    import os, sys
    def help():
        print __doc__ % (__author__, __date__)

    from getopt import getopt
    opts, files = getopt(sys.argv[1:], 'hk:d:',
                         ['help', 'kindle=', 'alf='])
    serial = None
    alfdir = None
    for (opt, val) in opts:
        if   opt == '-h' or opt == '--help':
            help()
            sys.exit(1)
        elif opt == '-k' or opt == '--kindle':
            serial = val
        elif opt == '-d' or opt == '--alf':
            alfdir = val

    if not serial:
        print "** Won't be able to clean up without a kindle serial number."
        sys.exit(1)

    cl = Cleanup(serial, alfdir, outdir='')
    for fname in files:
        print cl.decrypt(fname)

if __name__ == '__main__':
    as_main()

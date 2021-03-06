#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os
import codecs
import re

def parse_loc(loc):
    """Parse the location.  Useful to locate notes (single-value
    location) using adjacent highlights (range location and text to
    link to).  Returns a tuple, one integer if single-value location
    or two integers if range location.

    >>> parse_loc('631-32')
    (631, 632)
    >>> parse_loc('1411')
    (1411,)
    >>> parse_loc('1420-21')
    (1420, 1421)
    """
    loc = loc.split('-')
    start = loc[0]
    if len(loc) == 1:
        return int(start),
    digits = len(loc[1])
    end = int(start[0:-digits] + '0' * digits) + int(loc[1])
    return int(start), end

def parse_metadata(line):
    """Parse the metadata line.

    Returns a named tuple with 'kind page loc when' fields.  The
    'kind' field can be either highlight, note or bookmark.  The
    'when' field is a datetime object if the dateutil library was
    available, None otherwise.

    >>> parse_metadata('- Highlight Loc. 631-32  | Added on Tuesday, June 05, 2012, 11:43 PM')
    Meta(kind='highlight', page=None, loc=(631, 632), when=datetime.datetime(2012, 6, 5, 23, 43))
    >>> parse_metadata('- Note Loc. 631  | Added on Tuesday, June 05, 2012, 11:45 PM')
    Meta(kind='note', page=None, loc=(631,), when=datetime.datetime(2012, 6, 5, 23, 45))
    >>> parse_metadata('- Note on Page 124 | Loc. 1411  | Added on Saturday, April 20, 2013, 02:18 PM')
    Meta(kind='note', page=124, loc=(1411,), when=datetime.datetime(2013, 4, 20, 14, 18))
    >>> parse_metadata('- Highlight on Page 125 | Loc. 1420-21  | Added on Saturday, April 20, 2013, 02:19 PM')
    Meta(kind='highlight', page=125, loc=(1420, 1421), when=datetime.datetime(2013, 4, 20, 14, 19))
    >>> parse_metadata('- Bookmark on Page 137 | Loc. 2396  | Added on Sunday, September 18, 2011, 10:37 PM')
    Meta(kind='bookmark', page=137, loc=(2396,), when=datetime.datetime(2011, 9, 18, 22, 37))
    >>> parse_metadata('- Your Highlight on page 122 | Location 2184-2188 | Added on Saturday, August 2, 2014 8:16:19 PM')
    Meta(kind='highlight', page=122, loc=(2184, 2188), when=datetime.datetime(2014, 8, 2, 20, 16, 19))
    """
    if '- Highlight' in line or '- Your Highlight' in line:
        kind = 'highlight'
    elif '- Note' in line or '- Your Note' in line:
        kind = 'note'
    elif '- Bookmark' in line or '- Your Bookmark' in line:
        kind = 'bookmark'
    else:
        return None
    line = line.split('|')

    page = None
    m = re.search(r'[Pp]age (\d+)', line[0])
    if m:
        page = int(m.group(1))

    loc = None
    m = re.search(r'Loc. (\d+-?\d+)', line[-2])
    if m:
        loc = parse_loc(m.group(1))
    else:
        m = re.search(r'Location (\d+-?\d+)', line[-2])
        if m:
            loc = parse_loc(m.group(1))

    when = None
    if 'Added on' in line[-1]:
        try:
            import dateutil.parser
            when = dateutil.parser.parse(line[-1][9:])
        except:
            pass
    Meta = collections.namedtuple('Meta', 'kind page loc when')
    return Meta(kind, page, loc, when)

def parse_clippings(clips_file):
    """Reads a kindle clippings file and returns a dictionary indexed by book
    name whose values are arrays of clippings.
    """
    with codecs.open(clips_file, 'r', encoding="utf-8") as f:
        content = f.read()

    ## Deprecated zero-width no-break unicode space
    content = content.replace(u'\ufeff', u'')

    # At some point it started coming with \r that mess everything up
    content = content.replace(u'\r','')

    clips = collections.defaultdict(list)
    for section in content.split(u"=========="):
        lines = [l for l in section.split(u'\n') if l]
        if len(lines) >= 3:
            book, what = lines[0], lines[1]
            content = '\n'.join(lines[2:])
            meta = parse_metadata(what)
            if meta is not None:
                if meta.kind == 'note':
                    ## We associate notes to the previous highlight.
                    clips[book][-1][2] = content
                else:
                    clips[book].append([content, meta, ''])

    return clips


class Clippings(object):
    def __init__(self, clips_file, bu_clips_file=None):
        parse_from = bu_clips_file
        if os.path.exists(clips_file):
            parse_from = clips_file
            if bu_clips_file:
                import shutil
                shutil.copy(clips_file, bu_clips_file)
        if os.path.exists(parse_from):
            self.clips = parse_clippings(parse_from)
        else:
            print "** Warning, no clippings file found."
            self.clips = {}

    def list_book_titles(self):
        return sorted(self.clips.keys())

    def book_full_name(self, title):
        if title in self.clips:
            return title
        title = title.split(':')[0]
        for k in self.clips.keys():
            if title in k:
                return k

        titlelc = title.lower()
        for k in self.clips.keys():
            if titlelc in k.lower():
                return k
        return title

    def list_book(self, title):
        full_name = self.book_full_name(title)
        if full_name:
            return self.clips.get(full_name, [])
        else:
            return []

def _test():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    #kc = Clippings()
    #print kc.list_book_titles()
    #print kc.list_book('Where Good Ideas Come From')
    _test()

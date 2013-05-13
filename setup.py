#!/usr/bin/env python

from setuptools import setup

setup(name='orgbib',
      version='0.0.1',
      description='Bibliography to org-mode, including kindle book clipping.',
      author='Juan Reyero',
      author_email='juan@juanreyero.com',
      url='http://juanreyero.com/',
      packages=['orgbib'],
      entry_points = {
            'console_scripts': ['bibimport = orgbib.importer:as_main',
                                'azwclean = orgbib.cleanup:as_main',
                                'docmeta = orgbib.docmeta:as_main',
                                'docbib = orgbib.docid:as_main',
                                'bookclips = orgbib.clipper:as_main']},
      test_suite='orgbib.test.orgbib_test.suite')

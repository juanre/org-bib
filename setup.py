#!/usr/bin/env python

from setuptools import setup

setup(name='storebook',
      version='0.0.1',
      description='Properly organize kindle books.',
      author='Juan Reyero',
      author_email='juan@juanreyero.com',
      url='http://juanreyero.com/',
      packages=['storebook'],
      entry_points = {
            'console_scripts': ['storebook = storebook.importer:as_main',
                                'azwclean = storebook.cleanup:as_main']})

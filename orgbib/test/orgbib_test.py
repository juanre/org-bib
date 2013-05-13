"""Integrate unittest and docstring.  Main entry for testing.
"""

import orgbib.parse
import orgbib.docid

import unittest, doctest

def suite():
    tests = [doctest.DocTestSuite(orgbib.parse),
             doctest.DocTestSuite(orgbib.docid)]
    return unittest.TestSuite(tests)

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

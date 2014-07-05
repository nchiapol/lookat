# -*- coding: utf-8 -*-
"""
Special test for bug due to root messing up readline's tab-completion 
This test must be run independently:
  nosetests readline_test.py

"""
from nose.tools import assert_equal

def test_tabcompleter():
    import readline
    orig = readline.get_completer()
    import lookat
    c = readline.get_completer()
    assert_equal(c, orig)


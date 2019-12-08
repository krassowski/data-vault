from data_vault import clean_line
from data_vault.parsing import unquote, bool_or_str


def test_clean_line():
    pieces = clean_line('from module import a, b, c')
    assert pieces == ['from', 'module', 'import', 'a,b,c']

    # commas
    pieces = clean_line('from "a/path/with/c,o,m,m,a,s" import a, b, c')
    assert pieces == ['from', '"a/path/with/c,o,m,m,a,s"', 'import', 'a,b,c']

    pieces = clean_line("from 'a/path/with/c,o,m,m,a,s' import a, b, c")
    assert pieces == ['from', "'a/path/with/c,o,m,m,a,s'", 'import', 'a,b,c']

    # escaped paths
    pieces = clean_line(r"from 'an/escaped\'path/' import a, b, c")
    assert pieces == ['from', r"'an/escaped\'path/'", 'import', 'a,b,c']

    # comments
    pieces = clean_line('from module import a, b#, c')
    assert pieces == ['from', 'module', 'import', 'a,b']


def test_unquote():
    assert unquote("'an/escaped\'path/'") == 'an/escaped\'path/'
    assert unquote('"an/escaped\"path/"') == 'an/escaped\"path/'


def test_bool_or_str():
    assert bool_or_str('a') == 'a'
    assert bool_or_str('True') is True
    assert bool_or_str('False') is False
    assert bool_or_str('true') == 'true'

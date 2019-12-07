from unittest.mock import patch

from pandas import DataFrame, read_csv
from pytest import raises
from IPython import get_ipython

from . import file_from_storage
from .frames import frame_manager


ipython = get_ipython()
EXAMPLE_DATA_FRAME = DataFrame([{'a': 1, 'b': 1}, {'a': 1, 'b': 2}])


def patch_ipython_globals(dummy_globals):
    return patch.object(frame_manager, 'get_ipython_globals', return_value=dummy_globals)


def test_usage_help(tmpdir):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        with raises(ValueError) as error_info:
            ipython.magic('vault store x')
            assert error_info.match('No command matched. Did you mean:\n\t - store .*?')


def test_variable_not_defined(tmpdir):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip')

    with patch_ipython_globals(locals()):
        with raises(ValueError) as error_info:
            ipython.magic('vault store x')
            assert error_info.match(".*variable 'x' is not defined in the global namespace.*")


def test_function_not_defined(tmpdir):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        with raises(NameError) as error_info:
            ipython.magic('vault store x in my_frames with pipe_delimited')
            assert error_info.match("function 'pipe_delimited' is not defined in the global namespace")


def test_store(tmpdir):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')

    with file_from_storage(f'{tmpdir}/archive.zip', 'my_frames/x') as f:
        data = read_csv(f, csv='\t')
        assert x.equals(data)

        
def test_store_with_exporter(tmpdir):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip')
    x = EXAMPLE_DATA_FRAME

    def pipe_delimited(df):
        df.to_csv(sep='|')

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames with pipe_delimited')

    with file_from_storage(f'{tmpdir}/archive.zip', 'my_frames/x') as f:
        data = read_csv(f, csv='|')
        assert x.equals(data)

def test_open_vault_message(tmpdir):
    with raises(Exception) as error_info:
        ipython.magic('vault del x')
        assert error_info.match('Please setup the storage with %open_valut first')
        
def test_comments_in_magics():
    pass
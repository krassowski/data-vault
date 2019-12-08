from unittest.mock import patch

from _pytest.recwarn import warns
from pandas import DataFrame, read_csv
from pytest import raises, fixture
from IPython import get_ipython

from .seven_zip import file_from_storage
from .frames import frame_manager


ipython = get_ipython()
EXAMPLE_DATA_FRAME = DataFrame([{'a': 1, 'b': 1}, {'a': 1, 'b': 2}])


def patch_ipython_globals(dummy_globals):
    return patch.object(frame_manager, 'get_ipython_globals', return_value=dummy_globals)


@fixture
def mock_key(monkeypatch):
    monkeypatch.setenv('KEY', 'a_strong_password')


def test_open_vault_message():
    with raises(Exception, match='Please setup the storage with %open_vault first'):
        ipython.magic('vault del x')


def test_vault_security_alert(tmpdir):
    # should warn if not encryption key provided
    with warns(UserWarning, match='Encryption variable not set - no encryption will be used..*'):
        ipython.magic(f'open_vault --path {tmpdir}/archive.zip')

    # should not warn if secure explicitly toggled off
    with warns(None) as record:
        ipython.magic(f'open_vault --path {tmpdir}/archive.zip --secure False')
        assert not record.list

    # should not warn if encryption key provided
    with warns(None) as record:
        ipython.magic(f'open_vault --path {tmpdir}/archive.zip -e SOME_KEY')
        assert not record.list


def test_usage_help(tmpdir, mock_key):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip -e KEY')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        with raises(ValueError, match='No command matched. Did you mean:\n\t - store .*?'):
            ipython.magic('vault store x')


def test_variable_not_defined(tmpdir, mock_key):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip -e KEY')

    with patch_ipython_globals(locals()):
        with raises(ValueError, match=".*variable 'x' is not defined in the global namespace.*"):
            ipython.magic('vault store x')


def test_function_not_defined(tmpdir, mock_key):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip -e KEY')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        with raises(NameError, match="function 'pipe_delimited' is not defined in the global namespace"):
            ipython.magic('vault store x in my_frames with pipe_delimited')


def test_store(tmpdir):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip --secure False')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')

    with file_from_storage(f'{tmpdir}/archive.zip', 'my_frames/x') as f:
        data = read_csv(f, sep='\t', index_col=0)
        assert x.equals(data)


def test_store_with_encryption(tmpdir, mock_key):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip -e KEY')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')

    with raises(RuntimeError, match="File 'my_frames/x' is encrypted, password required for extraction"):
        with file_from_storage(f'{tmpdir}/archive.zip', 'my_frames/x') as f:
            data = read_csv(f, sep='\t', index_col=0)


def test_store_with_exporter(tmpdir):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip --secure False')
    x = EXAMPLE_DATA_FRAME

    def pipe_delimited(path: str, df):
        df.to_csv(path, sep='|')

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames with pipe_delimited')

    with file_from_storage(f'{tmpdir}/archive.zip', 'my_frames/x') as f:
        data = read_csv(f, sep='|', index_col=0)
        assert x.equals(data)


def test_comments_in_magics():
    pass

from contextlib import contextmanager
from unittest.mock import patch
from zipfile import ZipFile

from pandas import DataFrame, read_csv
from pandas.util.testing import assert_frame_equal
from pytest import raises, fixture, warns, mark
from IPython import get_ipython

from data_vault import Vault, parse_arguments, VaultMagics
from data_vault.frames import frame_manager


@contextmanager
def file_from_storage(archive_path, file_path, pwd: str = None, mode='r'):

    if pwd:
        pwd = pwd.encode()

    with ZipFile(archive_path) as archive:
        yield archive.open(
            file_path,
            mode=mode,
            pwd=pwd
        )


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


def test_store_import_del_using_path(tmpdir, mock_key):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip --secure False')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in "my_frames/custom_path.tsv"')

    with file_from_storage(f'{tmpdir}/archive.zip', 'my_frames/custom_path.tsv') as f:
        data = read_csv(f, sep='\t', index_col=0)
        assert x.equals(data)

    with patch_ipython_globals(globals()):
        ipython.magic('vault import "my_frames/custom_path.tsv" as y')

    assert_frame_equal(x, y, check_dtype=False)

    # TODO: fails on Windows, paths thing
    # ipython.magic('vault del "my_frames/custom_path.tsv"')

    # with raises(KeyError, match="There is no item named 'my_frames/custom_path.tsv' in the archive"):
    #     ipython.magic('vault import "my_frames/custom_path.tsv" as z')


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


def test_comments_in_magics(tmpdir):
    with warns(UserWarning, match='Encryption variable not set - no encryption will be used..*'):
        ipython.magic(f'open_vault --path {tmpdir}/archive.zip # --secure False')


@mark.parametrize('secure', ['--secure False', '-e KEY'])
def test_import_as(tmpdir, mock_key, secure):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip {secure}')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')

    with patch_ipython_globals(globals()):
        ipython.magic('vault import x from my_frames as y')

    # dtype should be optimized
    assert_frame_equal(x, y, check_dtype=False)

    with raises(AssertionError, match='.*Attribute "dtype" are different.*'):
        assert_frame_equal(x, y)


@mark.parametrize('secure', ['--secure False', '-e KEY'])
def test_del(tmpdir, mock_key, secure):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip {secure}')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')
        ipython.magic('vault del x from my_frames')

    with raises(KeyError, match="There is no item named 'my_frames/x' in the archive"):
        ipython.magic('vault import x from my_frames')


@mark.parametrize('secure', ['--secure False', '-e KEY'])
def test_del_not_in_namespace(tmpdir, mock_key, secure):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip {secure}')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x as y in my_frames')
        ipython.magic('vault del y from my_frames')


@mark.parametrize('secure', ['--secure False', '-e KEY'])
def test_exists_after_storage(tmpdir, mock_key, secure):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip {secure}')
    x = EXAMPLE_DATA_FRAME

    vault = Vault(parse_arguments(f'--path {tmpdir}/archive.zip {secure}', VaultMagics.defaults))
    assert 'my_frames/x' not in vault.archive
    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')
    assert 'my_frames/x' in vault.archive


@mark.parametrize('secure', ['--secure False', '-e KEY'])
def test_assert(tmpdir, mock_key, secure):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip {secure}')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')

        with raises(ValueError, match=r'Hash needs to have either 8 \(CRC32\) or 64 \(SHA256\) characters'):
            ipython.magic('vault assert x in my_frames is JH54')

        with raises(AssertionError):
            ipython.magic('vault assert x in my_frames is JH56321T')

        ipython.magic('vault assert x in my_frames is 3FDAA797')
        ipython.magic('vault assert x in my_frames is 3FDAA797 with CRC32')

        with raises(AssertionError):
            ipython.magic(f'vault assert x in my_frames is {"_" * 64} with SHA256')


@mark.parametrize('secure', ['--secure False', '-e KEY'])
def test_import_module(tmpdir, mock_key, secure):
    ipython.magic(f'open_vault --path {tmpdir}/archive.zip {secure}')
    x = EXAMPLE_DATA_FRAME

    with patch_ipython_globals(locals()):
        ipython.magic('vault store x in my_frames')
        ipython.magic('vault store x in my_frames as y')

    with patch_ipython_globals(globals()):
        ipython.magic('vault import my_frames')
        assert set(dir(my_frames)) == {'x', 'y'}

        assert_frame_equal(my_frames.x, x, check_dtype=False)
        assert_frame_equal(my_frames.y, y, check_dtype=False)

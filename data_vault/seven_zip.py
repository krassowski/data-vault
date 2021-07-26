import subprocess
from contextlib import contextmanager
from pathlib import Path
from zipfile import ZipFile, ZipInfo
from io import BytesIO


class SevenZip:

    command = '7z'

    def __init__(self, archive_path: str, password=None):
        self.path = archive_path
        self.password = password

    @contextmanager
    def open(self, file_path, mode='r', password: str = None, use_7z: bool = True):
        password = password or self.password

        if use_7z:
            yield BytesIO(self._execute(
                'e', file_path, '-so', *self._password_arg(password),
                decode=False, expect_ok_message=False
            ))
        else:
            if password:
                password = password.encode()

            with ZipFile(self.path) as archive:
                yield archive.open(file_path, mode=mode, pwd=password)

    def _execute(self, command, *args, decode: bool = True, expect_ok_message: bool = True):
        o = subprocess.check_output(
            [self.command, command, self.path, *args]
        )
        if expect_ok_message:
            assert b'Everything is Ok' in o
        if decode:
            o = o.decode('utf-8')
        return o

    def rename(self, old_path: str, new_path: str):
        return self._execute('rn', old_path, new_path)

    def exists(self):
        return Path(self.path).exists()

    def __contains__(self, file_path: str):
        if not self.exists():
            return False
        return file_path in self.list_members()

    def _password_arg(self, password: str):
        """Set password argument for given argument:
        - the password set at initialization if `password` is None,
        - given `password` if not None,
        - empty if `password` is `False`
        """
        if password is False:
            return []
        if password is not None:
            return ['-p' + password]
        if self.password:
            return ['-p' + self.password]
        return []

    def calc_checksum(self, file_path: str, method='CRC32', password=None):
        """Method: usually one of CRC32, CRC64, SHA1, SHA256, BLAKE2sp, CRC32 by default.
        """
        args = [file_path, '-scrc' + method] + self._password_arg(password)
        result = self._execute('t', *args)
        lines = [line for line in result.split('\n') if 'for data:' in line]
        assert len(lines) == 1
        method_used, hashsum = lines[0].split('for data:')
        return hashsum.strip()

    def check_integrity(self, password=None):
        return self._execute('t', *self._password_arg(password))

    def _add_file(self, file_path: str, password=None):
        args = ['-y', file_path] + self._password_arg(password)
        return self._execute('a', *args)

    def add_file(self, file_path: str, password=None, rename: str = False):
        assert rename is not True
        if not rename:
            self._add_file(file_path, password=password)
        else:
            added_path_in_archive = Path(file_path).name

            try:
                self._add_file(file_path, password=password)
                if rename in self:
                    self.delete(rename)
                self.rename(added_path_in_archive, rename)
            except Exception:
                self.delete(added_path_in_archive)
                raise

    def delete(self, file_to_remove: str):
        return self._execute('d', file_to_remove)

    def get_info(self, path) -> ZipInfo:
        with ZipFile(self.path) as archive:
            return archive.getinfo(path)

    def list_members(self, relative_to=''):
        with ZipFile(self.path) as archive:
            return [
                (
                    member.split(relative_to + '/')[1]
                    if relative_to else
                    member
                )
                for member in archive.namelist()
                if member.startswith(relative_to + '/' if relative_to else '')
            ]

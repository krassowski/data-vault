import subprocess
from pathlib import Path


class SevenZip:

    command = '7z'

    def __init__(self, archive_path: str, password=None):
        self.path = archive_path
        self.password = password

    def _execute(self, command, *args):
        o = subprocess.check_output(
            [self.command, command, self.path, *args]
        )
        assert b'Everything is Ok' in o
        return o.decode('utf-8')

    def rename(self, old_path: str, new_path: str):
        return self._execute('rn', old_path, new_path)

    def __contains__(self, file_path: str):
        try:
            self._execute('t', file_path)
            return False
        except subprocess.CalledProcessError:
            return True

    def _password_arg(self, password: str):
        """Set password argument for given argumnet:
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

    def add_file(self, file_path: str, password=None, rename=False):
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
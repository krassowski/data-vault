from tempfile import NamedTemporaryFile
from io import BytesIO
import os
import hashlib
from typing import Dict
import zlib
from warnings import warn

from pandas import read_csv

from .seven_zip import SevenZip
from .memory import optimize_memory
from .frames import frame_manager


class Vault:

    def __init__(self, settings: Dict):
        self.settings = settings

    def list_members(self, relative_to=None):
        return self.archive.list_members(relative_to=relative_to)

    def _default_exporter(self, variable, file_object):
        # line terminator set to '\n' to have the same hashes between Unix and Windows
        return variable.to_csv(file_object, sep='\t', line_terminator='\n')

    @property
    def archive(self):
        return SevenZip(
            archive_path=self.settings['path'],
            password=self._password
        )

    def save_object(self, path, value, exporter, **metadata):

        if not exporter:
            exporter = self._default_exporter

        old_checksum_crc, old_checksum_sha = None, None

        archive = self.archive

        if path in archive:
            old_checksum_crc = archive.calc_checksum(path, method='CRC32')
            old_checksum_sha = archive.calc_checksum(path, method='SHA256')

        with NamedTemporaryFile(delete=False) as f:

            try:
                f.close()
                try:
                    exporter(value, f.name)
                except AttributeError as e:
                    # json
                    if str(e) != "'str' object has no attribute 'write'":
                        raise
                    with open(f.name, 'w') as f2:
                        exporter(value, f2)
                except TypeError as e:
                    # pickle
                    if str(e) != "file must have a 'write' attribute":
                        raise
                    with open(f.name, 'wb') as f2:
                        exporter(value, f2)
                archive.add_file(f.name, rename=path)
            except Exception as e:
                raise e
            finally:
                os.remove(f.name)

        new_checksum_crc = archive.calc_checksum(path, method='CRC32')
        new_checksum_sha = archive.calc_checksum(path, method='SHA256')
        archive.check_integrity()

        return {
            'new_file': {
                'crc32': new_checksum_crc,
                'sha256': new_checksum_sha
            },
            'old_file': {
                'crc32': old_checksum_crc,
                'sha256': old_checksum_sha
            },
            **metadata
        }

    @property
    def _password(self):
        key_name = self.settings['encryption_variable']

        return (
            os.environ[key_name]
            if key_name else
            False
        )

    def _default_importer(self, file_object):
        df = read_csv(file_object, sep='\t', index_col=0, parse_dates=True)
        if self.settings['optimize_df']:
            df = optimize_memory(
                df,
                categorise_numbers=self.settings['numbers_as_categories'],
                categorise_booleans=self.settings['booleans_as_categories'],
                report=self.settings['report_memory_gain']
            )
        return df

    def load_object(self, path, variable_name, importer=None, to_globals=True):
        if not importer:
            importer = self._default_importer

        archive = self.archive
        info = archive.get_info(path)

        with archive.open(path) as f:
            content = f.read()
            crc_as_int = zlib.crc32(content)
            new_checksum_crc = hex(crc_as_int)[2:].upper()
            new_checksum_sha = hashlib.sha256(content).hexdigest().upper()
            obj = importer(BytesIO(content))
            if to_globals:
                frame_manager.get_ipython_globals()[variable_name] = obj

        # check integrity of a single file
        if info.CRC != crc_as_int:
            if info.CRC == 0:
                # https://sourceforge.net/p/sevenzip/discussion/45798/thread/c284a85f3f/
                warn(
                    'CRC not found, cannot verify integrity (note:'
                    ' this is expected for newer versions of 7zip when using AES encryption)'
                )
            else:
                raise ValueError(f'CRC do not match: {info.CRC} { crc_as_int}')

        metadata = {
            'new_file': {
                'crc32': new_checksum_crc,
                'sha256': new_checksum_sha
            },
            'subject': variable_name
        }

        if to_globals:
            return metadata
        else:
            return obj

    def check_integrity(self):
        self.archive.check_integrity()

    def remove_object(self, path):

        archive = self.archive

        old_checksum_crc = archive.calc_checksum(path, method='CRC32')
        old_checksum_sha = archive.calc_checksum(path, method='SHA256')

        archive.delete(path)

        return [{
            'old_file': {
                'crc32': old_checksum_crc,
                'sha256': old_checksum_sha
            },
            'subject': path
        }]

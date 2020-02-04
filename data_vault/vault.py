from tempfile import NamedTemporaryFile
import os
from typing import Dict

from pandas import read_csv

from .seven_zip import SevenZip
from .memory import optimize_memory
from .frames import frame_manager


class Vault:

    def __init__(self, settings: Dict):
        self.settings = settings

    def list_members(self, relative_to=None):
        return self.archive.list_members(relative_to=relative_to)

    def _default_exporter(self, file_object, variable):
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
                exporter(f.name, value)
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

        with archive.open(path) as f:
            obj = importer(f)
            if to_globals:
                frame_manager.get_ipython_globals()[variable_name] = obj

        new_checksum_crc = archive.calc_checksum(path, method='CRC32')
        new_checksum_sha = archive.calc_checksum(path, method='SHA256')
        archive.check_integrity()

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

from typing import Dict, Callable

from .action import record_action
from .vault import Vault


class DynamicVault:

    def __init__(self, path, vault: Vault, cache=True, display_timestamp=True, display_metadata=True):
        self.path = path
        self.vault = vault
        self.importers = {}
        self.cache = cache
        self.cached = {}
        self.display_timestamp = display_timestamp
        self.display_metadata = display_metadata
        self.default_importer = None

    def set_importers(self, importers: Dict[str, Callable]):
        self.importers = importers
        return self

    def use_importer(self, importer: Callable):
        self.default_importer = importer
        return self

    def __getattr__(self, key):
        prefixes = {
            '/'.join(full[:subset + 1])
            for item in self.__dir__()
            for full in [item.split('/')[:-1]]
            if full
            for subset in range(len(full))
        }
        path = key if not self.path else self.path + '/' + key
        if key in self.__dir__():
            if self.cache and key in self.cached:
                return self.cached[key]
            importer = self.importers.get(key, self.default_importer)
            with record_action(
                command=f'dynamic import of {key}',
                verb='imported',
                display_timestamp=self.display_timestamp,
                display_metadata=self.display_metadata
            ) as metadata:
                value, result_metadata = self.vault.load_object(path, key, importer, to_globals=False)
                action_metadata = {
                    'action': 'import',
                    'result': [result_metadata]
                }
                metadata.update(action_metadata)
            if self.cache:
                self.cached[key] = value
            return value
        elif key in prefixes:
            vault = DynamicVault(
                path=path,
                vault=self.vault,
                cache=self.cache
            )
            vault.importers = self.importers.copy()
            return vault
        raise AttributeError

    def __dir__(self):
        """Make members tab-completable"""
        return self.vault.list_members(relative_to=self.path)

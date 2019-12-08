# TODO
from typing import Dict, Callable

from .vault import Vault


class DynamicVault:

    def __init__(self, path, vault: Vault):
        self.path = path
        self.vault = vault
        self.importers = {}

    def set_importers(self, importers: Dict[str, Callable]):
        self.importers = importers

    def __getattr__(self, key):
        if key in self.__dir__():
            importer = self.importers.get(key, None)
            # TODO: display metadata
            return self.vault.load_object(self.path + '/' + key, key, importer, to_globals=False)
        raise AttributeError

    def __dir__(self):
        """Make members tab-completable"""
        return self.vault.list_members(relative_to=self.path)

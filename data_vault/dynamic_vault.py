# TODO
from typing import Dict, Callable

from .vault import Vault


class DynamicVault:

    def __init__(self, path, vault: Vault):
        self.path = path
        self.vault = vault
        self.importers = {}
        # TODO: make it tab-completable

    def set_importers(self, importers: Dict[str, Callable]):
        self.importers = importers

    def __getattr__(self, key):
        if key in self.__dir__():
            pass

    def __dir__(self):
        return self.vault.list_members(relative_to=self.path)

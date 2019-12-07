# TODO
class DynamicVault:

    def __init__(self, path, importer):
        self.path = path
        self.imporer = importer
        # TODO: make it tab-completable

    def __getattr__(self, key):
        pass
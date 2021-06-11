from .action import Action, Syntax
from .parameters import ParametersValidator
from .parsing import split_variables, unquote
from .dynamic_vault import DynamicVault

params = ParametersValidator()


class StoreAction(Action):
    main_keyword = 'store'
    verb = 'stored'

    def store_in_module_as(self, arguments):
        path = arguments['in'] + '/' + arguments['as']
        variable = arguments['store']
        return self._store({path: variable}, arguments)

    def store_in_module(self, arguments):
        return self._store(
            {
                arguments['in'] + '/' + variable: variable
                for variable in split_variables(arguments['store'])
            },
            arguments
        )

    def store_in_path(self, arguments):
        path = unquote(arguments['in'])
        variable = arguments['store']
        return self._store({path: variable}, arguments)

    handlers = {
        store_in_module_as: Syntax(
            required={'store': params.one_or_many_variables, 'in': params.module, 'as': params.valid_id},
            optional={'with': params.function}
        ),
        store_in_module: Syntax(
            required={'store': params.one_or_many_variables, 'in': params.module},
            optional={'with': params.function, 'as': params.valid_id}
        ),
        store_in_path: Syntax(
            required={'store': params.one_variable, 'in': params.path},
            optional={'with': params.function},
            disallowed={
                'as': (
                    '"as" is not allowed for storing in path'
                    ' (it would be redundant as the path already specifies the target).'
                    ' If you wanted to point to a module in the archive, remove the quotes around {in}.'
                )
            }
        )
    }

    def _store(self, variables_by_paths, arguments):
        exporter = self.with_function(arguments)

        return [
            self.vault.save_object(path, self.ipython_globals[variable], exporter, subject=variable)
            for path, variable in variables_by_paths.items()
        ]


class ImportAction(Action):
    """Load a variable(s) exported from a notebook arbitrary data from the active storage.

    > %vault from notebook_path import variable
    > %vault from notebook_path import variable with your_function as variable
    > %vault import 'file.tsv' with your_function as variable

    It also allows you to specify custom import function, which:
        - has to be available in the global or local namespace
        - should accept a file object
        - should return the data loaded from the file object
    """

    main_keyword = 'import'
    verb = 'imported'

    def from_module_import_as(self, arguments):
        path = arguments['from']
        variable = arguments['import']
        name = arguments.get('as', variable)

        return self._import(
            {path + '/' + variable: name},
            arguments
        )

    def from_module_import(self, arguments):
        path = arguments['from']
        variables = split_variables(arguments['import'])

        return self._import(
            {
                path + '/' + variable: variable
                for variable in variables
            },
            arguments
        )

    def import_path_as(self, arguments):
        path = arguments['import']

        return self._import(
            {unquote(path): arguments['as']},
            arguments
        )

    def import_module(self, arguments):
        path = arguments['import']
        parent = path.split('.')[0]
        name = arguments.get('as', parent)

        if 'as' not in arguments:
            path = parent

        dynamic_vault = DynamicVault(path=path, vault=self.vault)
        self.ipython_globals[name] = dynamic_vault

        return []

    handlers = {
        from_module_import_as: Syntax(
            required={'import': params.valid_id, 'from': params.module, 'as': params.valid_id},
            optional={'with': params.function}
        ),
        from_module_import: Syntax(
            required={'import': params.one_or_many_valid_id, 'from': params.module},
            optional={'with': params.function, 'as': params.valid_id}
        ),
        import_path_as: Syntax(
            required={'import': params.path, 'as': params.valid_id},
            optional={'with': params.function}
        ),
        import_module: Syntax(
            required={'import': params.module},
            optional={'as': params.valid_id},
            disallowed={
                'with': (
                    '"with" not allowed for module import;'
                    ' to change the loading function for variables in the module,'
                    ' use module.set_importers({variable: function})'
                )
            }
        )
    }

    def _import(self, variables_by_paths, arguments):
        importer = self.with_function(arguments)

        return [
            self.vault.load_object(path, variable, importer)
            for path, variable in variables_by_paths.items()
        ]


class DeleteAction(Action):

    main_keyword = 'del'
    verb = 'deleted'

    def delete_variable(self, arguments):
        location = arguments['del']
        path = arguments['from'] + '/' + location

        return self._delete(arguments, path)

    def delete_path(self, arguments):
        location = arguments['del']
        path = unquote(location)

        return self._delete(arguments, path)

    handlers = {
        delete_variable: Syntax(
            required={'del': params.valid_id, 'from': params.module}
        ),
        delete_path: Syntax(
            required={'del': params.path}
        )
    }

    def _delete(self, arguments, path):
        # TODO test for folders, require all to remove a folder?
        # TODO: what to do about wildcards?
        assert '*' not in path

        return self.vault.remove_object(path)


class AssertAction(Action):
    """Verify the checksum of the input file, raise AssertionError if it differs.

    By default the checksum is calculated with CRC32."""
    main_keyword = 'assert'
    verb = 'verified'

    def assert_variable_hash(self, arguments):
        path = arguments['in'] + '/' + arguments['assert']
        return self._assert_hash(path=path, arguments=arguments)

    def assert_path_hash(self, arguments):
        return self._assert_hash(path=arguments['assert'], arguments=arguments)

    def _assert_hash(self, path, arguments):
        expected = arguments['is']
        method = arguments.get('with', 'CRC32')
        calculated = self.vault.archive.calc_checksum(path, method=method)
        assert expected == calculated
        return [{
            'subject': path,
            'old_file': {
                'crc32': calculated
            }
        }]

    handlers = {
        assert_variable_hash: Syntax(
            required={'assert': params.one_variable, 'in': params.module, 'is': params.hash},
            optional={'with': params.hash_method}
        ),
        assert_path_hash: Syntax(
            required={'assert': params.path, 'is': params.hash},
            optional={'with': params.hash_method}
        )
    }

import gzip
import json
from typing import List
from warnings import warn
from datetime import datetime

from IPython.display import display, Markdown
from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, line_magic, needs_local_scope

from .action import Action
from .actions import StoreAction, ImportAction, DeleteAction, AssertAction
from .frames import frame_manager
from .parsing import parse_arguments, clean_line
from .vault import Vault


def one(values):
    assert len(values) == 1
    return list(values)[0]


@magics_class
class VaultMagics(Magics):
    """The `%vault` magic provides a reproducible caching mechanism for variables exchange between notebooks.

    To open the vault use `%open_vault` magic.
    """

    defaults = {
        'path': 'storage.zip',
        'encryption_variable': None,
        'secure': True,
        'optimize_df': True,
        'timestamp': True,
        'metadata': True,
        'logs_path': '{path}.vault.log.gz',
        'gzip_logs': True,
        'report_memory_gain': False,
        # aggressive memory optimisation by categorising numbers
        'numbers_as_categories': False,
        'booleans_as_categories': False
        # 'allowed_duration': 30,  # seconds
    }

    assert len(set([d[0] for d in defaults])) == len(defaults)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = None
        self.current_vault: Vault = None

    actions: List[Action] = [
        StoreAction,
        ImportAction,
        DeleteAction,
        AssertAction
    ]

    @needs_local_scope
    @line_magic
    def open_vault(self, line, local_ns=None):
        """Open a zip archive for the vault. Once opened, all subsequent `%vault` magics operate on this archive."""
        frame_manager.ipython_globals = local_ns
        self.settings = parse_arguments(line, self.defaults)
        self.current_vault = Vault(self.settings)
        if self.settings['secure'] and not self.settings['encryption_variable']:
            warn(
                'Encryption variable not set - no encryption will be used.'
                ' Your data may be susceptible,'
                ' and you may not be able to access stored objects if those were previously encrypted.'
                ' Please provide the name of the environment variable with the storage key using `-e env_var_name`, or'
                ' set `--secure False` to silence this warning if you do not need additional protection.'
            )

    open_vault.__doc__ += '\n\nOpen vault arguments:\n\n' + '\n'.join([
        f'\t --{key}, -{key[0]}, default {value}'
        for key, value in defaults.items()
    ])

    def _ensure_configured(self):
        if not self.settings:
            raise Exception('Please setup the storage with %open_vault first.')

    def append_to_logs(self, metadata):
        logs_path = self.settings['logs_path'].format(**self.settings)
        opener = (gzip.open if self.settings['gzip_logs'] else open)
        with opener(logs_path, mode='ta+') as f:
            f.write(json.dumps(metadata) + '\n')

    def extract_arguments(self, line):
        iterable = iter(clean_line(line))
        return {key: next(iterable) for key in iterable}

    def select_action(self, arguments):

        actions = {
            action.main_keyword: action
            for action in self.actions
        }

        requested_actions = set(actions).intersection(arguments)
        requested_action = one(requested_actions)

        action_class = actions[requested_action]
        action = action_class(vault=self.current_vault)
        return action

    @needs_local_scope
    @line_magic
    def vault(self, line, local_ns=None):
        """Perform one of the available actions, print the description and save metadata in the cell."""
        self._ensure_configured()
        frame_manager.ipython_globals = local_ns

        started = self._timestamp()

        arguments = self.extract_arguments(line)
        action = self.select_action(arguments)
        metadata = action.perform(arguments)

        finished = self._timestamp()

        # if finished - started > settings['allowed_duration']:
        # warn that the operations took longer than expected

        metadata['started'] = started.isoformat()
        metadata['finished'] = finished.isoformat()
        metadata['finished_human_readable'] = finished.strftime('%A, %d. %b %Y %H:%M')
        metadata['command'] = line

        self.append_to_logs(metadata)

        display(Markdown(
            (
                action.short_stamp(metadata)
                if self.settings['timestamp'] else
                None
            ),
            metadata=(
                metadata
                if self.settings['metadata'] else
                None
            )
        ))

    vault.__doc__ += '\n\nVault commands:\n\n' + '\n'.join(
        [action.explain() for action in actions]
    )

    @staticmethod
    def _timestamp():
        return datetime.utcnow()


ip = get_ipython()
if ip:
    ip.register_magics(VaultMagics)
else:
    warn('Could not register VaultMagics - are you running from IPython?')

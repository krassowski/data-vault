from typing import Dict, Callable, List, Union
from abc import ABC, abstractproperty
from collections import Counter

from .vault import Vault
from .frames import frame_manager
from .parameters import get_dotted


Metadata = Dict[str, Union[str, List[Dict]]]


class Syntax:

    def __init__(self, required, optional=None, disallowed=None):
        self.required = required
        self.optional = optional or {}
        self.disallowed = disallowed or {}

    def calc_concordance(self, arguments, target, raise_exceptions=False):
        concordance = 0

        ruleset = getattr(self, target)
        misses = {}

        for arg, validator in ruleset.items():

            key = arg + ' <' + validator.__name__ + '>'

            if arg not in arguments:
                misses[key] = 'is missing'
                continue

            concordance += 0.5
            value = arguments[arg]

            try:
                if validator(value):
                    concordance += 0.5
                else:
                    misses[key] = 'not a ' + validator.__name__
            except Exception as e:
                if raise_exceptions:
                    raise e
                misses[key] = e

        return {
            'ratio': concordance / len(ruleset) if len(ruleset) else 0,
            'misses': misses
        }

    def diff(self, arguments):
        return ', '.join([
            f"'{keyword}': {explanation}"
            for keyword, explanation in
            self.calc_concordance(arguments, 'required', raise_exceptions=False)['misses'].items()
        ])

    def validate(self, arguments):
        assert self.calc_concordance(arguments, 'required', raise_exceptions=True)['ratio'] == 1
        # if it does not raise, it's ok
        self.calc_concordance(arguments, 'optional', raise_exceptions=True)
        self.check_disallowed(arguments)

    def check_disallowed(self, arguments):
        for keyword, error in self.disallowed.items():
            if keyword in arguments:
                raise ValueError(error)

    def _repr_args(self, args):
        return ' '.join([
            f'{keyword} <{param.__name__}>'
            for keyword, param in args.items()
        ])

    def __repr__(self):
        return (
            self._repr_args(self.required)
            + ' ['
            + self._repr_args(self.optional)
            + ']'
        )


class Action(ABC):

    def __init__(self, vault: Vault):
        self.vault: Vault = vault

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.__doc__ = (cls.__doc__ or '') + cls.explain()

    @abstractproperty
    def handlers(self) -> Dict[Callable, Syntax]:
        """Should be ordered from the most specific to the most general."""

    @abstractproperty
    def verb(self) -> str:
        """Past form of a verb describing the finished action."""

    @abstractproperty
    def main_keyword(self) -> str:
        """The main keyword which defines the kind of action"""

    def choose_handler(self, arguments):
        for handler, syntax in self.handlers.items():
            concordance = syntax.calc_concordance(arguments, 'required', raise_exceptions=False)['ratio']

            if concordance == 1:
                return handler

        return None

    def closest_syntax(self, arguments, n=3):
        counter = Counter({
            syntax: syntax.calc_concordance(arguments, 'required', raise_exceptions=False)['ratio']
            for handler, syntax in self.handlers.items()
        })
        return counter.most_common(n)

    def syntax_help(self, n=None, arguments=None):
        arguments = arguments or {}
        closest = [
            str(syntax) + (
                '\n\t\t> ' + syntax.diff(arguments)
                if arguments else
                ''
            )
            for syntax, concordance in self.closest_syntax(arguments, n=n)
        ]
        return '\n\t - '.join(map(str, [''] + closest))

    def perform(self, arguments) -> Metadata:
        # choose handler using syntax concordance with the required arguments
        handler = self.choose_handler(arguments)
        if not handler:
            error = 'No command matched. Did you mean:' + self.syntax_help(n=3, arguments=arguments)
            raise ValueError(error)

        # validate the optional and disallowed parts of the syntax
        syntax = self.handlers[handler]
        syntax.validate(arguments)

        bound_handler = getattr(self, handler.__name__)

        return {
            'action': self.main_keyword,
            'result': bound_handler(arguments)
        }

    def short_stamp(self, metadata: Metadata) -> str:
        """Return short, human readable description of the action"""

        def repr_result(result, hash_method='crc32'):
            hashcodes = [
                f'{result[file][hash_method]}'
                for file in ['old_file', 'new_file']
                if file in result
            ]
            return f"`{result['subject']}`" + ' (' + ' → '.join(hashcodes) + ')'

        results_n = len(metadata['result'])

        return (
            self.verb.capitalize()
            + (':\n\n - ' if results_n > 1 else ' ')
            + '\n - '.join([
                repr_result(result)
                for result in metadata['result']
            ])
            + ('\n\n' if results_n > 1 else ' ')
            + 'at '
            + metadata['finished_human_readable']
        )

    @property
    def ipython_globals(self):
        return frame_manager.get_ipython_globals()

    def with_function(self, arguments):
        if 'with' in arguments:
            func_name = arguments['with']
            return get_dotted(self.ipython_globals, func_name)
        return None

    @classmethod
    def explain(cls):
        instance = cls(None)
        return f'# {instance.main_keyword}' + instance.syntax_help()

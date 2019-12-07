from .frames import frame_manager
from .parsing import split_variables, unquote

# TODO, rewrite this part, the return True everywhere is bad... or differentiate between validators and probes? or always return, or always rise.

class ParametresValidator:

    # TODO rename module to folder (or other way of locating something in the vault)?
    def module(self, param: str):
        """Valid name of a folder"""
        return unquote(param) == param

    def path(self, param: str):
        """Valid path in the storage represented as a string; has to be packed in (single or double) quotes."""
        return unquote(param) != param

    def _get_from_globals(self, param: str, kind: str):
        # 1. is a valid identifier?
        if not param.isidentifier():
            raise ValueError(f"'{param}' is not a valid {kind} name")
        # 2. exists in the global namespace?
        ipython_globals = frame_manager.get_ipython_globals()
        try:
            return ipython_globals[param]
        except KeyError:
            raise NameError(f"{kind} '{param}' is not defined in the global namespace")

    def one_variable(self, param: str):
        """Valid Python variable"""
        self._get_from_globals(param, 'variable')
        return True

    def one_or_many_variables(self, param: str):
        """Valid Python variables separated by colon"""
        for v in split_variables(param):
            self._get_from_globals(v, 'variable')
        return True

    def function(self, param: str):
        """Valid Python function"""
        function = self._get_from_globals(param, 'function')
        if not callable(function):
            raise ValueError(f'not a function')
        return True

    def valid_id(self, param: str):
        """Valid Python identifier"""
        assert param.isidentifier()
        return True
    
    def one_or_many_valid_id(self, param: str):
        for v in split_variables(param):
            assert v.isidentifier()
        return True

    def hash_method(self, param: str):
        """Hash method, one of CRC32 or SHA256"""
        assert param in {'CRC32', 'SHA256'}
        return True
        
    def hash(self, param: str):
        assert len(hash) == 8 or len(hash) == 32
        return True
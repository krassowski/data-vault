from warnings import warn
from datetime import datetime

from IPython.display import display
from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, line_magic

from .actions import StoreAction, ImportAction, DeleteAction, AssertAction
from .parsing import parse_arguments, clean_line
from .vault import Vault


def one(values):
    assert len(values) == 1
    return list(values)[0]


@magics_class
class StorageMagics(Magics):
    """The storage magics provide a reproducible caching mechanism for variables exchange between notebooks.
    
    Differently to the builtin %store magic, the variables are stored in plain sight,
    in a zipped archive, so that they can be easily accessed for manual inspection,
    or for the use by other tools.
    
    ### Demonstration by usage:
    
        
    ### Design:
    
    Syntax:
    - easy to understand in plain language (avoid abbreviations when possible),
    - while intuitive for Python developers,
    - ... but sufficiently different so that it would not be mistaken with Python constructs
       - for example, we could have %from x import y, but this looks very like normal Python;
         having %vault from x import y makes it sufficiently easy to distinguish

    Reproducibility:
    - promote good reproducible and traceable organization of files:
       - promote storage in plain text files and the use of DataFrame
          - pickling is initially fun, but really try to change your class definitions and load your data again.
       - print out a short hashsum and human-readable datetime (always in UTC),
       - while providing even more details in cell metadata
    - allow to trace instances of the code being modified post execution
    - star imports are bad
    - as imports are confusing if there is more than one

    Security:

    ### Metadata for storage operations

    Each operation will print out the timestamp and the CRC32 short checksum of the files involved.
    The timestamp of the operation is reported in the UTC timezone in a human-readable format.

    This can be disabled by setting -t False or --timestamp False, however for the sake of reproducibility
    it is encouraged to keep this information visible in the notebook.

    More precise information including the SHA256 cheksum (with a lower probability of collisions),
    and a full timestamp (to detect potential race condition errors in file write operations) are
    embedded in the metadata of the cell. You can disable this by setting --metadata False.
    
    The exact command line is also stored in the metadata, so that if you accidentally modify the code cell
    without re-running the code, the change can be tracked down.

    ### Storage

    In order to enforce interoperability plain text files are used for pandas DataFrame and Series objects.
    Other variables are stores as pickle objects. The location of the storage archive on the disk defaults
    to `storage.zip` in the current directory, and can changed using `setup_storage` magic:
    
    > %open_vault -p custom_storage.zip
    
    #### Encryption
    
    **The encryption is not intended as a high security mechanism,
    but only as an additional layer of protection for already anonymized data.**
    
    The password to encrypt the storage archive is retrieved from the environmental variable,
    using a name provided in `encryption_variable` during the setup.
    
    > %open_vault -e ENV_STORAGE_KEY
    
    ### Memory optimizations
    
    Pandas DataFrames are by-default memory optimized by conversion of string variables to (ordered) categorical
    columns (pandas equivalent of R's factors/levels). Each string column will be tested for the memory improvement
    and the optimization will be only applied if it does reduce the memory usage.
    
    ### Simple filtering - IDEA FOR DISCUSSION, NOT IMPLEMENTED
    
    To enable high-performance subsetting a simple, grep-like pre-filtering is provided:
    
    Import only first five rows:
       > %vault from notebook import large_frame.rows[:5] as large_frame_head

    When subsetting, the use of `as` is required to prevent potential confusion of the original `large_frame` object with its subset.
    
    To import only rows including text "SNP":
        > %vault from notebook import large_frame.grep("SNP") as large_frame_snps
        
    By design, no advanced filtering is intended at this step.
    
    However, if your file is too big to fit into memory and you need more advanced filtering,
    you can provide your custom import function to the low-level `load_storage_object` magic:
    
        > def your_function(f):
        >     return f.read()  # do some fancy filtering here
        > %vault import 'notebook_path/variable.tsv' as variable with your_function
    
    ### Why not ZIP and not HDF?
    
    The storage archive is conceptually similar to Hierarchical Data Format (e.g. HDF5) object - it contains:
      - a hierarchy of files, and
      - a metadata files

    I believe that HDF may be the future, but this future is not here yet - numerous issues with the packages handling
    the HDF files, as well as low performance and compression rate prompted me to stay with a simple zip format now.
    
    ZIP is a popular file format with known features and limitations - files can be password encrypted, while the file
    list is always accessible. This is okay given that the code of the project is assumed to be public, and only the
    files in the storage area are assumed to be of encrypted, increasing the security in case of unauthorized access.
    
    As the limitations of the ZIP encryption are assumed to be a common knowledge, I hope that managing expectations
    of the level of security offered by this package will be easier.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaults = {
            'path': 'storage.zip',
            'encryption_variable': None,
            'secure': True,
            'optimize_df': True,
            'timestamp': True,
            'metadata': True,
            'allowed_duration': 30,  # seconds
        }
        self.settings = None
        self.current_vault = None

    actions = [
        StoreAction,
        ImportAction,
        DeleteAction,
        AssertAction
    ]

    @line_magic
    def open_vault(self, line):
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

    def _ensure_configured(self):
        if not self.settings:
            raise Exception('Please setup the storage with %open_vault first.')

    @line_magic
    def vault(self, line):
        self._ensure_configured()

        iterable = iter(clean_line(line))
        arguments = {key: next(iterable) for key in iterable}

        actions = {
            action.main_keyword: action
            for action in self.actions
        }

        requested_actions = set(actions).intersection(arguments)
        requested_action = one(requested_actions)

        started = self._timestamp()

        action_class = actions[requested_action]
        action = action_class(vault=self.current_vault)
        metadata = action.perform(arguments)

        finished = self._timestamp()

        #if finished - started > settings['allowed_duration']:
        # warn that the operations took longer than expected

        metadata['started'] = started.isoformat()
        metadata['finished'] = finished.isoformat()
        metadata['finished_human_readable'] = finished.strftime('%A, %d. %b %Y %H:%M')
        metadata['command'] = line
    
        display(
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
        )

    @staticmethod
    def _timestamp():
        return datetime.utcnow()


ip = get_ipython()
ip.register_magics(StorageMagics)

# IPython data-vault
[![Build Status](https://travis-ci.org/krassowski/data-vault.svg?branch=master)](https://travis-ci.org/krassowski/data-vault)
[![codecov](https://codecov.io/gh/krassowski/data-vault/branch/master/graph/badge.svg)](https://codecov.io/gh/krassowski/data-vault)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](http://choosealicense.com/licenses/mit/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/krassowski/data-vault/master?filepath=Example.ipynb)

IPython magic for simple, organized, compressed and encrypted storage & transfer of files between notebooks.

## Background and demo

### Right tool for a simple job

The `%vault` magic provides a reproducible caching mechanism for variables exchange between notebooks.
The cache is compressed, persistent and safe.

Differently to the builtin `%store` magic, the variables are stored in plain sight,
in a zipped archive, so that they can be easily accessed for manual inspection,
or for the use by other tools.

### Demonstration by usage:

Let's open the vault (it will be created if not here yet):

```python
%open_vault -p data/storage.zip
```

Generate some dummy dataset:
```python
from pandas import DataFrame
from random import choice, randint
cities = ['London', 'Delhi', 'Tokyo', 'Lagos', 'Warsaw', 'Chongqing']
salaries = DataFrame([
    {'salary': randint(0, 100), 'city': choice(cities)}
    for i in range(10000)
])
```

#### Store variable in a module

And store it in the vault:

```python
%vault store salaries in datasets
```

> Stored salaries (None → 40CA7812) at Sunday, 08. Dec 2019 11:58

A short description including a short CRC32 hashsum and timestamp is printed out by default and can be disabled by passing `--timestamp False` to `%open_vault` magic.
More variables supporting the reproducibility of analyses are stored in the cell metadata - see [Metadata for storage operations](#metadata-for-storage-operations).

#### Import variable from a module

We can now load it in a different (or the same) notebook:

```python
%vault import salaries from datasets
```

> Reduced memory usage by 87.28%, from 0.79 MB to 0.10 MB.

> Imported salaries (40CA7812) at Sunday, 08. Dec 2019 12:02

Thanks to [memory optimizations](memory-optimizations) (which can be disabled) we saved on some RAM as compared to the plain pandas requirements.

#### Import variable as something else

If we already have the salaries variable, we can use `as`, just like in the Python import system.
```python
%vault import salaries from datasets as salaries_dataset
```

### Goals

Syntax:
- easy to understand in plain language (avoid abbreviations when possible),
- while intuitive for Python developers,
- ...but sufficiently different so that it would not be mistaken with Python constructs
   - for example, we could have `%from x import y`, but this looks very like normal Python;
     having `%vault from x import y` makes it sufficiently easy to distinguish
- star imports are better avoided, thus not supported
- as imports may be confusing if there is more than one

Reproducibility:
- promote good reproducible and traceable organization of files:
   - promote storage in plain text files and the use of DataFrame
      - pickling is initially fun, but really try to change your class definitions and load your data again.
   - print out a short hashsum and human-readable datetime (always in UTC),
   - while providing even more details in cell metadata
- allow to trace instances of the code being modified post execution

Security:

* think of it as a tool to minimize the damage in case of accidental `git add` of data files (even if those should have been elsewhere and `.gitignore`d in the first place),
* or, as an additional layer of security for already anonymized data,
* but this tool is **not** aimed at facilitating the storage of highly sensitive data
* you have to set a password, or explicitly set `--secure False` to get rid of a security warning

## Features overview

### Metadata for storage operations

Each operation will print out the timestamp and the CRC32 short checksum of the files involved.
The timestamp of the operation is reported in the UTC timezone in a human-readable format.

This can be disabled by setting `-t False` or `--timestamp False`, however for the sake of reproducibility
it is encouraged to keep this information visible in the notebook.

More precise information including the SHA256 cheksum (with a lower probability of collisions),
and a full timestamp (to detect potential race condition errors in file write operations) are
embedded in the metadata of the cell. You can disable this by setting --metadata False.

The exact command line is also stored in the metadata, so that if you accidentally modify the code cell
without re-running the code, the change can be tracked down.

### Storage

In order to enforce interoperability plain text files are used for pandas DataFrame and Series objects.
Other variables are stores as pickle objects. The location of the storage archive on the disk defaults
to `storage.zip` in the current directory, and can changed using `%open_vault` magic:

```python
%open_vault -p custom_storage.zip
```

#### Encryption

> **The encryption is not intended as a high security mechanism,
but only as an additional layer of protection for already anonymized data.**

The password to encrypt the storage archive is retrieved from the environmental variable,
using a name provided in `encryption_variable` during the setup.

```python
%open_vault -e ENV_STORAGE_KEY
```

### Memory optimizations

Pandas DataFrames are by-default memory optimized by conversion of string variables to (ordered) categorical
columns (pandas equivalent of R's factors/levels). Each string column will be tested for the memory improvement
and the optimization will be only applied if it does reduce the memory usage.


### Why ZIP and not HDF?

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

## Installation and requirements

Pre-requirements:
- Python 3.6+
- 7zip (16.02+)

Installation:

```bash
pip3 install data_vault
```

## Draft ideas for future

**not implemented, up for discussion**

### Simple filtering

To enable high-performance subsetting a simple, grep-like pre-filtering is provided:

Import only first five rows:
```python
%vault from notebook import large_frame.rows[:5] as large_frame_head
```

When subsetting, the use of `as` is required to prevent potential confusion of the original `large_frame` object with its subset.

To import only rows including text "SNP":
```python
%vault from notebook import large_frame.grep("SNP") as large_frame_snps
```
    
By design, no advanced filtering is intended at this step.

However, if your file is too big to fit into memory and you need more advanced filtering,
you can provide your custom import function to the low-level `load_storage_object` magic:

```python
def your_function(f):
    return f.read()  # do some fancy filtering here
%vault import 'notebook_path/variable.tsv' as variable with your_function
```

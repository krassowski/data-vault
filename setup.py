from pathlib import Path
from setuptools import setup
from setuptools import find_packages


if __name__ == '__main__':
    setup(
        name='data_vault',
        packages=find_packages(),
        version='0.4.5',
        license='MIT',
        description='IPython magic for simple, organized, compressed and encrypted storage of files',
        long_description=Path('README.md').read_text(),
        author='Michal Krassowski',
        author_email='krassowski.michal+pypi@gmail.com',
        url='https://github.com/krassowski/data-vault',
        keywords=['jupyter', 'jupyterlab', 'notebook', 'ipython', 'storage', 'store', 'magic', 'vault'],
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: MIT License',
            'Framework :: IPython',
            'Framework :: Jupyter',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: Linux',
            'Operating System :: MacOS',
            'Topic :: Utilities',
            'Topic :: Database',
            'Topic :: System :: Archiving',
            'Topic :: System :: Archiving :: Compression',
            'Topic :: Software Development :: User Interfaces',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9'
        ],
        install_requires=[
            'pandas', 'IPython'
        ],
    )

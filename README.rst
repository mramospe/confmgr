Introduction
============

Small package to extend the functionality of the configparser module.
The classes and functions allow to:

- Read and save configurations in INI format.
- The class :class:`confmgr.Config`, which allows to save a class constructor together with the arguments used to build it.
- The configuration of the saved classes is then used to rebuild the same classes from the configuration file.
- Some functions also allow to manage files with duplicated configuration.

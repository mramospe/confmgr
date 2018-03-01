=======
confmgr
=======

.. image:: https://img.shields.io/travis/mramospe/confmgr.svg
   :target: https://travis-ci.org/mramospe/confmgr

.. image:: https://img.shields.io/badge/documentation-link-blue.svg
   :target: https://mramospe.github.io/confmgr/

.. inclusion-marker-do-not-remove

Small package to manage configurations of classes, managing them via XML files.
The classes and functions allow to:

- Read and save configurations in XML format.
- Save a class constructor together with the arguments used to build it through the :class:`confmgr.Config` class.
- The configuration of the saved classes is then used to rebuild the same classes from the configuration file.
- Some functions also allow to manage files with duplicated configuration.

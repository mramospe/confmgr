'''
Functions to manage configurations.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'

# Python
import os, re

# confmgr
from confmgr.core import ConfMgr


__all__ = ['check_configurations', 'get_configurations']


def check_configurations( config, cfglst, skip = None ):
    '''
    Check in the given set of configuration manager if
    any other file exists with the same configuration.
    The option "skip" allows to do not consider certain
    attributes of the configuration.

    :param config: configuration to check.
    :type config: dict
    :param cfglst: list of configuration files.
    :type cfglst: list(ConfMgr)
    :param skip: dictionary with the parameters to avoid \
    for each section.
    :type skip: dict(str, list(str))
    :returns: list of configurations matching the input.
    :rtype: list(ConfMgr)
    '''
    rmd = [ConfMgr(_drop(c, skip)) for c in cfglst]

    r = ConfMgr(_drop(config, skip))

    matches = []
    for cfg, rm in zip(cfglst, rmd):

        if cfg == config:
            matches.append(cfg)

        cfg.update(rm)

    config.update(r)

    return matches


def _drop( dct, drop = None ):
    '''
    Drop the information at the paths specified by the given
    dictionary.
    :param dct: input dictionary.
    :type dct: dict
    :param drop: information to drop.
    :type drop: dict or None
    :returns: dropped configuration.
    :rtype: ConfMgr
    '''
    drop = drop or {}

    out = ConfMgr()
    for c in dct.viewkeys() & drop.viewkeys():

        obj = drop[c]
        if obj is not None:
            # It is assumed to be a dictionary
            out[c] = _drop(dct[c].kwargs(), obj)
        else:
            out[c] = dct.pop(c)

    return out


def get_configurations( path, pattern ):
    '''
    Get the list of current configurations in "path"
    following the given pattern.

    :param path: path to get the configurations from.
    :type path: str
    :param pattern: regex to filter the configurations.
    :type pattern: str
    :returns: configurations following "pattern".
    :rtype: list(ConfMgr)
    '''
    comp = re.compile(pattern)

    matches = [comp.match(f) for f in os.listdir(path)]

    full_lst = [ConfMgr.from_file('{}/{}'.format(path, f.string))
                for f in matches if f is not None]

    return full_lst

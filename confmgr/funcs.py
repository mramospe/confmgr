'''
Functions to manage configurations.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'

# Python
import os, re

# confmgr
from confmgr.core import ConfMgr, main_section_name


__all__ = ['check_configurations', 'get_configurations']


def _remove_elements( cfg, drop = None ):
    '''
    Remove the elements from the configuration given
    a dictionary.

    :param cfg: input configuration.
    :type cfg: ConfMgr
    :param drop: "section, element" values to drop.
    :type drop: dict(str, list(str)) or None
    :returns: dropped values as a new configuration.
    :rtype: ConfMgr()
    '''
    rm_cfg = ConfMgr()

    if drop is not None:
        for s, l in drop.iteritems():

            tr = set(map(lambda i: i[0], cfg.items(s))) & set(l)
        
            if len(tr) > 0:
            
                rm_cfg.add_section(s)
            
                for e in tr:
                    rm_cfg.set(s, e, cfg.get(s, e))
                    cfg.remove_option(s, e)
    
    return rm_cfg


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
    rmd = [_remove_elements(c, skip) for c in cfglst]
    
    r = _remove_elements(config, skip)
    
    matches = []
    for cfg, rm in zip(cfglst, rmd):

        if cfg == config:
            matches.append(cfg)

        cfg.update(rm)

    config.update(r)
    
    return matches


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

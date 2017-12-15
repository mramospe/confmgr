'''
Functions to manage configurations.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'

# Python
import os, re

# confmgr
from confmgr.core import ConfMgr, main_section_name


__all__ = ['check_configurations', 'get_configurations', 'manage_config_matches']


def _remove_elements( cfg, drop ):
    '''
    Remove the elements from the configuration given
    a dictionary.

    :param cfg: input configuration.
    :type cfg: ConfMgr
    :param drop: "section, element" values to drop.
    :type drop: dict
    :returns: dropped values as a new configuration.
    :rtype: ConfMgr()
    '''
    rm_cfg = ConfMgr()

    for s, l in drop.iteritems():
        rm_cfg.add_section(s)
        for e in l:
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


def manage_config_matches( matches, conf_id ):
    '''
    Manage the matched configurations, asking 
    to overwrite the first matching file or create
    a new one with the given configuration ID.

    :param matches: list of files matching the configuration.
    :type matches: list(ConfMgr)
    :param conf_id: proposed configuration ID.
    :type conf_id: str
    :returns: configuration ID.
    :rtype: str
    '''
    if matches:

        print 'Found {} file(s) with the same configuration'.format(len(matches))
        
        expath = matches[-1][0]
        
        d = ''
        while d not in ('Y', 'n'):
            d = raw_input('Overwrite existing configuration file '\
                              '"{}"? (Y/[n]): '.format(expath)
                          ).strip()
            if not d:
                d = 'n'

        if d == 'Y':

            confmgr = ConfMgr()
            confmgr.read(expath)
            
            cfg_path = expath
            conf_id  = confmgr[main_section_name()]['confid']
            
        else:
            d = ''
            while d not in ('Y', 'n'):
                d = raw_input('Do you want to create a new configuration file? (Y/[n]): ')
                    
                if not d:
                    d = 'n'
            
            if d == 'n':
                exit(0)

    return conf_id

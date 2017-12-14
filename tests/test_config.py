'''
Generate a configuration and read it from the output file, checking
that they are the identical.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'


# Python
import os

# confmgr
import confmgr
from confmgr.core import __main_config_name__


__fname__ = 'test_config.ini'


def _generate_and_check( func ):
    '''
    Decorator to study the configuration created from an
    input function.

    :param func: input function, with no arguments, that \
    creates a configuration dictionary.
    :type func: function
    '''
    def wrapper():
        '''
        Create the configuration file and read it, checking
        that the two versions match.
        '''
        cfg = confmgr.ConfMgr.from_dict(func())
        cfg.save(__fname__)

        read = confmgr.ConfMgr.from_config(__fname__)

        matches = confmgr.check_configurations(cfg, [read], skip = {__main_config_name__: ['int']})

        os.remove(__fname__)

        assert len(matches) == 1

    return wrapper


@_generate_and_check
def test_basic_config():
    '''
    Test a basic configuration.
    '''
    return {
        'string' : 'this is a test',
        'int'    : 1,
        'float'  : 0.1,
        }


class ttcl:
    '''
    Small class to test the configuration module.
    '''
    def __init__( self, name, first, second = 2. ):
        '''
        Store some attributes.
        '''
        self.name   = name
        self.first  = first
        self.second = second


@_generate_and_check
def test_class_config():
    '''
    Test a configuration holding a class.
    '''
    return {
        'string' : 'this is a test',
        'object' : confmgr.Config(ttcl,
                                  {'name' : 'ttcl',
                                   'first': 1
                                  }),
        'int'    : 1,
        'float'  : 0.1
        }

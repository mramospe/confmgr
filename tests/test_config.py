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


__fname__ = 'test_config.xml'


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
        cfg = confmgr.ConfMgr(func())
        cfg.save(__fname__)

        read = confmgr.ConfMgr.from_file(__fname__)

        matches = confmgr.check_configurations(cfg, [read])

        os.remove(__fname__)

        assert len(matches) == 1

    return wrapper


def test_config_equivalence():
    '''
    Check the equivalence behaviour of the Config class.
    '''
    class dummy:
        def __init__( self, a, b ):
            pass

    c1 = confmgr.Config(dummy, 1, 0)
    c2 = confmgr.Config(dummy, 1, b = 0)

    assert c1 != c2


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


@_generate_and_check
def test_no_str_to_obj_builtins():
    '''
    Test a configuration with a dict, list, set and tuple objects.
    '''
    return {
        'dict'  : {'first': 1, 'second': 2},
        'list'  : ['A', 'B', 'C'],
        'set'   : {'A', 'B', 'C'},
        'tuple' : ('A', 'B', 'C')
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
                                  name  = 'ttcl',
                                  first = 1
                                  ),
        'int'    : 1,
        'float'  : 0.1
        }


@_generate_and_check
def test_empty_class():
    '''
    Test a configuration with a class constructor
    being called with no arguments.
    '''
    return {
        'string' : 'this is a test',
        'object' : confmgr.Config(ttcl),
        'int'    : 1,
        'float'  : 0.1
        }

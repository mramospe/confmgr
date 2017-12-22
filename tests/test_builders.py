'''
Test some constructors.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'


# Python
import os

# Scikit-learn
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier

# confmgr
from confmgr import ConfMgr, Config, check_configurations


__fname__ = 'test_config.xml'


class A:
    '''
    Simple class to test.
    '''
    def __init__( self, arg ):
        '''
        Stores one argument.
        '''
        self.arg = arg


class B:
    '''
    Another class to test.
    '''
    def __init__( self, arg1, arg2 ):
        '''
        Stores two arguments.
        '''
        self.arg1 = arg1
        self.arg2 = arg2


def test_configmgr():
    '''
    Test the configuration manager constructor from a configuration file.
    '''
    # Generate a fake manager and save its configuration
    base = Config(A, {'arg': 1})

    der = Config(B, {'arg1': base, 'arg2': 'name'})

    cfg = ConfMgr({'derived': der})

    path = './' + __fname__

    cfg.save(path)

    # Build the configuration from the file and get the second class
    rcfg = ConfMgr.from_file(path)

    der = rcfg.proc_conf()['derived']

    os.remove(__fname__)

    assert cfg == rcfg


def test_check_configurations():
    '''
    Create two configurations with some differences and check
    their equivalence asking to remove those indices.
    '''
    # Configuration 1
    base_1 = Config(A, {'arg': 1})
    der_1  = Config(B, {'base': base_1, 'nm': 'name'})
    cfg_1  = ConfMgr({'derived': der_1})

    # Configuration 2
    base_2 = Config(A, {'arg': 1, 'extra': 2})
    der_2  = Config(B, {'base': base_2, 'nm': 'name'})
    cfg_2  = ConfMgr({'derived': der_2})

    # Configuration 3
    base_3 = Config(A, {'arg': 1, 'extra': 2})
    der_3  = Config(B, {'base': base_3, 'nm': 'name'})
    cfg_3  = ConfMgr({'derived': der_3, 'useless': 4})

    assert len(check_configurations(cfg_1, [cfg_2, cfg_3],
                                    skip = {
                                        'useless': None,
                                        'derived': {'base': {'arg': None}}
                                    })) == 0

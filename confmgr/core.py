'''
Classes to parse configuration files.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'


# Python
import importlib, inspect
from configparser import ConfigParser
from collections import OrderedDict as odict


__all__ = ['ConfMgr', 'Config', 'main_config_name']


# Name of the section holding the general configuration variables
__main_config_name__ = 'GENERAL'


def main_config_name():
    '''
    Return the name of the main configurations for any file.

    :returns: main configuration name ({} by default).
    :rtype: str
    '''.format(__main_config_name__)
    return __main_config_name__


class ConfMgr(ConfigParser):
    '''
    Class to manage configurations built using the
    :class:`Config` class.
    '''
    def __init__( self, *args, **kwargs ):
        '''
        See :meth:`configparser.ConfigParser.__init__`.
        '''
        ConfigParser.__init__(self, *args, **kwargs)
        
        self._dct = odict()

    def __str__( self ):
        '''
        This class is displayed showing separately each section.
        '''
        out = '\n'
        
        maxl = max(map(len, self.sections()))
        
        lines = []
        for s in self.sections():
            
            items = self.items(s)
            
            if len(items) > 0:

                frmt = '{:<{}}'.format(s, maxl)
                
                lines.append('{} = ('.format(frmt))
                
                mxi = max(map(lambda it: len(it[0]), items)) + 5
                for n, it in items:
                    lines.append('{:>{}} = {}'.format(n, mxi, it))
                
                lines.append('{:>6}'.format(')'))
                
        return out.join(lines)

    def _proc_config( self, name, config ):
        '''
        Process the given configuration dictionary.
        
        :param name: name of the section.
        :type name: str
        :param config: items to process.
        :type config: dict
        :returns: processed dictionary.
        :rtype: dict
        '''
        return odict((k, self._proc_config_element(name, k, v))
                     for k, v in sorted(config.iteritems())
                     )

    def _proc_config_element( self, section, name, element ):
        '''
        Process one configuration element.

        :param section: section attached to the element.
        :type section: str
        :param name: name of the element.
        :type name: str
        :param element: element to process.
        :type element: any class type
        :returns: processed element.
        :rtype: any built class type
        '''
        if isinstance(element, Config):

            # So later it can be easily loaded
            self.set(section, name, element.full_name())
            
            self.add_section(name)
            
            dct = self._proc_config(name, element.config())

            return element.build(dct)
        else:
            self.set(section, name, str(element))

            try:
                return eval(element)
            except:
                return element

    @classmethod
    def from_file( cls, path ):
        '''
        Build the class from a configuration file.

        :param path: path to the configuration file.
        :type path: str
        :returns: configuration manager.
        :rtype: this class type
        '''
        cfg = cls()
        cfg.read(path)

        # Process the configuration
        res = odict()
        for name, section in reversed(cfg.items()):
            
            sub = odict()
            
            for k, v in section.iteritems():
                try:
                    sub[k] = eval(v)
                except:
                    sub[k] = v

            res[name] = sub

        # Build all the classes
        its = res.items()
        for i, (name, dct) in enumerate(its):
            for n, d in its[:i]:
                if n in dct:

                    # Access the class constructor
                    path = dct[n]
                    
                    modname = path[:path.rfind('.')]
                    clsname = path[path.rfind('.') + 1:]
                    
                    const  = getattr(importlib.import_module(modname), clsname)
                    
                    # Remove the attributes not present in the constructor
                    args = inspect.getargspec(const.__init__).args
                    args.remove('self')

                    inputs = {k: v for k, v in d.iteritems() if k in args}

                    # Call the constructor
                    dct[n] = const(**inputs)

        cfg._dct = res

        return cfg

    @classmethod
    def from_config( cls, name, cfg ):
        '''
        Build the class from a :class:`Config` object.

        :param cfg: input configurable.
        :type cfg: Config
        :returns: configuration manager.
        :rtype: this class type
        '''
        return cls.from_dict({name: cfg})
        
    @classmethod
    def from_dict( cls, dct ):
        '''
        Build the class from a dictionary.

        :param dct: input dictionary.
        :type dct: dict
        :returns: configuration manager.
        :rtype: this class type
        '''
        cfg = cls()
        
        cfg.add_section(main_config_name())
        
        cfg._dct = cfg._proc_config(main_config_name(), dct)
        
        return cfg
        
    def processed_config( self ):
        '''
        :returns: processed configuration dictionary, where \
        all the built classes are saved.
        :rtype: dict
        '''
        return self._dct

    def save( self, path ):
        '''
        :param cfg: configuration.
        :type cfg: ConfigParser
        :param path: path to save the output file.
        :type path: str
        '''
        print 'INFO: Generate new configuration file "{}"'\
            ''.format(path)

        with open(path, 'wb') as f:
            self.write(f)


class Config:
    '''
    Class to store any class constructor plus its
    configuration.
    '''
    def __init__( self, const, dct = None ):
        '''
        :param const: constructor of the configurable class.
        :type const: any class constructor
        :param dct: configuration of the class.
        :type dct: dict
        '''
        dct = dct or {}
        
        self._dct   = dct
        self._const = const

    def build( self, dct ):
        '''
        :param dct: configuration to build the class.
        :type dct: dict
        :returns: built class
        :rtype: built class type
        '''
        return self._const(**dct)

    def config( self ):
        '''
        :returns: configuration for the class in this object.
        :rtype: dict
        '''
        return self._dct

    def full_name( self ):
        '''
        :returns: full name of the class attached to \
        this configurable.
        :rtype: str
        '''
        cl = self._const
        return '{}.{}'.format(cl.__module__, cl.__name__)

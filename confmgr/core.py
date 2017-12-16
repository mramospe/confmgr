'''
Classes to parse configuration files.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'


# Python
import importlib, inspect
from configparser import ConfigParser
from collections import OrderedDict as odict


__all__ = ['ConfMgr', 'Config', 'main_section_name']


# Name of the section holding the general configuration variables
__main_section_name__ = 'GENERAL'


def main_section_name():
    '''
    Return the name of the main configuration section
    for any file.

    :returns: main configuration name ("GENERAL" by default).
    :rtype: str
    '''
    return __main_section_name__


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
        
        self._conf = odict()

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

    def _process_conf( self, name, conf ):
        '''
        Process the given configuration dictionary.
        
        :param name: name of the section.
        :type name: str
        :param conf: items to process.
        :type conf: dict
        :returns: processed dictionary.
        :rtype: dict
        '''
        out = odict()
        for k, v in sorted(conf.iteritems()):

            if isinstance(v, Config):

                # So later it can be easily loaded
                self.set(name, k, v.full_name())
            
                self.add_section(k)
            
                dct = self._process_conf(k, v.conf())

                out[k] = v.build(dct)
            else:
                self.set(name, k, str(v))

                try:
                    out[k] = eval(v)
                except:
                    out[k] = v
        
        return out

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

        cfg._conf = res

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
        
        cfg.add_section(main_section_name())
        
        cfg._conf = cfg._process_conf(main_section_name(), dct)
        
        return cfg
        
    def proc_conf( self ):
        '''
        :returns: processed configuration dictionary, where \
        all the built classes are saved.
        :rtype: dict
        '''
        return self._conf

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
        :type dct: dict or None
        '''
        self._conf  = dct or {}
        self._const = const

    def build( self, dct = None ):
        '''
        :param dct: configuration to build the class. If None \
        is provided, it is assumed that the stored configuration \
        has the correct format i.e there are no other Config \
        classes within it, or the constructor expects them.
        :type dct: dict or None
        :returns: built class.
        :rtype: built class type
        '''
        if dct is None:
            return self._const(**self._conf)
        else:
            return self._const(**dct)

    def conf( self ):
        '''
        :returns: configuration for the class in this object.
        :rtype: dict
        '''
        return self._conf

    def full_name( self ):
        '''
        :returns: full name of the class attached to \
        this configurable.
        :rtype: str
        '''
        cl = self._const
        return '{}.{}'.format(cl.__module__, cl.__name__)

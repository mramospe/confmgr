'''
Classes to parse configuration files.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'


# Python
import importlib, inspect
import xml.etree.cElementTree as et


__all__ = ['ConfMgr', 'Config']


def _class_path( const ):
    '''
    Return the python path to the given class constructor,
    which consists on <module>.<class>.

    :returns: whole python path to the given class constructor.
    :rtype: str
    '''
    return '{}.{}'.format(const.__module__, const.__name__)


def _matching_dicts( first, second ):
    '''
    Define the way to match to dictionaries. Returns True
    if the two dictionaries have the same structure (but the
    keys can have arbitrary order).

    :param first: first dictionary.
    :type first: dict
    :param second: second dictionary.
    :type second: dict
    :returns: comparison decision.
    :rtype: bool
    '''
    if len(first) == len(second):

        for k, v in first.iteritems():

            if k in second:
                if v == second[k]:
                    continue

            # A key or value does not match
            return False
    else:
        # Lengths are different
        return False

    # Everything went fine
    return True


class ConfMgr(dict):
    '''
    Class to manage configurations built using the
    :class:`Config` class.
    '''
    def __init__( self, *args, **kwargs ):
        '''
        This class is constructed as a dictionary.

        .. seealso: :meth:`dict.__init__`
        '''
        dict.__init__(self, *args, **kwargs)

    def __eq__( self, other ):
        '''
        :param other: another configuration to compare.
        :type other: ConfMgr
        :returns: comparison decision.
        :rtype: bool
        '''
        return _matching_dicts(self, other)

    def __ne__( self, other ):
        '''
        :param other: another configuration to compare.
        :type other: ConfMgr
        :returns: comparison decision.
        :rtype: bool
        '''
        return not self.__eq__(other)

#    def __str__( self ):
        '''
        This class is displayed showing separately each section.
        '''
 #       return self._str()

    def _str( self, indent = 0 ):
        out = '\n'

        maxl = max(map(len, self.keys()))

        lines = []
        for k, v in self.iteritems():

            frmt = '{:<{}}'.format(k, maxl)

            if isinstance(v, Config):
                lines.append('{} = ('.format(frmt))
                lines.append(v._conf._str(indent + 5))
                lines.append('{:>{}}'.format(')', indent + 6))
            else:
                lines.append('{:>{}} = {}'.format(frmt, v))

        return '\n'.join(lines)

    def _create_xml_node( self, root, name, value ):

        if isinstance(value, Config):

            el = et.SubElement(root, _class_path(value._const), name = name)

            for k, v in value._conf.iteritems():
                self._create_xml_node(el, k, v)
        else:
            el = et.SubElement(root, _class_path(value.__class__), name = name)
            el.text = str(value)

    @classmethod
    def _from_xml_node( cls, node ):

        children = node.getchildren()

        if children:

            d = cls((c.get('name'), cls._from_xml_node(c)) for c in children)

            path = node.tag

            p = path.rfind('.')
            if p > 0:
                modname = path[:p]
                clsname = path[p + 1:]

                const = getattr(importlib.import_module(modname), clsname)
            else:
                const = globals()[path]

            return Config(const, d)

        else:

            txt = node.text

            try:
                return eval(txt)
            except:
                return txt

    @classmethod
    def from_file( cls, path ):
        '''
        Build the class from a configuration file.

        :param path: path to the configuration file.
        :type path: str
        :returns: configuration manager.
        :rtype: this class type
        '''
        tree = et.parse(path)
        root = tree.getroot()

        return cls((c.get('name'), cls._from_xml_node(c))
                   for c in root.getchildren())

    def proc_conf( self ):
        '''
        :returns: processed configuration dictionary, where \
        all the built classes are saved.
        :rtype: dict
        '''
        cfg = {}
        for k, v in self.iteritems():
            if isinstance(v, Config):
                cfg[k] = v.build()
            else:
                cfg[k] = v

        return cfg

    def save( self, path ):
        '''
        :param path: path to the output file (adding the '.xml' \
        extension is recomended).
        :type path: str
        '''
        print 'INFO: Generate new configuration file "{}"'\
            ''.format(path)

        root = et.Element(_class_path(self.__class__))

        for k, v in self.iteritems():
            self._create_xml_node(root, k, v)

        tree = et.ElementTree(root)

        tree.write(path)


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

    def __eq__( self, other ):
        '''
        :param other: another configurable to compare.
        :type other: Config
        :returns: comparison decision.
        :rtype: bool
        '''
        m_c = (self._const == other._const)

        return m_c and _matching_dicts(self._conf, other._conf)

    def __ne__( self, other ):
        '''
        :param other: another configurable to compare.
        :type other: Config
        :returns: comparison decision.
        :rtype: bool
        '''
        return not self.__eq__(other)

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

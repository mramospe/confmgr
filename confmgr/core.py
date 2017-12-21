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

    def __str__( self, indent = 0 ):
        '''
        Represent this class as a string, using the given indentation level.
        The latter is meant for internal use only.

        :param indent: indentation level.
        :type indent: int
        '''
        out = '\n'

        maxl = max(map(len, self.keys()))

        lines = []
        for k, v in self.iteritems():

            frmt = '{:<{}}'.format(k, maxl)

            if isinstance(v, Config):
                lines.append('{:>{}} = ('.format(frmt, indent))
                lines.append(v._conf.__str__(indent + 5))
                lines.append('{:>{}}'.format(')', indent + 6))
            else:
                lines.append('{:>{}} = {}'.format(frmt, indent + 5, v))

        return '\n'.join(lines)

    def _create_xml_node( self, root, name, value ):
        '''
        Create an XML element in the given root.

        :param root: XML element to write into.
        :type root: xml.etree.cElementTree.Element
        :param name: name of the new element.
        :type name: str
        :param value: object to write. It can be either a Config object \
        or a class with a string representation.

        .. seealso: :meth:`ConfMgr._from_xml_node`
        '''
        if isinstance(value, Config):

            el = et.SubElement(root, _class_path(value._const), name = name)

            for k, v in value._conf.iteritems():
                self._create_xml_node(el, k, v)
        else:
            el = et.SubElement(root, _class_path(value.__class__), name = name)
            el.text = str(value)

    @classmethod
    def _from_xml_node( cls, node ):
        '''
        Extract the information from a XML node. If the node represents
        an object, then a Config object is built with its constructor
        and configuration. Otherwise an "eval" call is done. If it fails,
        the raw string is saved.

        :param cls: object constructor.
        :type cls: this class constructor.
        :param node: XML node to process.
        :type node: xml.etree.cElementTree.Element
        :returns: saved class as a python object.
        '''
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
    def __init__( self, const, conf = None ):
        '''
        The input configuration in "conf" is saved as a ConfMgr object,
        to ensure that the :meth:`Config.build` method works properly.
        This does not make any copy of the internal classes in "conf".

        :param const: constructor of the configurable class.
        :type const: any class constructor
        :param conf: configuration of the class.
        :type conf: dict or None

        .. seealso: :meth:`Config.build`
        '''
        self._conf  = ConfMgr(conf or {})
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

    def build( self ):
        '''
        Return a class using the stored constructor and configuration.

        :returns: built class.
        :rtype: built class type
        '''
        return self._const(**self._conf.proc_conf())

    def conf( self ):
        '''
        :returns: configuration for the class in this object.
        :rtype: dict
        '''
        return self._conf

    def const( self ):
        '''
        :returns: constructor for the class in this object.
        :rtype: class constructor
        '''
        return self._const

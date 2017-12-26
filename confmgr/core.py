'''
Classes to parse configuration files.
'''

__author__ = 'Miguel Ramos Pernas'
__email__  = 'miguel.ramos.pernas@cern.ch'


# Python
import importlib, inspect
import xml.etree.cElementTree as et


__all__ = ['ConfMgr', 'Config', 'config_builder']


class config_builder:
    '''
    Decorator to wrap a class, creating a Config object when called.
    For example:

    >>> from confmgr import config_builder
    >>> @config_builder
    ... def func( a, b ):
    ...     return a, b
    ...
    >>> print func
    <confmgr.core.config_builder instance at 0x7f9895318680>
    >>> c = func(a = 0, b = 2)
    >>> c
    <confmgr.core.Config instance at 0x7f98950cb050>
    >>> print c
    func(
         a = 0
         b = 2
         )
    '''
    def __init__( self, obj ):
        '''
        :param obj: object to build.
        :type obj: any class
        '''
        self._obj = obj

    def __call__( self, *args, **kwargs ):
        '''
        :param args: parameters for the class constructor.
        :type args: tuple
        :param kwargs: keyword parameters for the class constructor.
        :type kwargs: dict
        :returns: configurable built from the stored object and the arguments.
        :rtype: Config
        '''
        return Config(self._obj, *args, **kwargs)


def _class_path( const ):
    '''
    Return the python path to the given class constructor,
    which consists on <module>.<class>.

    :returns: whole python path to the given class constructor.
    :rtype: str
    '''
    return '{}.{}'.format(const.__module__, const.__name__)


class ConfObj:
    '''
    Base class for the configuration objects.
    '''
    def __init__( self ):
        '''
        Empty constructor.
        '''
        pass

    def kwargs( self ):
        '''
        This is an abstract method

        :returns: stored configuration.
        :rtype: ConfDict
        '''
        raise NotImplementedError('Attempt to call abstract class method')


class ConfDict(dict, ConfObj):
    '''
    Represent a dictionary to store configurations. Some methods of the
    dict class are overriden. The classes must be stored using the Config
    class, unless they can be built using their string representation.
    '''
    def __init__( self, *args, **kwargs ):
        '''
        This class is constructed as a dictionary.

        .. seealso: :meth:`dict.__init__`
        .. seealso: :meth:`ConfObj.__init__`
        '''
        dict.__init__(self, *args, **kwargs)
        ConfObj.__init__(self)

    def __eq__( self, other ):
        '''
        The dictionaries are considered to be equivalent if the
        information stored is the same.

        :param other: another configuration to compare.
        :type other: ConfMgr
        :returns: comparison decision.
        :rtype: bool
        '''
        if len(self) == len(other):

            for k, v in self.iteritems():

                if k in other:
                    if v == other[k]:
                        continue

                # A key or value does not match
                return False
        else:
            # Lengths are different
            return False

        # Everything went fine
        return True

    def __ne__( self, other ):
        '''
        :param other: another configuration to compare.
        :type other: ConfMgr
        :returns: comparison decision.
        :rtype: bool

        .. seealso: :meth:`ConfDict.__eq__`
        '''
        return not self.__eq__(other)

    def __str__( self, indent = 0 ):
        '''
        Represent this class as a string, using the given
        indentation level. The latter is meant for internal
        use only.

        :param indent: indentation level.
        :type indent: int
        :returns: this class as a string.
        :rtype: str
        '''
        if len(self):
            maxl = max(map(len, self.keys()))
        else:
            maxl = None

        lines = []
        for k, v in self.iteritems():

            frmt = k.ljust(maxl)

            ind = indent + maxl

            if isinstance(v, Config):
                lines.append('{:>{}} = {}'.format(frmt, ind, v.__str__(ind)))
            else:
                lines.append('{:>{}} = {}'.format(frmt, ind, v))

        return '\n'.join(lines)

    def kwargs( self ):
        '''
        :returns: stored configuration.
        :rtype: ConfDict
        '''
        return self

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


class ConfMgr(ConfDict):
    '''
    Class to manage configurations built using the :class:`Config` class. It
    allows to read/save the stored information from/to XML files.
    '''
    def __init__( self, *args, **kwargs ):
        '''
        This class is constructed as a configuration dictionary.

        .. seealso: :meth:`ConfDict.__init__`
        '''
        ConfDict.__init__(self, *args, **kwargs)

    def _create_xml_node( self, root, value, name = None ):
        '''
        Create an XML element in the given root.

        :param root: XML element to write into.
        :type root: xml.etree.cElementTree.Element
        :param value: object to write. It can be either a Config object \
        or a class with a string representation.
        :param name: name of the new element.
        :type name: str or None

        .. seealso: :meth:`ConfMgr._from_xml_node`
        '''
        if isinstance(value, Config):

            el = et.SubElement(root, _class_path(value._const), name = name)

            arels = et.SubElement(el, 'args')
            for v in value.args():
                self._create_xml_node(arels, v)

            kwels = et.SubElement(el, 'kwargs')
            for k, v in value.kwargs().iteritems():
                self._create_xml_node(kwels, v, k)
        else:
            if name is None:
                el = et.SubElement(root, _class_path(value.__class__))
            else:
                el = et.SubElement(root, _class_path(value.__class__),
                                   name = name)
            el.text = str(value)

        return el

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

            # The only children must be args and kwargs
            arels, kwels = children

            a = [cls._from_xml_node(c) for c in arels.getchildren()]

            d = cls((c.get('name'), cls._from_xml_node(c))
                    for c in kwels.getchildren())

            path = node.tag

            p = path.rfind('.')
            if p > 0:
                modname = path[:p]
                clsname = path[p + 1:]

                const = getattr(importlib.import_module(modname), clsname)
            else:
                const = globals()[path]

            return Config(const, *a, **d)

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

    def save( self, path ):
        '''
        :param path: path to the output file (adding the '.xml' \
        extension is recomended).
        :type path: str
        '''
        root = et.Element(_class_path(self.__class__))

        for k, v in self.iteritems():
            self._create_xml_node(root, v, k)

        tree = et.ElementTree(root)

        tree.write(path)


class Config(ConfObj):
    '''
    Class to store any class constructor plus its configuration. Note that two
    Config objects are considered equivalent only if the provided arguments and
    keyword arguments are identical. Defaults are thus omitted, leading to
    the following behaviour:

    >>> from confmgr import Config
    >>> class dummy:
    ...     def __init__( self, a, b ):
    ...         pass
    ...
    >>> c1 = Config(dummy, 1, 0)
    >>> c2 = Config(dummy, 1, b = 0)
    >>> c1 == c2
    False
    '''
    def __init__( self, const, *args, **kwargs ):
        '''
        The input configuration in "conf" is saved as a ConfMgr object,
        to ensure that the :meth:`Config.build` method works properly.
        This does not make any copy of the internal classes in "conf".

        :param const: constructor of the configurable class.
        :type const: any class constructor
        :param args: arguments to :meth:`ConfDict.__init__`.
        :type args: tuple
        :param kwargs: keyword arguments to :meth:`ConfDict.__init__`.
        :type kwargs: dict

        .. seealso: :meth:`Config.build`
        '''
        self._const  = const
        self._args   = args
        self._kwargs = ConfDict(kwargs)

    def __eq__( self, other ):
        '''
        :param other: another configurable to compare.
        :type other: Config
        :returns: comparison decision.
        :rtype: bool
        '''
        # Check the constructor
        m_c = (self._const == other._const)
        if not m_c:
            return False

        # Check the arguments
        m_s = (set(self._args) == set(other._args))
        if not m_s:
            return False

        # Check the keyword arguments
        return self._kwargs == other._kwargs

    def __str__( self, indent = 0 ):
        '''
        Override the default :meth:`ConfDict.__str__` method,
        displaying as well the information of the class.

        :returns: this class as a string.
        :rtype: str
        '''
        if not (self._args or self._kwargs):
            return '{}()'.format(self._const.__name__)

        lines = ['{}('.format(self._const.__name__)]

        args = ['{:>{}}'.format(a, indent + 6) for a in self._args]
        if args:
            lines.append('{},\n'.join(args))

        if self._kwargs:
            lines.append(self._kwargs.__str__(indent + 5))

        lines.append(')'.rjust(indent + 1))

        return '\n'.join(lines)

    def args( self ):
        '''
        :returns: standard arguments.
        :rtype: tuple
        '''
        return self._args

    def build( self ):
        '''
        Return a class using the stored constructor and
        configuration.

        :returns: built class.
        :rtype: built class type
        '''
        return self._const(*self._args, **self._kwargs.proc_conf())

    def const( self ):
        '''
        :returns: constructor for the class in this object.
        :rtype: class constructor
        '''
        return self._const

    def kwargs( self ):
        '''
        :returns: stored configuration.
        :rtype: ConfDict
        '''
        return self._kwargs

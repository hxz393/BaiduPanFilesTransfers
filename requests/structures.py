# -*- coding: utf-8 -*-

"""
requests.structures
~~~~~~~~~~~~~~~~~~~

Data structures that power Requests.
"""

from .compat import OrderedDict, Mapping, MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        """
        Initialize the cache.

        Args:
            self: (todo): write your description
            data: (todo): write your description
        """
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        """
        Sets the value of a key.

        Args:
            self: (todo): write your description
            key: (str): write your description
            value: (str): write your description
        """
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        """
        Return the value of the key.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        """
        Remove an item from the cache.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        del self._store[key.lower()]

    def __iter__(self):
        """
        Return an iterable of all values for this item.

        Args:
            self: (todo): write your description
        """
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        """
        Returns the length of the record.

        Args:
            self: (todo): write your description
        """
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        """
        Compares two dicts.

        Args:
            self: (dict): write your description
            other: (dict): write your description
        """
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        """
        Return a copy of the dictionary.

        Args:
            self: (todo): write your description
        """
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        """
        Return a repr representation of this object.

        Args:
            self: (dict): write your description
        """
        return str(dict(self.items()))


class LookupDict(dict):
    """Dictionary lookup object."""

    def __init__(self, name=None):
        """
        Initialize this instance.

        Args:
            self: (todo): write your description
            name: (str): write your description
        """
        self.name = name
        super(LookupDict, self).__init__()

    def __repr__(self):
        """
        Return a human - friendly name.

        Args:
            self: (todo): write your description
        """
        return '<lookup \'%s\'>' % (self.name)

    def __getitem__(self, key):
        """
        Returns the value of a key.

        Args:
            self: (todo): write your description
            key: (str): write your description
        """
        # We allow fall-through here, so values default to None

        return self.__dict__.get(key, None)

    def get(self, key, default=None):
        """
        Returns the value of a key.

        Args:
            self: (todo): write your description
            key: (todo): write your description
            default: (todo): write your description
        """
        return self.__dict__.get(key, default)

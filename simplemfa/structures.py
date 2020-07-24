"""
A custom immutable dictionary data structure
"""


class CustomImmutableDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        # self[key] = value
        return self._immutable()

    def __delattr__(self, key):
        return self._immutable()
        # try:
        #    del self[key]
        # except KeyError as k:
        #    raise AttributeError(k)

    def __repr__(self):
        return '<CustomImmutableDict ' + dict.__repr__(self) + '>'

    def __hash__(self):
        return id(self)

    def _immutable(self, *args, **kws):
        raise TypeError('This object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable
    pop = _immutable
    popitem = _immutable

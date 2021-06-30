class _LocalBase:
    """A class used to denote the current uncommitted version of data"""

    def __getstate__(self):
        raise RuntimeError('This object cannot be pickled')

    def __eq__(self, other):
        return isinstance(other, _LocalBase)


Local = _LocalBase()

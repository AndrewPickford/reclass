class ParameterDict(dict):
    def __init__(self, *args, **kwargs):
        self._uri = kwargs.pop('uri', None)
        dict.__init__(self, *args, **kwargs)

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = uri

class ParameterList(list):
    def __init__(self, *args, **kwargs):
        self._uri = kwargs.pop('uri', None)
        list.__init__(self, *args, **kwargs)

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = uri

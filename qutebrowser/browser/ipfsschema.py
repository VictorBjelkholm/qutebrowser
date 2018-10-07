class add_handler:  # noqa: N801,N806 pylint: disable=invalid-name

    """Decorator to register a qute://* URL handler.

    Attributes:
        _name: The 'foo' part of qute://foo
    """

    def __init__(self, name):
        self._name = name
        self._function = None

    def __call__(self, function):
        self._function = function
        _HANDLERS[self._name] = self.wrapper
        return function

    def wrapper(self, *args, **kwargs):
        """Call the underlying function."""
        return self._function(*args, **kwargs)

@add_handler('anything')
def qute_bookmarks(_url):
    """Handler for qute://bookmarks. Display all quickmarks / bookmarks."""
    # bookmarks = sorted(objreg.get('bookmark-manager').marks.items(),
    #                    key=lambda x: x[1])  # Sort by title
    return 'text/html', 'hello world'

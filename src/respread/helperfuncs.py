from functools import wraps


def redirect(path: tuple[str], error: Exception | tuple[Exception], append_name: bool = False):
    """
    Decorator that redirects calls to the component defined by the path.
    The wrapped function handles exceptions matching ``error``.
    
    The function's ``__name__`` will  be appended to the path if ``append_name`` is ``True`` (default is ``False``).
    
    Multiple exceptions can be handled by providing a tuple of exceptions. The path is relative to ``self``.
    
    Parameters
    ----------
    path : tuple[str]
        Path to redirect call
    error: Exception | tuple(Exception)
        Exception(s) that will be handled by the wrapped function
    append_name: bool, default False
        Append the name of the wrapped function to the end of the path
    
    Examples
    --------
    Redirects are a way to provide a default value to a function if it raises and exception.
    
    Note that the path must be a tuple, even if there is only one element.
    
    >>> class UserPreferences(Node):
    ...     def custom_theme(self, user):
    ...         themes = {'John Doe': 'dark-mode'}
    ...         return themes[user]
    ...     @redirect(('custom_theme',), KeyError)
    ...     def theme(self, user):
    ...         return 'light-mode'
    ... 
    >>> UserPreferences().theme('John Doe')
    'dark-mode'
    >>> UserPreferences().theme('Adam Smith')
    'light-mode'
    
    Use redirects with custom exceptions to provide default values for only a subset of scenarios.
    
    The example below uses a custom exception type to indicate that the key error in out of bounds to the right of the historical data (in other words, the requested data is after the historical range).
    
    This pattern avoids inserting a conditional clause in ``revenue`` that has to test whether the year is in the historical range. It also avoids a recursion error if the year is before the historical range.
    
    >>> class AfterPeriodError(Exception):
    ...     pass
    ... 
    >>> class Revenue(Node):
    ...     def historical_revenue(self, year):
    ...         data = {2020: 100_000, 2021: 110_000}
    ...         if year > max(data.keys()):
    ...             raise AfterPeriodError
    ...         return data[year]
    ...     @redirect(('historical_revenue',), AfterPeriodError)
    ...     def revenue(self, year):
    ...         return self.revenue(year - 1) * 1.08
    ... 
    >>> Revenue().revenue(2021)  # in historical range
    110000
    >>> Revenue().revenue(2022)  # after historical range
    118800.00000000001
    >>> Revenue().revenue(2000)  # before historical range
    KeyError: 2000
    
    The path is determined relative to ``self``. Any attribute of ``self``, including the root property, will be followed. Optionally, you can append the function's ``__name__`` to the end of the path.
    
    >>> class Historical(Node):
    ...     def revenue(self, year):
    ...         data = {2020: 100_000, 2021: 110_000}
    ...         if year > max(data.keys()):
    ...             raise AfterPeriodError
    ...         return data[year]
    ... 
    >>> class OperatingStatement(Node):
    ...     # path will be pro_forma.historical.revenue
    ...     @redirect(('root', 'historical'), AfterPeriodError, append_name=True)
    ...     def revenue(self, year):
    ...         return self.revenue(year - 1) * 1.08
    ... 
    >>> pro_forma = Node()
    >>> pro_forma.add_child('historical', Historical().set_parent(pro_forma))
    >>> pro_forma.add_child('operating_statement', OperatingStatement().set_parent(pro_forma))
    ... 
    >>> pro_forma.operating_statement.revenue(2021)
    110000
    >>> pro_forma.operating_statement.revenue(2022)
    118800.00000000001
    """
    def redirect_wrapper(func):
        @wraps(func)
        def redirect_func(self, *args, **kwargs):
            # try to follow path
            path_obj = self
            try:
                path_obj = self
                for e in path:
                    path_obj = getattr(path_obj, e)
                if append_name:
                    path_obj = getattr(path_obj, func.__name__)
            except AttributeError:
                raise ValueError(f'Could not find path {e} for object {path_obj}.\nException raised while tring to follow path: {path}')
            
            # if calling the path obj results in the handled error,
            # call the handler function
            try:
                return path_obj(*args, **kwargs)
            except error:
                return func(self, *args, **kwargs)
        
        return redirect_func
    return redirect_wrapper

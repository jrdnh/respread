from functools import wraps


def redirect(path: tuple[str], error: Exception | tuple[Exception], append_name: bool = False):
    """
    Decorator that redirects calls to the component defined by the path.
    The wrapped function handles exceptions matching ``error``.
    
    The function's ``__name__`` will  be appended to the path if ``append_name`` is ``True`` (default is ``False``).
    
    Multiple exceptions can be handled by providing a tuple of exceptions. 
    
    Parameters
    ----------
    path : tuple[str]
        Path to redirect call
    error: Exception | tuple(Exception)
        Exception(s) that will be handled by the wrapped function
    append_name: bool, default False
        Append the name of the wrapped function to the end of the path
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
                raise ValueError(f'Could not find path {path} for object {self}.\nException raised while tring to follow path: {e}')
            
            # if calling the path obj results in the handled error,
            # call the handler function
            try:
                return path_obj(*args, **kwargs)
            except error:
                return func(self, *args, **kwargs)
        
        return redirect_func
    return redirect_wrapper

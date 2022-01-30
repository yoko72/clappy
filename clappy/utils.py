import inspect
import functools
import pathlib

import __main__


def get_caller_name(name_change_count: int = 2):
    """
    Returns the name of module calling this function.
    depth: int
        Explores with f_back() till the name of module changes by this depth.
    """
    first_frame = inspect.currentframe()
    last_filename = first_frame.f_code.co_filename
    count = 0
    frame = first_frame.f_back
    while True:
        while last_filename == frame.f_code.co_filename:
            frame = frame.f_back
        else:
            last_filename = frame.f_code.co_filename
            count += 1
            if count >= name_change_count:
                break
            else:
                frame = frame.f_back
    name = pathlib.Path(frame.f_code.co_filename).stem
    return name


if hasattr(__main__, "__file__"):
    filename_of_main = pathlib.Path(__main__.__file__).stem
else:  # In Jupyter Notebook, __main__ module has no attribute of __file__
    filename_of_main = "__main__"


def is_called_from_main():
    caller_name = get_caller_name(4)
    if filename_of_main == caller_name:
        return True
    else:
        return False


def normalize_bound(func):
    """
    'As long as given args are same', callable with @functools.lrc_cache returns cache by this func.
    Without this, it might not return cache. It depends on the way or order of giving args.

    @normalize_bound
    @lrc_cache()
    def example(foo, bar):
        pass
    """
    signature = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return func(*bound.args, **bound.kwargs)
    return wrapper

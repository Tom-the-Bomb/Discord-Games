from typing import Callable
import functools
import asyncio

def executor():

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(None, partial)

        return wrapper
    return decorator
from typing import Callable, Union

import functools
import asyncio

import discord

__all__ = (
    'DiscordColor',
    'DEFAULT_COLOR',
    'executor',
)

DiscordColor = Union[discord.Color, int]

DEFAULT_COLOR: discord.Color = discord.Color(DEFAULT_COLOR)

def executor():

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(None, partial)

        return wrapper
    return decorator
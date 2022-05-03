from typing import Callable, Union

import functools
import asyncio

import discord

__all__ = (
    'DiscordColor',
    'DEFAULT_COLOR',
    'executor',
    'chunk',
)

DiscordColor = Union[discord.Color, int]

DEFAULT_COLOR: discord.Color = discord.Color(0x2F3136)

def chunk(iterable: list[int], *, count: int) -> list[list[int]]:
    return [iterable[i:i + count] for i in range(0, len(iterable), count)]

def executor():

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(None, partial)

        return wrapper
    return decorator
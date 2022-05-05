from __future__ import annotations

from typing import Awaitable, Callable, Final, Union, TypeVar, TYPE_CHECKING

import functools
import asyncio

import discord

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeAlias
    
    P = ParamSpec('P')
    T = TypeVar('T')

__all__ = (
    'DiscordColor',
    'DEFAULT_COLOR',
    'executor',
    'chunk',
)

DiscordColor: TypeAlias = Union[discord.Color, int]

DEFAULT_COLOR: Final[discord.Color] = discord.Color(0x2F3136)

def chunk(iterable: list[int], *, count: int) -> list[list[int]]:
    return [iterable[i:i + count] for i in range(0, len(iterable), count)]

def executor() -> Callable[[Callable[P, T]], Callable[P, Awaitable[T]]]:
    
    def decorator(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(None, partial)

        return wrapper
    return decorator
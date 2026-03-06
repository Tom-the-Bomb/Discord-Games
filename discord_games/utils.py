from __future__ import annotations

from typing import (
    Optional,
    Coroutine,
    Callable,
    Final,
    Union,
    TypeVar,
    TYPE_CHECKING,
    Any,
)

import functools
import asyncio

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeAlias

    P = ParamSpec("P")
    T = TypeVar("T")

    A = TypeVar("A", bound=bool)
    B = TypeVar("B", bound=bool)

__all__: tuple[str, ...] = (
    "DiscordColor",
    "DEFAULT_COLOR",
    "executor",
    "chunk",
    "BaseView",
    "double_wait",
    "wait_for_delete",
)

DiscordColor: TypeAlias = Union[discord.Color, int]

DEFAULT_COLOR: Final[discord.Color] = discord.Color(0xFFFFFF)


def chunk(iterable: list[T], *, count: int) -> list[list[T]]:
    return [iterable[i : i + count] for i in range(0, len(iterable), count)]


def executor() -> Callable[[Callable[P, T]], Callable[P, asyncio.Future[T]]]:
    def decorator(func: Callable[P, T]) -> Callable[P, asyncio.Future[T]]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = asyncio.get_running_loop()
            return loop.run_in_executor(None, partial)

        return wrapper

    return decorator


async def wait_for_delete(
    ctx: commands.Context[commands.Bot],
    message: discord.Message,
    *,
    emoji: str = "⏹️",
    bot: Optional[discord.Client] = None,
    user: Optional[
        Union[discord.User, discord.Member, tuple[discord.User, ...]]
    ] = None,
    timeout: Optional[float] = None,
) -> bool:
    if not user:
        user = ctx.author
    try:
        await message.add_reaction(emoji)
    except discord.DiscordException:
        pass

    def check(reaction: discord.Reaction, _user: discord.User) -> bool:
        if reaction.emoji == emoji and reaction.message.id == message.id:
            if isinstance(user, tuple):
                return _user in user
            else:
                return _user == user
        return False

    resolved_bot: discord.Client = bot or ctx.bot
    try:
        await resolved_bot.wait_for("reaction_add", timeout=timeout, check=check)
    except asyncio.TimeoutError:
        return False
    else:
        await message.delete()
        return True


async def double_wait(
    task1: Coroutine[Any, Any, A],
    task2: Coroutine[Any, Any, B],
    *,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> tuple[
    set[Union[asyncio.Task[A], asyncio.Task[B]]],
    set[Union[asyncio.Task[A], asyncio.Task[B]]],
]:
    if not loop:
        loop = asyncio.get_running_loop()

    done, pending = await asyncio.wait(
        [
            loop.create_task(task1),
            loop.create_task(task2),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    return done, pending


if hasattr(discord, "ui"):

    class BaseView(discord.ui.View):
        message: Optional[discord.Message] = None

        def disable_all(self) -> None:
            for button in self.children:
                if isinstance(button, discord.ui.Button):
                    button.disabled = True

        async def on_timeout(self) -> None:
            self.disable_all()
            if self.message is not None:
                try:
                    await self.message.edit(view=self)
                except discord.HTTPException:
                    pass
            self.stop()

from __future__ import annotations

from typing import Optional
import time
import random
import asyncio

import discord
from discord.ext import commands

from .utils import DiscordColor, DEFAULT_COLOR


class ReactionGame:
    """Reaction time test, reaction-based.

    Measures how quickly a player reacts to an emoji change.
    """

    def __init__(self, emoji: str = "🖱️") -> None:
        self.emoji = emoji

    async def wait_for_reaction(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        timeout: Optional[float],
        start_time: float,
        reacted: set[int],
    ) -> tuple[discord.User, float]:

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                str(reaction.emoji) == self.emoji
                and reaction.message.id == self.message.id
                and user.id not in reacted
                and not user.bot
            )

        _, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)
        elapsed = time.perf_counter() - start_time

        return user, elapsed

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        timeout: Optional[float] = None,
        embed_color: DiscordColor = DEFAULT_COLOR,
    ) -> discord.Message:
        """
        starts the reaction game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        timeout : Optional[float], optional
            the timeout for when waiting, by default None
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR

        Returns
        -------
        discord.Message
            returns the game message
        """
        embed = discord.Embed(
            title="Reaction Game",
            description=f"React with {self.emoji} when the embed is edited!",
            color=embed_color,
        )

        self.message = await ctx.send(embed=embed)
        await self.message.add_reaction(self.emoji)

        pause = random.uniform(1.0, 5.0)
        await asyncio.sleep(pause)

        embed.description = f"React with {self.emoji} now!"
        await self.message.edit(embed=embed)

        results: list[str] = []
        reacted: set[int] = set()

        start_time = time.perf_counter()

        while not ctx.bot.is_closed():
            try:
                user, reaction_time = await self.wait_for_reaction(
                    ctx, timeout=timeout, start_time=start_time, reacted=reacted,
                )
            except asyncio.TimeoutError:
                break

            reacted.add(user.id)
            place = len(results) + 1
            results.append(f"**{place}.** {user.mention} — `{reaction_time:.2f}s`")

            embed.description = "\n".join(results)
            await self.message.edit(embed=embed)

        if not results:
            embed.description = "No one reacted in time!"
            await self.message.edit(embed=embed)

        return self.message

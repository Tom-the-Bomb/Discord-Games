from __future__ import annotations

import time
import random
import asyncio

import discord
from discord.ext import commands

from .utils import DiscordColor, DEFAULT_COLOR

class ReactionGame:
    """
    Reaction Game
    """
    def __init__(self, emoji: str = '🖱️') -> None:
        self.emoji = emoji

    async def wait_for_reaction(self, ctx: commands.Context[commands.Bot]) -> tuple[discord.Member, float]:
        start = time.perf_counter()

        def check(reaction: discord.Reaction, _: discord.Member) -> bool:
            return str(reaction.emoji) == self.emoji and reaction.message == self.message

        _, user = await ctx.bot.wait_for('reaction_add', check=check)
        end = time.perf_counter()

        return user, (end - start)
    
    async def start(
        self, 
        ctx: commands.Context[commands.Bot], 
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
    ) -> discord.Message:
        """
        starts the reaction game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR

        Returns
        -------
        discord.Message
            returns the game message
        """
        embed = discord.Embed(
            title='Reaction Game',
            description=f'React with {self.emoji} when the embed is edited!',
            color=embed_color,
        )

        self.message = await ctx.send(embed=embed)
        await self.message.add_reaction(self.emoji)

        pause = random.uniform(1.0, 5.0)
        await asyncio.sleep(pause)

        embed.description = f'React with {self.emoji} now!'
        await self.message.edit(embed=embed)

        user, elapsed = await self.wait_for_reaction(ctx)

        embed.description = f'{user.mention} reacted first in `{elapsed:.2f}s` !'
        return await self.message.edit(embed=embed)
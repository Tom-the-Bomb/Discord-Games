from __future__ import annotations

from typing import Union
import time
import random
import asyncio

import discord
from discord.ext import commands

from ..reaction_test import ReactionGame

class ReactionButton(discord.ui.Button):
    view: ReactionView

    def __init__(self, style: discord.ButtonStyle) -> None:
        super().__init__(label='\u200b', style=style)

        self.clicked: bool = False
    
    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game

        if game.author_only and interaction.user != game.author:
            return await interaction.response.send_message('This game is only for the author!', ephemeral=True)

        if self.style == discord.ButtonStyle.blurple:
            return await interaction.response.defer()
        else:
            end_time = time.perf_counter()
            elapsed = self.view.game - end_time

            game.embed.description = f'{interaction.user.mention} reacted first in `{elapsed:.2f}s` !'
            await interaction.response.edit_message(embed=game.embed)
            return self.view.stop()

class ReactionView(discord.ui.View):
    game: ReactionGame

    def __init__(
        self, 
        game: ReactionGame,
        *,
        button_style: discord.ButtonStyle,  
        timeout: float
    ) -> None:

        super().__init__(timeout=timeout)

        self.game = game
        self.button_style = button_style
        self.button = ReactionButton(self.button_style)
        self.add_item(self.button)

class ReactionGame(ReactionGame):
    
    async def start(
        self, 
        ctx: commands.Context, 
        *,
        author_only: bool = False,
        button_style: discord.ButtonStyle = discord.ButtonStyle.blurple, 
        embed_color: Union[discord.Color, int] = 0x2F3136,
        timeout: float = None,
    ) -> discord.Message:

        self.author_only = author_only
        self.author = ctx.author

        self.embed = discord.Embed(
            title='Reaction Game',
            description=f'React with {self.emoji} when the button changes color!',
            color=embed_color,
        )
        view = ReactionView(self, button_style=button_style, timeout=timeout)
        self.message = await ctx.send(embed=self.embed, view=view)
        
        pause = random.uniform(1.0, 5.0)
        await asyncio.sleep(pause)

        view.button.style = discord.ButtonStyle.red
        await self.message.edit(view=view)

        self.start_time = time.perf_counter()
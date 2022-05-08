from __future__ import annotations

from typing import Optional
import time
import random
import asyncio

import discord
from discord.ext import commands

from ..utils import DiscordColor, DEFAULT_COLOR

class ReactionButton(discord.ui.Button['ReactionView']):

    def __init__(self, style: discord.ButtonStyle) -> None:
        super().__init__(label='\u200b', style=style)

        self.edited: bool = False
        self.clicked: bool = False
    
    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game

        if game.author_only and interaction.user != game.author:
            return await interaction.response.send_message('This game is only for the author!', ephemeral=True)

        if not self.edited or self.clicked:
            return await interaction.response.defer()
        else:
            end_time = time.perf_counter()
            elapsed = end_time - self.view.game.start_time

            game.embed.description = f'{interaction.user.mention} reacted first in `{elapsed:.2f}s` !'
            await interaction.response.edit_message(embed=game.embed)
            
            self.clicked = True
            game.finished_event.set()

class ReactionView(discord.ui.View):
    game: BetaReactionGame

    def __init__(
        self, 
        game: BetaReactionGame,
        *,
        button_style: discord.ButtonStyle,  
        timeout: float
    ) -> None:

        super().__init__(timeout=timeout)

        self.game = game
        self.button_style = button_style
        self.button = ReactionButton(self.button_style)
        self.add_item(self.button)

class BetaReactionGame:
    
    async def start(
        self, 
        ctx: commands.Context, 
        *,
        author_only: bool = False,
        button_style: discord.ButtonStyle = discord.ButtonStyle.blurple, 
        embed_color: DiscordColor = DEFAULT_COLOR,
        timeout: Optional[float] = None,
    ) -> bool:

        self.finished_event = asyncio.Event()

        self.author_only = author_only
        self.author = ctx.author

        self.embed = discord.Embed(
            title='Reaction Game',
            description=f'Click the button below, when the button changes color!',
            color=embed_color,
        )
        view = ReactionView(self, button_style=button_style, timeout=timeout)
        self.message = await ctx.send(embed=self.embed, view=view)
        
        pause = random.uniform(1.0, 5.0)
        await asyncio.sleep(pause)

        styles = (discord.ButtonStyle.green, discord.ButtonStyle.red)
        view.button.style = random.choices(styles, weights=[1, 2])[0]

        await self.message.edit(view=view)
        self.start_time = time.perf_counter()
        view.button.edited = True

        return await self.finished_event.wait()
from __future__ import annotations

import random

import discord
from discord.ext import commands

from ..twenty_48 import Twenty48

class Twenty48_Button(discord.ui.Button):

    view: discord.ui.View
    
    def __init__(self, game: BetaTwenty48, emoji: str) -> None:
        self.game = game
        super().__init__(
            style=discord.ButtonStyle.primary, 
            emoji=discord.PartialEmoji(name=emoji), 
            label="\u200b"
        )

    async def callback(self, interaction: discord.Interaction) -> discord.Message:

        assert self.view

        if interaction.user != self.game.player:
            return await interaction.response.send_message(content="This isn't your game!", ephemeral=True)

        emoji = str(self.emoji)

        if emoji == '➡️':
            await self.game.move_right()

        elif emoji == '⬅️':
            await self.game.move_left()

        elif emoji == '⬇️':
            await self.game.move_down()

        elif emoji == '⬆️':
            await self.game.move_up()

        await self.game.spawn_new()
        board_string = await self.game.number_to_emoji()

        return await interaction.response.edit_message(content=board_string)


class BetaTwenty48(Twenty48):
    player: discord.Member
    view: discord.ui.View

    async def start(self, ctx: commands.Context, *, timeout: float = None, **kwargs) -> None:
        
        self.player = ctx.author
        self.view = discord.ui.View(timeout=timeout)

        self.board[random.randrange(4)][random.randrange(4)] = 2
        self.board[random.randrange(4)][random.randrange(4)] = 2

        for button in self._controls:
            self.view.add_item(Twenty48_Button(self, button))
        
        board_string = await self.number_to_emoji()
        self.message = await ctx.send(content=board_string, view=self.view, **kwargs)
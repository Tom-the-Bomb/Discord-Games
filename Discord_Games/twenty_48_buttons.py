import random

import discord
from discord.components import Button
from discord.types.components import ButtonComponent
from discord.enums import ButtonStyle
from discord.ext import commands
from discord.ui import View

from ..twenty_48 import Twenty_48

class Twenty48_Button(discord.ui.Button['Twenty48']):
    
    def __init__(self, emoji: str):
        super().__init__(style=discord.ButtonStyle.secondary, label=emoji)
        self.y = y

    async def callback(self, interaction: discord.Interaction):

        assert self.view

        emoji = self.view.label

        if emoji == '➡️':
            await self.view.MoveRight()

        elif emoji == '⬅️':
            await self.view.MoveLeft()

        elif emoji == '⬇️':
            await self.view.MoveDown()

        elif emoji == '⬆️':
            await self.view.MoveUp()

        await self.view.spawn_new()
        BoardString = await self.number_to_emoji()

        await interaction.response.edit_message(content=BoardString)

class BetaTwenty48(Twenty_48, discord.ui.View):

    async def start(self, ctx: commands.Context, **kwargs):

        self.board[random.randrange(4)][random.randrange(4)] = 2
        self.board[random.randrange(4)][random.randrange(4)] = 2
        
        BoardString = await self.number_to_emoji()
        self.message = await ctx.send(BoardString, **kwargs)

        for button in self._controls:
            self.add_item(Twenty48_Button(button))
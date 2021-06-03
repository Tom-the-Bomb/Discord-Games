import random

import discord
from discord.ext import commands

from .twenty_48 import Twenty48

class Twenty48_Button(discord.ui.Button['Twenty48']):
    
    def __init__(self, emoji: str):
        super().__init__(style=discord.ButtonStyle.blurple, label=emoji)

    async def callback(self, interaction: discord.Interaction):

        assert self.view

        emoji = self.label

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

        await interaction.message.edit_message(content=BoardString)


class BetaTwenty48(Twenty48):

    async def start(self, ctx: commands.Context, **kwargs):

        self.view = discord.ui.View()
        self.board[random.randrange(4)][random.randrange(4)] = 2
        self.board[random.randrange(4)][random.randrange(4)] = 2

        for button in self._controls:
            self.view.add_item(Twenty48_Button(button))
        
        BoardString = await self.number_to_emoji()
        self.message = await ctx.send(content=BoardString, view=self.view, **kwargs)
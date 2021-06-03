import random

import discord
from discord.ext import commands

from .twenty_48 import Twenty48

class Twenty48_Button(discord.ui.Button['Twenty48']):
    
    def __init__(self, game, emoji: str):
        self.game = game
        super().__init__(style=discord.ButtonStyle.blurple, label=emoji)

    async def callback(self, interaction: discord.Interaction):

        assert self.view

        emoji = self.label

        if emoji == '➡️':
            await self.game.MoveRight()

        elif emoji == '⬅️':
            await self.game.MoveLeft()

        elif emoji == '⬇️':
            await self.game.MoveDown()

        elif emoji == '⬆️':
            await self.game.MoveUp()

        await self.game.spawn_new()
        BoardString = await self.game.number_to_emoji()

        await interaction.message.edit(content=BoardString)


class BetaTwenty48(Twenty48):

    async def start(self, ctx: commands.Context, **kwargs):

        self.view = discord.ui.View()
        self.board[random.randrange(4)][random.randrange(4)] = 2
        self.board[random.randrange(4)][random.randrange(4)] = 2

        for button in self._controls:
            self.view.add_item(Twenty48_Button(self, button))
        
        BoardString = await self.number_to_emoji()
        self.message = await ctx.send(content=BoardString, view=self.view, **kwargs)
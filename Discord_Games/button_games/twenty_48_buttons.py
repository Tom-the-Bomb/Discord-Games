from __future__ import annotations

from typing import Optional
import random

import discord
from discord.ext import commands

from ..twenty_48 import Twenty48

class Twenty48_Button(discord.ui.Button):

    view: discord.ui.View
    
    def __init__(self, game: BetaTwenty48, emoji: str) -> None:

        style = discord.ButtonStyle.red if emoji == '⏹️' else discord.ButtonStyle.blurple

        self.game = game
        super().__init__(
            style=style, 
            emoji=discord.PartialEmoji(name=emoji), 
            label="\u200b"
        )

    async def callback(self, interaction: discord.Interaction) -> discord.Message:

        assert self.view

        if interaction.user != self.game.player:
            return await interaction.response.send_message(content="This isn't your game!", ephemeral=True)

        emoji = str(self.emoji)

        if emoji == '⏹️':
            return await interaction.message.delete()

        elif emoji == '➡️':
            await self.game.move_right()

        elif emoji == '⬅️':
            await self.game.move_left()

        elif emoji == '⬇️':
            await self.game.move_down()

        elif emoji == '⬆️':
            await self.game.move_up()

        self.game.spawn_new()

        if self.game._render_image:
            image = await self.game.render_image()
            return await interaction.response.edit_message(attachments=[image])
        else:
            board_string = self.game.number_to_emoji()
            return await interaction.response.edit_message(content=board_string)


class BetaTwenty48(Twenty48):
    view: discord.ui.View

    async def start(
        self, 
        ctx: commands.Context, 
        *,
        timeout: Optional[float] = None, 
        delete_button: bool = False,
        **kwargs,
    ) -> None:
        
        self.player = ctx.author
        self.view = discord.ui.View(timeout=timeout)

        self.board[random.randrange(4)][random.randrange(4)] = 2
        self.board[random.randrange(4)][random.randrange(4)] = 2

        if delete_button:
            self._controls.append("⏹️")

        for button in self._controls:
            self.view.add_item(Twenty48_Button(self, button))
        
        if self._render_image:
            image = await self.render_image()
            self.message = await ctx.send(file=image, view=self.view, **kwargs)
        else:
            board_string = self.number_to_emoji()
            self.message = await ctx.send(content=board_string, view=self.view, **kwargs)
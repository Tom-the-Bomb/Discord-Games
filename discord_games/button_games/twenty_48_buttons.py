from __future__ import annotations

from typing import Optional, Literal
import random

import discord
from discord.ext import commands

from ..twenty_48 import Twenty48
from ..utils import DiscordColor, DEFAULT_COLOR, BaseView


class Twenty48_Button(discord.ui.Button['BaseView']):
    
    def __init__(self, game: BetaTwenty48, emoji: str) -> None:

        style = discord.ButtonStyle.red if emoji == '⏹️' else discord.ButtonStyle.blurple

        self.game = game
        super().__init__(
            style=style, 
            emoji=discord.PartialEmoji(name=emoji), 
            label="\u200b"
        )

    async def callback(self, interaction: discord.Interaction) -> None:

        assert self.view

        if interaction.user != self.game.player:
            return await interaction.response.send_message('This isn\'t your game!', ephemeral=True)

        emoji = str(self.emoji)

        if emoji == '⏹️':
            self.view.stop()
            return await interaction.message.delete()

        elif emoji == '➡️':
            self.game.move_right()

        elif emoji == '⬅️':
            self.game.move_left()

        elif emoji == '⬇️':
            self.game.move_down()

        elif emoji == '⬆️':
            self.game.move_up()

        self.game.spawn_new()
        won = self.game.check_win()

        if self.game._render_image:
            image = await self.game.render_image()
            await interaction.response.edit_message(attachments=[image], embed=self.game.embed)
        else:
            board_string = self.game.number_to_emoji()
            await interaction.response.edit_message(content=board_string, embed=self.game.embed)

        if won:
            return self.view.stop()

class BetaTwenty48(Twenty48):
    view: discord.ui.View

    async def start(
        self, 
        ctx: commands.Context, 
        *,
        win_at: Literal[2048, 4096, 8192] = 8192,
        timeout: Optional[float] = None, 
        delete_button: bool = False,
        embed_color: DiscordColor = DEFAULT_COLOR,
        **kwargs,
    ) -> bool:
        
        self.win_at = win_at
        self.embed_color = embed_color

        self.player = ctx.author
        self.view = BaseView(timeout=timeout)

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

        return await self.view.wait()
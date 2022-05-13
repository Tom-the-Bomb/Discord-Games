from __future__ import annotations

from typing import ClassVar, Optional

import discord
from discord.ext import commands

from ..tictactoe import Tictactoe
from ..utils import *

class TTTButton(discord.ui.Button['TTTView']):

    def __init__(self, label: str, style: discord.ButtonStyle, *, row: int, col: int):
        super().__init__(
            label=label, 
            style=style,
            row=row,
        )

        self.col = col

    async def callback(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        game = self.view.game

        if user not in (game.cross, game.circle):
            return await interaction.response.send_message('You are not part of this game!', ephemeral=True)

        if user != game.turn:
            return await interaction.response.send_message('it is not your turn!', ephemeral=True)

        self.label = game.player_to_emoji[user]
        self.disabled = True

        game.board[self.row][self.col] = self.label
        game.turn = game.circle if user == game.cross else game.cross

        tie = all(button.disabled for button in self.view.children)

        await interaction.response.edit_message(embed=game.make_embed(self.view.embed_color, tie=tie), view=self.view)

        if game.is_game_over(tie=tie):
            if game.winning_indexes:
                self.view.disable_all()
                game.create_streak()
                await interaction.message.edit(view=self.view)
            return self.view.stop()


class TTTView(BaseView):

    def __init__(self, 
        game: BetaTictactoe, 
        *,
        embed_color: DiscordColor,
        button_style: discord.ButtonStyle,
        win_button_style: discord.ButtonStyle,
        timeout: Optional[float] = None
    ) -> None:

        super().__init__(timeout=timeout)

        self.game = game
        self.embed_color = embed_color
        self.button_style = button_style
        self.win_button_style = win_button_style

        for x, row in enumerate(game.board):
            for y, square in enumerate(row):
                button = TTTButton(
                    label=square, 
                    style=self.button_style,
                    row=x,
                    col=y,
                )
                self.add_item(button)


class BetaTictactoe(Tictactoe):
    BLANK: ClassVar[str] = '\u200b'
    CIRCLE: ClassVar[str] = 'O'
    CROSS: ClassVar[str] = 'X'

    def create_streak(self) -> None:
        chunked = chunk(self.view.children, count=3)
        for row, col in self.winning_indexes:
            button = chunked[row][col]
            button.style = self.view.win_button_style

    async def start(
        self, 
        ctx: commands.Context,
        button_style: discord.ButtonStyle = discord.ButtonStyle.green,
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
        win_button_style: discord.ButtonStyle = discord.ButtonStyle.red,
        timeout: Optional[float] = None,
    ) -> bool:

        self.view = TTTView(
            self,
            embed_color=embed_color,
            button_style=button_style,
            win_button_style=win_button_style,
            timeout=timeout,
        )
        self.message = await ctx.send(embed=self.make_embed(embed_color), view=self.view)

        return await double_wait(
            wait_for_delete(ctx, self.message, user=(self.cross, self.circle)),
            self.view.wait(),
        )
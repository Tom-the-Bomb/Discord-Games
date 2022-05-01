from __future__ import annotations

from typing import ClassVar, Union, Optional

import discord
from discord.ext import commands

from ..tictactoe import Tictactoe

class TTTButton(discord.ui.Button):
    view: TTTView

    def __init__(self, label: str, style: discord.ButtonStyle, row: int):
        super().__init__(
            label=label, 
            style=style,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        game = self.view.game

        if user not in (game.cross, game.circle):
            return await interaction.response.send_message('You are not part of this game!', ephemeral=True)

        if user != game.turn:
            return await interaction.response.send_message('it is not your turn!', ephemeral=True)

        self.label = game.player_to_emoji[user]
        self.disabled = True

        column_idx = [button for button in self.view.children if button.row == self.row].index(self)
        game.board[self.row][column_idx] = self.label
        game.turn = game.circle if user == game.cross else game.cross

        tie = all(button.disabled for button in self.view.children)

        await interaction.response.edit_message(embed=game.make_embed(self.view.embed_color, tie=tie), view=self.view)

        if game.is_game_over():
            for button in self.view.children:
                if isinstance(button, discord.ui.Button):
                    button.disabled = True
            
            for y, x in game.winning_indexes:
                row = [button for button in self.view.children if button.row == y]
                button = row[x]
                button.style = self.view.win_button_style

            await interaction.message.edit(view=self.view)
            return self.view.stop()


class TTTView(discord.ui.View):

    def __init__(self, 
        game: BetaTictactoe, 
        *,
        embed_color: Union[discord.Color, int],
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
            for square in row:
                button = TTTButton(
                    label=square, 
                    style=self.button_style,
                    row=x
                )
                self.add_item(button)


class BetaTictactoe(Tictactoe):
    BLANK: ClassVar[str] = '\u200b'
    CIRCLE: ClassVar[str] = 'O'
    CROSS: ClassVar[str] = 'X'

    async def start(
        self, 
        ctx: commands.Context,
        button_style: discord.ButtonStyle = discord.ButtonStyle.green,
        *,
        embed_color: Union[discord.Color, int] = 0x2F3136,
        win_button_style: discord.ButtonStyle = discord.ButtonStyle.red,
        timeout: Optional[float] = None,
    ) -> discord.Message:

        view = TTTView(
            self,
            embed_color=embed_color,
            button_style=button_style,
            win_button_style=win_button_style,
            timeout=timeout,
        )

        return await ctx.send(embed=self.make_embed(embed_color), view=view)
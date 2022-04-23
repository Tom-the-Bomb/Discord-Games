from __future__ import annotations

from typing import ClassVar

import discord
from discord.ext import commands

from ..tictactoe import Tictactoe

class TTTButton(discord.ui.Button):
    view: TTTView

    def __init__(self, label: str, row: int):
        super().__init__(
            label=label, 
            row=row,
            style=discord.ButtonStyle.green
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

        await interaction.response.edit_message(embed=game.make_embed(), view=self.view)

        if game.is_game_over():
            for button in self.view.children:
                if isinstance(button, discord.ui.Button):
                    button.disabled = True
            
            for y, x in game.winning_indexes:
                row = [button for button in self.view.children if button.row == y]
                button = row[x]
                button.style = discord.ButtonStyle.red
                
            await interaction.message.edit(view=self.view)
            return self.view.stop()

class TTTView(discord.ui.View):

    def __init__(self, game: BetaTictactoe, *, timeout: float = None) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        for x, row in enumerate(game.board):
            for square in row:
                self.add_item(TTTButton(square, row=x))


class BetaTictactoe(Tictactoe):
    BLANK: ClassVar[str] = "\u200b"
    CIRCLE: ClassVar[str] = "O"
    CROSS: ClassVar[str] = "X"

    def __init__(self, cross: discord.Member, circle: discord.Member) -> None:
        super().__init__(cross, circle)

        self.board = [[self.BLANK for _ in range(3)] for _ in range(3)]

    async def start(self, ctx: commands.Context, *, timeout: float = None) -> discord.Message:
        return await ctx.send(
            embed=self.make_embed(), 
            view=TTTView(self, timeout=timeout)
        )
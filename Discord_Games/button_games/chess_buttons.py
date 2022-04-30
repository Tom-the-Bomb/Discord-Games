from __future__ import annotations

from typing import Optional, Union
import discord
from discord.ext import commands

from ..chess_game import Chess
from .wordle_buttons import WordInputButton

class ChessInput(discord.ui.Modal, title='Make your move'):

    def __init__(self, view: ChessView) -> None:
        super().__init__()
        self.view = view

        self.move_from = discord.ui.TextInput(
            label='from coordinate',
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=2,
        )

        self.move_to = discord.ui.TextInput(
            label='to coordinate',
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=2,
        )

        self.add_item(self.move_from)
        self.add_item(self.move_to)
        
    async def on_submit(self, interaction: discord.Interaction) -> discord.Message:
        game = self.view.game
        from_coord = self.move_from.value.strip().lower()
        to_coord = self.move_to.value.strip().lower()

        uci = from_coord + to_coord

        try:
            is_valid_uci = game.board.parse_uci(uci)
        except ValueError:
            is_valid_uci = False
        
        if not is_valid_uci:
            return await interaction.response.send_message(f'Invalid coordinates for move: `{from_coord} -> {to_coord}`', ephemeral=True)
        else:
            await game.place_move(uci)

            if game.board.is_game_over():
                self.view.disable_all()
                embed = await game.fetch_results()
            else:
                embed = await game.make_embed()

            return await interaction.response.edit_message(embed=embed, view=self.view)

class ChessButton(WordInputButton):
    view: ChessView

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game
        if interaction.user not in (game.black, game.white):
            return await interaction.response.send_message("You are not part of this game!", ephemeral=True)
        else:
            if self.label == 'Cancel':
                self.view.disable_all()
                await interaction.message.edit(view=self.view)
                return await interaction.response.send_message(f'**Game Over!** Cancelled')
            else:
                if interaction.user != game.turn:
                    return await interaction.response.send_message('It is not your turn yet!', ephemeral=True)
                else:
                    return await interaction.response.send_modal(ChessInput(self.view))

class ChessView(discord.ui.View):

    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True
    
    def __init__(self, game: BetaChess, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        inpbutton = ChessButton()
        inpbutton.label = 'Make your move!'

        self.add_item(inpbutton)
        self.add_item(ChessButton(cancel_button=True))

class BetaChess(Chess):

    async def start(
        self, 
        ctx: commands.Context, 
        *, 
        embed_color: Union[discord.Color, int] = 0x2F3136, 
        timeout: Optional[float] = None, 
    ) -> None:

        self.embed_color = embed_color

        embed = await self.make_embed()
        view = ChessView(self, timeout=timeout)

        self.message = await ctx.send(embed=embed, view=view)
from __future__ import annotations

from typing import Optional, Union
import discord
from discord.ext import commands
import chess

from ..chess_game import Chess

class ChessModal(discord.ui.Modal, title='Make your move')

    def __init__(self, view: ChessView) -> None:
        super().__init__()
        self.view = view

        self.move_from = discord.ui.TextInput(
            label='from coordinate',
            style=discord.TextStyle.short,
            required=True,
            min_length=2
            max_length=2,
        )

        self.move_to = discord.ui.TextInput(
            label='to coordinate',
            style=discord.TextStyle.short,
            required=True,
            min_length=2
            max_length=2,
        )

        self.add_item(self.move_to)
        self.add_item(self.move_from)
        
    async def on_submit(self, interaction: discord.Interaction) -> discord.Message:
        from_coord = self.move_from.value.strip().lower()
        to_coord = self.move_from.value.strip().lower()

class ChessView(discord.ui.View):
    ...

class BetaChess:

    async def start(
        self, 
        ctx: commands.Context, 
        *, 
        embed_color: Union[discord.Color, int] = 0x2F3136, 
        timeout: Optional[float] = None, 
    ) -> discord.Message:
        ...
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Literal
import random

import discord
from discord.ext import commands

from ..utils import *

if TYPE_CHECKING:
    from typing_extensions import TypeAlias
    Board: TypeAlias = list[list[Optional[int]]] 

class SlideButton(discord.ui.Button['SlideView']):

    def __init__(self, label: str, *, style: discord.ButtonStyle, row: int) -> None:
        super().__init__(
            label=label,
            style=style,
            row=row,
        )

        if label == '\u200b':
            self.disabled = True

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game

        if interaction.user != game.player:
            return await interaction.response.send_message('This is not your game!', ephemeral=True)
        else:
            num = int(self.label)

            if num not in game.beside_blank():
                return await interaction.response.defer()
            else:
                ix, iy = game.get_item(num)
                nx, ny = game.get_item()

                game.numbers[nx][ny], game.numbers[ix][iy] = game.numbers[ix][iy], game.numbers[nx][ny]

                self.view.update_board(clear=True)

                game.moves += 1
                game.embed.set_field_at(0, name='\u200b', value=f'Moves: `{game.moves}`')

                if game.numbers == game.completed:
                    self.view.disable_all()
                    game.embed.description = '**Congrats! You won!**'
                        
                return await interaction.response.edit_message(embed=game.embed, view=self.view)
            
class SlideView(discord.ui.View):

    def __init__(self, game: NumberSlider, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        self.update_board()

    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    def update_board(self, *, clear: bool = False) -> None:
        
        if clear:
            self.clear_items()
            
        for i, row in enumerate(self.game.numbers):
            for number in row:
                button = SlideButton(
                    label=number or '\u200b', 
                    style=self.game.button_style,
                    row=i,
                )
                self.add_item(button)
        
class NumberSlider:

    def __init__(self, count: Literal[1, 2, 3, 4, 5] = 4) -> None:

        if count not in range(1, 6):
            raise ValueError('Count must be an integer between 1 and 5')

        self.all_numbers = list(range(1, count ** 2))

        self.player: Optional[discord.Member] = None

        self.moves: int = 0
        self.count = count
        self.numbers: Board = []
        self.completed: Board = []

        self.button_style: discord.ButtonStyle = discord.ButtonStyle.green

    def get_item(self, obj: Optional[int] = None) -> tuple[int, int]:
        return next(
            (x, y) for x, row in enumerate(self.numbers) for y, item in enumerate(row) if item == obj
        )

    def beside_blank(self) -> list[int]:
        nx, ny = self.get_item()

        beside_item = [
            (nx-1, ny), 
            (nx, ny-1), 
            (nx+1, ny), 
            (nx, ny+1),
        ]

        data = [
            self.numbers[i][j] for i, j in beside_item
            if i in range(self.count) and j in range(self.count)
        ]
        return data

    async def start(
        self, 
        ctx: commands.Context, 
        *,
        button_style: discord.ButtonStyle = discord.ButtonStyle.green,
        embed_color: DiscordColor = DEFAULT_COLOR,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        
        self.player = ctx.author
        self.button_style = button_style

        numbers = self.all_numbers[:]
        random.shuffle(numbers)
        random.shuffle(numbers)

        numbers.append(None)
        self.numbers = chunk(numbers, count=self.count)

        self.completed = chunk(self.all_numbers + [None], count=self.count)
        
        view = SlideView(self, timeout=timeout)
        self.embed = discord.Embed(description='Slide the tiles back in ascending order!', color=embed_color)
        self.embed.add_field(name='\u200b', value='Moves: `0`')

        return await ctx.send(embed=self.embed, view=view)
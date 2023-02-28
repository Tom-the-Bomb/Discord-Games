from __future__ import annotations

from typing import Optional
import random

import discord
from discord.ext import commands

from ..utils import *


class ChimpButton(discord.ui.Button["ChimpView"]):
    def __init__(self, num: int, *, style: discord.ButtonStyle, row: int = 0) -> None:
        self.value = num

        super().__init__(
            label=self.value or "\u200b",
            style=style,
            row=row,
        )

        self.step = 0
        self.first_clicked = False

    def update_view(self, style: discord.ButtonStyle, show: bool = False) -> None:
        for num, button in zip(self.view.game.grid, self.view.children):
            if isinstance(button, discord.ui.Button):
                if num:
                    button.style = style
                button.label = str(self.value) if show else "\u200b"

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game

        if not self.first_clicked:
            self.first_clicked = True

            self.update_view(style=discord.ButtonStyle.blurple)
            await interaction.response.edit_message(
                content="Now click the buttons in order!", view=self.view
            )
        else:
            idx = self.view.children.index(self)
            if idx == game.coordinates[self.step]:
                self.label = str(self.value)
                self.step += 1
                await interaction.response.edit_message(view=self.view)
            else:
                self.update_view(style=discord.ButtonStyle.red)
                await interaction.response.edit_message(
                    content="You Lose!", view=self.view
                )
                self.view.stop()

class ChimpView(BaseView):
    def __init__(
        self,
        game: ChimpTest,
        *,
        timeout: Optional[float] = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.game = game

        for i, row in enumerate(chunk(self.game.grid, count=5)):
            for item in row:
                button = ChimpButton(item, style=discord.ButtonStyle.gray, row=i)
                button.disabled = not item
                self.add_item(button)


class ChimpTest:
    """
    ChimpTest Memory Game
    """
    def __init__(self, count: int = 9) -> None:
        self.count = count

        self.coordinates = []
        self.grid = [0] * 25
        for i in range(self.count):
            j = random.randrange(25)
            while self.grid[j] != 0:
                j = random.randrange(25)

            self.coordinates.append(j)
            self.grid[j] = i + 1

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        """
        starts the chimpanzee memory game test

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.view = ChimpView(
            game=self,
            timeout=timeout,
        )
        self.message = await ctx.send(view=self.view)

        await double_wait(
            wait_for_delete(ctx, self.message),
            self.view.wait(),
        )
        return self.message
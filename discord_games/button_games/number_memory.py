from __future__ import annotations

from typing import Optional
import random
import string

import discord
from discord.ext import commands

from ..utils import *

class NumModal(discord.ui.Modal, title="Answer"):
    word = discord.ui.TextInput(
        label="number",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
    )

    def __init__(self, view: NumView) -> None:
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        ...

class NumButton(discord.ui.Button["NumView"]):
    def __init__(self, label: str, style: discord.ButtonStyle) -> None:
        super().__init__(
            label=label,
            style=style,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view

        if self.label == "Cancel" and interaction.message:
            await interaction.message.delete()
            return self.view.stop()
        else:
            return await interaction.response.send_modal(NumModal())


class NumView(BaseView):
    def __init__(
        self,
        game: NumberMemory,
        *,
        button_style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        timeout: Optional[float] = None,
    ) -> None:
        super().__init__(timeout=timeout)

        self.game = game
        self.button_style = button_style

        self.add_item(NumButton(label="Answer", style=self.button_style))
        self.add_item(NumButton(label="Cancel", style=discord.ButtonStyle.red))


class NumberMemory:
    def __init__(self) -> None:
        self.embed: Optional[discord.Embed] = None
        self.level = 1

    def update_description(self) -> None:
        assert self.embed
        self.embed.description = (
            f"```py\n{self.generate_number()}\n```"
        )

    def generate_number(self) -> str:
        return ''.join(random.choices(string.digits, k=self.level))

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        pause_time: float = 5.0,
        button_style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        embed_color: DiscordColor = DEFAULT_COLOR,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        """
        starts the chimpanzee memory game test

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        lives : int
            the amount of errors that are allowed by the player, by default 1
        weights : tuple[float, float]
            the weights when choosing a word, as (NEW, SEEN), by default (0.7, 0.3)
        button_style : discord.ButtonStyle, optional
            the button style to use for the game buttons, by default discord.ButtonStyle.blurple
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.pause_time = pause_time
        self.embed = discord.Embed(
            title=f'Level: {self.level}',
            color=embed_color,
        )
        self.update_description()
        self.view = NumView(
            game=self,
            button_style=button_style,
            timeout=timeout,
        )
        self.message = await ctx.send(embed=self.embed, view=self.view)

        await self.view.wait()
        return self.message

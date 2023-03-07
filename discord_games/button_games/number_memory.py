from __future__ import annotations

from typing import Optional
import random
import string
import asyncio
import datetime

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
        game = self.view.game
        value = self.word.value
        assert game.embed

        if not value.isdigit():
            return await interaction.response.send_message(
                f"`{value}` is not a valid number!", ephemeral=True
            )

        if value == game.number:
            game.level += 1
            game.pause_time += game.pause_incr
            game.number = game.generate_number()
            game.update_embed()
            self.view.answer.disabled = True
            await interaction.response.edit_message(embed=game.embed, view=self.view)

            await asyncio.sleep(game.pause_time)
            game.update_embed(hide=True)

            if interaction.message:
                await interaction.message.edit(embed=game.embed, view=self.view)
        else:
            game.embed.description = (
                "You Lost!\n\n```diff\nCorrect Number:\n"
                f"+ {game.number}\n"
                "Your Guess:\n"
                f"- {value}\n```"
            )
            self.view.disable_all()
            await interaction.response.edit_message(embed=game.embed, view=self.view)
            return self.view.stop()


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
            return await interaction.response.send_modal(NumModal(self.view))


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

        self.answer = NumButton(label="Answer", style=self.button_style)
        self.answer.disabled = True
        self.add_item(self.answer)
        self.add_item(NumButton(label="Cancel", style=discord.ButtonStyle.red))


class NumberMemory:
    def __init__(self) -> None:
        self.embed: Optional[discord.Embed] = None
        self.level = 1
        self.number = self.generate_number()

    def update_embed(self, hide: bool = False) -> None:
        assert self.embed
        self.embed.title = f"Level: `{self.level}`"

        if hide:
            self.view.answer.disabled = False
            self.embed.description = "```yml\nGuess!\n```"
        else:
            time = discord.utils.utcnow() + datetime.timedelta(
                seconds=self.pause_time + 1
            )
            pause = discord.utils.format_dt(time, style="R")

            self.embed.description = f"Guess in {pause}!\n```py\n{self.number}\n```"

    def generate_number(self) -> str:
        return "".join(random.choices(string.digits, k=self.level))

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        initial_pause_time: float = 2.0,
        pause_time_increment: float = 1.0,
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
        initial_pause_time : float
            the initial time the user gets to look at the number (1 digit) before they have to guess, by default 2.0
        pause_time_increment : float
            the increment by which the pause time is increased every level, by default 1.0
        button_style : discord.ButtonStyle, optional
            the button style to use for the game buttons, by default discord.ButtonStyle.blurple
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.pause_incr = pause_time_increment
        self.pause_time = initial_pause_time

        self.embed = discord.Embed(color=embed_color)
        self.update_embed()

        self.view = NumView(
            game=self,
            button_style=button_style,
            timeout=timeout,
        )
        self.message = await ctx.send(embed=self.embed, view=self.view)

        await asyncio.sleep(self.pause_time)
        self.update_embed(hide=True)

        await self.message.edit(embed=self.embed, view=self.view)

        await self.view.wait()
        return self.message

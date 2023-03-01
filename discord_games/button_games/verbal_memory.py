from __future__ import annotations

from typing import Optional
import random

import discord
from discord.ext import commands
from english_words import get_english_words_set

from ..utils import *

class VerbalButton(discord.ui.Button["VerbalView"]):
    def __init__(self, label: str, style: discord.ButtonStyle) -> None:
        super().__init__(
            label=label,
            style=style,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view
        game = self.view.game

        if self.label == "Cancel":
            await interaction.message.delete()
            return self.view.stop()

        if not (
            self.label == "Seen" and game.word in game.seen or
            self.label == "New" and game.word not in game.seen
        ):
            game.lives -= 1
            game.update_description()

            if game.lives == 0:
                game.embed.title = "You Lost!"
                await interaction.response.edit_message(embed=game.embed, view=self.view)
                return self.view.stop()
        else:
            game.score += 1

        if game.word not in game.seen:
            game.seen.append(game.word)

        game.word = random.choice(game.word_set)
        game.embed.title = game.word
        game.update_description()
        return await interaction.response.edit_message(embed=game.embed, view=self.view)

class VerbalView(BaseView):
    def __init__(
        self,
        game: VerbalMemory,
        *,
        button_style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        timeout: Optional[float] = None,
    ) -> None:
        super().__init__(timeout=timeout)

        self.game = game
        self.button_style = button_style

        self.add_item(VerbalButton(label="Seen", style=self.button_style))
        self.add_item(VerbalButton(label="New", style=self.button_style))
        self.add_item(VerbalButton(label="Cancel", style=discord.ButtonStyle.red))

class VerbalMemory:
    def __init__(self, word_set: Optional[tuple[str, ...]] = None, sample_size: int = 100) -> None:
        self.lives: int = 0
        self.embed: Optional[discord.Embed] = None
        self.word_set = word_set or tuple(random.choices(
            tuple(get_english_words_set(
                ["web2"],
                alpha=True,
                lower=True,
            )),
            k=sample_size,
        ))

        self.score: int = 0
        self.word = random.choice(self.word_set)
        self.seen: list[str] = [self.word]

    def update_description(self) -> None:
        self.embed.description = (
            f"```yml\nSCore: `{self.score}`\nLives: `{self.lives}`\n```"
        )

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        lives: int = 3,
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
        button_style : discord.ButtonStyle, optional
            the button style to use for the game buttons, by default discord.ButtonStyle.blurple
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.lives = lives
        self.embed = discord.Embed(
            title=self.word,
            description=f"Lives: `{self.lives}`",
            color=embed_color,
        )
        self.view = VerbalView(
            game=self,
            button_style=button_style,
            timeout=timeout,
        )
        self.message = await ctx.send(embed=self.embed, view=self.view)

        await self.view.wait()
        return self.message
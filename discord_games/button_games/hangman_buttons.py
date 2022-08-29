from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from .wordle_buttons import WordInputButton
from ..hangman import Hangman
from ..utils import DiscordColor, DEFAULT_COLOR, BaseView


class HangmanInput(discord.ui.Modal, title="Make a guess!"):
    def __init__(self, view: HangmanView) -> None:
        super().__init__()
        self.view = view

        self.word = discord.ui.TextInput(
            label="Input your guess",
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=len(self.view.game.word),
        )

        self.add_item(self.word)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        content = self.word.value.lower()
        game = self.view.game

        if len(content) == 1 and content not in game._alpha:
            return await interaction.response.send_message(
                "This is not a valid letter to guess (or you've guessed it before)",
                ephemeral=True,
            )

        elif len(content) > 1 and content not in game._all_words:
            return await interaction.response.send_message(
                "This is not a valid word!", ephemeral=True
            )

        else:
            await game.make_guess(content)

            if await game.check_win():
                self.view.disable_all()
                await interaction.response.edit_message(view=self.view)
                return self.view.stop()
            else:
                return await interaction.response.defer()


class HangmanButton(WordInputButton):
    view: HangmanView

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game
        if interaction.user != game.player:
            return await interaction.response.send_message(
                "This isn't your game!", ephemeral=True
            )
        else:
            if self.label == "Cancel":
                await interaction.response.send_message(
                    f"Game Over! the word was: **{game.word}**"
                )
                await interaction.message.delete()
                return self.view.stop()
            else:
                return await interaction.response.send_modal(HangmanInput(self.view))


class HangmanView(BaseView):
    def __init__(self, game: BetaHangman, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        self.add_item(HangmanButton())
        self.add_item(HangmanButton(cancel_button=True))


class BetaHangman(Hangman):
    """
    Hangman(buttons) Game
    """

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> discord.Message:
        """
        starts the Hangman(buttons) Game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.player = ctx.author
        self.embed_color = embed_color

        embed = self.initialize_embed()
        self.view = HangmanView(self, timeout=timeout)
        self.message = await ctx.send(embed=embed, view=self.view, **kwargs)

        await self.view.wait()
        return self.message

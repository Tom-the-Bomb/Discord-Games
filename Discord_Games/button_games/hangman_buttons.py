from __future__ import annotations

from typing import Optional, Union

import discord
from discord.ext import commands

from ..hangman import Hangman
from .wordle_buttons import WordInputButton


class HangmanInput(discord.ui.Modal, title='Make a guess!'):
    def __init__(self, view: HangmanView) -> None:
        super().__init__()
        self.view = view

        self.word = discord.ui.TextInput(
            label='Input your guess',
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=len(self.view.game.word),
        )

        self.add_item(self.word)

    def disable_all(self) -> None:
        for button in self.view.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    async def on_submit(self, interaction: discord.Interaction) -> None:
        content = self.word.value.lower()
        game = self.view.game

        if len(content) == 1 and content not in game._alpha:
            return await interaction.response.send_message("You've guessed this letter before!", ephemeral=True)

        elif len(content) > 1 and content not in game._all_words:
            return await interaction.response.send_message('This is not a valid word!', ephemeral=True)

        else:
            await game.make_guess(content)

            if await game.check_win():
                self.disable_all()

                return await interaction.response.edit_message(view=self.view)
            else:
                return await interaction.response.defer()


class HangmanButton(WordInputButton):
    view: HangmanView

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game
        if interaction.user != game.player:
            return await interaction.response.send_message("This isn't your game!", ephemeral=True)
        else:
            if self.label == 'Cancel':
                await interaction.response.send_message(f'Game Over! the word was: **{game.word}**')
                return await interaction.message.delete()
            else:
                return await interaction.response.send_modal(HangmanInput(self.view))


class HangmanView(discord.ui.View):
    def __init__(self, game: BetaHangman, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        self.add_item(HangmanButton())
        self.add_item(HangmanButton(cancel_button=True))


class BetaHangman(Hangman):
    async def start(
        self,
        ctx: commands.Context,
        *,
        embed_color: Union[discord.Color, int] = 0x2F3136,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> discord.Message:

        self.player = ctx.author
        self.embed_color = embed_color

        embed = self.initialize_embed()
        view = HangmanView(self, timeout=timeout)
        self._message = await ctx.send(embed=embed, view=view, **kwargs)

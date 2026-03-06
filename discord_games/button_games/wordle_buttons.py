from __future__ import annotations

from typing import Optional, Union

import discord
from discord.ext import commands

from ..wordle import Wordle
from ..utils import DiscordColor, DEFAULT_COLOR, BaseView


class WordInput(discord.ui.Modal, title="Word Input"):
    word = discord.ui.TextInput(
        label="Input your guess",
        style=discord.TextStyle.short,
        required=True,
        min_length=5,
        max_length=5,
    )

    def __init__(self, view: WordleView) -> None:
        super().__init__()
        self.wordle_view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        content = self.word.value.lower()
        game = self.wordle_view.game

        if content not in game._valid_words:
            await interaction.response.send_message(
                "That is not a valid word!", ephemeral=True
            )
            return
        else:
            won = game.parse_guess(content)
            buf = await game.render_image()

            embed = discord.Embed(
                title="Wordle!", color=self.wordle_view.game.embed_color
            )
            embed.set_image(url="attachment://wordle.png")
            file = discord.File(buf, "wordle.png")

            lost = False
            if won:
                assert interaction.message is not None
                await interaction.message.reply(
                    "Game Over! You won!", mention_author=True
                )
            elif lost := len(game.guesses) >= 6:
                assert interaction.message is not None
                await interaction.message.reply(
                    f"Game Over! You lose, the word was: **{game.word}**",
                    mention_author=True,
                )

            if won or lost:
                self.wordle_view.disable_all()
                self.wordle_view.stop()

            await interaction.response.edit_message(
                embed=embed, attachments=[file], view=self.wordle_view
            )


class WordInputButton(discord.ui.Button["WordleView"]):
    def __init__(self, *, cancel_button: bool = False):
        super().__init__(
            label="Cancel" if cancel_button else "Make a guess!",
            style=discord.ButtonStyle.red
            if cancel_button
            else discord.ButtonStyle.blurple,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        game = self.view.game
        if interaction.user != game.player:
            await interaction.response.send_message(
                "This isn't your game!", ephemeral=True
            )
            return
        else:
            if self.label == "Cancel":
                await interaction.response.send_message(
                    f"Game Over! the word was: **{game.word}**"
                )
                assert interaction.message is not None
                await interaction.message.delete()
                self.view.stop()
                return
            else:
                await interaction.response.send_modal(WordInput(self.view))


class WordleView(BaseView):
    def __init__(self, game: BetaWordle, *, timeout: Optional[float]):
        super().__init__(timeout=timeout)

        self.game = game
        self.add_item(WordInputButton())
        self.add_item(WordInputButton(cancel_button=True))


class BetaWordle(Wordle):
    """Wordle game, button-based.

    Same as :class:`Wordle` but uses a modal for word input.
    """

    player: Union[discord.User, discord.Member]

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        """
        starts the wordle(buttons) game

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
        self.embed_color = embed_color
        self.player = ctx.author

        buf = await self.render_image()
        embed = discord.Embed(title="Wordle!", color=self.embed_color)
        embed.set_image(url="attachment://wordle.png")

        self.view = WordleView(self, timeout=timeout)
        self.message = await ctx.send(
            embed=embed,
            file=discord.File(buf, "wordle.png"),
            view=self.view,
        )
        await self.view.wait()
        return self.message

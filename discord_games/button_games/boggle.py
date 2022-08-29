from __future__ import annotations

from typing import Optional, ClassVar
import random
import string

import discord
from discord.ext import commands
from english_words import english_words_alpha_set

from ..utils import *


class BoggleButton(discord.ui.Button["BoggleView"]):
    def __init__(
        self, label: str, style: discord.ButtonStyle, *, row: int, col: int
    ) -> None:
        super().__init__(
            style=style,
            label=label,
            row=row,
        )

        self.col = col

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game

        if self.style == game.button_style:
            if game.indices:
                beside_current = game.beside_current(*game.indices[-1])
            else:
                beside_current = [(self.row, self.col)]

            if (self.row, self.col) in beside_current:
                game.current_word += self.label
                game.indices.append((self.row, self.col))

                self.style = game.selected_style
            else:
                return await interaction.response.defer()

        elif (self.row, self.col) == game.indices[-1]:
            self.style = game.button_style
            game.current_word = game.current_word[:-1]
            game.indices.pop(-1)
        else:
            return await interaction.response.defer()

        embed = game.get_embed()
        await interaction.response.edit_message(view=self.view, embed=embed)


class BoggleView(BaseView):
    def __init__(self, game: Boggle, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        for i, row in enumerate(self.game.board):
            for j, letter in enumerate(row):
                button = BoggleButton(
                    label=letter,
                    style=self.game.button_style,
                    row=i,
                    col=j,
                )
                self.add_item(button)

        clean_children = [item for item in self.children if item.row != 4]
        self.nested_children: list[list[BoggleButton]] = chunk(clean_children, count=4)

    async def on_timeout(self) -> None:
        embed = self.game.win()

        message = self.game.message
        await message.edit(view=self)
        await message.reply(embed=embed)
        return self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if check := interaction.user != self.game.player:
            await interaction.response.send_message(
                "This is not your game!", ephemeral=True
            )
        return check

    @discord.ui.button(label="Enter", style=discord.ButtonStyle.green, row=4)
    async def enter_button(self, interaction: discord.Interaction, _) -> None:
        game = self.game

        if not game.current_word:
            return await interaction.response.send_message(
                "You have no current guesses!", ephemeral=True
            )

        if len(game.current_word) < 3:
            return await interaction.response.send_message(
                "Word must be of at least 3 letters in length!", ephemeral=True
            )

        if game.current_word in game.correct_guesses:
            return await interaction.response.send_message(
                "You have guessed this word before!", ephemeral=True
            )

        if game.current_word.lower() in english_words_alpha_set:
            game.correct_guesses.append(game.current_word)
        else:
            game.wrong_guesses.append(game.current_word)

        game.reset()

        embed = game.get_embed()
        return await interaction.response.edit_message(view=self, embed=embed)

    @discord.ui.button(label="Clear", style=discord.ButtonStyle.blurple, row=4)
    async def clear_button(self, interaction: discord.Interaction, _) -> None:

        if not self.game.current_word:
            return await interaction.response.send_message(
                "You have no current guesses to clear!", ephemeral=True
            )

        self.game.reset()

        embed = self.game.get_embed()
        return await interaction.response.edit_message(view=self, embed=embed)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, row=4)
    async def stop_button(self, interaction: discord.Interaction, _) -> None:
        embed = self.game.win()

        await interaction.response.send_message(embed=embed)
        await interaction.message.edit(view=self)
        return self.stop()


class Boggle:
    """
    Boggle Game
    """

    DICE_MATRIX: ClassVar[tuple[tuple[str]]] = (
        ("RIFOBX", "IFEHEY", "DENOWS", "UTOKND"),
        ("HMSRAO", "LUPETS", "ACITOA", "YLGKUE"),
        ("5BMJOA", "EHISPN", "VETIGN", "BALIYT"),
        ("EZAVND", "RALESC", "UWILRG", "PACEMD"),
    )

    def __init__(self) -> None:
        self.board = self.generate_board()

        self.button_style: discord.ButtonStyle = discord.ButtonStyle.gray
        self.selected_style: discord.ButtonStyle = discord.ButtonStyle.green

        self.correct_guesses: list[str] = []
        self.wrong_guesses: list[str] = []

        self.current_word: str = ""
        self.indices: list[tuple[int, int]] = []

        self.embed_color: Optional[DiscordColor] = None

    def generate_board(self) -> list[list[str]]:
        return [[random.choice(die) for die in row] for row in self.DICE_MATRIX]

    def get_results(self) -> tuple[int, int, int]:
        corr = len(guesses := self.correct_guesses)
        wrong = len(self.wrong_guesses)

        points = sum(len(guess) - 2 for guess in guesses)
        points -= sum([1] * len(self.wrong_guesses))
        return corr, wrong, points

    def reset(self) -> None:
        self.current_word = ""
        self.indices = []

        for button in self.view.children:
            if isinstance(button, discord.ui.Button) and button.row != 4:
                button.style = self.button_style

    def get_embed(self) -> discord.Embed:
        correct_guesses = "\n- ".join(self.correct_guesses)
        wrong_guesses = "\n- ".join(self.wrong_guesses)

        embed = discord.Embed(title="Boggle!", color=self.embed_color)
        embed.description = f"```yml\nCurrent-word: {self.current_word}\n```"
        embed.add_field(
            name="Correct Guesses",
            value=f"```yml\n- {correct_guesses}\n```",
        )
        embed.add_field(
            name="Wrong Guesses",
            value=f"```yml\n- {wrong_guesses}\n```",
        )
        return embed

    def win(self) -> discord.Embed:
        self.view.disable_all()

        embed = discord.Embed(title="Game Over!", color=self.embed_color)
        embed.description = (
            "```yml\n"
            "3-letter-word: 1p\n"
            "4-letter-word: 2p\n"
            "5-letter-word: 3p\n"
            "...\nwrong-word: -1p\n```"
        )
        corr, wrong, points = self.get_results()
        embed.add_field(
            name="\u200b",
            value=f"You found **{corr}** correct words (plus **{wrong}** wrong guesses)\nand earned **{points}** points!",
        )
        return embed

    def beside_current(self, row: int, col: int) -> list[tuple[int, int]]:

        indexes = (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
            (row + 1, col + 1),
            (row - 1, col - 1),
            (row + 1, col - 1),
            (row - 1, col + 1),
        )

        return [
            (i, j)
            for (i, j) in indexes
            if i in range(4)
            and j in range(4)
            and self.view.nested_children[i][j].style != self.selected_style
        ]

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
        button_style: discord.ButtonStyle = discord.ButtonStyle.gray,
        selected_style: discord.ButtonStyle = discord.ButtonStyle.green,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        """
        starts the boggle game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        button_style : discord.ButtonStyle, optional
            the primary button style to use, by default discord.ButtonStyle.gray
        selected_style : discord.ButtonStyle, optional
            the button style to use for selected tiles, by default discord.ButtonStyle.green
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.embed_color = embed_color

        self.button_style = button_style
        self.selected_style = selected_style
        self.player = ctx.author

        self.view = BoggleView(self, timeout=timeout)
        self.message = await ctx.send(view=self.view, embed=self.get_embed())

        await self.view.wait()
        return self.message

from __future__ import annotations

from typing import Optional, Final
import random
import string
import asyncio

import discord
from discord.ext import commands
from english_words import english_words_lower_alpha_set

from .utils import DiscordColor, DEFAULT_COLOR

BLANK: Final[str] = "  \u200b"
STAGES: Final[tuple[str, ...]] = (
    """
            _________\t
            |/      |\t
            |      😵\t
            |      \\|/\t
            |       |\t
            |      / \\\t
         ___|___
            """,
    """
            _________\t
            |/      |\t
            |      😦\t
            |      \\|/\t
            |       |\t
            |      /\t
         ___|___
            """,
    """
            _________\t
            |/      |\t
            |      😦\t
            |      \\|/\t
            |       |\t
            |
         ___|___
            """,
    """
            --------\t
            |/     |\t
            |     😦\t
            |     \\|\t
            |      |\t
            |
         ___|___
            """,
    """
            _________\t
            |/      |\t
            |      😦\t
            |       |\t
            |       |\t
            |
         ___|___
            """,
    """
            _________\t
            |/      |\t
            |      😦\t
            |
            |
            |
         ___|___
            """,
    """
            _________\t
            |/      |\t
            |
            |
            |
            |
         ___|___
            """,
    """
            _________\t
            |/
            |
            |
            |
            |
         ___|___
            """,
    """
            ___      \t
            |/
            |
            |
            |
            |
         ___|___
            """,
)


class Hangman:
    """
    Hangman Game
    """

    def __init__(self, word: Optional[str] = None) -> None:
        self._alpha: list[str] = list(string.ascii_lowercase)
        self._all_words = tuple(english_words_lower_alpha_set)

        if word:
            if not word.isalpha():
                raise ValueError("Word must be an alphabetical string")

            self.word = word
        else:
            self.word = self.get_word()

        self.letters: tuple[str, ...] = tuple(self.word)

        self.correct: list[str] = [r"\_" for _ in self.word]
        self.wrong_letters: list[str] = []

        self.embed: discord.Embed = discord.Embed(title="HANGMAN")
        self.message: Optional[discord.Message] = None
        self._counter: int = 8

        self.game_over: bool = False

    def get_word(self) -> str:
        word = random.choice(self._all_words).lower()
        if len(word) == 1:
            word = self.get_word()
        return word

    def lives(self) -> str:
        return f"`{('❤️' * self._counter) or '💀'} ({self._counter})`"

    async def make_guess(self, guess: str) -> None:

        if guess == self.word:
            self.game_over = True
            self.embed.set_field_at(0, name="Word", value=self.word)
            await self.message.edit(content="**YOU WON**", embed=self.embed)

        elif guess in self.letters:
            self._alpha.remove(guess)
            matches = [a for a, b in enumerate(self.letters) if b == guess]

            for match in matches:
                self.correct[match] = guess

            self.embed.set_field_at(0, name="Word", value=f"{' '.join(self.correct)}")
            await self.message.edit(embed=self.embed)
        else:
            if len(guess) == 1:
                self._alpha.remove(guess)
                self.wrong_letters.append(guess)

            self._counter -= 1

            self.embed.set_field_at(
                1,
                name="Wrong letters",
                value=f"{', '.join(self.wrong_letters) or BLANK}",
            )
            self.embed.set_field_at(
                2, name="Lives left", value=self.lives(), inline=False
            )
            self.embed.description = f"```\n{STAGES[self._counter]}\n```"
            await self.message.edit(embed=self.embed)

    async def check_win(self) -> bool:

        if self._counter == 0:
            self.game_over = True
            self.embed.set_field_at(0, name="Word", value=self.word)
            await self.message.edit(content="**YOU LOST**", embed=self.embed)

        elif r"\_" not in self.correct:
            self.game_over = True
            self.embed.set_field_at(0, name="Word", value=self.word)
            await self.message.edit(content="**YOU WON**", embed=self.embed)

        return self.game_over

    def initialize_embed(self) -> discord.Embed:
        self.embed.description = f"```\n{STAGES[self._counter]}\n```"
        self.embed.color = self.embed_color
        self.embed.add_field(name="Word", value=f"{' '.join(self.correct)}")

        wrong_letters = ", ".join(self.wrong_letters) or BLANK
        self.embed.add_field(name="Wrong letters", value=wrong_letters)
        self.embed.add_field(name="Lives left", value=self.lives(), inline=False)
        return self.embed

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        timeout: Optional[float] = None,
        embed_color: DiscordColor = DEFAULT_COLOR,
        delete_after_guess: bool = False,
        **kwargs,
    ) -> discord.Message:
        """
        starts the hangman game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        timeout : Optional[float], optional
            the timeout for when waiting, by default None
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        delete_after_guess : bool, optional
            specifies whether or not to delete the guess after each time, by default False

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.player = ctx.author
        self.embed_color = embed_color
        embed = self.initialize_embed()

        self.message = await ctx.send(embed=embed, **kwargs)

        while not ctx.bot.is_closed():

            def check(m: discord.Message) -> bool:
                if m.channel == ctx.channel and m.author == self.player:
                    return (
                        len(m.content) == 1 and m.content.lower() in self._alpha
                    ) or (m.content.lower() == self.word)

            try:
                message: discord.Message = await ctx.bot.wait_for(
                    "message", timeout=timeout, check=check
                )
            except asyncio.TimeoutError:
                break

            await self.make_guess(message.content.lower())
            gameover = await self.check_win()

            if gameover:
                break

            if delete_after_guess:
                try:
                    await message.delete()
                except discord.DiscordException:
                    pass
        return self.message

from __future__ import annotations

from typing import Optional, ClassVar, Any
from enum import Enum
import asyncio

import discord
from discord.ext import commands

from akinator import (
    AsyncAkinator as AkinatorGame,
    CantGoBackAnyFurther,
    Language,
    Answer,
    Theme,
)

from .utils import DiscordColor, DEFAULT_COLOR

BACK = "◀️"
STOP = "⏹️"


class Options(Enum):
    yes = "✅"
    no = "❌"
    idk = "🤷"
    p = "🤔"
    pn = "😕"


class Akinator:
    """
    Akinator Game, utilizes reactions
    """

    BAR: ClassVar[str] = "██"
    instructions: ClassVar[str] = (
        "✅ 🠒 `yes`\n"
        "❌ 🠒 `no`\n"
        "🤷 🠒 `I dont know`\n"
        "🤔 🠒 `probably`\n"
        "😕 🠒 `probably not`\n"
    )

    def __init__(self) -> None:
        self.aki: AkinatorGame = AkinatorGame()

        self.player: Optional[discord.User] = None
        self.win_at: Optional[int] = None
        self.guess: Optional[dict[str, Any]] = None
        self.message: Optional[discord.Message] = None

        self.embed_color: Optional[DiscordColor] = None
        self.back_button: bool = False
        self.delete_button: bool = False

        self.bar: str = ""

    def build_bar(self) -> str:
        prog = round(self.aki.progression / 8)
        self.bar = f"[`{self.BAR * prog}{'  ' * (10 - prog)}`]"
        return self.bar

    def build_embed(self, *, instructions: bool = True) -> discord.Embed:

        embed = discord.Embed(
            title="Guess your character!",
            description=(
                "```swift\n"
                f"Question-Number  : {self.aki.step + 1}\n"
                f"Progression-Level: {self.aki.progression:.2f}\n```\n"
                f"{self.build_bar()}"
            ),
            color=self.embed_color,
        )
        embed.add_field(name="- Question -", value=self.aki.question)

        if instructions:
            embed.add_field(name="\u200b", value=self.instructions, inline=False)

        embed.set_footer(text="Figuring out the next question | This may take a second")
        return embed

    async def win(self) -> discord.Embed:

        await self.aki.win()
        self.guess = self.aki.first_guess

        embed = discord.Embed(color=self.embed_color)
        embed.title = "Character Guesser Engine Results"
        embed.description = f"Total Questions: `{self.aki.step + 1}`"

        embed.add_field(
            name="Character Guessed",
            value=f"\n**Name:** {self.guess.name}\n{self.guess.description}",
        )

        embed.set_image(url=self.guess.absolute_picture_path)
        embed.set_footer(text="Was I correct?")

        return embed

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
        remove_reaction_after: bool = False,
        win_at: int = 80,
        timeout: Optional[float] = None,
        back_button: bool = False,
        delete_button: bool = False,
        aki_theme: str = "Characters",
        aki_language: str = "English",
        child_mode: bool = True,
    ) -> Optional[discord.Message]:
        """
        starts the akinator game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        remove_reaction_after : bool, optional
            indicates whether to remove the user's reaction after or not, by default False
        win_at : int, optional
            indicates when to tell the akinator to make it's guess, by default 80
        timeout : Optional[float], optional
            indicates the timeout for when waiting, by default None
        back_button : bool, optional
            indicates whether to add a back button, by default False
        delete_button : bool, optional
            indicates whether to add a stop button to stop the game, by default False
        child_mode : bool, optional
            indicates to filter out NSFW content or not, by default True

        Returns
        -------
        Optional[discord.Message]
            returns the game message
        """

        self.back_button = back_button
        self.delete_button = delete_button
        self.embed_color = embed_color
        self.player = ctx.author
        self.win_at = win_at

        if self.back_button:
            self.instructions += f"{BACK} 🠒 `back`\n"

        if self.delete_button:
            self.instructions += f"{STOP} 🠒 `cancel`\n"

        self.aki.theme = Theme.from_str(aki_theme)
        self.aki.language = Language.from_str(aki_language)
        self.aki.child_mode = child_mode
        await self.aki.start_game()

        embed = self.build_embed()
        self.message = await ctx.send(embed=embed)

        for button in Options:
            await self.message.add_reaction(button.value)

        if self.back_button:
            await self.message.add_reaction(BACK)

        if self.delete_button:
            await self.message.add_reaction(STOP)

        while self.aki.progression <= self.win_at:

            def check(reaction: discord.Reaction, user: discord.User) -> bool:
                emoji = str(reaction.emoji)
                if reaction.message == self.message and user == ctx.author:
                    try:
                        return bool(Options(emoji))
                    except ValueError:
                        return emoji in (BACK, STOP)

            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add", timeout=timeout, check=check
                )
            except asyncio.TimeoutError:
                return

            if remove_reaction_after:
                try:
                    await self.message.remove_reaction(reaction, user)
                except discord.DiscordException:
                    pass

            emoji = str(reaction.emoji)

            if emoji == STOP:
                await ctx.send("**Session ended**")
                return await self.message.delete()

            if emoji == BACK:
                try:
                    await self.aki.back()
                except CantGoBackAnyFurther:
                    await self.message.reply(
                        "I cannot go back any further", delete_after=10
                    )
            else:
                answer = Answer.from_str(Options(emoji).name)
                await self.aki.answer(answer)

            embed = self.build_embed()
            await self.message.edit(embed=embed)

        embed = await self.win()
        return await self.message.edit(embed=embed)

from __future__ import annotations

from typing import Optional, ClassVar, Any
from enum import Enum
import asyncio

import discord
from discord.ext import commands
from akinator.async_aki import Akinator as AkinatorGame

from .utils import DiscordColor, DEFAULT_COLOR

class Options(Enum):
    yes = "✅"
    no = "❌"
    idk = "🤷"
    p = "🤔"
    pn  = "😕"
    stop = "⏹️"

class Akinator:
    BAR: ClassVar[str] = "██"
    INSTRUCTIONS: ClassVar[str] = (
        '✅ 🠒 `yes`\n'
        '❌ 🠒 `no`\n'
        '🤷 🠒 `I dont know`\n'
        '🤔 🠒 `probably`\n'
        '😕 🠒 `probably not`\n'
        '⏹️ 🠒 `cancel`\n'
    )

    def __init__(self) -> None:
        self.aki: AkinatorGame = AkinatorGame()

        self.player: Optional[discord.Member] = None
        self.win_at: Optional[int] = None
        self.guess: Optional[dict[str, Any]] = None
        self.message: Optional[discord.Message] = None

        self.embed_color: Optional[DiscordColor] = None
        self.delete_button: bool = False
        
        self.bar: str = ''
        self.questions: int = 0

    def build_bar(self) -> str:
        prog = round(self.aki.progression / 8)
        self.bar = f"[`{self.BAR * prog}{'  ' * (10 - prog)}`]"
        return self.bar

    def build_embed(self, *, instructions: bool = True) -> discord.Embed:

        embed = discord.Embed(
            title = "Guess your character!", 
            description = (
                "```swift\n"
                f"Question-Number  : {self.questions}\n"
                f"Progression-Level: {self.aki.progression:.2f}\n```\n"
                f"{self.build_bar()}"
            ), 
            color = self.embed_color,
        )
        embed.add_field(name="- Question -", value=self.aki.question)
        
        if instructions:
            embed.add_field(name="\u200b", value=self.INSTRUCTIONS, inline=False)

        embed.set_footer(text= "Figuring out the next question | This may take a second")
        return embed

    async def win(self) -> discord.Embed:

        await self.aki.win()
        self.guess = self.aki.first_guess

        embed = discord.Embed(color=self.embed_color)
        embed.title = "Character Guesser Engine Results"
        embed.description = f"Total Questions: `{self.questions}`"

        embed.add_field(name="Character Guessed", value=f"\n**Name:** {self.guess['name']}\n{self.guess['description']}")

        embed.set_image(url=self.guess['absolute_picture_path'])
        embed.set_footer(text="Was I correct?")

        return embed

    async def start(
        self, 
        ctx: commands.Context,
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
        remove_reaction_after: bool = False, 
        win_at: int = 80, 
        timeout: Optional[float] = None, 
        delete_button: bool = False, 
        child_mode: bool = True, 
    ) -> Optional[discord.Message]:
        
        self.delete_button = delete_button
        self.embed_color = embed_color
        self.player = ctx.author
        self.win_at = win_at

        await self.aki.start_game(child_mode=child_mode)

        embed = self.build_embed()
        self.message = await ctx.send(embed=embed)

        for button in Options:
            await self.message.add_reaction(button.value)

        if self.delete_button:
            await self.message.add_reaction(Options.stop.value)

        while self.aki.progression <= self.win_at:

            def check(reaction: discord.Reaction, user: discord.Member) -> bool:
                emoji = str(reaction.emoji)
                if reaction.message == self.message and user == ctx.author:
                    try:
                        return bool(Options(emoji))
                    except ValueError:
                        return False

            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            except asyncio.TimeoutError:
                return

            if remove_reaction_after:
                try:
                    await self.message.remove_reaction(reaction, user)
                except discord.DiscordException:
                    pass

            emoji = str(reaction.emoji)

            if emoji == Options.stop.value:
                await ctx.send("**Session ended**")
                return await self.message.delete()
            else:
                self.questions += 1

                await self.aki.answer(Options(emoji).name)
                
                embed = self.build_embed()
                await self.message.edit(embed=embed)
            
        embed = await self.win()
        return await self.message.edit(embed=embed)
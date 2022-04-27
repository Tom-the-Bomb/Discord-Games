from __future__ import annotations

from typing import Optional, Union
import asyncio

import discord
from discord.ext import commands
from akinator.async_aki import Akinator as Akinator_


class Options:
    YES = "✅"
    NO = "❌"
    IDK = "🤷"
    PY = "🤔"
    PN  = "😔"
    STOP = "⏹️"

class Akinator:

    def __init__(self) -> None:
        self.player: Optional[discord.Member] = None
        self.win_at: Optional[int] = None
        self.aki: Akinator_ = Akinator_()
        self.bar_emojis: tuple[str, str] = ("  ", "██")
        self.guess = None
        self.bar: str = ""
        self.message: Optional[discord.Message] = None
        self.questions: int = 0

        self.mapping: dict[str, str] = {
            Options.YES: "y", 
            Options.NO : "n", 
            Options.IDK: "i", 
            Options.PY : "p", 
            Options.PN : "pn"
        }

    def build_bar(self) -> str:
        prog = round(self.aki.progression/8)
        emp, full = self.bar_emojis
        self.bar = f"[`{full*prog}{emp*(10-prog)}`]"
        return self.bar

    async def build_embed(self) -> discord.Embed:

        embed = discord.Embed(
            title = "Guess your character!", 
            description = (
                "```swift\n"
                f"Question-Number  : {self.questions}\n"
                f"Progression-Level: {self.aki.progression:.2f}\n```\n"
                f"{self.build_bar()}"
            ), 
            color = discord.Color.random()
        )
        embed.add_field(name= "- Question -", value= self.aki.question)
        embed.set_footer(text= "Figuring out the next question | This may take a second")
        return embed

    async def win(self) -> discord.Embed:

        await self.aki.win()
        self.guess = self.aki.first_guess

        embed = discord.Embed(color=self.embed_color)
        embed.title = "Character Guesser Engine Results"
        embed.description = f"Total Questions: `{self.questions}`"
        embed.add_field(name= "Character Guessed", value=f"\n**Name:** {self.guess['name']}\n{self.guess['description']}")
        embed.set_image(url=  self.guess['absolute_picture_path'])
        embed.set_footer(text="Was I correct?")

        return embed

    async def start(
        self, 
        ctx: commands.Context,
        *,
        embed_color: Union[discord.Color, int] = 0x2F3136,
        remove_reaction_after: bool = False, 
        win_at: int = 80, 
        timeout: int = None, 
        delete_button: bool = False, 
        child_mode: bool = True, 
    ) -> Optional[discord.Message]:
        
        self.embed_color = embed_color
        self.player = ctx.author
        self.win_at = win_at

        await self.aki.start_game(child_mode=child_mode)

        embed = await self.build_embed()
        self.message = await ctx.send(embed=embed)

        for button in self.mapping:
            await self.message.add_reaction(button)

        if delete_button:
            await self.message.add_reaction(Options.STOP)

        while self.aki.progression <= self.win_at:

            def check(reaction: discord.Reaction, user: discord.Member) -> bool:
                if reaction.message == self.message and user == ctx.author:
                    return str(reaction.emoji) in self.mapping or str(reaction.emoji) == Options.STOP

            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            except asyncio.TimeoutError:
                return

            if remove_reaction_after:
                await self.message.remove_reaction(reaction, user)

            emoji = str(reaction.emoji)

            if emoji == Options.STOP:
                await ctx.send("Session ended")
                return await self.message.delete()

            self.questions += 1

            await self.aki.answer(self.mapping[emoji])
            try:
                await self.message.remove_reaction(emoji, ctx.author)
            except discord.DiscordException:
                pass
            
            embed = await self.build_embed()
            await self.message.edit(embed=embed)
            
        embed = await self.win()
        return await self.message.edit(embed=embed)
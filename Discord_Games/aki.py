import akinator
import asyncio
from   akinator.async_aki import Akinator as _Akinator_

import discord
from   discord.ext import commands

YES  = "✅"
NO   = "❌"
IDK  = "🤷"
P    = "🤔"
PN   = "😔"
STOP = "⏹️"

class Akinator:

    def __init__(self):
        self.aki     = _Akinator_()
        self.bar_emojis = ("  ", "██")
        self.guess   = None
        self.bar     = ""
        self.message = None
        self.questions = 0
        self.mapping = {
            YES: "y", 
            NO : "n", 
            IDK: "i", 
            P  : "p", 
            PN : "pn"
        }

    def build_bar(self) -> str:
        prog = round(self.aki.progression/8)
        emp, full = self.bar_emojis
        self.bar  = f"[`{full*prog}{emp*(10-prog)}`]"
        return self.bar

    async def build_embed(self) -> discord.Embed:

        embed = discord.Embed(
            title = "Guess your character!", 
            description = (
                f"Question number `{self.questions}`\n"
                f"Progression-Level: `{self.aki.progression}`\n"
                f"{self.build_bar()}"
            ), 
            color = discord.Color.random()
        )
        embed.add_field(name= "- Question -", value= self.aki.question)
        embed.set_footer(text= "Figuring out the next question | This may take a second")
        return embed

    async def win(self):

        await self.aki.win()
        self.guess = self.aki.first_guess

        embed       = discord.Embed()
        embed.title = "Character Guesser Engine Results"
        embed.description = f"Total Questions: `{self.questions}`"
        embed.add_field(name= "Character Guessed", value=f"\n**Name:** {self.guess['name']}\n{self.guess['description']}")
        embed.set_image(url=  self.guess['absolute_picture_path'])
        embed.set_footer(text="Was I correct?")

        return embed

    async def start(self, ctx: commands.Context, remove_reaction_after: bool = False, win_at_: int = 80, timeout: int = None, delete_button: bool = False, child_mode: bool = True, **kwargs):

        await self.aki.start_game(child_mode=child_mode)

        embed = await self.build_embed()
        self.message = await ctx.send(embed=embed)

        for button in self.mapping:
            await self.message.add_reaction(button)
        if delete_button:
            await self.message.add_reaction(STOP)

        while self.aki.progression <= win_at_:

            def check(reaction, user):
                return str(reaction.emoji) in self.mapping and reaction.message == self.message and user == ctx.author

            try:
                reaction, __ = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            except asyncio.TimeoutError:
                return
            
            emoji = str(reaction.emoji)

            if emoji == STOP:
                await ctx.send("Session ended")
                return await self.message.delete()

            self.questions += 1

            await self.aki.answer(self.mapping[emoji])
            try:
                await self.message.remove_reaction(emoji, ctx.author)
            except:
                pass
            
            embed = await self.build_embed()
            await self.message.edit(embed=embed)
            
        embed = await self.win()
        return await self.message.edit(embed=embed)
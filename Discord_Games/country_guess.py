
from typing import Union, Optional
import os
import pathlib
import random
import difflib

import discord
from discord.ext import commands

class CountryGuesser:
    country: str

    def __init__(self, *, guesses: int = 5, hint: bool = True) -> None:
        self.has_hint = hint
        self.guesses = guesses

    def get_blanks(self) -> str:
        return ' '.join('_' if char != ' ' else ' ' for char in self.country)

    def get_hint(self) -> str:
        blanks = ['_' if char != ' ' else ' ' for char in self.country]
        times = round(len(blanks) / 3)

        for _ in range(times):
            idx = random.choice(range(len(self.country)))
            blanks[idx] = self.country[idx]
        return ' '.join(blanks)

    def get_accuracy(self, guess: str) -> int:
        return round(difflib.SequenceMatcher(None, guess, self.country).ratio() * 100)

    async def wait_for_response(
        self, 
        ctx: commands.Context, 
        *, 
        options: tuple[str, ...] = (), 
        length: Optional[int] = None,
    ) -> Optional[tuple[discord.Message, str]]:

        def check(m: discord.Message) -> bool:
            if length:
                return m.channel == ctx.channel and m.author == ctx.author and len(m.content) == length
            else:
                return m.channel == ctx.channel and m.author == ctx.author

        message: discord.Message = await ctx.bot.wait_for('message', check=check)
        content = message.content.strip().lower()

        if options:
            if not content in options:
                return
            
        return message, content

    async def start(
        self, 
        ctx: commands.Context, 
        *, 
        embed_color: Union[discord.Color, int] = 0x2F3136,
        ignore_diff_len: bool = False
    ) -> discord.Message:
        
        data_path = fr'{pathlib.Path(__file__).parent}\assets\country-data'
        countries = os.listdir(data_path)

        country_file = random.choice(countries)
        self.country = country_file.strip().removesuffix('.png').lower()

        country_file = discord.File(os.path.join(data_path, country_file), 'country.png')

        embed = discord.Embed(
            title='Guess that country!',
            description=f'```\u001b[0;37m\n{self.get_blanks()}\n```',
            color=embed_color,
        )
        embed.set_footer(text='send your guess into the chat now!')
        embed.set_image(url='attachment://country.png')
        await ctx.send(embed=embed, file=country_file)

        length = len(self.country) if ignore_diff_len else None

        while self.guesses > 0:

            msg, response = await self.wait_for_response(ctx, length=length)

            if response == self.country:
                return await msg.reply(f'That is correct! The country was `{self.country.title()}`')
            else:
                self.guesses -= 1
                acc = self.get_accuracy(response)

                if not self.has_hint:
                    await msg.reply(f'That was incorrect! but you are `{acc}%` of the way there!\nYou have **{self.guesses}** guesses left.', mention_author=False)
                else:
                    await msg.reply(f'That is incorrect! but you are `{acc}%` of the way there!\nWould you like a hint? type: `(y/n)`', mention_author=False)

                    hint_msg, resp = await self.wait_for_response(ctx, options=('y', 'n'))
                    if resp == 'y':
                        hint = self.get_hint()
                        self.has_hint = False
                        await hint_msg.reply(f'Here is your hint: `{hint}`', mention_author=False)
                    else:
                        await hint_msg.reply(f'Okay continue guessing! You have **{self.guesses}** guesses left.', mention_author=False)
        
        return await msg.reply(f'Game Over! you lost, The country was `{self.country.title()}`')
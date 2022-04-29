
from typing import Union, Optional
import os
import pathlib
import random
import difflib

import discord
from discord.ext import commands

class CountryGuesser:
    country: str

    def __init__(self) -> None:
        self.hints: int = 0
        self.guesses: int = 5

    def get_blanks(self) -> str:
        return ' '.join('_' if char != ' ' else ' ' for char in self.country)

    def get_hint(self) -> str:
        blanks = self.get_blanks()
        times = int(len(blanks.split()) / 3)

        for i in range(times):
            idx = random.choice(range(len(self.country)))
            blanks[idx] = self.country[idx]
        return blanks

    def get_accuracy(self, guess: str) -> int:
        return difflib.SequenceMatcher(None, guess, self.country).ratio() * 100

    async def wait_for_response(self, ctx: commands.Context, options: tuple[str, ...] = ()) -> Optional[tuple[discord.Message, str]]:

        def check(m: discord.Message) -> bool:
            return m.channel == ctx.channel and m.author == ctx.author

        message: discord.Message = await ctx.bot.wait_for('message', check=check)
        content = message.content.strip().lower()

        if options:
            if not content in options:
                return
            
        return message, content

    async def start(self, ctx: commands.Context, *, embed_color: Union[discord.Color, int] = 0x2F3136) -> discord.Message:
        
        data_path = fr'{pathlib.Path(__file__).parent}\assets\country-data'
        countries = os.listdir(data_path)

        country_file = random.choice(countries)
        self.country = country_file.strip().removesuffix('.png').lower()

        country_file = discord.File(os.path.join(data_path, country_file), 'country.png')

        embed = discord.Embed(
            title='Guess that country!',
            description=self.get_blanks(),
            color=embed_color,
        )
        message = await ctx.send(embed=embed, file=country_file)

        while self.guesses > 0:

            msg, response = await self.wait_for_response(ctx)

            if response == self.country:
                return await msg.reply(f'That is correct! The country was {self.country.title()}')
            else:
                self.guesses -= 1
                acc = self.get_accuracy(response)

                if self.hints:
                    await msg.reply(f'That is incorrect! but you are `{acc}%` of the way there!\nWould you like a hint? type: `(y/n)`', mention_author=False)
                else:
                    await msg.reply(f'That was incorrect! but you are `{acc}%` of the way there!\nYou have **{self.guesses}** guesses left.', mention_author=False)

                hint_msg, resp = await self.wait_for_response(ctx, options=('y', 'n'))
                if resp == 'y':
                    hint = self.get_hint()
                    await hint_msg.reply(f'Here is your hint: `{hint}`', mention_author=False)
                else:
                    await hint_msg.reply(f'Okay continue guessing! You have **{self.guesses}** guesses left.', mention_author=False)
        
        return await msg.reply(f'Game Over! you lost, The country wwas `{self.country}`')
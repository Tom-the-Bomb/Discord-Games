from __future__  import annotations
from typing import Optional

import pathlib
import random
from io import BytesIO

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from .utils import *

BORDER = 40
SQ = 100  
SPACE = 10

WIDTH = BORDER * 2 + SQ * 5 + SPACE * 4
HEIGHT = BORDER * 2 + SQ * 6 + SPACE * 5

GRAY = (119, 123, 125)
ORANGE = (200, 179, 87)
GREEN = (105, 169, 99)

class Wordle:

    def __init__(self) -> None:
        self.embed_color: Optional[DiscordColor] = None

        self._valid_words = tuple(
            open(fr'{pathlib.Path(__file__).parent}\assets\words.txt', 'r').read().splitlines()
        )
        self._font = ImageFont.truetype('arial.ttf', 70)
        self.guesses: list[list[dict[str, str]]] = []
        self.word: str = random.choice(self._valid_words)

    def parse_guess(self, guess: str) -> bool:
        self.guesses.append([])
        for ind, l in enumerate(guess):
            if l in self.word:
                color = GREEN if self.word[ind] == l else ORANGE
            else:
                color = GRAY
            self.guesses[-1].append({'letter': l, 'color': color})

        return guess == self.word

    @executor()
    def render_image(self) -> BytesIO:
        with Image.new('RGB', (WIDTH, HEIGHT), (255, 255, 255)) as img:
            cursor = ImageDraw.Draw(img)

            x = y = BORDER
            for i in range(6):
                for j in range(5):
                    try:
                        letter = self.guesses[i][j]
                        color = letter['color']
                        act_letter = letter['letter']
                    except (IndexError, KeyError):
                        cursor.rectangle((x, y, x+SQ, y+SQ), outline='gray', width=2)
                    else:
                        cursor.rectangle((x, y, x+SQ, y+SQ), width=0, fill=color)
                        cursor.text((x+SQ/2, y+SQ/2), act_letter, font=self._font, anchor='mm', fill=(255, 255, 255))

                    x += SQ + SPACE
                x = BORDER
                y += SQ + SPACE
        
            buf = BytesIO()
            img.save(buf, 'PNG')
        buf.seek(0)
        return buf

    async def start(self, ctx: commands.Context, *, embed_color: DiscordColor = DEFAULT_COLOR) -> Optional[discord.Message]:

        self.emebd_color = embed_color

        buf = await self.render_image()

        embed = discord.Embed(title='Wordle!', color=self.color)
        embed.set_image(url='attachment://wordle.png')

        message = await ctx.send(embed=embed, file=discord.File(buf, 'wordle.png'))
        
        while True:
            
            def check(m):
                return len(m.content) == 5 and m.author == ctx.author and m.channel == ctx.channel
            
            guess: discord.Message = await ctx.bot.wait_for('message', check=check)
            content = guess.content.lower()

            if content not in self._valid_words:
                await ctx.send('That is not a valid word!')
            else:
                won = self.parse_guess(content)
                buf = await self.render_image()

                await message.delete()

                embed = discord.Embed(title='Wordle!', color=self.embed_color)
                embed.set_image(url='attachment://wordle.png')

                message = await ctx.send(embed=embed, file=discord.File(buf, 'wordle.png'))

                if won:
                    return await ctx.send('Game Over! You won!')
                elif len(self.guesses) >= 6:
                    return await ctx.send(f'Game Over! You lose, the word was: **{self.word}**')
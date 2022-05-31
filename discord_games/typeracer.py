from __future__ import annotations

from typing import Optional, ClassVar, TypedDict
from datetime import datetime as dt
from io import BytesIO

import textwrap
import time
import random
import asyncio
import aiohttp
import difflib
import pathlib

from PIL import Image, ImageDraw, ImageFont
import discord
from discord.ext import commands

from .utils import *

class UserData(TypedDict):
    user: discord.Member
    time: float
    wpm: float 
    acc: float

class TypeRacer:
    """
    TypeRace Game
    """
    SENTENCE_URL: ClassVar[str] = 'https://api.quotable.io/random'
    SHORT_WORDS: ClassVar[tuple[str, ...]] = (
        'the', 'of', 'to', 'and', 'a', 'in', 'is', 'it',
        'you', 'that', 'he', 'was', 'for', 'on', 'are',
        'with', 'as', 'his', 'they', 'be', 'at', 'one',
        'have', 'this', 'from', 'or', 'had', 'by', 'not',
        'word', 'but', 'what', 'some', 'we', 'can', 'out',
        'other', 'were', 'all', 'there', 'when', 'up', 'use',
        'your', 'how', 'said', 'an', 'each', 'she', 'which',
        'do', 'their', 'time', 'if', 'will', 'way', 'about',
        'many', 'then', 'them', 'write', 'would', 'like', 'so',
        'these', 'her', 'long', 'make', 'thing', 'see', 'him',
        'two', 'has', 'look', 'more', 'day', 'could', 'go', 'come',
        'did', 'number', 'sound', 'no', 'most', 'people', 'my',
        'over', 'know', 'water', 'than', 'call', 'first', 'who',
        'may', 'down', 'side', 'been', 'now', 'find', 'any', 'new',
        'work', 'part', 'take', 'get', 'place', 'made', 'live',
        'where', 'after', 'back', 'little', 'only', 'round', 'man',
        'year', 'came', 'show', 'every', 'good', 'me', 'give', 'our',
        'under', 'name', 'very', 'through', 'just', 'form', 'sentence',
        'great', 'think', 'say', 'help', 'low', 'line', 'differ', 'turn',
        'cause', 'much', 'mean', 'before', 'move', 'right', 'boy', 'old',
        'too', 'same', 'tell', 'does', 'set', 'three', 'want', 'air', 'well',
        'also', 'play', 'small', 'end', 'put', 'home', 'read', 'hand', 'port',
        'large', 'spell', 'add', 'even', 'land', 'here', 'must', 'big', 'high',
        'such', 'follow', 'act', 'why', 'ask', 'men', 'change', 'went', 'light',
        'kind', 'off', 'need', 'house', 'picture', 'try', 'us', 'again', 'animal',
        'point', 'mother', 'world', 'near', 'build', 'self', 'earth', 'father', 'head',
        'stand', 'own', 'page', 'should', 'country', 'found', 'answer', 'school',
        'grow', 'study', 'still', 'learn', 'plant', 'cover', 'food', 'sun', 'four',
        'between', 'state', 'keep', 'eye', 'never', 'last', 'let', 'thought', 'city',
        'tree', 'cross', 'farm', 'hard', 'start', 'might', 'story', 'saw', 'far',
        'sea', 'draw', 'left', 'late', 'run', "don't", 'while', 'press', 'close',
        'night', 'real', 'life', 'few', 'north'
    )
    EMOJI_MAP: ClassVar[dict[int, str]] = {
        1: "🥇", 
        2: "🥈", 
        3: "🥉",
    }

    @executor()
    def _tr_img(self, text: str, font: str) -> BytesIO:

        text = "\n".join(textwrap.wrap(text, width=25))

        font = ImageFont.truetype(font, 30)
        x, y = font.getsize_multiline(text)

        with Image.new("RGB", (x+20, y+30), (0, 0, 30)) as image:
            cursor = ImageDraw.Draw(image)
            cursor.multiline_text((10, 10), text, font=font, fill=(220, 200, 220))

            buffer = BytesIO()
            image.save(buffer, "PNG")
            buffer.seek(0)
            return buffer

    def format_line(self, i: int, data: UserData) -> str:
        return f" • {self.EMOJI_MAP[i]} | {data['user'].mention} in {data['time']:.2f}s | **WPM:** {data['wpm']:.2f} | **ACC:** {data['acc']:.2f}%"

    async def wait_for_tr_response(self, ctx: commands.Context[commands.Bot], text: str, *, timeout: float) -> discord.Message:

        self.embed.description = ""

        text = text.lower().replace("\n", " ")
        winners = []
        start = time.perf_counter()

        while not ctx.bot.is_closed():

            def check(m: discord.Message) -> bool:
                content = m.content.lower().replace("\n", " ")
                if m.channel == ctx.channel and not m.author.bot and m.author not in map(lambda m: m["user"], winners):
                    sim = difflib.SequenceMatcher(None, content, text).ratio()
                    return sim >= 0.9

            try:
                message: discord.Message = await ctx.bot.wait_for("message", timeout=timeout, check=check)
            except asyncio.TimeoutError:
                if winners:
                    break
                else:
                    return await ctx.reply("Looks like no one responded", allowed_mentions=discord.AllowedMentions.none())

            end = time.perf_counter()
            content = message.content.lower().replace("\n", " ")
            timeout -= round(end - start)

            winners.append({
                "user": message.author, 
                "time": end - start, 
                "wpm" : len(text.split()) / ((end - start) / 60), 
                "acc" : difflib.SequenceMatcher(None, content, text).ratio() * 100
            })

            self.embed.description += self.format_line(len(winners), winners[len(winners) - 1]) + "\n"
            await self.message.edit(embed=self.embed)

            await message.add_reaction(self.EMOJI_MAP[len(winners)])

            if len(winners) >= 3:
                break
        
        desc = [self.format_line(i, x) for i, x in enumerate(winners, 1)]
        embed = discord.Embed(
            title="Typerace results",
            color=self.embed_color, 
            timestamp=dt.utcnow()
        )
        embed.add_field(name="Winners", value="\n".join(desc))

        return await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    async def start(
        self, 
        ctx: commands.Context[commands.Bot], 
        *, 
        embed_title: str = 'Type the following sentence in the chat now!', 
        embed_color: DiscordColor = DEFAULT_COLOR, 
        path_to_text_font: Optional[str] = None,
        timeout: float = 40, 
        words_mode: bool = False,
        show_author: bool = True,
        max_quote_length: Optional[int] = None,
    ) -> discord.Message:
        """
        starts the typerace game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        embed_title : str, optional
            the title of the game embed, by default 'Type the following sentence in the chat now!'
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        path_to_text_font : Optional[str], optional
            path to the font you want to use for the image
            fallbacks to SegoeUI if not specified, by default None
        timeout : float, optional
            the game timeout, by default 40
        words_mode : bool, optional
            specifies whether or not to just use random words instead of a quote, by default False
        show_author : bool, optional
            specifies whether or not to show the command author in the embed, by default True
        max_quote_length : int, optional
            specifies the maximum length of the quote to truncate to if necessary, by default None

        Returns
        -------
        discord.Message
            the game message

        Raises
        ------
        RuntimeError
            requesting the quote failed
        """
        self.embed_color = embed_color

        if not words_mode:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.SENTENCE_URL) as r:
                    if r.ok:
                        text: dict = await r.json()
                        text = text.get('content', '')
                    else:
                        raise RuntimeError(f"HTTP request raised an error: {r.status}; {r.reason}")

        else:
            text = " ".join(random.choice(self.SHORT_WORDS).lower() for _ in range(15))

        if max_quote_length is not None:
            if len(text) > max_quote_length:
                text = textwrap.shorten(text, width=max_quote_length, placeholder='')

        if not path_to_text_font:
            path_to_text_font = str(pathlib.Path(__file__).parent / 'assets/segoe-ui-semilight-411.ttf')

        buffer = await self._tr_img(text, path_to_text_font)

        embed = discord.Embed(
            title=embed_title,
            color=self.embed_color, 
            timestamp=dt.utcnow()
        )
        embed.set_image(url="attachment://tr.png")

        if show_author:
            if discord.version_info.major >= 2:
                av = ctx.author.avatar.url
            else:
                av = ctx.author.avatar_url
            embed.set_author(name=ctx.author.name, icon_url=av)

        self.embed = embed
        self.message = await ctx.send(
            embed=embed,
            file=discord.File(buffer, "tr.png")
        )

        await self.wait_for_tr_response(ctx, text, timeout=timeout)
        return self.message
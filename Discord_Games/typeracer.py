import textwrap
import time
import random
import asyncio
import aiohttp

import discord
from PIL import Image, ImageDraw, ImageFont
from io  import BytesIO
from discord.ext import commands
from typing import Union, SupportsFloat
from datetime import datetime as dt
from math import ceil


class TypeRacer:

    SENTENCE_URL  = "https://api.quotable.io/random"
    GRAMMAR_WORDS = (
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

    def _tr_img(self, text: str, font: str):
        text = "\n".join(textwrap.wrap(text, width=25))
        height = ceil(len(text) / 25) * 50
        image  = Image.new("RGBA", (640, height), (10, 10, 10))
        font   = ImageFont.truetype(font, 40)

        draw  = ImageDraw.Draw(image)
        draw.text((5, 5), text, font=font, fill=(255,255,255))

        draw.line((220,0,220,height), fill=(180,180,180), width=1)
        draw.line((420,0,420,height), fill=(180,180,180), width=1)

        buffer = BytesIO()
        image.save(buffer, "png")
        buffer.seek(0)
        return buffer

    async def wait_for_tr_response(self, ctx: commands.Context, text: str, *, timeout: int, start):
        
        text = text.lower().replace("\n", " ").strip(".")

        try:
            message = await ctx.bot.wait_for(
                "message", 
                timeout=timeout, 
                check = lambda m: m.channel == ctx.channel and m.content.lower().replace("\n", " ").strip(".") == text
            )
        except asyncio.TimeoutError:
            return await ctx.reply("Looks like no one responded", allowed_mentions=discord.AllowedMentions.none())

        end = time.perf_counter()
        wpm = len(text.split(" ")) / ((end - start) / 60)
        
        embed = discord.Embed(
            description=f"`{message.author.name} won the typerace`\n**Time-took:** {(end - start):.2f} seconds\n**WPM:** {wpm:.2f}", 
            color = discord.Color.gold(), 
            timestamp = dt.utcnow()
        )

        await message.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        return True

    async def start(
        self, ctx: commands.Context, *, 
        embed_title: str = "Type the following sentence in the chat now!", 
        embed_color: Union[discord.Color, int] = discord.Color.greyple(), 
        path_to_text_font: str = "arial.ttf",
        timeout: SupportsFloat = None, 
        mode: str = "sentence"
    ):

        if  mode == "sentence":
            async with aiohttp.ClientSession() as session:
                async with session.get(self.SENTENCE_URL) as r:
                    if r.status in range(200, 299):
                        text = await r.json()
                        text = text["content"]
                    else:
                        return await ctx.send("Oops an error occured")
        elif mode == "random":
            text = " ".join([random.choice(self.GRAMMAR_WORDS).lower() for _ in range(15)])
        else:
            raise TypeError("Invalid game mode , must be either 'random' or 'sentence'")

        buffer = await ctx.bot.loop.run_in_executor(None, self._tr_img, text, path_to_text_font)

        embed  = discord.Embed(
            title = embed_title,
            color = embed_color, 
            timestamp = dt.utcnow()
        )
        embed.set_image(url="attachment://tr.png")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        await ctx.send(
            embed = embed,
            file  = discord.File(buffer, "tr.png")
        )

        start = time.perf_counter()
        await self.wait_for_tr_response(ctx, text, start=start, timeout=timeout)

        return True
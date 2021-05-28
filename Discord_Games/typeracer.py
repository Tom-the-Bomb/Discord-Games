import textwrap
import time
import random
import asyncio
import aiohttp
import difflib

import discord
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from discord.ext import commands
from typing import Union, Optional
from datetime import datetime as dt


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

    def _tr_img(self, text: str, font: str) -> BytesIO:
        text = "\n".join(textwrap.wrap(text, width=25))
        font = ImageFont.truetype(font, 30)
        x, y = font.getsize_multiline(text)
        image = Image.new("RGBA", (x+20, y+30), (0, 0, 30))

        cursor = ImageDraw.Draw(image)
        cursor.multiline_text((10, 10), text, font=font, fill=(220, 200, 220))

        buffer = BytesIO()
        image.save(buffer, "png")
        buffer.seek(0)
        return buffer

    async def wait_for_tr_response(self, ctx: commands.Context, text: str, *, timeout: int):
        
        emoji_map = {
            1: "🥇", 2: "🥈", 3: "🥉"
        }

        self._embed.description = ""
        format_line = lambda i, x: f" • {emoji_map[i]} | {x['user'].mention} in {x['time']:.2f}s | **WPM:** {x['wpm']:.2f} | **ACC:** {x['acc']:.2f}%"

        text = text.lower().replace("\n", " ")
        winners = []
        start = time.perf_counter()

        while True:

            def check(m):
                content = m.content.lower().replace("\n", " ")
                if m.channel == ctx.channel and not m.author.bot and m.author not in map(lambda m: m["user"], winners):
                    sim = difflib.SequenceMatcher(None, content, text).ratio()
                    return sim >= 0.9

            try:
                message = await ctx.bot.wait_for(
                    "message", 
                    timeout = timeout, 
                    check = check
                )
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
                "wpm" : len(text.split(" ")) / ((end - start) / 60), 
                "acc" : difflib.SequenceMatcher(None, content, text).ratio() * 100
            })

            self._embed.description += format_line(len(winners), winners[len(winners)-1]) + "\n"
            await self._message.edit(embed=self._embed)

            await message.add_reaction(emoji_map[len(winners)])

            if len(winners) >= 3:
                break
        
        desc = [format_line(i, x) for i, x in enumerate(winners, 1)]
        embed = discord.Embed(
            title = "Typerace results",
            color = 0x2F3136, 
            timestamp = dt.utcnow()
        )
        embed.add_field(name="Winners", value="\n".join(desc))

        await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        return True

    async def start(
        self, 
        ctx: commands.Context, *, 
        embed_title: Optional[str] = "Type the following sentence in the chat now!", 
        embed_color: Optional[Union[discord.Color, int]] = discord.Color.greyple(), 
        path_to_text_font: Optional[str] = "arial.ttf",
        timeout: Optional[float] = None, 
        mode: Optional[str] = "sentence",
        show_author: Optional[bool] = True
    ):

        if mode == "sentence":
            async with aiohttp.ClientSession() as session:
                async with session.get(self.SENTENCE_URL) as r:
                    if r.ok:
                        text = await r.json()
                        text = text.get("content")
                    else:
                        raise RuntimeError(f"ERROR: {r.status}, {r.reason}")
        elif mode == "random":
            text = " ".join([random.choice(self.GRAMMAR_WORDS).lower() for _ in range(15)])
        else:
            raise TypeError("Invalid game mode , must be either 'random' or 'sentence'")

        buffer = await ctx.bot.loop.run_in_executor(None, self._tr_img, text, path_to_text_font)

        embed = discord.Embed(
            title = embed_title,
            color = embed_color, 
            timestamp = dt.utcnow()
        )
        embed.set_image(url="attachment://tr.png")

        if show_author:
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        self._embed = embed
        self._message = await ctx.send(
            embed = embed,
            file = discord.File(buffer, "tr.png")
        )

        await self.wait_for_tr_response(ctx, text, timeout=timeout)
        return True
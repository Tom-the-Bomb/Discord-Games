from __future__ import annotations

from typing import Union, Optional, ClassVar, Literal
import asyncio

import discord
from discord.ext import commands
import chess

class Chess:
    BASE_URL: ClassVar[str] = 'http://www.fen-to-image.com/image/64/double/coords/'

    def __init__(self, *, white: discord.Member, black: discord.Member) -> None:
        self.white = white
        self.black = black
        self.turn = self.white

        self.winner: Optional[discord.Member] = None
        self.message: Optional[discord.Message] = None

        self.board: chess.Board = chess.Board()

        self.last_move: dict[str, str] = {}

    def get_color(self) -> Literal['white', 'black']:
        return "white" if self.turn == self.white else "black"

    async def make_embed(self) -> discord.Embed:
        embed = discord.Embed(title="Chess Game", color=self.embed_color)
        embed.description = f"**Turn:** `{self.turn}`\n**Color:** `{self.get_color()}`\n**Check:** `{self.board.is_check()}`"

        embed.add_field(name='Last Move', value=f"```yml\n{self.last_move['color']}: {self.last_move['move']}\n```")
        embed.set_image(url=f"{self.BASE_URL}{self.board.board_fen()}")
        return embed

    async def place_move(self, uci: str) -> chess.Board:
        self.board.push_uci(uci)
        self.turn = self.white if self.turn == self.black else self.black

        self.last_move = {
            'color': self.get_color(),
            'move': f'{uci[:2]} -> {uci[2:]}'
        }
        return self.board

    async def fetch_results(self) -> discord.Embed:
        results = self.board.result()
        embed = discord.Embed(title="Chess Game")

        if self.board.is_checkmate():
            embed.description = f"Game over\nCheckmate | Score: `{results}`"
        elif self.board.is_stalemate():
            embed.description = f"Game over\nStalemate | Score: `{results}`"
        elif self.board.is_insufficient_material():
            embed.description = f"Game over\nInsufficient material left to continue the game | Score: `{results}`"
        elif self.board.is_seventyfive_moves():
            embed.description = f"Game over\n75-moves rule | Score: `{results}`"
        elif self.board.is_fivefold_repetition():
            embed.description = f"Game over\nFive-fold repitition. | Score: `{results}`"
        else:
            embed.description = f"Game over\nVariant end condition. | Score: `{results}`"

        embed.set_image(url=f"{self.BASE_URL}{self.board.board_fen()}")
        return embed

    async def start(
        self, 
        ctx: commands.Context, 
        *, 
        timeout: Optional[float] = None, 
        embed_color: Union[discord.Color, int] = 0x2F3136, 
        add_reaction_after_move: bool = False, 
        **kwargs,
    ) -> Optional[discord.Message]:

        self.embed_color = embed_color

        embed = await self.make_embed()
        self.message = await ctx.send(embed=embed, **kwargs)

        while True:

            def check(m: discord.Message) -> bool:
                try:
                    if self.board.parse_uci(m.content.lower()):
                        return m.author == self.turn and m.channel == ctx.channel
                    else:
                        return False
                except ValueError:
                    return False

            try:
                message: discord.Message = await ctx.bot.wait_for("message", timeout=timeout, check=check)
            except asyncio.TimeoutError:
                return

            await self.place_move(message.content.lower())
            embed = await self.make_embed()

            if add_reaction_after_move:
                await message.add_reaction("✅")

            if self.board.is_game_over():
                break
            
            await self.message.edit(embed=embed)

        embed = await self.fetch_results()
        await self.message.edit(embed=embed)

        return await ctx.send("~ Game Over ~")
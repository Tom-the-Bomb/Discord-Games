from typing import Union, Optional
import asyncio

import discord
from discord.ext import commands
import chess

class Chess:

    def __init__(self, *, white: discord.Member, black: discord.Member) -> None:
        self._base = "http://www.fen-to-image.com/image/64/double/coords/"
        self.white = white
        self.black = black
        self.turn  = self.white
        self.winner = None
        self.board  = chess.Board()
        self.message = None

    async def make_embed(self) -> discord.Embed:
        color = "white" if self.turn == self.white else "black"
        embed = discord.Embed(title="Chess Game")
        embed.description = f"**Turn:** `{self.turn.name}`\n**Color:** `{color}`\n**Check:** `{self.board.is_check()}`"
        embed.set_image(url=f"{self._base}{self.board.board_fen()}")
        return embed

    async def place_move(self, uci: str) -> chess.Board:
        self.board.push_uci(uci)
        self.turn = self.white if self.turn == self.black else self.black
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

        embed.set_image(url=f"{self._base}{self.board.board_fen()}")
        return embed

    async def start(self, 
        ctx: commands.Context, 
        *, 
        timeout: Optional[int] = None, 
        color: Union[int, discord.Color] = 0x2F3136, 
        add_reaction_after_move: bool = False, 
        **kwargs,
    ) -> discord.Message:

        embed = await self.make_embed()
        embed.color = color
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
                message: str = await ctx.bot.wait_for("message", timeout=timeout, check=check)
            except asyncio.TimeoutError:
                return

            await self.place_move(message.content.lower())
            embed = await self.make_embed()
            embed.color = color

            if add_reaction_after_move:
                await message.add_reaction("✅")

            if self.board.is_game_over():
                break
            
            await self.message.edit(embed=embed)

        embed = await self.fetch_results()
        embed.color = color
        await self.message.edit(embed=embed)

        return await ctx.send("~ Game Over ~")
from typing import Optional, ClassVar

import discord
from discord.ext import commands

from .utils import DiscordColor, DEFAULT_COLOR

class Tictactoe:
    BLANK: ClassVar[str] = "⬛"
    CIRCLE: ClassVar[str] = "⭕"
    CROSS: ClassVar[str] = "❌"

    def __init__(self, cross: discord.Member, circle: discord.Member) -> None:
        self.cross = cross
        self.circle = circle

        self.board: list[list[str]] = [[self.BLANK for _ in range(3)] for _ in range(3)]
        self.turn: discord.Member  = self.cross

        self.winner: Optional[discord.Member] = None
        self.winning_indexes: list = []
        self.message: Optional[discord.Message] = None

        self._controls: list[str] = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
        self._conversion: dict[str, tuple[int, int]] = {
            '1️⃣': (0, 0), 
            '2️⃣': (0, 1), 
            '3️⃣': (0, 2), 
            '4️⃣': (1, 0), 
            '5️⃣': (1, 1), 
            '6️⃣': (1, 2), 
            '7️⃣': (2, 0), 
            '8️⃣': (2, 1), 
            '9️⃣': (2, 2), 
        }
        self.emoji_to_player = {
            self.CIRCLE: self.circle, 
            self.CROSS : self.cross, 
        }
        self.player_to_emoji = {
            self.cross: self.CROSS, 
            self.circle: self.CIRCLE, 
        }

    def board_string(self) -> str:
        board = ""
        for row in self.board:
            board += "".join(row) + "\n"
        return board

    def make_embed(self, color: DiscordColor = DEFAULT_COLOR, *, tie: bool = False) -> discord.Embed:
        embed = discord.Embed(color=color)
        if self.is_game_over() or tie:
            status = f"{self.winner.mention} won!" if self.winner else "Tie"
            embed.description = f"**Game over**\n{status}"
        else:
            embed.description = f"**Turn:** {self.turn.mention}\n**Piece:** `{self.player_to_emoji[self.turn]}`"
        return embed

    def make_move(self, emoji: str, user: discord.Member) -> list:

        if emoji not in self._controls:
            raise KeyError("Provided emoji is not one of the valid controls")
        else:
            x, y = self._conversion[emoji]
            piece = self.player_to_emoji[user]
            self.board[x][y] = piece

            self.turn = self.circle if user == self.cross else self.cross
            self._conversion.pop(emoji)
            self._controls.remove(emoji)
            return self.board

    def is_game_over(self) -> bool:

        if not self._controls:
            return True

        for i in range(3):

            if (self.board[i][0] == self.board[i][1] == self.board[i][2]) and self.board[i][0] != self.BLANK:
                self.winner = self.emoji_to_player[self.board[i][0]]
                self.winning_indexes = [(i, 0), (i, 1), (i, 2)]

                return True

            if (self.board[0][i] == self.board[1][i] == self.board[2][i]) and self.board[0][i] != self.BLANK:
                self.winner = self.emoji_to_player[self.board[0][i]]
                self.winning_indexes = [(0, 1), (1, i), (2, i)]

                return True

        if (self.board[0][0] == self.board[1][1] == self.board[2][2]) and self.board[0][0] != self.BLANK:
            self.winner = self.emoji_to_player[self.board[0][0]]
            self.winning_indexes = [(0, 0), (1, 1), (2, 2)]

            return True
           
        if (self.board[0][2] == self.board[1][1] == self.board[2][0]) and self.board[0][2] != self.BLANK:
            self.winner = self.emoji_to_player[self.board[0][2]]
            self.winning_indexes = [(0, 2), (1, 1), (2, 0)]

            return True
           
        return False

    async def start(
        self, 
        ctx: commands.Context, 
        *, 
        embed_color: DiscordColor = DEFAULT_COLOR, 
        remove_reaction_after: bool = False, 
        **kwargs,
    ) -> discord.Message:

        embed = self.make_embed(embed_color)
        self.message = await ctx.send(self.board_string(), embed=embed, **kwargs)

        for button in self._controls:
            await self.message.add_reaction(button)

        while True:

            def check(reaction, user):
                return str(reaction.emoji) in self._controls and user == self.turn and reaction.message == self.message

            reaction, user = await ctx.bot.wait_for("reaction_add", check=check)

            if self.is_game_over():
                break
            
            emoji = str(reaction.emoji)
            self.make_move(emoji, user)
            embed = self.make_embed(embed_color)

            if remove_reaction_after:
                await self.message.remove_reaction(emoji, user)

            await self.message.edit(content=self.board_string(), embed=embed)
        
        embed = self.make_embed(embed_color)
        return await self.message.edit(content=self.board_string(), embed=embed)
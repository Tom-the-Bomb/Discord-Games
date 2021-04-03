from typing import Optional, Union
import discord
from discord.ext import commands

BLANK  = "⬛"
CIRCLE = "⭕"
CROSS  = "❌"

class Tictactoe:

    def __init__(self, cross: discord.Member, circle: discord.Member) -> None:
        self.cross       = cross
        self.circle      = circle
        self.board       = [[BLANK for __ in range(3)] for __ in range(3)]
        self.turn        = self.cross
        self.winner      = None
        self.message     = None
        self._controls   = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
        self._conversion = {
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
        self._EmojiToPlayer = {
            CIRCLE: self.circle, 
            CROSS : self.cross, 
        }
        self._PlayerToEmoji = {
            self.cross: CROSS, 
            self.circle: CIRCLE, 
        }

    def BoardString(self) -> str:
        board = ""
        for row in self.board:
            board += "".join(row) + "\n"
        return board

    async def add_reactions(self) -> None:
        for button in self._controls:
            await self.message.add_reaction(button)

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed()
        if not self.GameOver():
            embed.description = f"**Turn:** {self.turn}"
        else:
            status = f"{self.winner} won!" if self.winner else "Tie"
            embed.description = f"**Game over**\n{status}"
        return embed

    async def MakeMove(self, emoji: str, user: discord.Member) -> list:

        if emoji not in self._controls:
            raise KeyError("Provided emoji is not one of the valid controls")

        else:
            x, y = self._conversion[emoji]
            piece = self._PlayerToEmoji[user]
            self.board[x][y] = piece
            self.turn        = self.circle if user == self.cross else self.cross
            self._conversion.pop(emoji)
            self._controls.remove(emoji)
            return self.board

    def GameOver(self) -> bool:

        if not self._controls:
            return True

        for i in range(3):

            if (self.board[i][0] == self.board[i][1] == self.board[i][2]) and self.board[i][0] != BLANK:
                self.winner = self._EmojiToPlayer[self.board[i][0]]
                return True
            if (self.board[0][i] == self.board[1][i] ==self.board[2][i]) and self.board[0][i] != BLANK:
                self.winner = self._EmojiToPlayer[self.board[0][i]]
                return True

        if (self.board[0][0] == self.board[1][1] == self.board[2][2]) and self.board[0][0] != BLANK:
            self.winner = self._EmojiToPlayer[self.board[0][0]]
            return True
           
        if (self.board[0][2] == self.board[1][1] == self.board[2][0]) and self.board[0][2] != BLANK:
            self.winner = self._EmojiToPlayer[self.board[0][2]]
            return True
           
        return False

    async def start(self, ctx: commands.Context) -> None:
        embed = self.make_embed()
        self.message = await ctx.send(self.BoardString(), embed=embed)
        await self.add_reactions()

        while True:

            def check(reaction, user):
                return str(reaction.emoji) in self._controls and user == self.turn and reaction.message == self.message

            reaction, user = await ctx.bot.wait_for("reaction_add", check=check)

            if self.GameOver():
                break
            
            emoji = str(reaction.emoji)
            await self.MakeMove(emoji, user)
            embed = self.make_embed()
            await self.message.edit(content=self.BoardString(), embed=embed)
        
        embed = self.make_embed()
        return await self.message.edit(content=self.BoardString(), embed=embed)
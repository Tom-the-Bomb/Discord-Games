import discord
from discord.ext import commands

RED   = "🔴"
BLUE  = "🔵"
BLANK = "⬛"

class ConnectFour:

    def __init__(self, *, red: discord.Member, blue: discord.Member):
        self.red_player  = red
        self.blue_player = blue
        self.board       = [[BLANK for __ in range(7)] for __ in range(6)]
        self._controls   = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣')
        self.turn        = self.red_player
        self.message    = None
        self.winner      = None
        self._conversion = {
            '1️⃣': 0, 
            '2️⃣': 1, 
            '3️⃣': 2, 
            '4️⃣': 3, 
            '5️⃣': 4, 
            '6️⃣': 5, 
            '7️⃣': 6, 
        }
        self._PlayerToEmoji = {
            self.red_player : RED, 
            self.blue_player: BLUE,
        }
        self._EmojiToPlayer = {
            RED: self.red_player, 
            BLUE: self.blue_player,
        }

    def BoardString(self) -> str:
        board = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣\n"
        for row in self.board:
            board += "".join(row) + "\n"
        return board

    async def make_embed(self) -> discord.Embed:
        embed = discord.Embed()
        if not await self.GameOver():
            embed.description = f"**Turn:** {self.turn.name}\n**Piece:** `{self._PlayerToEmoji[self.turn]}`"
        else:
            status = f"{self.winner} won!" if self.winner else "Tie"
            embed.description = f"**Game over**\n{status}"
        return embed
        
    async def PlacePiece(self, emoji: str, user) -> list:
        
        if emoji not in self._controls:
            raise KeyError("Provided emoji is not one of the valid controls")
        y = self._conversion[emoji]

        for x in range(5,-1,-1):
            if self.board[x][y] == BLANK:
                self.board[x][y] = self._PlayerToEmoji[user]
                break

        self.turn = self.red_player if user == self.blue_player else self.blue_player
        return self.board

    async def GameOver(self) -> bool:

        if all([i != BLANK for i in self.board[0]]):
            return True

        for x in range(6):
            for i in range(4):
                if (self.board[x][i] == self.board[x][i+1] == self.board[x][i+2] == self.board[x][i+3]) and self.board[x][i] != BLANK:
                    self.winner = self._EmojiToPlayer[self.board[x][i]]
                    return True

        for x in range(3):
            for i in range(7):
                if (self.board[x][i] == self.board[x+1][i] == self.board[x+2][i] == self.board[x+3][i]) and self.board[x][i] != BLANK:
                    self.winner = self._EmojiToPlayer[self.board[x][i]]
                    return True

        for x in range(3):
            for i in range(4):
                if (self.board[x][i] == self.board[x + 1][i + 1] == self.board[x + 2][i + 2] == self.board[x + 3][i + 3]) and self.board[x][i] != BLANK:
                    self.winner = self._EmojiToPlayer[self.board[x][i]]
                    return True

        for x in range(5, 2, -1):
            for i in range(4):
                if (self.board[x][i] == self.board[x - 1][i + 1] == self.board[x - 2][i + 2] == self.board[x - 3][i + 3]) and self.board[x][i] != BLANK:
                    self.winner = self._EmojiToPlayer[self.board[x][i]]
                    return True

        return False
    
    async def start(self, ctx: commands.Context, *, remove_reaction_after: bool = False):

        embed = await self.make_embed()
        self.message = await ctx.send(self.BoardString(), embed=embed)

        for button in self._controls:
            await self.message.add_reaction(button)

        while True:

            def check(reaction, user):
                return str(reaction.emoji) in self._controls and user == self.turn and reaction.message == self.message and self.board[0][self._conversion[str(reaction.emoji)]] == BLANK

            reaction, user = await ctx.bot.wait_for("reaction_add", check=check)

            if await self.GameOver():
                break

            emoji = str(reaction.emoji)
            await self.PlacePiece(emoji, user)
            embed = await self.make_embed()

            if remove_reaction_after:
                await self.message.remove_reaction(emoji, user)

            await self.message.edit(content=self.BoardString(), embed=embed)
        
        embed = await self.make_embed()
        return await self.message.edit(content=self.BoardString(), embed=embed)
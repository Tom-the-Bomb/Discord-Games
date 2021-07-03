import asyncio

import discord
from discord.ext import commands
from typing import Dict

import random

class Twenty48:

    def __init__(self, number_to_display_dict: Dict[str, str]):

        self.board = [[0 for _ in range(4)] for _ in range(4)]
        self.message = None
        self._controls = ['➡️', '⬅️', '⬇️', '⬆️']
        self._conversion = number_to_display_dict

    async def reverse(self, board: list) -> list:
        new_board = []
        for i in range(4):
            new_board.append([])
            for j in range(4):
                new_board[i].append(board[i][3-j])
        return new_board

    async def transp(self, board: list) -> list:
        new_board = [[0 for _ in range(4)] for _ in range(4)]
        for i in range(4):
            for j in range(4):
                new_board[i][j] = board[j][i]
        return new_board

    async def merge(self, board: list) -> list:
        for i in range(4):
            for j in range(3):
                if board[i][j] == board[i][j+1] and board[i][j] != 0:
                    board[i][j] += board[i][j]
                    board[i][j + 1] = 0
        return board
            
    async def compress(self, board: list) -> list:
        new_board = [[0 for _ in range(4)] for _ in range(4)]
        for i in range(4):
            pos = 0
            for j in range(4):
                if board[i][j] != 0:
                    new_board[i][pos] = board[i][j]
                    pos += 1
        return new_board

    async def MoveLeft(self) -> None:
        stage = await self.compress(self.board)
        stage = await self.merge(stage)
        stage = await self.compress(stage)
        self.board = stage
        
    async def MoveRight(self) -> None:
        stage = await self.reverse(self.board)
        stage = await self.compress(stage)
        stage = await self.merge(stage)
        stage = await self.compress(stage)
        stage = await self.reverse(stage)
        self.board = stage
        
    async def MoveUp(self) -> None:
        stage = await self.transp(self.board)
        stage = await self.compress(stage)
        stage = await self.merge(stage)
        stage = await self.compress(stage)
        stage = await self.transp(stage)
        self.board = stage
        
    async def MoveDown(self) -> None:
        stage = await self.transp(self.board)
        stage = await self.reverse(stage)
        stage = await self.compress(stage)
        stage = await self.merge(stage)
        stage = await self.compress(stage)
        stage = await self.reverse(stage)
        stage = await self.transp(stage)
        self.board = stage

    async def spawn_new(self) -> None:
        board  = self.board
        zeroes = [(j, i) for j, sub in enumerate(board) for i, el in enumerate(sub) if el == 0]
        if not zeroes:
            return
        i, j = random.choice(zeroes)
        board[i][j] = 2

    async def number_to_emoji(self) -> str:
        board = self.board
        GameString = ""
        emoji_array = [[self._conversion[str(l)] for l in row] for row in board]
        for row in emoji_array:
            GameString += "".join(row) + "\n"
        return GameString

    async def start(
        self, 
        ctx: commands.Context, *, 
        timeout: float = None,
        remove_reaction_after: bool = True, 
        delete_button: bool = False, 
        **kwargs
    ):

        self.player = ctx.author
        self.board[random.randrange(4)][random.randrange(4)] = 2
        self.board[random.randrange(4)][random.randrange(4)] = 2
        
        BoardString = await self.number_to_emoji()
        self.message = await ctx.send(BoardString, **kwargs)

        for button in self._controls:
            await self.message.add_reaction(button)
        
        if delete_button:
            self._controls.append("⏹️")
            await self.message.add_reaction("⏹️")

        while True:

            def check(reaction, user):
                return str(reaction.emoji) in self._controls and user == self.player and reaction.message == self.message
            
            try:
                reaction, _ = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)
            except asyncio.TimeoutError:
                return False

            emoji = str(reaction.emoji)

            if delete_button and emoji == "⏹️":
                return await self.message.delete()

            if emoji == '➡️':
                await self.MoveRight()

            elif emoji == '⬅️':
                await self.MoveLeft()

            elif emoji == '⬇️':
                await self.MoveDown()

            elif emoji == '⬆️':
                await self.MoveUp()

            await self.spawn_new()
            BoardString = await self.number_to_emoji()

            if remove_reaction_after:
                try:
                    await self.message.remove_reaction(emoji, ctx.author)
                except Exception:
                    pass

            await self.message.edit(content=BoardString)
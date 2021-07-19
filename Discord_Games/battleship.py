
from typing import Tuple, List, Optional, Union, Callable, Dict
from itertools import chain
from enum import Enum
from io import BytesIO

import asyncio
import functools
import random
import re

import discord
from discord.ext import commands
from PIL import Image, ImageDraw

Coords = Tuple[int, int]

SHIPS: Dict[str, Tuple[int, Tuple[int, int, int]]] = {
    "carrier": (5, 
        (80, 80, 80)),
    "battleship": (4, 
        (110, 110, 110)),
    "submarine": (3, 
        (150, 150, 150)),
    "cruiser": (2, 
        (190, 190, 190)),
}

def executor():

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(None, partial)

        return wrapper
    return decorator

class Ship:

    def __init__(self, 
        name: str, 
        size: int, 
        start: Coords,
        color: Tuple[int, int, int],
        vertical: bool = False,
    ) -> None:

        self.name: str = name
        self.size: int = size

        self.start: Coords = start
        self.vertical: bool = vertical
        self.color: Tuple[int, int, int] = color
        
        self.end: Coords = (
            (self.start[0], self.start[1] + self.size) if self.vertical else
            (self.start[0] + self.size, self.start[1])
        )

        self.span: List[Coords] = (
            [
                (self.start[0], i) for i in range(self.start[1], self.end[1])
            ] if self.vertical else [
                (i, self.start[1]) for i in range(self.start[0], self.end[0])
            ]
        )

        self.hits: List[bool] = [False] * self.size

class Board:

    def __init__(self, player: discord.Member) -> None:
        
        self.player: discord.Member = player
        self.ships: List[Ship] = []

        self.my_hits: List[Coords] = []
        self.my_misses: List[Coords] = []

        self.op_hits: List[Coords] = []
        self.op_misses: List[Coords] = []

        self._place_ships()

    @property
    def moves(self) -> List[Coords]:
        return self.my_hits + self.my_misses

    def _is_valid(self, ship: Ship) -> bool:

        if ship.end[0] > 10 or ship.end[1] > 10:
            return False

        for existing in self.ships:
            if any(c in existing.span for c in ship.span):
                return False
        return True

    def _place_ships(self) -> None:

        def place_ship(ship: Ship, size: int, color: Tuple[int, int, int]) -> None:
            start = random.randint(1, 10), random.randint(1, 10)
            vertical = bool(random.randint(0, 1))

            new_ship = Ship(
                name=ship, 
                size=size, 
                start=start, 
                vertical=vertical,
                color=color,
            )

            if self._is_valid(new_ship):
                self.ships.append(new_ship)
            else:
                place_ship(ship, size, color)

        for ship, (size, color) in SHIPS.items():
            place_ship(ship, size, color)

    def won(self) -> bool:
        return all(all(ship.hits) for ship in self.ships)

    def draw_dot(self, cur: ImageDraw.Draw, x: int, y: int, fill: Union[int, Tuple[int, ...]]) -> None:
        x1, y1 = x - 10, y - 10
        x2, y2 = x + 10, y + 10
        cur.ellipse((x1, y1, x2, y2), fill=fill)

    def draw_sq(self, cur: ImageDraw.Draw, x: int, y: int, *, coord: Coords, ship: Ship) -> None:
        vertical = ship.vertical
        left_end = ship.span.index(coord) == 0
        right_end = ship.span.index(coord) == ship.size - 1
        
        if vertical and left_end:
            diffs = (18, 18, 25, 18)
        elif vertical and right_end:
            diffs = (25, 18, 18, 18)
        elif not vertical and left_end:
            diffs = (18, 18, 18, 25)
        elif not vertical and right_end:
            diffs = (18, 25, 18, 18)
        elif vertical:
            diffs = (25, 18, 25, 18)
        else:
            diffs = (18, 25, 18, 25)
            
        d1, d2, d3, d4 = diffs
        x1, y1 = x - d1, y - d2
        x2, y2 = x + d3, y + d4
        cur.rectangle((x1, y1, x2, y2), fill=ship.color)

    def get_ship(self, coord: Coords) -> Optional[Ship]:
        if s := [ship for ship in self.ships if coord in ship.span]:
            return s[0]
    
    @executor()
    def to_image(self, hide: bool = False) -> Image.Image:
        RED = (255, 0, 0)
        GRAY = (128, 128, 128)

        with Image.open('./assets/battleship.png') as img:
            cur = ImageDraw.Draw(img)
            
            for i, y in zip(
                range(1, 11), range(75, 530, 50)
            ):
                for j, x in zip(
                    range(1, 11), range(75, 530, 50)
                ):
                    coord = (i, j)
                    if coord in self.my_misses:
                        self.draw_dot(cur, x, y, fill=GRAY)

                    elif coord in self.my_hits:
                        if hide:
                            self.draw_dot(cur, x, y, fill=RED)
                        else:
                            ship = self.get_ship(coord)
                            self.draw_sq(cur, x, y, coord=coord, ship=ship)
                            self.draw_dot(cur, x, y, fill=RED)

                    elif ship := self.get_ship(coord):
                        if not hide:
                            self.draw_sq(cur, x, y, coord=coord, ship=ship)
            return img

class BattleShip:

    def __init__(self, 
        player1: discord.Member, 
        player2: discord.Member,
    ) -> None:

        self.inputpat: re.Pattern = re.compile(r'([a-j])(10|[1-9])')
        self.player1: discord.Member = player1
        self.player2: discord.Member = player2

        self.player1_board: Board = Board(player1)
        self.player2_board: Board = Board(player2)

        self.turn: discord.Member = self.player1

        self.message1: Optional[discord.Message] = None
        self.message2: Optional[discord.Message] = None

    @executor()
    def stitch_image(self, left: Image.Image, right: Image.Image) -> BytesIO:
        SPACE = 10
        size = (
            left.width + SPACE + right.width, 
            max((left.height, right.height)),
        )

        with Image.new('RGB', size, color=(40, 40, 40)) as background:
            background.paste(left, (0, 0))
            background.paste(right, (left.width + SPACE, 0))

            left.close()
            right.close()
            
            buffer = BytesIO()
            background.save(buffer, 'PNG')
            buffer.seek(0)
            return buffer

    def get_board(self, player: discord.Member, other: bool = False) -> Board:
        if other:
            return (
                self.player2_board if player == self.player1 else self.player1_board
            )
        else:
            return (
                self.player1_board if player == self.player1 else self.player2_board
            )

    def place_move(self, player: discord.Member, coords: Coords) -> bool:
        board = self.get_board(player)
        op_board = self.get_board(player, other=True)
        
        for i, ship in enumerate(board.ships):
            for j, coord in enumerate(ship.span):
                if coords == coord:
                    op_board.ships[i].hits[j] = True
                    board.my_hits.append(coords)
                    return all(op_board.ships[i].hits), True

        board.my_misses.append(coords)
        op_board.op_misses.append(coords)
        return False, False

    async def get_file(self, player: discord.Member) -> discord.File:

        board = self.get_board(player)
        image = await board.to_image(hide=True)

        board2 = self.get_board(player, other=True)
        image2 = await board2.to_image()

        image = await self.stitch_image(image, image2)

        file = discord.File(image, 'board.png')
        return file

    def get_coords(self, inp: str) -> Tuple[str, Coords]:
        inp = inp.replace(' ', '').lower()
        match = self.inputpat.match(inp)
        x, y = match.group(1), match.group(2)
        return (inp, (ord(x) % 96, int(y)))

    def who_won(self) -> Optional[discord.Member]:
        if self.player1_board.won():
            return self.player2
        elif self.player2_board.won():
            return self.player1
        else:
            return None

    async def start(self, ctx: commands.Context, *, timeout: Optional[int] = None) -> None:

        await ctx.send('**Game Started!**\nI\'ve setup the boards in your dms!')
        
        file1 = await self.get_file(self.player1)
        file2 = await self.get_file(self.player2)
        
        self.message1 = await self.player1.send(file=file1)
        self.message2 = await self.player2.send(file=file2)

        while True:

            def check(msg: discord.Message) -> bool:
                if not msg.guild and msg.author == self.turn:
                    content = msg.content.replace(' ', '').lower()
                    return bool(self.inputpat.match(content))
            try:
                message = await ctx.bot.wait_for('message', check=check, timeout=timeout)
            except asyncio.TimeoutError:
                await ctx.send(f'The timeout of {timeout} has been reached. Aborting...')
                return None

            raw, coords = self.get_coords(message.content)

            sunk, hit = self.place_move(self.turn, coords)
            next_turn: discord.Member = self.player2 if self.turn == self.player1 else self.player1

            if hit and sunk:
                await self.turn.send(f'`{raw}` was a hit!, you also sank one of their ships! :)')
                await next_turn.send(f'They went for `{raw}`, and it was a hit!\nOne of your ships also got sunk! :(')
            elif hit:
                await self.turn.send(f'`{raw}` was a hit :)')
                await next_turn.send(f'They went for `{raw}`, and it was a hit! :(')
            else:
                await self.turn.send(f'`{raw}` was a miss :(')
                await next_turn.send(f'They went for `{raw}`, and it was a miss! :)')

            file1 = await self.get_file(self.player1)
            file2 = await self.get_file(self.player2)
            
            await self.player1.send(file=file1)
            await self.player2.send(file=file2)
            self.turn = next_turn

            if winner := self.who_won():
                await winner.send('Congrats, you won! :)')

                other = self.player2 if winner == self.player1 else self.player1
                await other.send('You lost, better luck next time :(')
                return None
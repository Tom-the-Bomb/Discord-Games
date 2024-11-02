
import asyncio
import random
from typing import Optional

import discord
from discord.ext import commands

class Tetris:
    WIDTH = 10
    HEIGHT = 20
    BASE_FALL_SPEED = 1.0
    MIN_FALL_SPEED = 0.15

    SHAPES = [
        [[1, 1, 1, 1]],
        [[1, 1], [1, 1]],
        [[1, 1, 1], [0, 1, 0]],
        [[1, 1, 1], [1, 0, 0]],
        [[1, 1, 1], [0, 0, 1]],
        [[1, 1, 0], [0, 1, 1]],
        [[0, 1, 1], [1, 1, 0]]
    ]

    @staticmethod
    def cell_to_emoji(cell: int) -> str:
        return ['⬛', '🟥', '🟦', '🟩', '🟨', '🟪', '🟧', '⬜', '⚪'][cell]

    def __init__(self) -> None:
        self.board = [[0] * self.WIDTH for _ in range(self.HEIGHT)]
        self.current_piece = None
        self.next_piece = self.new_piece()
        self.piece_x = 0
        self.piece_y = 0
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False
        self.started = False

        self.message: Optional[discord.Message] = None
        self.embed = discord.Embed(title='Tetris Game')

        self.game_loop_task: Optional[asyncio.Task] = None

    def new_piece(self):
        shape = random.choice(self.SHAPES)
        color = random.randint(1, 7)
        return {'shape': shape, 'color': color}

    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        self.piece_x = self.WIDTH // 2 - len(self.current_piece['shape'][0]) // 2
        self.piece_y = 0
        if not self.is_valid_move(self.piece_x, self.piece_y, self.current_piece['shape']):
            self.game_over = True

    def move(self, dx, dy):
        if self.current_piece and self.is_valid_move(self.piece_x + dx, self.piece_y + dy, self.current_piece['shape']):
            self.piece_x += dx
            self.piece_y += dy
            return True
        return False

    def rotate(self) -> bool:
        if not self.current_piece:
            return False
        rotated_shape = list(zip(*self.current_piece['shape'][::-1]))
        if self.is_valid_move(self.piece_x, self.piece_y, rotated_shape):
            self.current_piece['shape'] = rotated_shape
            return True
        return False

    def hard_drop(self) -> int:
        if not self.current_piece:
            return 0
        drop_distance = 0
        while self.move(0, 1):
            drop_distance += 1
        return drop_distance

    def is_valid_move(self, x: int, y: int, shape: list[list[int]]) -> bool:
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell and (y + i >= self.HEIGHT or x + j < 0 or x + j >= self.WIDTH or
                             (y + i >= 0 and self.board[y + i][x + j])):
                    return False
        return True

    def merge_piece(self) -> None:
        if not self.current_piece:
            return
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    self.board[self.piece_y + i][self.piece_x + j] = self.current_piece['color']

    def clear_lines(self) -> int:
        lines_cleared = 0
        for i in range(self.HEIGHT - 1, -1, -1):
            if all(self.board[i]):
                del self.board[i]
                self.board.insert(0, [0 for _ in range(self.WIDTH)])
                lines_cleared += 1

        if lines_cleared:
            self.lines_cleared += lines_cleared
            self.score += (lines_cleared ** 2) * 100 * self.level
            self.level = min(self.lines_cleared // 10 + 1, 15)

        return lines_cleared

    def render(self) -> str:
        board_copy = [row[:] for row in self.board]
        if self.current_piece:
            for i, row in enumerate(self.current_piece['shape']):
                for j, cell in enumerate(row):
                    if cell and 0 <= self.piece_y + i < self.HEIGHT and 0 <= self.piece_x + j < self.WIDTH:
                        board_copy[self.piece_y + i][self.piece_x + j] = self.current_piece['color']

        return '\n'.join(''.join(self.cell_to_emoji(cell) for cell in row) for row in board_copy)

    def get_fall_speed(self) -> float:
        return max(
            self.BASE_FALL_SPEED - (self.level - 1) * 0.05,
            self.MIN_FALL_SPEED
        )

    def update_embed(self) -> None:
        self.embed.clear_fields()

        if self.started:
            self.embed.add_field(name='\u200b', value=self.render(), inline=False)
            self.embed.add_field(name='Score', value=str(self.score), inline=True)
            self.embed.add_field(name='Level', value=str(self.level), inline=True)
            self.embed.add_field(name='Lines', value=str(self.lines_cleared), inline=True)
            next_piece_preview = '\n'.join(''.join(self.cell_to_emoji(cell) for cell in row) for row in self.next_piece['shape'])
            self.embed.add_field(name='Next Piece', value=next_piece_preview, inline=True)
        else:
            self.embed.add_field(name='How to Play', value='Press ▶️ to start the game!', inline=False)

        self.embed.color = discord.Color.green() if not self.paused else discord.Color.blue()

    async def game_loop(self) -> None:
        self.spawn_piece()
        await self.update_game()

        while not self.game_over and self.started:
            if not self.paused:
                await asyncio.sleep(self.get_fall_speed())
                if not self.move(0, 1):
                    self.merge_piece()
                    lines_cleared = self.clear_lines()
                    if lines_cleared > 0:
                        self.score += lines_cleared * 100
                        self.level_up(lines_cleared)
                        await self.update_game()
                    if self.game_over:
                        await self._end_game('Game Over!')
                        return
                    self.spawn_piece()
                await self.update_game()
            else:
                await asyncio.sleep(0.1)

    async def update_game(self) -> None:
        try:
            self.update_embed()
            await self.message.edit(embed=self.embed)
        except discord.errors.NotFound:
            self.game_over = True
        except discord.errors.HTTPException:
            pass  # Ignore rate limiting

    async def _end_game(self, end_message: str) -> None:
        self.game_over = True
        self.embed.title = end_message
        self.embed.color = discord.Color.red()
        try:
            await self.message.edit(embed=self.embed)
        except discord.errors.NotFound:
            pass  # Message might have been deleted

    def level_up(self, lines_cleared: int) -> None:
        self.lines_cleared += lines_cleared
        self.level = min(self.lines_cleared // 10 + 1, 15)

    async def show_help(self, channel: discord.abc.Messageable):
        help_embed = discord.Embed(title='Tetris Help', color=discord.Color.blue())
        help_embed.add_field(
            name='How to Play',
            value=(
                '• ▶️: Start the game\n'
                '• ⬅️: Move left\n'
                '• ➡️: Move right\n'
                '• 🔽: Soft drop (move down faster)\n'
                '• ⏬: Hard drop (instantly drop to bottom)\n'
                '• 🔄: Rotate piece\n'
                '• ⏸️: Pause/Resume game\n'
                '• 🛑: End game\n'
                '• Clear lines to score points and level up!\n'
                '• Game speeds up as you level up.\n'
                '• Game ends if pieces stack up to the top.'
            ),
            inline=False
        )
        await channel.send(embed=help_embed)

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        """
        starts the tetris game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        timeout : Optional[float], optional
            the timeout for when waiting, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.update_embed()
        self.embed.set_footer(text='▶️: Start | ⬅️: Left | ➡️: Right | 🔽: Soft Drop | ⏬: Hard Drop\n🔄: Rotate | ⏸️: Pause | 🛑: End | ❓: Help')
        self.message = await ctx.send(embed=self.embed)

        reactions = ['▶️', '⬅️', '➡️', '🔽', '⏬', '🔄', '⏸️', '🛑', '❓']
        for reaction in reactions:
            await self.message.add_reaction(reaction)

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == self.message.id

        while not ctx.bot.is_closed():
            try:
                task1 = asyncio.create_task(ctx.bot.wait_for(
                    'reaction_add',
                    timeout=timeout,
                    check=check,
                ))
                task2 = asyncio.create_task(ctx.bot.wait_for(
                    'reaction_remove',
                    timeout=timeout,
                    check=check,
                ))
                done, _ = await asyncio.wait(
                    tasks := [task1, task2], return_when=asyncio.FIRST_COMPLETED
                )
                reaction, _ = done.pop().result()

                for task in tasks:
                    task.cancel()
            except asyncio.TimeoutError:
                await self._end_game('Game timed out due to inactivity.')
                return self.message
            else:
                emoji = str(reaction.emoji)

                if emoji == '▶️' and not self.started:
                    self.started = True
                    self.game_loop_task = asyncio.create_task(self.game_loop())
                elif not self.started:
                    continue
                elif emoji == '⬅️':
                    self.move(-1, 0)
                elif emoji == '➡️':
                    self.move(1, 0)
                elif emoji == '🔽':
                    self.move(0, 1)
                elif emoji == '⏬':
                    drop_distance = self.hard_drop()
                    self.score += drop_distance * 2
                    self.merge_piece()
                    lines_cleared = self.clear_lines()
                    if lines_cleared > 0:
                        self.score += lines_cleared * 100
                        self.level_up(lines_cleared)
                    if self.game_over:
                        await self._end_game('Game Over!')
                        return self.message
                    self.spawn_piece()
                elif emoji == '🔄':
                    self.rotate()
                elif emoji == '⏸️':
                    self.paused = not self.paused
                elif emoji == '🛑':
                    await self._end_game('Game Ended')
                    return self.message
                elif emoji == '❓':
                    await self.show_help(ctx.channel)

                await self.update_game()

                if self.game_over:
                    await self._end_game('Game Over!')
                    return self.message
        return self.message

    async def end_game(self, end_message: str):
        if self.game_loop_task:
            self.game_loop_task.cancel()

        await self._end_game(end_message)

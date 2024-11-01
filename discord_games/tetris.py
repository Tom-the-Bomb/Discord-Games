import discord
from discord.ext import commands
import asyncio
import random
from typing import Optional

class TetrisGame:
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

    def __init__(self):
        self.board = [[0 for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
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
        self.embed: discord.Embed = discord.Embed(title="Tetris Game")
        self.game_loop_task: Optional[asyncio.Task] = None

    def new_piece(self):
        shape = random.choice(self.SHAPES)
        color = random.randint(1, 7)
        return {"shape": shape, "color": color}

    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        self.piece_x = self.WIDTH // 2 - len(self.current_piece["shape"][0]) // 2
        self.piece_y = 0
        if not self.is_valid_move(self.piece_x, self.piece_y, self.current_piece["shape"]):
            self.game_over = True

    def move(self, dx, dy):
        if self.current_piece and self.is_valid_move(self.piece_x + dx, self.piece_y + dy, self.current_piece["shape"]):
            self.piece_x += dx
            self.piece_y += dy
            return True
        return False

    def rotate(self):
        if not self.current_piece:
            return False
        rotated_shape = list(zip(*self.current_piece["shape"][::-1]))
        if self.is_valid_move(self.piece_x, self.piece_y, rotated_shape):
            self.current_piece["shape"] = rotated_shape
            return True
        return False

    def hard_drop(self):
        if not self.current_piece:
            return 0
        drop_distance = 0
        while self.move(0, 1):
            drop_distance += 1
        return drop_distance

    def is_valid_move(self, x, y, shape):
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell and (y + i >= self.HEIGHT or x + j < 0 or x + j >= self.WIDTH or
                             (y + i >= 0 and self.board[y + i][x + j])):
                    return False
        return True

    def merge_piece(self):
        if not self.current_piece:
            return
        for i, row in enumerate(self.current_piece["shape"]):
            for j, cell in enumerate(row):
                if cell:
                    self.board[self.piece_y + i][self.piece_x + j] = self.current_piece["color"]

    def clear_lines(self):
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

    def render(self):
        board_copy = [row[:] for row in self.board]
        if self.current_piece:
            for i, row in enumerate(self.current_piece["shape"]):
                for j, cell in enumerate(row):
                    if cell and 0 <= self.piece_y + i < self.HEIGHT and 0 <= self.piece_x + j < self.WIDTH:
                        board_copy[self.piece_y + i][self.piece_x + j] = self.current_piece["color"]

        return "\n".join("".join(self.cell_to_emoji(cell) for cell in row) for row in board_copy)

    @staticmethod
    def cell_to_emoji(cell):
        return ["⬛", "🟥", "🟦", "🟩", "🟨", "🟪", "🟧", "⬜", "⚪"][cell]

    def get_fall_speed(self):
        return max(self.BASE_FALL_SPEED - (self.level - 1) * 0.05, self.MIN_FALL_SPEED)

    def update_embed(self):
        self.embed.clear_fields()
        if self.started:
            self.embed.add_field(name="\u200b", value=self.render(), inline=False)
            self.embed.add_field(name="Score", value=str(self.score), inline=True)
            self.embed.add_field(name="Level", value=str(self.level), inline=True)
            self.embed.add_field(name="Lines", value=str(self.lines_cleared), inline=True)
            next_piece_preview = "\n".join("".join(self.cell_to_emoji(cell) for cell in row) for row in self.next_piece["shape"])
            self.embed.add_field(name="Next Piece", value=next_piece_preview, inline=True)
        else:
            self.embed.add_field(name="How to Play", value="Press ▶️ to start the game!", inline=False)
        self.embed.color = discord.Color.green() if not self.paused else discord.Color.blue()

    async def game_loop(self):
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
                        await self.end_game("Game Over!")
                        return
                    self.spawn_piece()
                await self.update_game()
            else:
                await asyncio.sleep(0.1)

    async def update_game(self):
        try:
            self.update_embed()
            await self.message.edit(embed=self.embed)
        except discord.errors.NotFound:
            self.game_over = True
        except discord.errors.HTTPException:
            pass  # Ignore rate limiting

    async def end_game(self, end_message: str):
        self.game_over = True
        self.embed.title = end_message
        self.embed.color = discord.Color.red()
        try:
            await self.message.edit(embed=self.embed)
        except discord.errors.NotFound:
            pass  # Message might have been deleted

    def level_up(self, lines_cleared: int):
        self.lines_cleared += lines_cleared
        self.level = min(self.lines_cleared // 10 + 1, 15)

    async def show_help(self, channel: discord.abc.Messageable):
        help_embed = discord.Embed(title="Tetris Help", color=discord.Color.blue())
        help_embed.add_field(
            name="How to Play",
            value=("• ▶️: Start the game\n"
                   "• ⬅️: Move left\n"
                   "• ➡️: Move right\n"
                   "• 🔽: Soft drop (move down faster)\n"
                   "• ⏬: Hard drop (instantly drop to bottom)\n"
                   "• 🔄: Rotate piece\n"
                   "• ⏸️: Pause/Resume game\n"
                   "• 🛑: End game\n"
                   "• Clear lines to score points and level up!\n"
                   "• Game speeds up as you level up.\n"
                   "• Game ends if pieces stack up to the top."),
            inline=False
        )
        await channel.send(embed=help_embed)

class Tetris:
    def __init__(self):
        self.games = {}

    async def start(self, ctx: commands.Context):
        if ctx.author.id in self.games:
            await ctx.send("You're already in a game! Use the 🛑 reaction to end it.")
            return

        game = TetrisGame()
        self.games[ctx.author.id] = game

        game.update_embed()
        game.embed.set_footer(text="▶️: Start | ⬅️: Left | ➡️: Right | 🔽: Soft Drop | ⏬: Hard Drop\n🔄: Rotate | ⏸️: Pause | 🛑: End | ❓: Help")
        game.message = await ctx.send(embed=game.embed)

        reactions = ["▶️", "⬅️", "➡️", "🔽", "⏬", "🔄", "⏸️", "🛑", "❓"]
        for reaction in reactions:
            await game.message.add_reaction(reaction)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == game.message.id

        while not ctx.bot.is_closed():
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=300.0, check=check)
            except asyncio.TimeoutError:
                await self.end_game(ctx.author.id, "Game timed out due to inactivity.")
                return

            emoji = str(reaction.emoji)
            if emoji == "▶️" and not game.started:
                game.started = True
                game.game_loop_task = asyncio.create_task(game.game_loop())
            elif not game.started:
                await game.message.remove_reaction(emoji, user)
                continue
            elif emoji == "⬅️":
                game.move(-1, 0)
            elif emoji == "➡️":
                game.move(1, 0)
            elif emoji == "🔽":
                game.move(0, 1)
            elif emoji == "⏬":
                drop_distance = game.hard_drop()
                game.score += drop_distance * 2
                game.merge_piece()
                lines_cleared = game.clear_lines()
                if lines_cleared > 0:
                    game.score += lines_cleared * 100
                    game.level_up(lines_cleared)
                if game.game_over:
                    await self.end_game(ctx.author.id, "Game Over!")
                    return
                game.spawn_piece()
            elif emoji == "🔄":
                game.rotate()
            elif emoji == "⏸️":
                game.paused = not game.paused
            elif emoji == "🛑":
                await self.end_game(ctx.author.id, "Game Ended")
                return
            elif emoji == "❓":
                await game.show_help(ctx.channel)

            await game.update_game()
            await game.message.remove_reaction(emoji, user)

            if game.game_over:
                await self.end_game(ctx.author.id, "Game Over!")
                return

    async def end_game(self, user_id: int, end_message: str):
        if user_id in self.games:
            game = self.games[user_id]
            if game.game_loop_task:
                game.game_loop_task.cancel()
            await game.end_game(end_message)
            del self.games[user_id]

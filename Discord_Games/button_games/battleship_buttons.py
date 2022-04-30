from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from ..battleship import BattleShip
from .wordle_buttons import WordInputButton
from .chess_buttons import ChessView

class BattleshipInput(discord.ui.Modal, title='Input a coordinate'):

    def __init__(self, view: BattleshipView) -> None:
        super().__init__()
        self.view = view

        self.coord = discord.ui.TextInput(
            label='Enter your target coordinate',
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=2,
        )

        self.add_item(self.coord)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        game = self.view.game
        content = self.coord.value
        content = content.strip().lower()

        if not game.inputpat.match(content):
            return await interaction.response.send_message(f'`{content}` is not a valid coordinate!', ephemeral=True)
        else:
            raw, coords = game.get_coords(content)

            sunk, hit = game.place_move(game.turn, coords)
            next_turn: discord.Member = game.player2 if game.turn == game.player1 else game.player1

            if hit and sunk:
                await game.turn.send(f'`{raw}` was a hit!, you also sank one of their ships! :)')
                await next_turn.send(f'They went for `{raw}`, and it was a hit!\nOne of your ships also got sunk! :(')
            elif hit:
                await game.turn.send(f'`{raw}` was a hit :)')
                await next_turn.send(f'They went for `{raw}`, and it was a hit! :(')
            else:
                await game.turn.send(f'`{raw}` was a miss :(')
                await next_turn.send(f'They went for `{raw}`, and it was a miss! :)')

            file1, file3 = await game.get_file(self.player1)
            file2, file4 = await game.get_file(self.player2)
            
            await game.message1.edit(attachments=[file1, file3])
            await game.message2.edit(attachments=[file2, file4])
            game.turn = next_turn

            if winner := game.who_won():
                await winner.send('Congrats, you won! :)')

                other = game.player2 if winner == game.player1 else game.player1
                return await other.send('You lost, better luck next time :(')

class BattleshipButton(WordInputButton):
    view: BattleshipView

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game

        if interaction.user != game.turn:
            return await interaction.response.send_message('It is not your turn yet!', ephemeral=True)
        else:
            return await interaction.response.send_modal(BattleshipInput(self.view))

class BattleshipView(ChessView):

    def __init__(self, game: BetaBattleShip, user: discord.Member, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        inpbutton = BattleshipButton()
        inpbutton.label = '\u200b'
        inpbutton.emoji = '🎯'

        self.player = user

        self.add_item(inpbutton)

class BetaBattleShip(BattleShip):

    async def start(self, ctx: commands.Context, *, timeout: Optional[float] = None) -> tuple[discord.Message, discord.Message]:

        file1, file3 = await self.get_file(self.player1)
        file2, file4 = await self.get_file(self.player2)

        view1 = BattleshipView(self, user=self.player1)
        view2 = BattleshipView(self, user=self.player1)
        
        self.message1 = await self.player1.send('Game starting!', view=view1, files=[file1, file3])
        self.message2 = await self.player2.send('Game starting!', view=view2, files=[file2, file4])
        self.timeout = timeout

        return self.message1, self.message2
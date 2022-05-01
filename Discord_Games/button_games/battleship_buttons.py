from __future__ import annotations

from typing import Optional, Union, Any

import discord
from discord.ext import commands

from ..battleship import BattleShip
from .wordle_buttons import WordInputButton
from .chess_buttons import ChessView

class Player:

    def __init__(self, player: discord.Member, *, game: BetaBattleShip) -> None:
        self.game = game
        self.player = player

        self.embed = discord.Embed(title='Log')
        
        self._logs: list[str] = []
        self.log: str = ''

        self.approves_cancel: bool = False

    def update_guesslog(self, log: str) -> None:
        self._logs.append(log)
        log_str = '\n\n'.join(self._logs[-17:])
        if len(self._logs) > 17:
            log_str = '...\n\n' + log_str
        self.embed.description = f'```diff\n{log_str}\n```'

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return self.player.__getattribute__(name)

class BattleshipInput(discord.ui.Modal, title='Input a coordinate'):

    def __init__(self, view: BattleshipView) -> None:
        super().__init__()
        self.view = view

        self.coord = discord.ui.TextInput(
            label='Enter your target coordinate',
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=3,
        )

        self.add_item(self.coord)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        game = self.view.game
        content = self.coord.value
        content = content.strip().lower()

        if not game.inputpat.fullmatch(content):
            return await interaction.response.send_message(f'`{content}` is not a valid coordinate!', ephemeral=True)
        else:
            await interaction.response.defer()
            raw, coords = game.get_coords(content)

            sunk, hit = game.place_move(game.turn, coords)
            next_turn = game.player2 if game.turn == game.player1 else game.player1

            if hit and sunk:
                game.turn.update_guesslog(f'+ ({raw}) was a hit!, you also sank one of their ships! :)')
                next_turn.update_guesslog(f'- They went for ({raw}), and it was a hit!\nOne of your ships also got sunk! :(')
            elif hit:
                game.turn.update_guesslog(f'+ ({raw}) was a hit :)')
                next_turn.update_guesslog(f'- They went for ({raw}), and it was a hit! :(')
            else:
                game.turn.update_guesslog(f'- ({raw}) was a miss :(')
                next_turn.update_guesslog(f'+ They went for ({raw}), and it was a miss! :)')

            file1, file3 = await game.get_file(game.player1)
            file2, file4 = await game.get_file(game.player2)
            
            await game.message1.edit(content='BattleShip', embed=game.player1.embed, attachments=[file1, file3])
            await game.message2.edit(content='BattleShip', embed=game.player2.embed, attachments=[file2, file4])
            game.turn = next_turn

            if winner := game.who_won():
                await winner.send('Congrats, you won! :)')

                other = game.player2 if winner == game.player1 else game.player1
                return await other.send('You lost, better luck next time :(')

class BattleshipButton(WordInputButton):
    view: BattleshipView

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game

        if self.label == 'Cancel':
            player = game.player2 if interaction.user == game.player2.player else game.player1
            other_player = game.player2 if interaction.user == game.player1.player else game.player1

            if not player.approves_cancel:
                player.approves_cancel = True

            await interaction.response.defer()

            if not other_player.approves_cancel:
                await player.send('- Waiting for opponent to approve cancellation -')
                await other_player.send('Opponent wants to cancel, press the `Cancel` button if you approve.')
            else:
                game.view1.disable_all()
                game.view2.disable_all()

                await game.player1.send('**GAME OVER**, Cancelled')
                await game.player2.send('**GAME OVER**, Cancelled')

                await game.message1.edit(view=game.view1)
                return await game.message2.edit(view=game.view2)
        else:
            if interaction.user != game.turn.player:
                return await interaction.response.send_message('It is not your turn yet!', ephemeral=True)
            else:
                return await interaction.response.send_modal(BattleshipInput(self.view))

class BattleshipView(discord.ui.View):

    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    def __init__(self, game: BetaBattleShip, user: discord.Member, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        inpbutton = BattleshipButton()
        inpbutton.label = '\u200b'
        inpbutton.emoji = '🎯'

        self.player = user

        self.add_item(inpbutton)
        self.add_item(BattleshipButton(cancel_button=True))

class BetaBattleShip(BattleShip):
    embed: discord.Embed

    def __init__(self, 
        player1: discord.Member, 
        player2: discord.Member,
        *,
        random: bool = True,
    ) -> None:

        super().__init__(player1, player2, random=random)

        self.player1: Player = Player(player1, game=self)
        self.player2: Player = Player(player2, game=self)

        self.turn: Player = self.player1

    async def start(
        self, 
        ctx: commands.Context, 
        *,
        embed_color: Union[discord.Color, int] = 0x2F3136,
        timeout: Optional[float] = None,
    ) -> tuple[discord.Message, discord.Message]:

        await ctx.send('**Game Started!**\nI\'ve setup the boards in your dms!')

        self.player1.embed.color = embed_color
        self.player2.embed.color = embed_color

        file1, file3 = await self.get_file(self.player1)
        file2, file4 = await self.get_file(self.player2)

        self.view1 = BattleshipView(self, user=self.player1, timeout=timeout)
        self.view2 = BattleshipView(self, user=self.player1, timeout=timeout)
        
        self.message1 = await self.player1.send('Game starting!', view=self.view1, files=[file1, file3])
        self.message2 = await self.player2.send('Game starting!', view=self.view2, files=[file2, file4])
        self.timeout = timeout

        return self.message1, self.message2
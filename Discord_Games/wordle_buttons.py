from __future__ import annotations

import discord
from discord.ext import commands

from .wordle import Wordle

class WordInput(discord.ui.Modal, title='Word Input'):
    word = discord.ui.TextInput(
        label=f'Input your guess', 
        style=discord.TextStyle.short,
        required=True,
        min_length=5, 
        max_length=5,
    )
    
    def __init__(self, view: WordleView) -> None:
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        content = self.word.value.lower()
        game = self.view.game

        if content not in game._valid_words:
            return await interaction.response.send_message('That is not a valid word!', ephemeral=True)
        else:
            won = game.parse_guess(content)
            buf = await game.render_image()

            embed = discord.Embed(title='Wordle!')
            embed.set_image(url='attachment://wordle.png')

            file = discord.File(buf, 'wordle.png')
            await interaction.response.edit_message(embed=embed, attachments=[file])

            if won:
                return await interaction.message.reply('Game Over! You won!', mention_author=True)
            elif len(game.guesses) >= 6:
                return await interaction.message.reply(f'Game Over! You lose, the word was: **{game.word}**', mention_author=True)

class WordInputButton(discord.ui.Button):
    view: WordleView

    def __init__(self, *, cancel_button: bool = False):
        super().__init__(
            label='Cancel' if cancel_button else 'Make a guess!',
            style=discord.ButtonStyle.red if cancel_button else discord.ButtonStyle.blurple,
        )
    
    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game
        if interaction.user != game.player:
            return await interaction.response.send_message("This isn't your game!", ephemeral=True)
        else:
            if self.label == 'Cancel':
                await interaction.response.send_message(f'Game Over! the word was {game.word}')
                return await interaction.message.delete()
            else:
                return await interaction.response.send_modal(WordInput(self.view))

class WordleView(discord.ui.View):
    
    def __init__(self, game: BetaWordle, *, timeout: float = None):
        super().__init__(timeout=timeout)

        self.game = game
        self.add_item(WordInputButton())
        self.add_item(WordInputButton(cancel_button=True))
    
class BetaWordle(Wordle):
    player: discord.Member

    async def start(self, ctx: commands.Context, *, timeout: float = None) -> discord.Message:
        self.player = ctx.author

        buf = await self.render_image()
        embed = discord.Embed(title='Wordle!')
        embed.set_image(url='attachment://wordle.png')

        return await ctx.send(
            embed=embed,
            file=discord.File(buf, 'wordle.png'), 
            view=WordleView(self, timeout=timeout)
        )
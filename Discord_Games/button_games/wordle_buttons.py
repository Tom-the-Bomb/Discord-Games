from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from ..wordle import Wordle

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

    def disable_all(self) -> None:
        for button in self.view.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    async def on_submit(self, interaction: discord.Interaction) -> None:
        content = self.word.value.lower()
        game = self.view.game

        if content not in game._valid_words:
            return await interaction.response.send_message('That is not a valid word!', ephemeral=True)
        else:
            won = game.parse_guess(content)
            buf = await game.render_image()

            embed = discord.Embed(title='Wordle!', color=self.view.game.color)
            embed.set_image(url='attachment://wordle.png')
            file = discord.File(buf, 'wordle.png')

            if won:
                self.disable_all()
                await interaction.message.reply('Game Over! You won!', mention_author=True)
            elif len(game.guesses) >= 6:
                self.disable_all()
                await interaction.message.reply(f'Game Over! You lose, the word was: **{game.word}**', mention_author=True)
            
            return await interaction.response.edit_message(embed=embed, attachments=[file], view=self.view)

class WordInputButton(discord.ui.Button['WordleView']):

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
                await interaction.response.send_message(f'Game Over! the word was: **{game.word}**')
                return await interaction.message.delete()
            else:
                return await interaction.response.send_modal(WordInput(self.view))

class WordleView(discord.ui.View):
    
    def __init__(self, game: BetaWordle, *, timeout: float):
        super().__init__(timeout=timeout)

        self.game = game
        self.add_item(WordInputButton())
        self.add_item(WordInputButton(cancel_button=True))
    
class BetaWordle(Wordle):
    player: discord.Member

    async def start(self, ctx: commands.Context, *, timeout: Optional[float] = None) -> discord.Message:
        self.player = ctx.author

        buf = await self.render_image()
        embed = discord.Embed(title='Wordle!', color=self.color)
        embed.set_image(url='attachment://wordle.png')

        return await ctx.send(
            embed=embed,
            file=discord.File(buf, 'wordle.png'), 
            view=WordleView(self, timeout=timeout)
        )
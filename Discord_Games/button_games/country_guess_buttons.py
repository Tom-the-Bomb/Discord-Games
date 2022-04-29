from __future__ import annotations

from typing import Union
import random
import os

import discord
from discord.ext import commands

from ..country_guess import CountryGuesser

class CountryInput(discord.ui.Modal, title='Input your guess!'):
    
    def __init__(self, view: CountryView) -> None:
        super().__init__()
        self.view = view

        self.guess = discord.ui.TextInput(
            label='Input your guess',
            style=discord.TextStyle.short,
            required=True,
            max_length=self.view.game.accepted_length,
        )

        self.add_item(self.guess)
        
    async def on_submit(self, interaction: discord.Interaction) -> discord.Message:
        guess = self.guess.value.strip().lower()
        game = self.view.game

        if guess == game.country:
            game.update_guesslog('+ GAME OVER, you won! +')
            await interaction.response.send_message(f'That is correct! The country was `{game.country.title()}`')

            self.view.disable_all()
            game.embed.description = f'```fix\n{game.country.title()}\n```'
            return await interaction.message.edit(view=self.view, embed=game.embed)
        else:
            game.guesses -= 1

            if not game.guesses:
                self.view.disable_all()
                game.update_guesslog('- GAME OVER, you lost -')

                await interaction.message.edit(embed=game.embed, view=self.view)
                return await interaction.response.send_message(f'Game Over! you lost, The country was `{game.country.title()}`')
            else:
                acc = game.get_accuracy(guess)
                game.update_guesslog(
                    f'- [{guess}] was incorrect! but you are ({acc}%) of the way there!\n'
                    f'+ You have {game.guesses} guesses left.\n'
                )

                return await interaction.response.edit_message(embed=game.embed)

class CountryView(discord.ui.View):
    
    def __init__(self, game: BetaCountryGuesser, *, timeout: float = None):
        super().__init__(timeout=timeout)

        self.game = game
    
    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    @discord.ui.button(label='Make a guess!', style=discord.ButtonStyle.blurple)
    async def guess_button(self, interaction: discord.Interaction, _) -> None:
        return await interaction.response.send_modal(CountryInput(self))

    @discord.ui.button(label='hint', style=discord.ButtonStyle.green)
    async def hint_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        hint = self.game.get_hint()
        self.game.hints -= 1
        await interaction.response.send_message(f'Here is your hint: `{hint}`', ephemeral=True)

        if not self.game.hints:
            button.disabled = True
            await interaction.message.edit(view=self)
            
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, _) -> discord.Message:
        self.disable_all()

        self.game.embed.description = f'```fix\n{self.game.country.title()}\n```'
        self.game.update_guesslog('- GAME OVER, CANCELLED -')

        await interaction.response.send_message(f'Game Over! The country was `{self.game.country.title()}`')
        return await interaction.message.edit(view=self, embed=self.game.embed)

class BetaCountryGuesser(CountryGuesser):
    guesslog: str = ''

    def update_guesslog(self, log: str) -> None:
        self.guesslog += log + '\n'
        self.embed.set_field_at(0, name='Guess Log', value=f'```diff\n{self.guesslog}\n```')

    async def start(
        self, 
        ctx: commands.Context, 
        *, 
        embed_color: Union[discord.Color, int] = 0x2F3136,
        ignore_diff_len: bool = False,
        timeout: float = None,
    ) -> discord.Message:

        self.accepted_length = len(self.country) if ignore_diff_len else None

        country_file = random.choice(self.all_countries)
        self.country = country_file.strip().removesuffix('.png').lower()

        country_file = discord.File(os.path.join(self._countries_path, country_file), 'country.png')

        self.embed = discord.Embed(
            title='Guess that country!',
            description=f'```fix\n{self.get_blanks()}\n```',
            color=embed_color,
        )
        self.embed.add_field(name='Guess Log', value='```diff\n\u200b\n```', inline=False)
        self.embed.set_image(url='attachment://country.png')

        view = CountryView(self, timeout=timeout)
        return await ctx.send(embed=self.embed, file=country_file, view=view)
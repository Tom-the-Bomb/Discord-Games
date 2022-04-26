from __future__ import annotations

from typing import Union, Optional
import random

import discord
from discord.ext import commands
from english_words import english_words_set

STAGES: list[str] = ['''
            _________\t
            |/      |\t
            |      😵\t
            |      \\|/\t
            |       |\t
            |      / \\\t
         ___|___
            ''',
            '''
            _________\t
            |/      |\t
            |      😦\t
            |      \\|/\t
            |       |\t
            |      /\t
         ___|___
            ''',
            '''
            _________\t
            |/      |\t
            |      😦\t
            |      \\|/\t
            |       |\t
            |
         ___|___
            ''',
            '''
            --------\t
            |/     |\t
            |     😦\t
            |     \\|\t
            |      |\t
            |
         ___|___
            ''',
            '''
            _________\t
            |/      |\t
            |      😦\t
            |       |\t
            |       |\t
            |
         ___|___
            ''',
            '''
            _________\t
            |/      |\t
            |      😦\t
            |        
            |
            |
         ___|___
            ''',
            '''
            _________\t
            |/      |\t
            |      
            |
            |
            |
         ___|___
            ''', 
            '''
            _________\t
            |/     
            |      
            |
            |
            |
         ___|___
            ''', 
            '''
            ___      \t
            |/      
            |      
            |
            |
            |
         ___|___
            '''
        ]

class Hangman:

    def __init__(self) -> None:
        self._alpha: list[str] = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        self.word: str = random.choice(tuple(english_words_set)).lower()
        self.letters: list[str] = list(self.word)
        
        self.correct: list[str] = [r"\_" for _ in self.word]
        self.wrong_letters: list[str] = []

        self._embed: discord.Embed = discord.Embed(title='HANGMAN')
        self._message: Optional[discord.Message] = None
        self._counter: int = 8

        self.game_over: bool = False

    def lives(self) -> str:
        return f"`{('❤️' * self._counter) or '-'}`"

    async def make_guess(self, guess: str) -> None:

        if guess == self.word:
            self.game_over = True
            self._embed.set_field_at(0, name='Word', value=self.word)
            await self._message.edit(content="**YOU WON**", embed=self._embed)

        elif guess in self.letters:
            self._alpha.remove(guess)
            matches = [a for a, b in enumerate(self.letters) if b == guess]

            for match in matches:
                self.correct[match] = guess

            self._embed.set_field_at(0, name='Word', value=f"{' '.join(self.correct)}")
            await self._message.edit(embed=self._embed)
        else:
            if len(guess) == 1:
                self._alpha.remove(guess)
                self.wrong_letters.append(guess)

            self._counter -= 1

            self._embed.set_field_at(1, name='Wrong letters', value=f"{', '.join(self.wrong_letters)}")
            self._embed.set_field_at(2, name='Lives left', value=self.lives(), inline=False)
            self._embed.description = f"```\n{STAGES[self._counter]}\n```"
            await self._message.edit(embed=self._embed)

    async def check_win(self) -> bool:

        if self._counter == 0:
            self.game_over = True
            self._embed.set_field_at(0, name='Word', value=self.word)
            await self._message.edit(content="**YOU LOST**", embed=self._embed)

        elif r'\_' not in self.correct:
            self.game_over = True
            self._embed.set_field_at(0, name='Word', value=self.word)
            await self._message.edit(content="**YOU WON**", embed=self._embed)

        return self.game_over

    def initialize_embed(self) -> discord.Embed:
        self._embed.description = f"```\n{STAGES[self._counter]}\n```"
        self._embed.color = self.embed_color
        self._embed.add_field(name='Word', value=f"{' '.join(self.correct)}")
        
        wrong_letters = ', '.join(self.wrong_letters) or '  \u200b'
        self._embed.add_field(name='Wrong letters', value=wrong_letters)
        self._embed.add_field(name='Lives left', value=self.lives(), inline=False)
        return self._embed

    async def start(self, ctx: commands.Context, *, delete_after_guess: bool = False, embed_color: Union[discord.Color, int] = 0x2F3136, **kwargs):
        
        self.player = ctx.author
        self.embed_color = embed_color
        embed = self.initialize_embed()

        self._message = await ctx.send(embed=embed, **kwargs)

        while True:

            def check(m: discord.Message) -> bool:
                if m.channel == ctx.channel and m.author == self.player:
                    return (len(m.content) == 1 and m.content.lower() in self._alpha) or (m.content.lower() == self.word)

            message = await ctx.bot.wait_for("message", check=check)

            await self.make_guess(message.content.lower())
            gameover = await self.check_win()

            if gameover:
                return

            if delete_after_guess:
                try:
                    await message.delete()
                except discord.DiscordException:
                    pass
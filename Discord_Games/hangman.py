import discord
from discord.ext import commands
from typing import Union

import random
from english_words import english_words_set

stages = ['''
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

    def __init__(self):
        self._alpha = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        self.word    = random.choice(list(english_words_set)).lower()
        self.letters = [l for l in self.word]
        self.correct = [r"\_" for __ in self.word]
        self.wrong_letters = []
        self._embed   = discord.Embed(title='HANGMAN')
        self._message = None
        self._counter = 8
        self.GameOver = False
        self.lives    = lambda : f"`{('❤️' * self._counter) or '-'}`"

    async def MakeGuess(self, guess: str) -> None:

        if guess == self.word:
            self.GameOver = True
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
            self._alpha.remove(guess)
            self._counter -= 1
            self.wrong_letters.append(guess)
            self._embed.set_field_at(1, name='Wrong letters', value=f"{', '.join(self.wrong_letters)}")
            self._embed.set_field_at(2, name='Lives left', value=self.lives(), inline=False)
            self._embed.description = f"```\n{stages[self._counter]}\n```"
            await self._message.edit(embed=self._embed)

        return

    async def CheckWin(self):

        if self._counter == 0:
            self.GameOver = True
            self._embed.set_field_at(0, name='Word', value=self.word)
            await self._message.edit(content="**YOU LOST**", embed=self._embed)

        elif r'\_' not in self.correct:
            self.GameOver = True
            self._embed.set_field_at(0, name='Word', value=self.word)
            await self._message.edit(content="**YOU WON**", embed=self._embed)

        return self.GameOver

    async def start(self, ctx: commands.Context, *, delete_after_guess: bool = False, color: Union[discord.Color, int] = 0x2F3136, **kwargs):

        self._embed.description = f"```\n{stages[self._counter]}\n```"
        self._embed.color = color
        self._embed.add_field(name='Word', value=f"{' '.join(self.correct)}")
        
        wrong_letters = ', '.join(self.wrong_letters) or '  \u200b'
        self._embed.add_field(name='Wrong letters', value=wrong_letters)
        self._embed.add_field(name='Lives left', value=self.lives(), inline=False)
        self._message = await ctx.send(embed=self._embed, **kwargs)

        while True:

            def check(m):
                if m.channel == ctx.channel and m.author == ctx.author:
                    return (len(m.content) == 1 and m.content.lower() in self._alpha) or (m.content.lower() == self.word)

            message = await ctx.bot.wait_for("message", check=check)

            await self.MakeGuess(message.content.lower())
            gameover = await self.CheckWin()

            if gameover:
                return

            if delete_after_guess:
                try:
                    await message.delete()
                except:
                    pass
        return 
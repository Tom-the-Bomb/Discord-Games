from __future__ import annotations

from typing import Union
import random

import discord
from discord.ext import commands

class RockPaperScissors:
    message: discord.Message
    OPTIONS: tuple[str, str, str] = ('\U0001faa8', '\U00002702', '\U0001f4f0')
    BEATS: dict[str, str] = {
        OPTIONS[0]: OPTIONS[1],
        OPTIONS[1]: OPTIONS[2],
        OPTIONS[2]: OPTIONS[0],
    }

    def check_win(self, bot_choice: str, user_choice: str) -> bool:
        return self.BEATS[user_choice] == bot_choice
    
    async def wait_for_choice(self, ctx: commands.Context) -> str:
         
        def check(reaction: discord.Reaction, user: discord.Member) -> bool:
            return (
                str(reaction.emoji) in self.OPTIONS and 
                user == ctx.author and 
                reaction.message == self.message
            )
        
        reaction, _ = await ctx.bot.wait_for('reaction_add', check=check)
        return str(reaction.emoji)

    async def start(self, ctx: commands.Context, *, embed_color: Union[discord.Color, int] = 0x2F3136) -> discord.Message:
        embed = discord.Embed(
            title='Rock Paper Scissors',
            description='React to play!',
            color=embed_color,
        )
        self.message = await ctx.send(embed=embed)
        
        for option in self.OPTIONS:
            await self.message.add_reaction(option)

        bot_choice = random.choice(self.OPTIONS)
        user_choice = await self.wait_for_choice(ctx)
        
        if user_choice == bot_choice:
            embed.description = f'**Tie!**\nWe both picked {user_choice}'  
        else:
            if self.check_win(bot_choice, user_choice):
                embed.description = f'**You Won!**\nYou picked {user_choice} and I picked {bot_choice}.'
            else:
                embed.description = f'**You Lost!**\nI picked {bot_choice} and you picked {user_choice}.'
                
        return await self.message.edit(embed=embed)
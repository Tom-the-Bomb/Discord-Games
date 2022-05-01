import json
import pathlib

import discord
from discord.ext import commands

from Discord_Games import button_games

bot = commands.Bot(command_prefix='!!', intents=discord.Intents.all())

@bot.command(name='test')
async def test(ctx: commands.Context, member: discord.Member):

    game = button_games.BetaBattleShip(ctx.author, member)
    await game.start(ctx)

if __name__ == '__main__':
    with open(f'{pathlib.Path(__file__).parent}/bot_config.json') as bot_config:
        bot_config = json.load(bot_config)
        token = bot_config['TOKEN']
    
    bot.run(token)
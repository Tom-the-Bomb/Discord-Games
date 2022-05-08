import json
import pathlib

import discord
from discord.ext import commands

import discord_games as games
from discord_games import button_games

bot = commands.Bot(command_prefix='!!', intents=discord.Intents.all())

@bot.command(name='test', aliases=['t'])
@commands.is_owner()
async def test(ctx: commands.Context, win_at: int = 8192):

    game = button_games.BetaTwenty48()
    await game.start(ctx, win_at=win_at, delete_button=True)

if __name__ == '__main__':
    with open(f'{pathlib.Path(__file__).parent}/bot_config.json') as bot_config:
        bot_config = json.load(bot_config)
        token = bot_config['TOKEN']
    
    bot.run(token)
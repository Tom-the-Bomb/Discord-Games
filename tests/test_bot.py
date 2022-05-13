import json
import pathlib

import discord
from discord.ext import commands

import discord_games as games
from discord_games import button_games

class TestBot(commands.Bot):

    async def setup_hook(self) -> None:
        await self.load_extension('jishaku')

bot = TestBot(command_prefix='!!', intents=discord.Intents.all())

@bot.command(name='test', aliases=['t'])
@commands.is_owner()
async def test(ctx: commands.Context) -> None:

    game = button_games.Boggle()
    await game.start(ctx)
    await ctx.reply('done!', mention_author=False)

if __name__ == '__main__':
    with open(f'{pathlib.Path(__file__).parent}/bot_config.json') as bot_config:
        bot_config = json.load(bot_config)
        token = bot_config['TOKEN']
    
    bot.run(token)
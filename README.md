# Discord-Games

A library for easily adding games to your [discord.py](https://github.com/Rapptz/discord.py) bot.

## Installation

From PyPI:

```bash
pip install discord-games
```

Or from GitHub for the latest changes:

```bash
pip install git+https://github.com/Tom-the-Bomb/Discord-Games.git
```

Requires **Python 3.9+** and **discord.py 1.7+** (button-based games require **2.0+**).

## Available Games

### Reaction-based

These use message reactions for input.

| Game                | Class               |
| ------------------- | ------------------- |
| Tic-Tac-Toe         | `Tictactoe`         |
| Connect Four        | `ConnectFour`       |
| Rock-Paper-Scissors | `RockPaperScissors` |
| Chess               | `Chess`             |
| Battleship          | `BattleShip`        |
| Hangman             | `Hangman`           |
| Akinator            | `Akinator`          |
| 2048                | `Twenty48`          |
| Wordle              | `Wordle`            |
| Type Racer          | `TypeRacer`         |
| Country Guesser     | `CountryGuesser`    |
| Reaction Test       | `ReactionGame`      |

### Button-based

These use discord UI components (buttons/modals). Available under `discord_games.button_games`.

| Game                | Class                   |
| ------------------- | ----------------------- |
| Tic-Tac-Toe         | `BetaTictactoe`         |
| Connect Four        | `BetaConnectFour`       |
| Rock-Paper-Scissors | `BetaRockPaperScissors` |
| Chess               | `BetaChess`             |
| Battleship          | `BetaBattleShip`        |
| Hangman             | `BetaHangman`           |
| Akinator            | `BetaAkinator`          |
| 2048                | `BetaTwenty48`          |
| Wordle              | `BetaWordle`            |
| Country Guesser     | `BetaCountryGuesser`    |
| Reaction Test       | `BetaReactionGame`      |
| Memory Game         | `MemoryGame`            |
| Number Slider       | `NumberSlider`          |
| Lights Out          | `LightsOut`             |
| Boggle              | `Boggle`                |
| Chimp Test          | `ChimpTest`             |
| Verbal Memory       | `VerbalMemory`          |
| Number Memory       | `NumberMemory`          |

## Quick Start

```python
import discord
from discord.ext import commands
from discord_games import button_games

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def wordle(ctx):
    game = button_games.BetaWordle()
    await game.start(ctx)

@bot.command()
async def tictactoe(ctx, member: discord.Member):
    game = button_games.BetaTictactoe(cross=ctx.author, circle=member)
    await game.start(ctx)
```

Every game follows the same pattern:

1. Import and create the game class
2. Call `await game.start(ctx)` with any optional arguments

See the full [examples file](https://github.com/Tom-the-Bomb/Discord-Games/blob/master/examples/examples.py) for more.

## License

[MIT](LICENSE)

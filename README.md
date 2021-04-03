# Discord-Games
---
Discord-Games is a lib made for discord-bot makers.
It offers premade classes for your bot to use.

### Connect 4 Example

```py
from Discord_Games import connect_four

@commands.command(name="connectfour")
async def connectfour(self, ctx, member: discord.Member):
    game = connect_four.ConnectFour(
        red  = ctx.author,         # "red" player
        blue = member,             # "blue" player
    )
    await game.start(ctx, remove_reaction_after=True) #starts the game

```
Or for a more custom setup you can create a class that inherits from the "Game" class
- You can overwrite certain methods such as the `start` method.
**Methods for connect-four and tictactoe**
- `BoardString` - Returns a formatted version of the board-array
- `make_embed`  - builds the embed that specifies who's turn it is etc.
- `MakeMove`    - Edits the array after a move and changes the turn attr
- `GameOver`    - Checks if the game is over and changes the winner attr
- `start`       - starts the game and sets up the `wait_for` and method calls

**Methods for Hangman**
- `MakeGuess`   - modifies the attrs based on player input
- `CheckWin`    - Checks if the user won
- `start`       - starts the game and sets up `wait_for` and method calls

**Coming soon**
- Chess
- 2048 

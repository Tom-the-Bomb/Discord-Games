# Discord-Games

This is a very simple package for implementing games into your discord bot
Dont expect too much from it
You can install it with

```
$ pip install git+https://github.com/Tom-the-Bomb/Discord-Games.git
```

__using it is fairly easy__
- Import the specific module from the main package
- Initialize the game class (with the needed arguments)
- Call the start method (with the needed arguments) to start the game

### Example

- **read the examples!!** [here](https://github.com/Tom-the-Bomb/Discord-Games/blob/master/examples/examples.py)

```py
from Discord_Games import ChessGame 

# do your bot stuff

@bot.command() #create a command
async def chess(ctx, member: discord.Member):
    game = ChessGame.Chess( #initialize a game instance
        white = ctx.author, #provide the white player
        black = member      #provide the black player
    )
    await game.start(ctx, 
        timeout=60, 
        add_reaction_after_move=True
    ) #start the game

#other games are very similar

```
---
*(Im not making documentation for this since this wasnt meant to be a real lib in the first place)*
*(It was intended for fun and for my bot only at the start)*
*(You can refer to the source if you want)*

# Discord-Games

Discord-Games is a lib made for discord-bot makers.
It offers premade classes for your bot to use.
### Installing the package
```
$ pip install git+https://github.com/Tom-the-Bomb/Discord-Games.git
```
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

### 2048
2048 example
```py
from Discord_Games import twenty_48

game = twenty_48.Twenty48()
game.update_emojis(
    #a dictionary with number as a key and display value as value
    #ex: {"2": "<:two:123238299123342>"...}
)
await game.start(ctx, remove_reaction_after = True, delete_button = False, embed = discord.Embed())
# remove_reaction_after removes the reaction after add
# delete_button adds a stop_button to stop the game on click
# the embed kwarg is an example of the **kwargs
```
- For 2048 you need to call the `update_emojis` method and pass in a dict with the `block number` as a key and the `emoji` as the value
- If you do not want emojis to display the board you can do `"2": " 2 "` etc. to get the raw value displayed *(might look ugly though)*
- If you do not call the `update_emojis` method properly you may run into errors.



### chess
- start signature (Example)
`async def start(self, ctx: commands.Context, *, timeout: int = None, color: Union[int, discord.Color] = 0x2F3136, add_reaction_after_move: bool = False, **kwargs):`
- aside from that chess is much similar to all the other games and the same logic applies when using the classes



All the start methods accept any `**kwargs` and those get passed into the `.send()` in the function, 
so you can add any kwargs you might want to pass in to the message like `embed=` etc.
### Typeracer
```py
game = typeracer.TypeRacer()
await game.start(
    ctx, 
    embed_color=0x2F3136,                     #embed color
    path_to_text_font='assets/font_file.ttf', #or use arial.ttf if you dont have one
    timeout=100, 
    mode="sentence"
)
```
### Akinator
same as the previous games
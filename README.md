# Discord-Games

This is a simple package for implementing **games** into your [discord.py](https://github.com/Rapptz/discord.py) bot<br/>
You can install it with:
```bash
$ py -m pip install git+https://github.com/Tom-the-Bomb/Discord-Games.git
```
---
## The basic usage of the library goes like this
- Import the specific game `class` from the library
    - Ex: `from Discord_Games import Wordle`
- Initialize the game class (with the appropriate arguments, normally none but varies from game to game)
    - Ex: `game = Wordle()`
- Call the start method (with the appropriate arguments) to start the game
    - Ex: `await game.start(ctx)` (ctx is always a required argument, rest are optional)<br/>
- refer to the source for more info on the arguments you *could* pass

- #### read the examples [here](https://github.com/Tom-the-Bomb/Discord-Games/blob/master/examples/examples.py)<br/>
---
### Documentation
Coming soon...!
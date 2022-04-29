"""
Discord-Games
"""

from typing import NamedTuple

from .aki import Akinator
from .battleship import BattleShip
from .chess_game import Chess
from .connect_four import ConnectFour
from .hangman import Hangman
from .tictactoe import Tictactoe
from .twenty_48 import Twenty48
from .typeracer import TypeRacer
from .rps import RockPaperScissors
from .reaction_test import ReactionGame
from .country_guess import CountryGuesser

__all__ = (
    'Akinator',
    'BattleShip',
    'Chess', 
    'ConnectFour',
    'Hangman', 
    'Tictactoe',
    'Twenty48', 
    'TypeRacer',
    'RockPaperScissors',
    'ReactionGame',
    'CountryGuesser',
)

__title__ = "Discord_Games"
__version__  = "1.9.22"
__author__   = "Tom-the-Bomb"
__license__  = "MIT"
__copyright__ = "Copyright 2021-present Tom-the-Bomb"

class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int

version_info: VersionInfo = VersionInfo(
    major=1, 
    minor=9, 
    micro=22,
)

del NamedTuple, VersionInfo
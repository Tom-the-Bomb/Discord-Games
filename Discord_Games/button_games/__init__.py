"""
This folder contains games that require discord.py v2.0.0 + to be used
they utilize UI components such as buttons.
"""

from .aki_buttons import BetaAkinator
from .twenty_48_buttons import BetaTwenty48
from .wordle_buttons import BetaWordle
from .tictactoe_buttons import BetaTictactoe

__all__ = (
    'BetaAkinator',
    'BetaTwenty48',
    'BetaWordle',
    'BetaTictactoe',
)
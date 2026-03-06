from __future__ import annotations

from typing import Optional, Union
import random

import discord
from discord.ext import commands

from ..rps import RockPaperScissors
from ..utils import DiscordColor, DEFAULT_COLOR, BaseView


class RPSButton(discord.ui.Button["RPSView"]):
    def __init__(self, emoji: str, *, style: discord.ButtonStyle) -> None:
        super().__init__(
            label="\u200b",
            emoji=emoji,
            style=style,
        )

    def get_choice(
        self, user: Union[discord.User, discord.Member], other: bool = False
    ) -> Optional[str]:
        assert self.view is not None
        game = self.view.game
        if other:
            return game.player2_choice if user == game.player1 else game.player1_choice
        else:
            return game.player1_choice if user == game.player1 else game.player2_choice

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        game = self.view.game
        players = (game.player1, game.player2) if game.player2 else (game.player1,)

        if interaction.user not in players:
            await interaction.response.send_message(
                "This is not your game!", ephemeral=True
            )
            return
        else:
            if not game.player2:
                bot_choice = random.choice(game.OPTIONS)
                assert self.emoji is not None and self.emoji.name is not None
                user_choice = self.emoji.name

                if user_choice == bot_choice:
                    game.embed.description = f"**Tie!**\nWe both picked {user_choice}"
                else:
                    if game.check_win(bot_choice, user_choice):
                        game.embed.description = f"**You Won!**\nYou picked {user_choice} and I picked {bot_choice}."
                    else:
                        game.embed.description = f"**You Lost!**\nI picked {bot_choice} and you picked {user_choice}."

                self.view.disable_all()
                self.view.stop()

            else:
                if self.get_choice(interaction.user):
                    await interaction.response.send_message(
                        "You have chosen already!", ephemeral=True
                    )
                    return

                other_player_choice = self.get_choice(interaction.user, other=True)

                assert self.emoji is not None and self.emoji.name is not None
                if interaction.user == game.player1:
                    game.player1_choice = self.emoji.name

                    if not other_player_choice:
                        game.embed.description = (
                            (game.embed.description or "")
                            + f"\n\n{game.player1.mention} has chosen...\n*Waiting for {game.player2.mention} to choose...*"
                        )
                else:
                    game.player2_choice = self.emoji.name

                    if not other_player_choice:
                        game.embed.description = (
                            (game.embed.description or "")
                            + f"\n\n{game.player2.mention} has chosen...\n*Waiting for {game.player1.mention} to choose...*"
                        )

                if game.player1_choice and game.player2_choice:
                    result = (
                        "You both tied!"
                        if game.player1_choice == game.player2_choice
                        else f"**{game.check_human_win()} Won!**"
                    )
                    game.embed.description = (
                        f"{result}"
                        f"\n\n{game.player1.mention} chose {game.player1_choice}."
                        f"\n{game.player2.mention} chose {game.player2_choice}."
                    )

                    self.view.disable_all()
                    self.view.stop()

            await interaction.response.edit_message(embed=game.embed, view=self.view)


class RPSView(BaseView):
    game: BetaRockPaperScissors

    def __init__(
        self,
        game: BetaRockPaperScissors,
        *,
        button_style: discord.ButtonStyle,
        timeout: Optional[float],
    ) -> None:
        super().__init__(timeout=timeout)

        self.button_style = button_style
        self.game = game

        for option in self.game.OPTIONS:
            self.add_item(RPSButton(option, style=self.button_style))


class BetaRockPaperScissors(RockPaperScissors):
    """Rock-Paper-Scissors, button-based.

    Same as :class:`RockPaperScissors` but uses emoji buttons
    instead of reactions.
    """

    player1: Union[discord.User, discord.Member]
    embed: discord.Embed

    def __init__(
        self, other_player: Optional[Union[discord.User, discord.Member]] = None
    ) -> None:
        self.player2: Optional[Union[discord.User, discord.Member]] = other_player

        if self.player2:
            self.player1_choice: Optional[str] = None
            self.player2_choice: Optional[str] = None

    def check_human_win(self) -> Union[discord.User, discord.Member]:
        assert self.player1_choice is not None
        assert self.player2 is not None
        return (
            self.player1
            if self.BEATS[self.player1_choice] == self.player2_choice
            else self.player2
        )

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        button_style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        embed_color: DiscordColor = DEFAULT_COLOR,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        """
        starts the rock-paper-scissors(buttons) game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        button_style : discord.ButtonStyle, optional
            the primary button style to use, by default discord.ButtonStyle.blurple
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game mesage
        """
        self.player1 = ctx.author

        self.embed = discord.Embed(
            title="Rock Paper Scissors",
            description="Select a button to play!",
            color=embed_color,
        )

        self.view = RPSView(self, button_style=button_style, timeout=timeout)
        self.message = await ctx.send(embed=self.embed, view=self.view)
        self.view.message = self.message

        await self.view.wait()
        return self.message

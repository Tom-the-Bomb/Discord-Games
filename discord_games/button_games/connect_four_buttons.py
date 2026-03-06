from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from ..connect_four import ConnectFour, BLANK
from ..utils import BaseView, DiscordColor, DEFAULT_COLOR


class ConnectFourButton(discord.ui.Button["ConnectFourView"]):
    def __init__(self, number: int, style: discord.ButtonStyle) -> None:
        self.number = number

        super().__init__(
            label=str(self.number),
            style=style,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        game = self.view.game

        if interaction.user not in (game.red_player, game.blue_player):
            await interaction.response.send_message(
                "You are not part of this game!", ephemeral=True
            )
            return

        if interaction.user != game.turn:
            await interaction.response.send_message(
                "It is not your turn yet!", ephemeral=True
            )
            return

        if game.board[0][self.number - 1] != BLANK:
            await interaction.response.send_message(
                "Selected column is full!", ephemeral=True
            )
            return

        game.place_move(self.number - 1, interaction.user)

        status = game.is_game_over()

        embed = game.make_embed(status=status)

        if status:
            self.view.disable_all()
            self.view.stop()

        await interaction.response.edit_message(
            view=self.view,
            embed=embed,
            content=game.board_string(),
        )


class ConnectFourView(BaseView):
    game: ConnectFour

    def __init__(self, game: BetaConnectFour, timeout: Optional[float]) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        for i in range(1, 8):
            self.add_item(ConnectFourButton(i, self.game.button_style))


class BetaConnectFour(ConnectFour):
    """Connect Four, button-based.

    Same as :class:`ConnectFour` but uses numbered buttons
    to select columns.
    """

    async def start(  # type: ignore[override]
        self,
        ctx: commands.Context[commands.Bot],
        *,
        timeout: Optional[float] = None,
        button_style: discord.ButtonStyle = discord.ButtonStyle.blurple,
        embed_color: DiscordColor = DEFAULT_COLOR,
    ) -> discord.Message:
        """
        starts the Connect-4(buttons) game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        timeout : Optional[float], optional
            the timeout for when waiting, by default None
        button_style : discord.ButtonStyle, optional
            the primary button style to use, by default discord.ButtonStyle.red
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.embed_color = embed_color
        self.button_style = button_style

        self.view = ConnectFourView(self, timeout=timeout)

        embed = self.make_embed(status=False)
        self.message = await ctx.send(
            content=self.board_string(),
            view=self.view,
            embed=embed,
        )

        await self.view.wait()
        return self.message

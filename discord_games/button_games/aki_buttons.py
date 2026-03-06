from __future__ import annotations

from typing import Optional, ClassVar, TYPE_CHECKING

import discord
from discord.ext import commands
from akinator import CantGoBackAnyFurther

from ..aki import Akinator
from ..utils import DiscordColor, DEFAULT_COLOR, BaseView

if TYPE_CHECKING:
    from typing import Literal


class AkiButton(discord.ui.Button["AkiView"]):
    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        assert self.label is not None
        await self.view.process_input(interaction, self.label.lower())


class AkiView(BaseView):
    OPTIONS: ClassVar[dict[str, discord.ButtonStyle]] = {
        "yes": discord.ButtonStyle.green,
        "no": discord.ButtonStyle.red,
        "idk": discord.ButtonStyle.blurple,
        "probably": discord.ButtonStyle.gray,
        "probably not": discord.ButtonStyle.gray,
    }

    def __init__(self, game: BetaAkinator, *, timeout: Optional[float]) -> None:
        super().__init__(timeout=timeout)

        self.embed_color: Optional[DiscordColor] = None
        self.game = game

        for label, style in self.OPTIONS.items():
            self.add_item(AkiButton(label=label, style=style))

        if self.game.back_button:
            delete = AkiButton(label="back", style=discord.ButtonStyle.red, row=1)
            self.add_item(delete)

        if self.game.delete_button:
            delete = AkiButton(label="Cancel", style=discord.ButtonStyle.red, row=1)
            self.add_item(delete)

    async def process_input(
        self, interaction: discord.Interaction, answer: str
    ) -> None:
        game = self.game

        if interaction.user != game.player:
            await interaction.response.send_message(
                content="This isn't your game", ephemeral=True
            )
            return

        if answer == "cancel":
            assert interaction.message is not None
            await interaction.message.reply("Session ended", mention_author=True)
            self.stop()
            await interaction.message.delete()
            return

        # defer to avoid 3s interaction timeout while waiting for the akinator API
        await interaction.response.defer()

        if answer == "back":
            try:
                await game.aki.back()
                embed = game.build_embed(instructions=False)
            except CantGoBackAnyFurther:
                await interaction.followup.send(
                    "I cant go back any further!", ephemeral=True
                )
                return
        else:
            await game.aki.answer(answer)

            if game.win_at is not None and game.aki.progression >= game.win_at:  # type: ignore[operator]
                self.disable_all()
                embed = await game.win()
                self.stop()
            else:
                embed = game.build_embed(instructions=False)
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            pass


class BetaAkinator(Akinator):
    """Akinator game, button-based.

    Same as :class:`Akinator` but uses UI buttons
    instead of reactions.
    """

    async def start(  # type: ignore[override]
        self,
        ctx: commands.Context[commands.Bot],
        *,
        back_button: bool = False,
        delete_button: bool = False,
        embed_color: DiscordColor = DEFAULT_COLOR,
        win_at: int = 80,
        timeout: Optional[float] = None,
        aki_theme: Literal["c", "a", "o"] = "c",
        aki_language: str = "en",
        child_mode: bool = True,
    ) -> discord.Message:
        """
        starts the Akinator(buttons) game

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            the context of the invokation command
        back_button : bool, optional
            indicates whether or not to add a back button, by default False
        delete_button : bool, optional
            indicates whether to add a stop button to stop the game, by default False
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        win_at : int, optional
            indicates when to tell the akinator to make it's guess, by default 80
        timeout : Optional[float], optional
            the timeout for the view, by default None
        aki_theme : Literal["c", "a", "o"], optional
            the akinator theme: "c" (characters), "a" (animals), "o" (objects), by default "c"
        aki_language : str, optional
            the language code (e.g. "en", "fr", "es") or full name (e.g. "english"), by default "en"
        child_mode : bool, optional
            indicates to filter out NSFW content or not, by default True

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.back_button = back_button
        self.delete_button = delete_button
        self.embed_color = embed_color

        self.player = ctx.author
        self.win_at = win_at
        self.view = AkiView(self, timeout=timeout)

        await self.aki.start_game(
            language=aki_language,
            child_mode=child_mode,
            theme=aki_theme,
        )

        embed = self.build_embed(instructions=False)
        self.message = await ctx.send(embed=embed, view=self.view)

        await self.view.wait()
        return self.message

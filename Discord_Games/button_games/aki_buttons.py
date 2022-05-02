from __future__ import annotations

from typing import Optional, ClassVar

import discord
from discord.ext import commands

from ..aki import Akinator
from ..utils import DiscordColor, DEFAULT_COLOR

class AkiButton(discord.ui.Button):
    view: AkiView

    async def callback(self, interaction: discord.Interaction) -> None:
        return await self.view.process_input(interaction, self.label.lower())

class AkiView(discord.ui.View):
    OPTIONS: ClassVar[dict[str, discord.ButtonStyle]] = {
        'yes': discord.ButtonStyle.green,
        'no': discord.ButtonStyle.red,
        'idk': discord.ButtonStyle.blurple,
        'probably': discord.ButtonStyle.gray,
        'probably not': discord.ButtonStyle.gray,
    }

    def __init__(self, game: BetaAkinator, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.embed_color: Optional[DiscordColor] = None
        self.game = game

        for label, style in self.OPTIONS.items():
            self.add_item(AkiButton(label=label, style=style))

        if self.game.delete_button:
            delete = AkiButton(
                label='Cancel', 
                style=discord.ButtonStyle.red, 
                row=1
            )
            self.add_item(delete)

    def disable_all(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True

    async def process_input(self, interaction: discord.Interaction, answer: str) -> None:

        game = self.game

        if interaction.user != game.player:
            return await interaction.response.send_message(content="This isn't your game", ephemeral=True)
        
        if answer == "cancel":
            await interaction.message.delete()
            return await interaction.message.reply("Session ended", mention_author=True)

        else:
            game.questions += 1
            await game.aki.answer(answer)
            
            if game.aki.progression >= game.win_at:
                self.disable_all()
                embed = await game.win()
            else:
                embed = game.build_embed(instructions=False)

            return await interaction.response.edit_message(embed=embed, view=self)
        
class BetaAkinator(Akinator):

    async def start(
        self, 
        ctx: commands.Context,
        *,
        delete_button: bool = False,
        embed_color: DiscordColor = DEFAULT_COLOR,
        win_at: int = 80, 
        timeout: Optional[float] = None,
        child_mode: bool = True,
    ) -> discord.Message:

        self.delete_button = delete_button
        self.embed_color = embed_color

        self.player = ctx.author
        self.win_at = win_at
        self.view = AkiView(self, timeout=timeout)

        await self.aki.start_game(child_mode=child_mode)

        embed = self.build_embed(instructions=False)
        self.message = await ctx.send(embed=embed, view=self.view)

        return self.message
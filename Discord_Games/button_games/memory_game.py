from __future__ import annotations

from typing import Optional, ClassVar
import random
import asyncio

import discord
from discord.ext import commands

class MemoryButton(discord.ui.Button):
    view: MemoryView

    def __init__(self, emoji: str, *, style: discord.ButtonStyle, row: int = 0) -> None:
        self.value = emoji

        super().__init__(
            label='\u200b',
            style=style,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        
        if opened := self.view.opened:
            self.emoji = self.value
            self.disabled = True
            await interaction.response.edit_message(view=self.view)

            if opened.value != self.value:
                await asyncio.sleep(self.view.pause_time)

                opened.emoji = None
                opened.disabled = False

                self.emoji = None
                self.disabled = False
                self.view.opened = None

                return await interaction.message.edit(view=self.view)
            else:
                self.view.opened = None

                if all(button.disabled for button in self.view.children):
                    return await interaction.message.edit(content='Game Over, Congrats!', view=self.view)
        else:
            self.emoji = self.value
            self.view.opened = self
            self.disabled = True
            return await interaction.response.edit_message(view=self.view)

class MemoryView(discord.ui.View):
    board: list[list[str]]
    DEFAULT_ITEMS: ClassVar[list[str]] = ['🥝', '🍓', '🍹', '🍋', '🥭', '🍎', '🍊', '🍍', '🍑', '🍇', '🍉', '🥬']
    
    def __init__(
        self, 
        items: list[str], 
        *, 
        button_style: discord.ButtonStyle,
        pause_time: float,
        timeout: float = None,
    ) -> None:

        super().__init__(timeout=timeout)

        self.button_style = button_style
        self.pause_time = pause_time
        self.opened: Optional[MemoryButton] = None
        
        if not items:
            items = self.DEFAULT_ITEMS
        assert len(items) == 12

        items *= 2
        random.shuffle(items)
        random.shuffle(items)
        items.insert(12, None)

        self.board = [items[i:i + 5] for i in range(0, len(items), 5)]

        for i, row in enumerate(self.board):
            for item in row:
                button = MemoryButton(item, style=self.button_style, row=i)
                
                if not item:
                    button.disabled = True
                self.add_item(button)

class MemoryGame:

    async def start(
        self, 
        ctx: commands.Context,
        *,
        items: list[str] = [],
        pause_time: float = 0.7,
        button_style: discord.ButtonStyle = discord.ButtonStyle.red,
        timeout: float = None,
    ) -> discord.Message:

        view = MemoryView(
            items=items, 
            button_style=button_style, 
            pause_time=pause_time,
            timeout=timeout
        )
        return await ctx.send(view=view)
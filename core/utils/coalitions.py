from __future__ import annotations
import discord
from core import Coalition
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from core import Server
    from services import DCSServerBot

__all__ = [
    "get_sides"
]


def get_sides(bot: DCSServerBot, ctx: Union[discord.Interaction, discord.Message], server: Server) -> list[str]:
    if isinstance(ctx, discord.Interaction):
        user = ctx.user
    else:
        user = ctx.author
    channel = ctx.channel

    sides = []
    if 'coalitions' in server.locals:
        da_roles = [bot.get_role(x) for x in bot.roles['DCS Admin']]
        gm_roles = [bot.get_role(x) for x in bot.roles['GameMaster']]
        blue_role = bot.get_role(server.locals['coalitions']['blue_role'])
        red_role = bot.get_role(server.locals['coalitions']['blue_role'])
        everyone = discord.utils.get(channel.guild.roles, name="@everyone")

        # check, which coalition specific data can be displayed in the questioned channel by that user
        for role in user.roles:
            if (role in gm_roles or role in da_roles) and \
                    not channel.overwrites_for(everyone).read_messages and \
                    not channel.overwrites_for(blue_role).read_messages and \
                    not channel.overwrites_for(red_role).read_messages:
                sides = [Coalition.BLUE, Coalition.RED]
                break
            elif (role in gm_roles or role in da_roles or role == blue_role) \
                    and channel.overwrites_for(blue_role).send_messages and \
                    not channel.overwrites_for(red_role).read_messages:
                sides = [Coalition.BLUE]
                break
            elif (role in gm_roles or role in da_roles or role == red_role) \
                    and channel.overwrites_for(red_role).send_messages and \
                    not channel.overwrites_for(blue_role).read_messages:
                sides = [Coalition.RED]
                break
    else:
        sides = [Coalition.BLUE, Coalition.RED]
    return sides

from typing import Iterable
import asyncio

from discord.ext import commands


async def channel_message(ctx: commands.Context, message: str) -> Exception | None:
    try:
        await ctx.send(message)

    except Exception as e:
        return e


async def mass_channel_message(
    ctx: commands.Context, messages: Iterable[str]
) -> list[Exception | None]:
    message_results = await asyncio.gather(
        *(channel_message(ctx, message) for message in messages)
    )
    return message_results

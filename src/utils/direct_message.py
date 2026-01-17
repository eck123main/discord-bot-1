import asyncio
from discord import Member
from typing import Callable


async def direct_message(member: Member, message: str) -> Exception | None:
    try:
        await member.send(message)
    except Exception as e:
        return e


async def dynamic_direct_message(
    member: Member, dynamic_message: Callable[[Member], str]
) -> Exception | None:
    try:
        await member.send(dynamic_message(member))
    except Exception as e:
        return e


async def dynamic_mass_direct_message(
    members: list[Member], dynamic_message: Callable[[Member], str]
) -> list[Exception | None]:
    message_results = await asyncio.gather(
        *(
            direct_message(
                member,
                dynamic_message(member),
            )
            for member in members
        )
    )
    return message_results


async def dynamic_test_mass_direct_message(
    members: list[Member], dynamic_message: Callable[[Member], str]
) -> list[tuple[Member, Exception]]:
    message_results = await dynamic_mass_direct_message(members, dynamic_message)

    # Check for messages that failed to send
    failed_messages = [(member, e) for member, e in zip(members, message_results) if e]

    return failed_messages


def fail_message(member: Member, e: Exception) -> str:
    return f"Failed to send a message to {member.mention}!\nError: {e}"

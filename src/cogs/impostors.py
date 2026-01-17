from discord import Member
from discord.ext import commands
from core import bot
from custom_types.discord import MemberId
from custom_types.impostors import GameId
from utils.direct_message import (
    dynamic_test_mass_direct_message,
    fail_message,
)
from utils.channel_message import mass_channel_message, channel_message


class Impostors(commands.Cog):
    def __init__(self, bot: bot.Bot):
        self.bot = bot
        self.service = bot.impostors_service

    @commands.command(
        "impostor",
        help="""
!impostor <USERS> <NO. IMPOSTORS> <CATEGORY>
    CATEGORY:
        - fruits
        - animals
        - colours
        - cr (Clash Royale)
        - minecraft
        - fnd (Foods & Drinks)
""",
    )
    async def impostor(
        self,
        ctx: commands.Context,
        members_: commands.Greedy[Member],
        num_impostors: int,
        category: str | None,
    ):
        if not members_:
            await ctx.send(
                "No players detected!\nUsage: !impostor <No. impostors> <Members>"
            )
            return

        members: list[Member] = list(set(members_))
        id_to_member = {member.id: member for member in members}

        # Attempt to send messages to all members
        test_message = """
You have been selected to play impostor! Standby. 
If you do not receive a message soon, something has gone wrong :(
"""
        failed_messages = await dynamic_test_mass_direct_message(
            members, lambda member: test_message
        )

        # List out all members that failed to receive a message and immediately return
        if failed_messages:
            assert not await mass_channel_message(
                ctx,
                (fail_message(member, e) for member, e in failed_messages),
            )
            return

        # Initialise game
        member_ids: list[MemberId] = list(id_to_member.keys())
        try:
            game_id: GameId = self.service.start_game(
                member_ids, num_impostors, category
            )
        except Exception as e:
            assert not await channel_message(ctx, f"Error starting game!\nError:{e}")
            return

        # Now send each member their messages to start the game
        failed_messages = await dynamic_test_mass_direct_message(
            members, lambda member: self.service.get_initial_message(game_id, member.id)
        )

        if failed_messages:
            assert not await mass_channel_message(
                ctx,
                (fail_message(member, e) for member, e in failed_messages),
            )
            return

        assert not await channel_message(
            ctx, "Successfully sent messages to each member!"
        )

        assert not await channel_message(
            ctx,
            f"First to play: {id_to_member[self.service.get_first_to_play(game_id)].mention}",
        )


async def setup(bot: bot.Bot):
    await bot.add_cog(Impostors(bot))

from datetime import timedelta
from discord import Member, Interaction, TextChannel, Poll, PollAnswer
from discord.ext import commands
from discord.ui import Button, View, button
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
        self.service = bot.get_impostors_service()

        self.id_to_member: dict[MemberId, Member] = {}

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
            assert not await channel_message(
                ctx.channel,
                "No players detected!\nUsage: !impostor <No. impostors> <Members>",
            )
            return

        members: list[Member] = list(set(members_))
        id_to_member = {member.id: member for member in members}

        self.id_to_member |= id_to_member

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
                ctx.channel,
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
            assert not await channel_message(
                ctx.channel, f"Error starting game!\nError:{e}"
            )
            return

        # Now send each member their messages to start the game
        failed_messages = await dynamic_test_mass_direct_message(
            members, lambda member: self.service.get_initial_message(game_id, member.id)
        )

        if failed_messages:
            assert not await mass_channel_message(
                ctx.channel,
                (fail_message(member, e) for member, e in failed_messages),
            )
            return

        assert not await channel_message(
            ctx.channel, "Successfully sent messages to each member!"
        )

        assert not await channel_message(
            ctx.channel,
            f"First to play: {id_to_member[self.service.get_first_to_play(game_id)].mention}",
        )

        # Send the game control view
        game_control_view = GameControlView(self, game_id)

        assert not await channel_message(
            ctx.channel,
            "**Game Controls**",
            view=game_control_view,
        )

    async def begin_poll(self, channel: TextChannel, game_id: GameId):
        # impostor_count = len(self.service.get_impostor_ids(game_id))
        member_ids = self.service.get_member_ids(game_id)
        poll = Poll(
            question="Who is the impostor?",
            multiple=True,
            duration=timedelta(hours=1),
        )
        for member_id in member_ids:
            member = self.id_to_member[member_id]
            assert member
            poll.add_answer(text=f"{member.display_name}")

        await channel_message(channel, "Poll time!", poll=poll)

    async def reveal_impostors(self, channel: TextChannel, game_id: GameId):
        impostor_ids = self.service.get_impostor_ids(game_id)
        members: list[Member] = [
            self.id_to_member[impostor_id] for impostor_id in impostor_ids
        ]

        assert not await channel_message(
            channel, f"The impostors: {', '.join(member.mention for member in members)}"
        )

    async def reveal_word(self, channel: TextChannel, game_id: GameId):
        word = self.service.get_word(game_id)
        assert not await channel_message(channel, f"The word: {word}!")


async def setup(bot: bot.Bot):
    await bot.add_cog(Impostors(bot))


class GameControlView(View):
    def __init__(self, impostors_cog: Impostors, game_id: GameId):
        super().__init__(timeout=None)
        self._cog = impostors_cog
        self._game_id = game_id

    @button(label="Begin Poll")
    async def begin_poll(self, interaction: Interaction, button: Button):
        assert type(interaction.channel) is TextChannel
        await interaction.response.defer()
        await self._cog.begin_poll(interaction.channel, self._game_id)

    @button(label="Reveal impostors")
    async def reveal_impostors(self, interaction: Interaction, button: Button):
        assert type(interaction.channel) is TextChannel
        await interaction.response.defer()
        await self._cog.reveal_impostors(interaction.channel, self._game_id)

    @button(label="Reveal word")
    async def reveal_word(self, interaction: Interaction, button: Button):
        assert type(interaction.channel) is TextChannel
        await interaction.response.defer()
        await self._cog.reveal_word(interaction.channel, self._game_id)

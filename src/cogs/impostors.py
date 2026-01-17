from datetime import timedelta
from discord import Member, Interaction, TextChannel, Poll
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
        - colours
        - cr (Clash Royale)
        - minecraft_mobs
        - minecraft_tools
        - minecraft
        - degrees
        - misc
        - fnd (Foods & Drinks)
        - pets
        - transportation
        - animals
        - sports
        - games
""",
    )
    async def impostor(
        self,
        ctx: commands.Context,
        members_: commands.Greedy[Member],
        num_impostors: int,
    ):
        if not members_:
            assert not await channel_message(
                ctx.channel,
                "No players detected!\nUsage: !impostor <Members> <No. impostors> Optional<Category>",
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

        # Get the category
        category = await self.query_category(ctx.channel)

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

    async def query_category(self, channel: TextChannel) -> str:
        categories = self.service.categories
        category_select_view = CategorySelectView(categories)

        assert not await channel_message(
            channel, "**Choose a category**", view=category_select_view
        )

        await category_select_view.wait()

        category = category_select_view.category

        return category

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


class CategorySelectView(View):
    MAX_PRESSES = 1

    def __init__(
        self,
        categories: list[str],
    ):
        super().__init__(timeout=60)
        self._pressed = 0
        self._category: str | None = None

        self.add_item(CategoryButton("All", None))
        for category in categories:
            self.add_item(CategoryButton(category, category))

    @property
    def category(self):
        return self._category

    def _set_category(self, category: str | None):
        self._category = category

    async def check_done(self):
        if self._pressed == self.MAX_PRESSES:
            self.stop()

    async def _do_after_press(self, interaction: Interaction, button: Button):
        if not button.label:
            return
        self._pressed += 1
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await self.check_done()


class CategoryButton(Button):
    def __init__(self, label: str, category: str | None):
        super().__init__(label=label)
        self.category = category

    async def callback(self, interaction: Interaction):
        view: CategorySelectView = self.view  # ty:ignore[invalid-assignment]
        view._set_category(self.category)
        await view._do_after_press(interaction, self)


class GameControlView(View):
    MAX_PRESSES = 3

    def __init__(self, impostors_cog: Impostors, game_id: GameId):
        super().__init__(timeout=3600)
        self._cog = impostors_cog
        self._game_id = game_id
        self._pressed = 0

    async def check_done(self):
        if self._pressed == self.MAX_PRESSES:
            self.stop()

    async def _do_after_press(self, interaction: Interaction, button: Button):
        if not button.label:
            return
        self._pressed += 1
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await self.check_done()

    @button(label="Begin Poll")
    async def begin_poll(self, interaction: Interaction, button: Button):
        assert type(interaction.channel) is TextChannel
        await self._cog.begin_poll(interaction.channel, self._game_id)
        await self._do_after_press(interaction, button)

    @button(label="Reveal impostors")
    async def reveal_impostors(self, interaction: Interaction, button: Button):
        assert type(interaction.channel) is TextChannel
        await self._cog.reveal_impostors(interaction.channel, self._game_id)
        await self._do_after_press(interaction, button)

    @button(label="Reveal word")
    async def reveal_word(self, interaction: Interaction, button: Button):
        assert type(interaction.channel) is TextChannel
        await self._cog.reveal_word(interaction.channel, self._game_id)
        await self._do_after_press(interaction, button)

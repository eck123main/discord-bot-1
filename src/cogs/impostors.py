from discord import Member, Forbidden
from discord.ext import commands
from core import bot
from custom_types.discord import MemberId
from custom_types.impostors import GameId


class Impostors(commands.Cog):
    def __init__(self, bot: bot.Bot):
        self.bot = bot
        self.service = bot.impostors_service

    @commands.command("impostor")
    async def impostor(
        self,
        ctx: commands.Context,
        num_impostors: int,
        members_: commands.Greedy[Member],
    ):
        if not members_:
            await ctx.send(
                "No players detected!\nUsage: !impostor <No. impostors> <Members>"
            )
            return

        members: list[Member] = list(set(members_))

        try:
            for member in members:
                await member.send(
                    "You have been selected to play impostor! Standby. If you do not receive a message soon, something has gone wrong :("
                )

        except Forbidden as e:
            await ctx.send(f"Failed to send a message to {member.mention}!\nError: {e}")
            return

        member_ids: list[MemberId] = [member.id for member in members]
        try:
            game_id: GameId = self.service.start_game(member_ids, num_impostors)
        except Exception as e:
            await ctx.send(f"Error starting game!\nError:{e}")
            return

        try:
            for member in members:
                member_id = member.id
                if self.service.check_impostor(game_id, member_id):
                    await member.send("You are an impostor!")
                else:
                    await member.send("You are a normal!")

        except Exception as e:
            await ctx.send(f"Something went wrong!\nError: {e}")

        await ctx.send("Successfully sent messages to each member!")


async def setup(bot: bot.Bot):
    await bot.add_cog(Impostors(bot))

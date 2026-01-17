from discord.ext import commands
from discord import Intents
from config import DISCORD_TOKEN
from services.greetings_service import GreetingsService
from services.impostors_service import ImpostorsService


class Bot(commands.Bot):
    # Token
    DISCORD_TOKEN = DISCORD_TOKEN

    def __init__(self):
        # Custom services
        self.greetings_service = GreetingsService()
        self.impostors_service = ImpostorsService()

        # Load intents
        intents = Intents.default()
        intents.message_content = True

        # Initialise bot
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    def get_impostors_service(self) -> ImpostorsService:
        return self.impostors_service

    # Sync commands
    async def setup_hook(self):
        # Load extensions
        await self.load_extension("cogs.greetings")
        await self.load_extension("cogs.impostors")

        # Sync commands
        synced = await self.tree.sync()
        print(f"Synced {synced}!")

    # Bot is ready
    async def on_ready(self):
        print(f"Logged in as {self.user}!")

    # Run bot
    def run_(self):
        super().run(DISCORD_TOKEN)

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
OPENROUTER_TOKEN = os.getenv("OPENROUTER_TOKEN")

assert DISCORD_TOKEN
assert OPENAI_TOKEN
assert OPENROUTER_TOKEN

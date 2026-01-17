from openai import OpenAI
from config import OPENROUTER_TOKEN

client = OpenAI(
    api_key=OPENROUTER_TOKEN,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/minip8/discord-bot-1",
        "X-Title": "Discord Impostor Bot",
    },
)


def query_hint(word: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
Game: Impostor.
Given a secret word, give ONE indirect hint word for the player who does not know it.
Avoid close synonyms.
""",
            },
            {
                "role": "user",
                "content": f"Give a hint for {word}.",
            },
        ],
        temperature=0.7,
        max_tokens=30,
    )

    return response.choices[0].message.content.strip()

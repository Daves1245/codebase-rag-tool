import os
import discord
from dotenv import load_dotenv

from src.core.config import settings
from src.core.rag_pipeline import CodebaseRAG
from src.utils.helpers import generate_repo_id
from src.utils.logger import init_logger

load_dotenv()
init_logger()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if DISCORD_BOT_TOKEN is None:
    raise KeyError("Could not find discord bot token env variable")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
rag = CodebaseRAG()

repo_id: int

def _get_option(interaction: discord.Interaction, name: str):
    options = {opt["name"]: opt["value"] for opt in interaction.data.get("options", [])}
    return options.get(name)


@client.event
async def on_ready():
    await rag.init()
    print(f"logged in as {client.user}")


@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.application_command:
        return

    name = interaction.data["name"]

    if name == "index":
        github_url = _get_option(interaction, "github_url")
        assert isinstance(github_url, str)

        await interaction.response.defer(thinking=True)
        try:
            await rag.index_repo(github_url, force_reindex=False)
            repo_id = generate_repo_id(github_url)
            await interaction.followup.send(
                f"indexed `{github_url}` (repo_id: `{repo_id}`)"
            )
        except Exception as e:
            await interaction.followup.send(f"failed to index: {e}")

    elif name == "query":
        github_url = _get_option(interaction, "github_url")
        question = _get_option(interaction, "question")
        assert isinstance(github_url, str) and isinstance(question, str)

        await interaction.response.defer(thinking=True)
        try:
            repo_id = generate_repo_id(github_url)
            result = await rag.query(repo_id=repo_id, query=question)
            answer = result.generated_response or "no response generated"
            await interaction.followup.send(answer[:1900])
        except Exception as e:
            await interaction.followup.send(f"query failed: {e}")


client.run(DISCORD_BOT_TOKEN)

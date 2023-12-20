import time
import logging
import disnake
from disnake.ext import commands

from rubby.database import DatabaseManager
from rubby.misc import Config
from rubby.misc import Env

logging.basicConfig(level=logging.INFO)

bot = commands.InteractionBot(
    intents=disnake.Intents.all(),
    command_sync_flags=commands.CommandSyncFlags.default(),
    test_guilds=Config.GUILD_IDS,
    owner_ids=Config.OWNER_IDS,
)


@bot.event
async def on_ready():
    await DatabaseManager.initialize()
    await load_extensions()

    logging.info("Bot is ready!")


async def load_extensions():
    logging.info("Initializing COGS ...")
    start_time = time.time()

    extension_paths = []

    for extension_file in Config.COGS_DIR.rglob("*.py"):
        if extension_file.stem.startswith("_"):
            continue

        extension_path = ".".join(
            extension_file.relative_to(Config.COGS_DIR).with_suffix("").parts
        )
        extension_paths.append(f"rubby.cogs.{extension_path}")

    for extension in extension_paths:
        try:
            bot.load_extension(extension)
            logging.info("Loaded %s successfully.", extension)
        except Exception as e:
            logging.error("Failed to load %s: %s", extension, e)

    end_time = time.time()
    logging.info(
        "Loaded %s cogs in %ss.", len(extension_paths), round(end_time - start_time, 2)
    )


def start():
    bot.run(Env.TOKEN)

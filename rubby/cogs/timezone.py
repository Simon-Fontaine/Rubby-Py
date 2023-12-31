import pendulum

import disnake
from disnake.ext import commands

from rubby.database import get_database
from rubby.models import Guild

TIMEZONES = pendulum.timezones()


async def auto_complete_timezones(
    inter: disnake.ApplicationCommandInteraction, user_input: str
):
    return [
        disnake.OptionChoice(name=timezone, value=timezone)
        for timezone in TIMEZONES
        if user_input.lower() in timezone.lower()
    ][:25]


class TimezoneCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="timezone",
        description="Checks or sets the timezone for the server.",
    )
    async def timezone(
        self,
        inter: disnake.ApplicationCommandInteraction,
        timezone: str = commands.Param(
            name="timezone",
            description="The timezone to set for the server.",
            autocomplete=auto_complete_timezones,
            default=None,
        ),
    ):
        await inter.response.defer(ephemeral=True)

        database = await get_database()

        guild: Guild = await database.guilds.find_one({"_id": inter.guild.id})

        if not guild:
            guild = Guild(
                _id=inter.guild.id,
                name=inter.guild.name,
                owner=inter.guild.owner_id,
                icon=inter.guild.icon.url,
                created_at=inter.guild.created_at,
            ).model_dump(by_alias=True)

            await database.guilds.insert_one(guild)

        if not timezone:
            return await inter.followup.send(
                f"The timezone for this server is `{guild['timezone']}`.",
                ephemeral=True,
            )

        if timezone not in TIMEZONES:
            return await inter.followup.send(
                "Invalid timezone. Please try again.",
                ephemeral=True,
            )

        await database.guilds.update_one(
            {"_id": inter.guild.id}, {"$set": {"timezone": timezone}}
        )

        await inter.followup.send(
            f"The timezone for this server has been set to `{timezone}`.",
            ephemeral=True,
        )


def setup(bot: commands.Bot):
    bot.add_cog(TimezoneCommand(bot))

import datetime
import disnake
from disnake.ext import commands


class PingCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="ping",
        description="Returns websocket & roundtrip latency.",
    )
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        roundtrip = round((now - inter.created_at).total_seconds(), 3)

        embed = disnake.Embed(
            color=disnake.Color.blurple(),
            description="\n".join(
                [
                    f"**Websocket:** `{round(self.bot.latency, 3)}s`",
                    f"**Round-trip:** `{roundtrip}s`",
                ]
            ),
        )

        shard_id = self.bot.shard_id + 1 if self.bot.shard_id is not None else 1
        shard_count = self.bot.shard_count if self.bot.shard_count is not None else 1

        embed.set_footer(
            text=f"Shard {shard_id}/{shard_count} • Guilds: {len(self.bot.guilds)} • Members: {len(self.bot.users)}"
        )

        await inter.response.send_message(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(PingCommand(bot))

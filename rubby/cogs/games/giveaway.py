import random
import pendulum

import disnake
from disnake.ext import commands

from rubby.database import get_database

from rubby.misc.emojis import Emojis
from rubby.functions.time_object import create_time_object
from rubby.functions.giveaways.create_giveaway_buttons import create_giveaway_buttons


error_embed = disnake.Embed(
    color=disnake.Color.red(),
    title=f"{Emojis.SYMBOLS['exclamation_mark_red']} Error!",
)

success_embed = disnake.Embed(
    color=disnake.Color.green(),
    title=f"{Emojis.SYMBOLS['check_mark_green']} Success!",
)


class GiveawayCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command()
    async def giveaway(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @giveaway.sub_command(
        name="create",
        description="Creates a new giveaway.",
    )
    async def create(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        time = await create_time_object(inter.guild.id, pendulum.now().add(hours=1))

        await inter.response.send_modal(
            title="Create a new giveaway",
            custom_id="create_giveaway",
            components=[
                disnake.ui.TextInput(
                    label="End date (Required)",
                    custom_id="duration",
                    style=disnake.TextInputStyle.short,
                    placeholder=f"e.g. {time.small_date_format}",
                    value=time.small_date_format,
                    required=True,
                ),
                disnake.ui.TextInput(
                    label="Name of the prize (Required)",
                    custom_id="prize",
                    style=disnake.TextInputStyle.short,
                    placeholder="e.g. Discord Nitro",
                    required=True,
                    max_length=1000,
                ),
                disnake.ui.TextInput(
                    label="Title text (Required)",
                    custom_id="title",
                    style=disnake.TextInputStyle.short,
                    placeholder="e.g. 🎉 New giveaway 🎉",
                    value="🎉 New giveaway 🎉",
                    required=True,
                    max_length=256,
                ),
                disnake.ui.TextInput(
                    label="Description text (Optional)",
                    custom_id="description",
                    style=disnake.TextInputStyle.long,
                    placeholder="e.g. Click on the button below to participate!",
                    value="Click on the button below to participate!",
                    required=False,
                    max_length=2000,
                ),
            ],
        )

    @giveaway.sub_command(
        name="end",
        description="Ends a giveaway.",
    )
    async def end(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_id: str = commands.Param(
            name="message_id",
            description="The message ID of the giveaway.",
        ),
    ):
        await inter.response.defer(ephemeral=True)

        if not message_id.isdigit():
            error_embed.description = "Please provide a valid message ID."
            return await inter.followup.send(embed=error_embed)

        database = await get_database()
        giveaway = await database.giveaways.find_one(
            {"_id": int(message_id), "guild_id": inter.guild.id}
        )

        if not giveaway:
            error_embed.description = "I couldn't find a giveaway with that message ID."
            return await inter.followup.send(embed=error_embed)

        if giveaway["ended"]:
            error_embed.description = "This giveaway has already ended."
            return await inter.followup.send(embed=error_embed)

        channel = self.bot.get_channel(giveaway["channel_id"])
        try:
            message = await channel.fetch_message(giveaway["_id"])
        except disnake.NotFound:
            message = None

        if not message:
            error_embed.description = "I couldn't find the giveaway message."
            await database.giveaways.delete_one({"_id": int(message_id)})
            return await inter.followup.send(embed=error_embed)

        end_date = await create_time_object(inter.guild.id)
        buttons = await create_giveaway_buttons(
            len(giveaway["participants"]), end_date, True
        )
        winners = []
        winners_mentions = None
        description = "There were not enough participants to draw winners."

        if len(giveaway["participants"]) > 0:
            if len(giveaway["participants"]) <= giveaway["winner_count"]:
                winners = giveaway["participants"]
            else:
                winners = random.sample(
                    giveaway["participants"], giveaway["winner_count"]
                )

            winners_mentions = ", ".join([f"<@{winner}>" for winner in winners])
            description = f"The winner of this giveaway {'are' if len(winners) > 1 else 'is'} tagged above! Congratulations 🎉"

        result_embed = disnake.Embed(
            title=f"{giveaway['title']} (Results)",
            description=description,
            color=disnake.Color.blurple(),
        )
        result_embed.add_field(
            name="Prize",
            value=giveaway["prize"],
        )
        message.embeds[0].title = f"{giveaway['title']} (Ended)"
        message.embeds[0].color = disnake.Color.red()

        await message.edit(content=None, embed=message.embeds[0], components=buttons)
        result_message = await message.reply(
            embed=result_embed, content=winners_mentions
        )

        await database.giveaways.update_one(
            {"_id": giveaway["_id"]},
            {
                "$set": {
                    "result_message_id": result_message.id,
                    "ended": True,
                    "end_date": end_date.date_time,
                }
            },
        )

        success_embed.description = f"Successfully ended the giveaway! \n\n**[Jump to results]({result_message.jump_url})**"
        await inter.followup.send(
            embed=success_embed,
            ephemeral=True,
        )

    @giveaway.sub_command(
        name="delete",
        description="Deletes a giveaway.",
    )
    async def delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_id: str = commands.Param(
            name="message_id",
            description="The message ID of the giveaway.",
        ),
    ):
        await inter.response.defer(ephemeral=True)

        if not message_id.isdigit():
            error_embed.description = "Please provide a valid message ID."
            return await inter.followup.send(embed=error_embed)

        database = await get_database()
        giveaway = await database.giveaways.find_one(
            {"_id": int(message_id), "guild_id": inter.guild.id}
        )

        if not giveaway:
            giveaway = await database.giveaways.find_one(
                {"result_message_id": int(message_id), "guild_id": inter.guild.id}
            )

        if not giveaway:
            error_embed.description = "I couldn't find a giveaway with that message ID."
            return await inter.followup.send(embed=error_embed)

        channel = self.bot.get_channel(giveaway["channel_id"])
        try:
            message = await channel.fetch_message(giveaway["_id"])
            await message.delete()
        except disnake.NotFound:
            pass

        if giveaway["result_message_id"]:
            try:
                result_message = await channel.fetch_message(
                    giveaway["result_message_id"]
                )
                await result_message.delete()
            except disnake.NotFound:
                pass

        await database.giveaways.delete_one({"_id": giveaway["_id"]})

        success_embed.description = "Successfully deleted the giveaway."
        await inter.followup.send(
            embed=success_embed,
            ephemeral=True,
        )

    @giveaway.sub_command(
        name="reroll",
        description="Rerolls a giveaway.",
    )
    async def reroll(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_id: str = commands.Param(
            name="message_id",
            description="The message ID of the giveaway.",
        ),
    ):
        await inter.response.defer(ephemeral=True)

        if not message_id.isdigit():
            error_embed.description = "Please provide a valid message ID."
            return await inter.followup.send(embed=error_embed)

        database = await get_database()
        giveaway = await database.giveaways.find_one(
            {"_id": int(message_id), "guild_id": inter.guild.id}
        )

        if not giveaway:
            giveaway = await database.giveaways.find_one(
                {"result_message_id": int(message_id), "guild_id": inter.guild.id}
            )

        if not giveaway:
            error_embed.description = "I couldn't find a giveaway with that message ID."
            return await inter.followup.send(embed=error_embed)

        if not giveaway["ended"]:
            error_embed.description = "This giveaway hasn't ended yet."
            return await inter.followup.send(embed=error_embed)

        if len(giveaway["participants"]) <= giveaway["winner_count"]:
            error_embed.description = (
                "There were not enough participants to reroll winners."
            )
            return await inter.followup.send(embed=error_embed)

        channel = self.bot.get_channel(giveaway["channel_id"])
        try:
            message = await channel.fetch_message(giveaway["_id"])
        except disnake.NotFound:
            message = None

        if not message:
            error_embed.description = "I couldn't find the giveaway message."
            await database.giveaways.delete_one({"_id": int(message_id)})
            return await inter.followup.send(embed=error_embed)

        try:
            result_message = await channel.fetch_message(giveaway["result_message_id"])
        except disnake.NotFound:
            result_message = None

        winners = random.sample(giveaway["participants"], giveaway["winner_count"])
        winners_mentions = ", ".join([f"<@{winner}>" for winner in winners])
        description = f"The winner of this giveaway {'are' if len(winners) > 1 else 'is'} tagged above! Congratulations 🎉"

        result_embed = disnake.Embed(
            title=f"{giveaway['title']} (Rerolled)",
            description=description,
            color=disnake.Color.blurple(),
        )
        result_embed.add_field(
            name="Prize",
            value=giveaway["prize"],
        )

        if result_message:
            await result_message.edit(
                embed=result_embed,
                content=winners_mentions,
            )
        else:
            result_message = await message.reply(
                embed=result_embed,
                content=winners_mentions,
            )

        await database.giveaways.update_one(
            {"_id": giveaway["_id"]},
            {
                "$set": {
                    "result_message_id": result_message.id,
                    "ended": True,
                }
            },
        )

        success_embed.description = f"Successfully rerolled the giveaway! \n\n**[Jump to results]({result_message.jump_url})**"
        await inter.followup.send(
            embed=success_embed,
            ephemeral=True,
        )

    @giveaway.sub_command(
        name="list",
        description="Lists all giveaways.",
    )
    async def list(
        self,
        inter: disnake.ApplicationCommandInteraction,
        status: str = commands.Param(
            name="status",
            description="The status of the giveaway.",
            choices=[
                disnake.OptionChoice(name="All", value="all"),
                disnake.OptionChoice(name="Active", value="active"),
                disnake.OptionChoice(name="Ended", value="ended"),
            ],
            default=None,
        ),
        message_id: str = commands.Param(
            name="message_id",
            description="The message ID of the giveaway.",
            default=None,
        ),
        channel_id: disnake.TextChannel = commands.Param(
            name="channel_id",
            description="The channel ID of the giveaway.",
            default=None,
        ),
        created_by: disnake.User = commands.Param(
            name="created_by",
            description="The user ID of the giveaway creator.",
            default=None,
        ),
    ):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(GiveawayCommand(bot))

import logging
import random
import dateparser
import pendulum
import pytz

import disnake
from disnake.ext import tasks, commands

from datetime import datetime

from pydantic import ValidationError

from rubby.database import get_database
from rubby.models import Giveaway

default_timezone = pytz.timezone("UTC")


def get_giveaway_buttons(
    second_label: str, first_label: str = "Participate", disabled: bool = False
):
    return [
        disnake.ui.Button(
            label=first_label,
            style=disnake.ButtonStyle.primary,
            emoji="🎉",
            custom_id="join_giveaway",
            disabled=disabled,
        ),
        disnake.ui.Button(
            label=second_label,
            style=disnake.ButtonStyle.secondary,
            custom_id="disabled_button",
            disabled=True,
        ),
    ]


def format_time(time: datetime):
    time = pendulum.instance(time)

    return time.format("MMMM Do YYYY [at] H:mm zz")


class GiveawayCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.giveaway_expiration_loop.start()

    def cog_unload(self):
        self.giveaway_expiration_loop.cancel()

    @tasks.loop(seconds=15.0)
    async def giveaway_expiration_loop(self):
        current_time = datetime.now(default_timezone)
        database = await get_database()
        cursor = database.giveaways.find(
            {
                "end_date": {"$lt": current_time},
                "ended": False,
            }
        )
        giveaway_list = await cursor.to_list(length=None)

        for giveaway in giveaway_list:
            try:
                channel = self.bot.get_channel(giveaway["channel_id"])
                message = await channel.fetch_message(giveaway["_id"])
            except disnake.NotFound:
                await database.giveaways.delete_one({"_id": giveaway["_id"]})
                logging.info(
                    'Deleted giveaway for "%s" because the message was not found!',
                    giveaway["prize"],
                )
                continue

            winners = None
            winners_mentions = None
            description = "There were not enough participants to draw winners."

            if len(giveaway["participants"]) > 0:
                if len(giveaway["participants"]) < giveaway["winner_count"]:
                    winners = giveaway["participants"]
                else:
                    winners = random.sample(
                        giveaway["participants"], giveaway["winner_count"]
                    )
                winners_mentions = " ".join([f"<@{winner}>" for winner in winners])
                description = f"The winner of this giveaway {'are' if len(winners) > 1 else 'is'} tagged above! Congratulations 🎉"

            embed = disnake.Embed(
                title=f"{giveaway['title']} [RESULTS]",
                description=description,
                color=disnake.Color.blurple(),
            )
            embed.add_field(name="Prize", value=giveaway["prize"])
            embed.set_footer(text=f"Participants: {len(giveaway['participants'])}")

            message.embeds[0].title = f"{giveaway['title']} [ENDED]"
            message.embeds[0].color = disnake.Color.red()

            buttons = get_giveaway_buttons(
                first_label=f"Participate ({len(giveaway['participants'])})",
                second_label="Ended on " + format_time(current_time),
                disabled=True,
            )

            await message.edit(embed=message.embeds[0], components=buttons)
            result_message = await message.reply(embed=embed, content=winners_mentions)

            await database.giveaways.update_one(
                {"_id": giveaway["_id"]},
                {
                    "$set": {
                        "result_message_id": result_message.id,
                        "ended": True,
                        "end_date": current_time,
                    }
                },
            )
            logging.info(
                'Ended giveaway for "%s" because the end date has passed!',
                giveaway["prize"],
            )

    @giveaway_expiration_loop.before_loop
    async def before_giveaway_expiration_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "join_giveaway":
            return

        await inter.response.defer(ephemeral=True)

        database = await get_database()
        giveaway = await database.giveaways.find_one({"_id": inter.message.id})
        current_time = datetime.now(default_timezone)

        if giveaway is None:
            inter.message.embeds[0].title += " [NOT FOUND]"
            inter.message.embeds[0].color = disnake.Color.orange()

            buttons = get_giveaway_buttons(
                second_label="Errored on " + format_time(current_time),
                disabled=True,
            )

            await inter.message.edit(embed=inter.message.embeds[0], components=buttons)
            return await inter.followup.send(
                "I couldn't find a giveaway associated with that message ID! Please try again.",
                ephemeral=True,
            )

        end_date = default_timezone.localize(giveaway["end_date"])

        if end_date < current_time:
            return await inter.followup.send(
                "This giveaway doesn't accept participants anymore!", ephemeral=True
            )

        if inter.user.id in giveaway["participants"]:
            giveaway["participants"].remove(inter.user.id)
            await inter.followup.send("You left the giveaway!", ephemeral=True)
        else:
            giveaway["participants"].append(inter.user.id)
            await inter.followup.send("You joined the giveaway!", ephemeral=True)

        buttons = get_giveaway_buttons(
            first_label=f"Participate ({len(giveaway['participants'])})",
            second_label="Ends on " + format_time(end_date),
        )

        await database.giveaways.update_one(
            {"_id": inter.message.id},
            {"$set": {"participants": giveaway["participants"]}},
        )
        await inter.message.edit(components=buttons)

    @commands.slash_command()
    async def giveaway(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @giveaway.sub_command()
    async def create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        prize: str,
        channel: disnake.TextChannel,
        winner_count: int,
        end_date: str = None,
        title: str = "🎉 New giveaway 🎉",
        description: str = "Click on the button below to participate!",
    ):
        await inter.response.defer(ephemeral=True)

        if end_date is None:
            end_date = datetime.now(default_timezone) + pendulum.Duration(hours=1)
        else:
            end_date = dateparser.parse(end_date, settings={"TIMEZONE": "UTC"})

        if end_date is None:
            return await inter.followup.send(
                f"I couldn't parse `{end_date}` into a valid date! Please try again.",
                ephemeral=True,
            )

        end_date = default_timezone.localize(end_date)
        current_time = datetime.now(default_timezone)

        if end_date < current_time:
            return await inter.followup.send(
                "End date cannot be in the past!",
                ephemeral=True,
            )

        embed = disnake.Embed(
            title=title,
            description=description,
            color=disnake.Color.blurple(),
        )

        embed.set_footer(text=f"Max Winners: {winner_count} | Hosted By: {inter.user}")

        buttons = get_giveaway_buttons(
            second_label="Ends on " + format_time(end_date),
        )

        message = await channel.send(
            embed=embed,
            components=buttons,
        )

        database = await get_database()

        try:
            giveaway = Giveaway(
                _id=message.id,
                channel_id=channel.id,
                guild_id=inter.guild.id,
                created_by=inter.user.id,
                title=title,
                description=description,
                prize=prize,
                winner_count=winner_count,
                end_date=end_date,
                created_at=current_time,
            )

            await database.giveaways.insert_one(giveaway.model_dump(by_alias=True))

            return await inter.followup.send(
                f'Successfully created giveaway for "{prize}"!',
                ephemeral=True,
            )
        except ValidationError as e:
            errors = "\n".join([error["msg"] for error in e.errors()])
            await inter.followup.send(
                f'Failed to create giveaway for "{prize}"! Error: {errors}',
                ephemeral=True,
            )
            return await message.delete()

    @giveaway.sub_command()
    async def end(self, inter: disnake.ApplicationCommandInteraction, message_id: str):
        await inter.response.defer(ephemeral=True)

        if not message_id.isdigit():
            return await inter.followup.send(
                "A message ID can only contain numbers! Please try again.",
                ephemeral=True,
            )

        message_id = int(message_id)

        database = await get_database()
        giveaway = await database.giveaways.find_one({"_id": message_id})

        if giveaway is None:
            return await inter.followup.send(
                "I couldn't find a giveaway associated with that message ID! Please try again.",
                ephemeral=True,
            )

        end_date = default_timezone.localize(giveaway["end_date"])

        if end_date < datetime.now(default_timezone):
            return await inter.followup.send(
                "This giveaway has already ended", ephemeral=True
            )

        try:
            channel = self.bot.get_channel(giveaway["channel_id"])
            message = await channel.fetch_message(message_id)
        except disnake.NotFound:
            await database.giveaways.delete_one({"_id": message_id})
            await inter.followup.send(
                "I couldn't find a giveaway associated with that message ID! Please try again.",
                ephemeral=True,
            )

        winners = None
        winners_mentions = None
        description = "There were not enough participants to draw winners."
        end_date = datetime.now(default_timezone)

        if len(giveaway["participants"]) > 0:
            if len(giveaway["participants"]) < giveaway["winner_count"]:
                winners = giveaway["participants"]
            else:
                winners = random.sample(
                    giveaway["participants"], giveaway["winner_count"]
                )
            winners_mentions = " ".join([f"<@{winner}>" for winner in winners])
            description = f"The winner of this giveaway {'are' if len(winners) > 1 else 'is'} tagged above! Congratulations 🎉"

        embed = disnake.Embed(
            title=f"{giveaway['title']} [RESULTS]",
            description=description,
            color=disnake.Color.blurple(),
        )
        embed.add_field(name="Prize", value=giveaway["prize"])
        embed.set_footer(text=f"Participants: {len(giveaway['participants'])}")

        message.embeds[0].title = f"{giveaway['title']} [ENDED]"
        message.embeds[0].color = disnake.Color.red()

        buttons = get_giveaway_buttons(
            first_label=f"Participate ({len(giveaway['participants'])})",
            second_label="Ended on " + format_time(end_date),
            disabled=True,
        )

        await message.edit(embed=message.embeds[0], components=buttons)
        result_message = await message.reply(embed=embed, content=winners_mentions)

        await database.giveaways.update_one(
            {"_id": message_id},
            {
                "$set": {
                    "result_message_id": result_message.id,
                    "ended": True,
                    "end_date": end_date,
                }
            },
        )

        await inter.followup.send(
            f"Successfully ended giveaway for \"{giveaway['prize']}\"!",
            ephemeral=True,
        )

    @giveaway.sub_command()
    async def delete(
        self, inter: disnake.ApplicationCommandInteraction, message_id: str
    ):
        await inter.response.defer(ephemeral=True)

        if not message_id.isdigit():
            return await inter.followup.send(
                "A message ID can only contain numbers! Please try again.",
                ephemeral=True,
            )

        message_id = int(message_id)

        database = await get_database()
        giveaway = await database.giveaways.find_one({"_id": message_id})

        if giveaway is None:
            giveaway = await database.giveaways.find_one(
                {"result_message_id": message_id}
            )

        if giveaway is None:
            return await inter.followup.send(
                "I couldn't find a giveaway associated with that message ID! Please try again.",
                ephemeral=True,
            )

        try:
            channel = self.bot.get_channel(giveaway["channel_id"])
            message = await channel.fetch_message(message_id)
            await message.delete()
        except disnake.NotFound:
            pass

        if channel is not None and giveaway["result_message_id"] is not None:
            try:
                result_message = await channel.fetch_message(
                    giveaway["result_message_id"]
                )
                await result_message.delete()
            except disnake.NotFound:
                pass

        await database.giveaways.delete_one({"_id": message_id})

        await inter.followup.send(
            f"Successfully deleted giveaway for \"{giveaway['prize']}\"!",
            ephemeral=True,
        )

    @giveaway.sub_command()
    async def reroll(
        self, inter: disnake.ApplicationCommandInteraction, message_id: str
    ):
        await inter.response.defer(ephemeral=True)

        if not message_id.isdigit():
            return await inter.followup.send(
                "A message ID can only contain numbers! Please try again.",
                ephemeral=True,
            )

        message_id = int(message_id)

        database = await get_database()
        giveaway = await database.giveaways.find_one({"_id": message_id})

        if giveaway is None:
            giveaway = await database.giveaways.find_one(
                {"result_message_id": message_id}
            )

        if giveaway is None:
            return await inter.followup.send(
                "I couldn't find a giveaway associated with that message ID! Please try again.",
                ephemeral=True,
            )

        end_date = default_timezone.localize(giveaway["end_date"])

        if end_date > datetime.now(default_timezone):
            return await inter.followup.send(
                "This giveaway hasn't ended yet!", ephemeral=True
            )

        if giveaway["result_message_id"] is None:
            return await inter.followup.send(
                "This giveaway hasn't ended yet!", ephemeral=True
            )

        if len(giveaway["participants"]) == 0:
            return await inter.followup.send(
                "This giveaway doesn't have any participants!", ephemeral=True
            )

        try:
            channel = self.bot.get_channel(giveaway["channel_id"])
            result_message = await channel.fetch_message(giveaway["result_message_id"])
        except disnake.NotFound:
            return await inter.followup.send(
                "I couldn't find a giveaway associated with that message ID! Please try again.",
                ephemeral=True,
            )

        winners = None
        winners_mentions = None

        if len(giveaway["participants"]) < giveaway["winner_count"]:
            winners = giveaway["participants"]
        else:
            winners = random.sample(giveaway["participants"], giveaway["winner_count"])
        winners_mentions = " ".join([f"<@{winner}>" for winner in winners])

        embed = disnake.Embed(
            title=f"{giveaway['title']} [REROLLED]",
            description="The winner of this giveaway has been rerolled! Congratulations 🎉",
            color=disnake.Color.blurple(),
        )

        embed.add_field(name="Prize", value=giveaway["prize"])
        embed.set_footer(text=f"Participants: {len(giveaway['participants'])}")

        await result_message.edit(embed=embed, content=winners_mentions)
        await inter.followup.send(
            f"Successfully rerolled giveaway for \"{giveaway['prize']}\"!",
            ephemeral=True,
        )

    @giveaway.sub_command()
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(GiveawayCommand(bot))

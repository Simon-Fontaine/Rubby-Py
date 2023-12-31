import logging
import pendulum
import random

import disnake
from disnake.ext import commands, tasks

from pydantic import ValidationError

from rubby.database import get_database
from rubby.models import Giveaway
from rubby.misc.emojis import Emojis

from rubby.functions.time_object import create_time_object
from rubby.functions.user_details import get_user_details
from rubby.functions.giveaways.create_giveaway_embed import create_giveaway_embed
from rubby.functions.giveaways.create_giveaway_buttons import create_giveaway_buttons

error_embed = disnake.Embed(
    color=disnake.Color.red(),
    title=f"{Emojis.SYMBOLS['exclamation_mark_red']} Error!",
)

success_embed = disnake.Embed(
    color=disnake.Color.green(),
    title=f"{Emojis.SYMBOLS['check_mark_green']} Success!",
)


class ConfirmButton(disnake.ui.Button):
    def __init__(self, original_interaction: disnake.MessageInteraction):
        self.original_interaction = original_interaction
        super().__init__(
            style=disnake.ButtonStyle.success,
            label="Confirm",
            custom_id="giveaway:confirm",
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)

        if inter.user.id != self.original_interaction.user.id:
            error_embed.description = "You are not allowed to use this button!"
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        database = await get_database()
        giveaway = await database.giveaways.find_one(
            {"_id": inter.message.id, "guild_id": inter.guild.id}
        )

        if not giveaway:
            error_embed.description = "An error occurred while creating your giveaway. Please try again later."
            return await inter.followup.send(
                embed=error_embed,
            )

        end_date = await create_time_object(
            inter.guild.id, pendulum.instance(giveaway["end_date"])
        )
        user = await get_user_details(inter.user, inter.client)

        embed = create_giveaway_embed(
            user,
            giveaway["title"],
            giveaway["description"],
            giveaway["winner_count"],
            end_date,
            giveaway["allowed_roles"],
        )

        buttons = await create_giveaway_buttons(0, end_date)

        await inter.message.edit(content=None, embed=embed, components=buttons)

        await database.giveaways.update_one(
            {"_id": inter.message.id},
            {"$set": {"finished_configuring": True}},
        )

        success_embed.description = f"Your giveaway has been created successfully ! \n\n**[Click here to enter it]({inter.message.jump_url})**"
        await inter.followup.send(
            embed=success_embed,
            ephemeral=True,
        )


class CancelButton(disnake.ui.Button):
    def __init__(self, original_interaction: disnake.MessageInteraction):
        self.original_interaction = original_interaction
        super().__init__(
            style=disnake.ButtonStyle.danger,
            label="Cancel",
            custom_id="giveaway:cancel",
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)

        if inter.user.id != self.original_interaction.user.id:
            error_embed.description = "You are not allowed to use this button!"
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        await inter.message.delete()

        database = await get_database()
        await database.giveaways.delete_one(
            {"_id": inter.message.id, "guild_id": inter.guild.id}
        )

        success_embed.description = "Your giveaway creation has been cancelled."
        await inter.followup.send(
            embed=success_embed,
            ephemeral=True,
        )


class RolesSelectMenu(disnake.ui.RoleSelect):
    def __init__(self, original_interaction: disnake.MessageInteraction):
        self.original_interaction = original_interaction
        super().__init__(
            custom_id="giveaway:roles",
            placeholder="Add/Remove roles that can participate for this giveaway",
            min_values=0,
            max_values=25,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)

        if inter.user.id != self.original_interaction.user.id:
            error_embed.description = "You are not allowed to use this selection menu!"
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        allowed_roles = [role.id for role in self.values] if self.values else []

        database = await get_database()
        await database.giveaways.update_one(
            {"_id": inter.message.id, "guild_id": inter.guild.id},
            {"$set": {"allowed_roles": allowed_roles}},
        )

        embed = inter.message.embeds[0]

        if len(allowed_roles) == 0:
            embed.remove_field(0)
        else:
            if embed.fields:
                embed.set_field_at(
                    index=0,
                    name="Allowed Roles",
                    value=", ".join([f"<@&{role_id}>" for role_id in allowed_roles]),
                )
            else:
                embed.add_field(
                    name="Allowed Roles",
                    value=", ".join([f"<@&{role_id}>" for role_id in allowed_roles]),
                )

        await inter.message.edit(embed=embed)


class WinnerCountSelectMenu(disnake.ui.StringSelect):
    def __init__(self, original_interaction: disnake.MessageInteraction):
        self.original_interaction = original_interaction
        super().__init__(
            custom_id="giveaway:winner_count",
            placeholder="Select the maximum number of winners",
            options=[
                disnake.SelectOption(label=str(i), value=str(i)) for i in range(1, 11)
            ],
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)

        if inter.user.id != self.original_interaction.user.id:
            error_embed.description = "You are not allowed to use this selection menu!"
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        winner_count = int(self.values[0])

        database = await get_database()
        await database.giveaways.update_one(
            {"_id": inter.message.id, "guild_id": inter.guild.id},
            {"$set": {"winner_count": winner_count}},
        )

        user = await get_user_details(inter.user, inter.client)
        embed = inter.message.embeds[0]
        embed.set_footer(
            text=f"Max Winners: {winner_count} • Hosted by {user.name}",
        )

        await inter.message.edit(embed=embed)


class GiveawayView(disnake.ui.View):
    def __init__(self, original_interaction: disnake.MessageInteraction):
        super().__init__(timeout=300)

        self.add_item(ConfirmButton(original_interaction))
        self.add_item(CancelButton(original_interaction))
        self.add_item(RolesSelectMenu(original_interaction))
        self.add_item(WinnerCountSelectMenu(original_interaction))


class GiveawayEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.end_giveaways.start()

    def cog_unload(self):
        self.end_giveaways.cancel()

    @tasks.loop(seconds=10.0)
    async def end_giveaways(self):
        database = await get_database()
        giveaways = await database.giveaways.find({}).to_list(None)
        logging.debug("Checking %s giveaways.", len(giveaways))

        for giveaway in giveaways:
            if giveaway["ended"] or not giveaway["finished_configuring"]:
                logging.debug(
                    "Skipped giveaway %s. (ENDED/NOT CONFIG)", giveaway["_id"]
                )
                continue

            if pendulum.instance(giveaway["end_date"]) <= pendulum.now():
                channel = self.bot.get_channel(giveaway["channel_id"])
                message = await channel.fetch_message(giveaway["_id"])

                if not message:
                    await database.giveaways.delete_one({"_id": giveaway["_id"]})
                    logging.debug("Deleted giveaway %s.", giveaway["_id"])
                    continue

                end_date = await create_time_object(giveaway["guild_id"])

                buttons = await create_giveaway_buttons(
                    len(giveaway["participants"]), end_date, disabled=True
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

                await message.edit(
                    content=None, embed=message.embeds[0], components=buttons
                )
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
                logging.debug("Ended giveaway %s.", giveaway["_id"])
            else:
                logging.debug("Skipped giveaway %s. (NOT ENDED)", giveaway["_id"])

    @commands.Cog.listener("on_modal_submit")
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id != "create_giveaway":
            return

        await inter.response.defer(ephemeral=True)

        duration = inter.text_values.get("duration")

        try:
            duration = await create_time_object(inter.guild.id, duration)
        except ValueError as error:
            error_embed.description = str(error)
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        prize = inter.text_values.get("prize")
        title = inter.text_values.get("title")
        description = inter.text_values.get("description")

        allowed_roles: list[int] = []
        max_winners = 1

        if duration.date_time <= pendulum.now():
            error_embed.description = (
                "The duration of the giveaway must be greater than the current time."
            )
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        user = await get_user_details(inter.user, self.bot)
        embed = create_giveaway_embed(
            user,
            title,
            description,
            max_winners,
            duration,
            allowed_roles,
        )

        giveaway_message: disnake.Message = await inter.channel.send(
            content="\n".join(
                [
                    "👀 **Here is a preview of your giveaway !**",
                    "",
                    "Click on the **`Confirm`** button to create your giveaway here.",
                ]
            ),
            embed=embed,
            view=GiveawayView(inter),
        )

        database = await get_database()

        try:
            giveaway = Giveaway(
                _id=giveaway_message.id,
                channel_id=inter.channel.id,
                guild_id=inter.guild.id,
                created_by=inter.user.id,
                title=title,
                description=description,
                prize=prize,
                winner_count=max_winners,
                end_date=duration.date_time,
                created_at=pendulum.now(),
            )
        except ValidationError as error:
            logging.error(error)
            error_embed.description = "An error occurred while creating your giveaway."
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        await database.giveaways.insert_one(giveaway.model_dump(by_alias=True))

        success_embed.description = f"Your giveaway creation process has been successfully initiated! \n\n**[Click here to configure it]({giveaway_message.jump_url})**"
        await inter.followup.send(
            embed=success_embed,
            ephemeral=True,
        )

    @commands.Cog.listener("on_button_click")
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "giveaway:enter":
            return

        await inter.response.defer(ephemeral=True)

        database = await get_database()
        giveaway = await database.giveaways.find_one(
            {"_id": inter.message.id, "guild_id": inter.guild.id}
        )

        if not giveaway:
            inter.message.embeds[0].title += " [NOT FOUND]"
            inter.message.embeds[0].color = disnake.Color.orange()

            errored_time = await create_time_object(guild_id=inter.guild.id)
            buttons = await create_giveaway_buttons(0, errored_time, disabled=True)

            await inter.message.edit(embed=inter.message.embeds[0], components=buttons)

            error_embed.description = (
                "An error occurred while entering the giveaway. Please try again later."
            )
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        end_date = await create_time_object(
            inter.guild.id, pendulum.instance(giveaway["end_date"])
        )

        if end_date.date_time <= pendulum.now():
            buttons = await create_giveaway_buttons(
                len(giveaway["participants"]), end_date, disabled=True
            )
            await inter.message.edit(components=buttons)
            error_embed.description = (
                "You cannot enter this giveaway, it has already ended."
            )
            return await inter.followup.send(
                embed=error_embed,
                ephemeral=True,
            )

        if (
            len(giveaway["allowed_roles"]) > 0
            and not inter.user.guild_permissions.administrator
        ):
            if not any(
                role.id in giveaway["allowed_roles"] for role in inter.user.roles
            ):
                error_embed.description = (
                    "You need to have one of the following roles to join this giveaway: "
                    + ", ".join(
                        [f"<@&{role_id}>" for role_id in giveaway["allowed_roles"]]
                    )
                )
                return await inter.followup.send(
                    embed=error_embed,
                    ephemeral=True,
                )

        if inter.user.id in giveaway["participants"]:
            giveaway["participants"].remove(inter.user.id)
            success_embed.description = "You have been removed from the giveaway."
            await inter.followup.send(
                embed=success_embed,
                ephemeral=True,
            )
        else:
            giveaway["participants"].append(inter.user.id)
            success_embed.description = "You have been added to the giveaway."
            await inter.followup.send(
                embed=success_embed,
                ephemeral=True,
            )

        buttons = await create_giveaway_buttons(len(giveaway["participants"]), end_date)

        await inter.message.edit(components=buttons)
        await database.giveaways.update_one(
            {"_id": inter.message.id},
            {"$set": {"participants": giveaway["participants"]}},
        )


def setup(bot: commands.Bot):
    bot.add_cog(GiveawayEvents(bot))

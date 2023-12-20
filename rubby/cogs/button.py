import disnake
from disnake.ext import commands


class ButtonCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command()
    async def buttons(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            "This is a button!",
            components=[
                disnake.ui.Button(
                    label="Yes", style=disnake.ButtonStyle.success, custom_id="yes"
                ),
                disnake.ui.Button(
                    label="No", style=disnake.ButtonStyle.danger, custom_id="no"
                ),
            ],
        )

    @commands.Cog.listener("on_button_click")
    async def help_listener(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in ["yes", "no"]:
            return

        if inter.component.custom_id == "yes":
            await inter.response.send_message("You clicked yes!")
        elif inter.component.custom_id == "no":
            await inter.response.send_message("You clicked no!")


def setup(bot: commands.Bot):
    bot.add_cog(ButtonCommand(bot))

import disnake
from disnake.ext import commands

from rubby.misc.emojis import Emojis


def user_name(user: disnake.User) -> str:
    name = (
        f"@{user.name}"
        if user.discriminator == "0"
        else f"{user.name}#{user.discriminator}"
    )
    return f"{name} {user_bot_badges(user)}"


def user_badges(user: disnake.User) -> str:
    badges = [
        Emojis.BADGES[flag.name]
        for flag in user.public_flags.all()
        if flag.name in Emojis.BADGES
    ]
    return " ".join(badges) if badges else None


def user_bot_badges(user: disnake.User) -> str:
    if user.bot:
        if user.public_flags.verified_bot:
            return Emojis.BOT["verified_bot"]
        else:
            return Emojis.BOT["bot"]
    else:
        return ""


class UserInfoCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="userinfo",
        description="Shows information about a user.",
        options=[
            disnake.Option(
                type=disnake.OptionType.user,
                name="user",
                description="The user to show information about.",
                required=False,
            )
        ],
    )
    async def userinfo(
        self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None
    ):
        await inter.response.defer()
        user = user or inter.author
        user = await self.bot.fetch_user(user.id) or user
        member = inter.guild.get_member(user.id)

        embed = disnake.Embed(title="User Information", color=user.accent_color)
        embed.set_thumbnail(url=user.display_avatar.url)

        badges = user_badges(user)
        user_lines = [
            f"> **User:** {user_name(user)}",
            f"> **ID:** {user.id}",
            f"> **Mention:** {user.mention}",
            f"> **Created:** <t:{int(user.created_at.timestamp())}:R>",
            f"> **Banner color:** {user.accent_color}",
            f"> **[Avatar]({user.display_avatar.url})**",
        ]

        if badges:
            user_lines.insert(1, f"> **Badges:** {badges}")

        embed.add_field(
            name="Name",
            value="\n".join(user_lines),
            inline=False,
        )

        if member:
            server_lines = [
                f"> **Joined:** <t:{round(member.joined_at.timestamp())}:R>",
            ]
            if member.nick:
                server_lines.append(f"> **Nickname:** {member.nick}")

            embed.add_field(
                name="Server",
                value="\n".join(server_lines),
                inline=False,
            )

            roles_mentions = [
                role.mention for role in member.roles[1:] if not role.is_default()
            ]
            role_list = (
                "\n".join([f"> `-` {role}" for role in roles_mentions[:10]])
                if roles_mentions
                else "None"
            )
            if len(roles_mentions) > 10:
                role_list += "\n> ...and more"

            embed.add_field(
                name="Roles",
                value=role_list,
                inline=False,
            )

        await inter.followup.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(UserInfoCommand(bot))
